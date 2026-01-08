#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Orchestrator Agent for AgentCore Runtime Deployment.

This module implements the orchestrator agent for deployment on Amazon Bedrock
AgentCore Runtime. It coordinates between five specialized sub-agents using the
"Agents as Tools" pattern and integrates with AgentCore Memory for conversation context.

Key Features:
- AgentCore Runtime entrypoint with @app.entrypoint decorator
- AgentCore Memory integration with session management
- Multi-agent coordination with specialized sub-agents
- Persona-based access control and data scoping
- SSM Parameter Store integration for configuration

Architecture:
- Orchestrator coordinates 5 specialized agents:
  1. Educational Assistant (student queries)
  2. Teacher Assistant (teacher queries)
  3. Financial Assistant (payment queries)
  4. Virtual Secretary (admin queries)
  5. General Questions (general queries)

Deployment:
- Deploy to AgentCore Runtime using bedrock-agentcore CLI
- Configure memory_id in SSM Parameter Store
- Invoke via AgentCore Runtime API with session management
"""

import os
import logging
import boto3
import sys
from pathlib import Path
from boto3 import Session
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
import uuid

# Load environment variables from .env file
from dotenv import load_dotenv

# Get the project root directory (2 levels up from this file)
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'

# Load .env file if it exists
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logging.info(f"Loaded environment variables from {env_path}")
else:
    logging.warning(f".env file not found at {env_path}")

# AgentCore imports
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager
)
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig
)

# Strands imports
from strands import Agent
from strands_tools import retrieve, calculator

# Add current directory to Python path for local imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import sub-agent tools (using local imports with path adjustment)
from educational_assistant_agent import answer_student_questions
from teacher_assistant_agent import answer_teacher_questions
from financial_assistant_agent import answer_payment_questions
from virtual_secretary_agent import answer_admin_questions
from general_questions_agent import answer_general_questions


#Gateway imports
import io
import time
import logging
import botocore
import json
import asyncio
from textwrap import dedent
from datetime import datetime, timedelta
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient
from strands import Agent, tool
from strands.models import BedrockModel

# Import utils from project root (2 levels up)
sys.path.insert(0, str(project_root))
import utils


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Set up logging for Strands components
loggers = [
    'strands',
    'strands.agent',
    'strands.tools',
    'strands.models',
    'strands.bedrock'
]

for logger_name in loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

# Main logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("orchestrator-runtime")

# ============================================================================
# AGENTCORE APP INITIALIZATION
# ============================================================================

app = BedrockAgentCoreApp()

# Model configuration
MODEL_ID = "openai.gpt-oss-20b-1:0"  # gptoss20b model

# Global variables for runtime state
memory_id_cache = None
memory_client_cache = None

# ============================================================================
# CONFIGURATION HELPERS
# ============================================================================

def get_memory_id_from_ssm(param_name: str = "/app/octank_edu_multi_agent/memory_id") -> str:
    """
    Retrieve memory_id from AWS Systems Manager Parameter Store.
    
    Args:
        param_name: SSM parameter name (default: /app/octank_edu_multi_agent/memory_id)
    
    Returns:
        Memory ID string
        
    Raises:
        Exception: If parameter cannot be retrieved
    """
    ssm = boto3.client("ssm")
    try:
        response = ssm.get_parameter(Name=param_name)
        memory_id = response["Parameter"]["Value"]
        logger.info(f"Retrieved memory_id from SSM: {memory_id}")
        return memory_id
    except ClientError as e:
        logger.error(f"Could not retrieve memory_id from SSM: {e}")
        raise Exception(f"Could not retrieve memory_id from SSM: {e}")


def get_memory_id(payload: Dict[str, Any]) -> str:
    """
    Get memory_id from payload or SSM Parameter Store.
    
    Priority:
    1. payload['memory_id'] - Direct from request
    2. SSM Parameter Store - Configured deployment value
    3. Environment variable - Fallback
    
    Args:
        payload: Request payload
        
    Returns:
        Memory ID string
        
    Raises:
        Exception: If memory_id cannot be determined
    """
    global memory_id_cache
    
    # Check payload first
    if "memory_id" in payload:
        memory_id = payload["memory_id"]
        logger.info(f"Using memory_id from payload: {memory_id}")
        return memory_id
    
    # Use cached value if available
    if memory_id_cache:
        logger.info(f"Using cached memory_id: {memory_id_cache}")
        return memory_id_cache
    
    # Try SSM Parameter Store
    try:
        memory_id_cache = get_memory_id_from_ssm()
        return memory_id_cache
    except Exception as e:
        logger.warning(f"Could not get memory_id from SSM: {e}")
    
    # Try environment variable as fallback
    memory_id = os.getenv("MEMORY_ID")
    if memory_id:
        logger.info(f"Using memory_id from environment: {memory_id}")
        memory_id_cache = memory_id
        return memory_id
    
    raise Exception(
        "memory_id is required but not found in payload, SSM, or environment. "
        "Please provide 'memory_id' in the request payload or configure it in SSM."
    )

def get_kb_id_from_ssm():
    param_name = '/app/octank_assistant/agentcore/kb_id'
    ssm = boto3.client("ssm")
    try:
        response = ssm.get_parameter(Name=param_name)
        kb_id = response["Parameter"]["Value"]
        logger.info(f"Mortgage Assistant runtime - get_kb_id_from_ssm kb_id: {kb_id}")
        return kb_id
    except ClientError as e:
        raise Exception(f"Could not retrieve kb_id from SSM: {e}")
        
# Get Cognito token
token = utils.get_cognito_token()

def create_streamable_http_transport():
    return streamablehttp_client(
        utils.get_ssm_parameter("/app/octank/agentcore/gatewayURL"),
        headers={"Authorization": f"Bearer {token}"}
    )

mcp_client = MCPClient(create_streamable_http_transport)

# ============================================================================
# ORCHESTRATOR AGENT CREATION
# ============================================================================

def create_orchestrator_agent_runtime(
    query: str,
    persona: str,
    session_manager: AgentCoreMemorySessionManager,
    persona_id: Optional[str] = None,
    whatsapp_phone_number: Optional[str] = None
) -> Any:
    """
    Create and invoke the orchestrator agent for runtime deployment.
    
    This function creates an orchestrator that coordinates between five specialized
    sub-agents using the "Agents as Tools" pattern. It integrates with AgentCore
    Memory for conversation context and implements persona-based access control.
    
    Args:
        query: User's question or request
        persona: User persona type - "student", "teacher", or "administrator"
        session_manager: AgentCore Memory session manager for context
        persona_id: Optional persona ID for personalized data
        whatsapp_phone_number: Optional WhatsApp phone number for message delivery
        
    Returns:
        Agent response object containing the orchestrated answer
        
    Raises:
        ValueError: If persona is invalid
    """
    # Validate persona
    valid_personas = ["student", "teacher", "administrator"]
    if persona not in valid_personas:
        raise ValueError(
            f"Invalid persona '{persona}'. Must be one of: {', '.join(valid_personas)}"
        )
    
    logger.info(f"Creating orchestrator agent - Persona: {persona}, Persona ID: {persona_id}")
    
    # Define orchestrator system prompt with memory awareness
    orchestrator_system_prompt = f"""You are an Educational System Orchestrator for the Octank Educational Multi-Agent System.

Your role is to analyze incoming queries, determine the appropriate specialized agent to handle them, 
and coordinate responses.

MEMORY SYSTEM - YOU HAVE ACCESS TO CONVERSATION HISTORY:
- You can remember what users told you in previous conversations
- When a user asks "What is my name?" - you should recall if they told you their name before
- When a user asks "What do I like to study?" - you should recall their preferences
- Use your memory to provide personalized, contextual responses
- Reference previous interactions naturally

CURRENT USER CONTEXT:
- Persona: {persona}
- Persona ID: {persona_id or 'Not specified'}
- Memory Enabled: Yes - Use it!

IMPORTANT: When invoking tools, you MUST pass the persona parameter to ensure proper access control.
- For answer_student_questions: Pass persona="{persona}" and student_id="{persona_id or ''}"
- For answer_teacher_questions: Pass persona="{persona}" and teacher_id="{persona_id or ''}"
- For answer_payment_questions: Pass persona="{persona}" and student_id="{persona_id or ''}"
- For answer_admin_questions: Pass persona="{persona}"
- For answer_general_questions: Pass persona="{persona}"

AVAILABLE SPECIALIZED AGENTS (as tools):

1. **answer_student_questions** - Educational Assistant Agent
   - Use for: Student academic queries about tasks, courses, grades, focus areas
   - Persona: Primarily for students
   - Examples: "What are my pending tasks?", "Show me my grades"

2. **answer_teacher_questions** - Teacher Assistant Agent
   - Use for: Teacher course management queries about metrics, student performance
   - Persona: Primarily for teachers
   - Examples: "Show my course metrics", "Who are my low-performing students?"

3. **answer_payment_questions** - Financial Assistant Agent
   - Use for: Payment and financial queries about tuition, receipts, payment status
   - Persona: Students or administrators
   - Examples: "What is my payment status?", "Process this receipt"

4. **answer_admin_questions** - Virtual Secretary Agent
   - Use for: Administrative operational queries about school-wide reports
   - Persona: Primarily for administrators
   - Examples: "Give me the operational report", "Show delinquent students"

5. **answer_general_questions** - General Questions Agent
   - Use for: General queries about policies, procedures, system usage
   - Persona: Any persona
   - Examples: "What is the grading scale?", "How do I enroll?"
   - FALLBACK: Use this when intent is unclear

ROUTING LOGIC:

Step 1: CHECK IF THIS IS A PERSONAL INFORMATION QUERY
Questions like:
- "What is my name?" / "Qual é o meu nome?"
- "What do I like to study?" / "O que eu gosto de estudar?"
- "When do I prefer to study?" / "Quando prefiro estudar?"
- "What did I tell you before?" / "O que eu disse antes?"

For these questions:
→ DO NOT USE TOOLS
→ Answer directly from your memory
→ Think: "The user is asking about something they told me before"
→ Your memory system will help you recall this information
→ If you remember, answer confidently
→ If you don't remember, say: "I don't recall you mentioning that. Could you tell me?"

Step 2: FOR SPECIALIZED DATA QUERIES, USE TOOLS
Questions like:
- "What are my pending tasks?" → Use answer_student_questions
- "Show my grades" → Use answer_student_questions
- "What is my payment status?" → Use answer_payment_questions
- "Show course metrics" → Use answer_teacher_questions
- "Generate operational report" → Use answer_admin_questions
- General system questions → Use answer_general_questions

Step 3: SYNTHESIZE AND RESPOND
- Provide clear, helpful answers
- Reference memory naturally
- Maintain conversational tone

PERSONA-BASED ACCESS CONTROL:
- Educational Assistant: Accessible by student and administrator personas
- Teacher Assistant: Accessible by teacher and administrator personas
- Financial Assistant: Accessible by all personas
- Virtual Secretary: Accessible ONLY by administrator persona
- General Questions: Accessible by all personas

CRITICAL - HOW TO USE MEMORY:
Your memory system automatically retrieves relevant information from past conversations.
When you receive a query, the system has already loaded relevant context from memory.

Examples of what you should remember:
- User's name (if they told you)
- User's study preferences (subjects they like, study times)
- Previous questions and answers
- User's goals and interests

When answering:
1. For personal questions ("What is my name?", "What do I like?"):
   - First, think: "Did the user tell me this before?"
   - Your memory will surface relevant past conversations
   - Answer based on what you remember
   - If you truly don't remember, say so politely

2. For specialized queries (grades, payments, etc.):
   - Use the appropriate tool
   - But still personalize based on memory

NEVER say "I don't have access" without first checking if you remember the information from past conversations.

IMPORTANT GUIDELINES:
- For personal information queries, answer directly from memory (no tools needed)
- For specialized data queries, use the appropriate tool
- ALWAYS pass the persona parameter when invoking tools
- ALWAYS pass the persona_id when available
- Use the most specific tool available for the query
- Respect persona-based access control
- Leverage memory to provide personalized experiences
- Be helpful, professional, and encouraging

WHATSAPP INTEGRATION:
- After generating your response, ALWAYS use send_whatsapp_message to send it to the user
- Extract the phone number from the context (it will be in whatsapp_phone_number field)
- Send your complete response as a WhatsApp message
- Example workflow:
  1. User asks: "Quais são minhas tarefas?"
  2. You call answer_student_questions to get the tasks
  3. You formulate a response: "Suas tarefas pendentes são: Matemática e História"
  4. You call send_whatsapp_message(phone_number="+5511999999999", message="Suas tarefas pendentes são: Matemática e História")

Your goal is to provide seamless coordination between specialized agents while maintaining
a unified, conversational experience with memory-enhanced personalization, and delivering
responses via WhatsApp.
"""
    
    # Register all sub-agent tools
    base_tools = [
        answer_student_questions,
        answer_teacher_questions,
        answer_payment_questions,
        answer_admin_questions,
        answer_general_questions,
        retrieve
        #send_whatsapp_message  # Tool para enviar mensagens no WhatsApp
    ]
    
    logger.info(f"Registered {len(base_tools)} base tools (5 sub-agents)")
    
    # Prepare contextualized query BEFORE creating the agent
    whatsapp_context = f", WhatsApp Phone={whatsapp_phone_number}" if whatsapp_phone_number else ""
    contextualized_query = f"""User Query: {query}

[Context: Persona={persona}, ID={persona_id or 'Not specified'}{whatsapp_context}]
"""
    
    logger.info(f"Processing query: {query[:100]}...")
    
    # Create and invoke orchestrator WITHIN MCP context
    with mcp_client:
        try:
            # Get MCP tools from Gateway
            mcp_tools = mcp_client.list_tools_sync()
            all_tools = base_tools + mcp_tools
            logger.info(f"Added {len(mcp_tools)} MCP tools from Gateway. Total tools: {len(all_tools)}")
            
            # Create orchestrator with all tools (base + MCP)
            orchestrator = Agent(
                model=MODEL_ID,
                system_prompt=orchestrator_system_prompt,
                tools=all_tools,
                session_manager=session_manager  # Enable memory
            )
            logger.info("Orchestrator agent created successfully with memory and MCP tools")
            
            # Invoke orchestrator (WITHIN MCP context)
            response = orchestrator(contextualized_query)
            logger.info("Orchestrator successfully processed query")
            
            return response
            
        except Exception as e:
            logger.error(f"Error with MCP tools: {str(e)}")
            logger.info("Falling back to base tools only")
            
            # Fallback: Create orchestrator without MCP tools
            orchestrator = Agent(
                model=MODEL_ID,
                system_prompt=orchestrator_system_prompt,
                tools=base_tools,
                session_manager=session_manager  # Enable memory
            )
            logger.info("Orchestrator agent created successfully with memory (fallback mode)")
            
            # Invoke orchestrator (fallback)
            response = orchestrator(contextualized_query)
            logger.info("Orchestrator successfully processed query (fallback)")
            
            return response


# ============================================================================
# AGENTCORE RUNTIME ENTRYPOINT
# ============================================================================

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for the orchestrator agent.
    
    This function is called by AgentCore Runtime when the agent is invoked.
    It handles request processing, memory integration, and response formatting.
    
    Payload Parameters:
        - inputText or prompt (required): User's query
        - persona (required): User persona - "student", "teacher", or "administrator"
        - user_id (required): Unique user identifier
        - persona_id (optional): Persona-specific ID (student_id, teacher_id, etc.)
        - memory_id (optional): Memory ID (can also be configured in SSM)
    
    Context Parameters:
        - session_id (required): Session identifier for conversation continuity
    
    Returns:
        Dictionary with 'result' key containing the agent's response message
        
    Raises:
        Exception: If required parameters are missing or processing fails
        
    Example Payload:
        {
            "inputText": "What are my pending tasks?",
            "persona": "student",
            "user_id": "user123",
            "persona_id": "STU-001",
            "memory_id": "OctankEduMultiAgentMemory-ABC123"
        }
    """
    global memory_id_cache
    global memory_client_cache
    global kb_id
    
    # Extract user message (support both 'inputText' and 'prompt' keys)
    user_message = payload.get("inputText") or payload.get("prompt")
    if not user_message:
        raise Exception("Payload must include 'inputText' or 'prompt' parameter")
    
    # Extract persona (required)
    persona = payload.get("persona")
    if not persona:
        raise Exception("Payload must include 'persona' parameter (student/teacher/administrator)")
    
    # Extract user_id (required)
    user_id = payload.get("user_id")
    if not user_id:
        raise Exception("Payload must include 'user_id' parameter")
    
    # Extract persona_id (optional)
    persona_id = payload.get("persona_id")
    
    # Extract WhatsApp phone number (optional, for WhatsApp integration)
    whatsapp_phone_number = payload.get("whatsapp_phone_number")
    
    # Extract session_id from context (required)
    session_id = context.session_id
    if not session_id:
        raise Exception("Context must include 'session_id'")
    
    # Get AWS region
    boto_session = Session()
    region = boto_session.region_name
    
    logger.info(f"Orchestrator Runtime - Entrypoint invoked")
    logger.info(f"Region: {region}")
    logger.info(f"User message: {user_message}")
    logger.info(f"Persona: {persona}")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Persona ID: {persona_id}")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"WhatsApp Phone: {whatsapp_phone_number}")
    
    # Get memory_id (from payload, SSM, or environment)
    try:
        memory_id = get_memory_id(payload)
        logger.info(f"Using memory_id: {memory_id}")
    except Exception as e:
        logger.error(f"Failed to get memory_id: {e}")
        raise
    
    # Initialize memory client if not already initialized
    if memory_client_cache is None:
        memory_client_cache = MemoryClient(region_name=region)
        logger.info("Memory client initialized")
    
    # Configure AgentCore Memory with leading slash
    # Pattern: /app_name/{actorId}/namespace
    # Using placeholders {actorId} and {sessionId}
    # Configure AgentCore Memory following official example (without leading slash)
    memory_config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=session_id,
        actor_id=user_id,
        retrieval_config={
            # Strategy 1: User preferences (long-term memory - cross-session)
            "/octank-edu/{actorId}/preferences": RetrievalConfig(
                top_k=5,
                relevance_score=0.7
            ),
            # Strategy 2: User facts (long-term memory - cross-session)
            "/octank-edu/{actorId}/facts": RetrievalConfig(
                top_k=5,
                relevance_score=0.7
            ),
            # Strategy 3: Current session (short-term memory)
            "/octank-edu/{actorId}/{sessionId}": RetrievalConfig(
                top_k=5,
                relevance_score=0.7
            )
        }
    )
    
    # Create AgentCore session manager
    session_manager = AgentCoreMemorySessionManager(
        memory_config,
        region_name=region
    )
    
    logger.info("AgentCore Memory session manager created")
    
    # Create and invoke orchestrator agent
    try:
        logger.info("Creating orchestrator agent")
        result = create_orchestrator_agent_runtime(
            query=user_message,
            persona=persona,
            session_manager=session_manager,
            persona_id=persona_id,
            whatsapp_phone_number=whatsapp_phone_number
        )
        
        # Extract message from result
        response_message = result.message if hasattr(result, 'message') else str(result)
        
        logger.info("Orchestrator successfully processed request")
        
        return {
            "result": response_message,
            "session_id": session_id,
            "persona": persona
        }
        
    except Exception as e:
        logger.error(f"Error in orchestrator processing: {str(e)}")
        raise


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Run the AgentCore Runtime application.
    
    This starts the AgentCore Runtime server that listens for invocations.
    The server handles request routing, session management, and response formatting.
    
    Deployment:
        1. Configure memory_id in SSM Parameter Store:
           aws ssm put-parameter --name /app/octank_edu_multi_agent/memory_id \
               --value "your-memory-id" --type String
        
        2. Deploy to AgentCore Runtime:
           bedrock-agentcore deploy --runtime-file orchestrator_agentcore_runtime.py
        
        3. Invoke via AgentCore Runtime API:
           POST /invoke
           {
               "inputText": "What are my pending tasks?",
               "persona": "student",
               "user_id": "user123",
               "persona_id": "STU-001"
           }
    """
    logger.info("Starting Orchestrator AgentCore Runtime application")
    app.run()
