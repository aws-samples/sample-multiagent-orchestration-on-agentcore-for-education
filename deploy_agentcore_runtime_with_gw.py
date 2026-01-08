#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Deploy AgentCore Runtime with Gateway Integration.

This script deploys the multi-agent educational system to Amazon Bedrock AgentCore Runtime
with MCP Gateway integration for tool access.
"""

from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
import utils
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

boto_session = Session()
region = boto_session.region_name
agentcore_gateway_iam_role = utils.create_agentcore_role("lambdagateway")

print(f"current region: {region}")
account_id = boto_session.client("sts").get_caller_identity()["Account"]
print(f"current account: {account_id}")

# Get MEMORY_ID from environment
memory_id = os.getenv("MEMORY_ID")
if not memory_id:
    raise ValueError("MEMORY_ID not found in environment variables. Please set it in .env file")

# Get WhatsApp configuration from environment
whatsapp_phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "phone-number-id-fe268d418d9b4e1296c47f86795987df")

print(f"Using MEMORY_ID: {memory_id}")
print(f"Using WHATSAPP_PHONE_NUMBER_ID: {whatsapp_phone_number_id}")


agentcore_runtime = Runtime()
agent_name = "Octank_edu_assistant"
response = agentcore_runtime.configure(
    entrypoint="src/agents/orchestrator_agentcore_runtime_gateway.py",
    execution_role=agentcore_gateway_iam_role['Role']['Arn'],
    auto_create_ecr=True,
    requirements_file="requirements.txt",
    region=region,
    agent_name=agent_name
)
print("✅ Configuration successful!")
print(response)
print()

print("🚀 Launching agent...")
# Pass environment variables to the runtime
env_vars = {
    "MEMORY_ID": memory_id,
    "WHATSAPP_PHONE_NUMBER_ID": whatsapp_phone_number_id
}
launch_result = agentcore_runtime.launch(
    auto_update_on_conflict=True,
    env_vars=env_vars
)
print()
print("✅ Launch successful!")
print("🔍 Debug - launch_result structure:")
print(f"Type: {type(launch_result)}")
print("Full response:")
print(launch_result)

# Save agent ID
if hasattr(launch_result, 'agent_id'):
    agent_id = launch_result.agent_id
    os.makedirs("deployment", exist_ok=True)  # Criar diretório se não existir
    with open("deployment/agent_id.txt", "w") as f:
        f.write(agent_id)
    print(f"\n📝 Agent ID saved: {agent_id}")

# Save Agent Runtime ARN to .env file
if hasattr(launch_result, 'agent_arn'):
    agent_runtime_arn = launch_result.agent_arn
    print(f"🎯 Found Agent ARN: {agent_runtime_arn}")
    
    # Update .env file
    env_file_path = '.env'
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            lines = f.readlines()
        
        # Update AGENT_RUNTIME_ARN line
        updated_lines = []
        arn_updated = False
        
        for line in lines:
            if line.startswith('AGENT_RUNTIME_ARN'):
                updated_lines.append(f'AGENT_RUNTIME_ARN={agent_runtime_arn}\n')
                arn_updated = True
            else:
                updated_lines.append(line)
        
        # Add AGENT_RUNTIME_ARN if not found
        if not arn_updated:
            updated_lines.append(f'AGENT_RUNTIME_ARN={agent_runtime_arn}\n')
        
        # Write back to .env file
        with open(env_file_path, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ .env file updated with AGENT_RUNTIME_ARN: {agent_runtime_arn}")
    else:
        print("⚠️ .env file not found, please add AGENT_RUNTIME_ARN manually")
else:
    print("❌ Agent Runtime ARN not found in launch_result")
    print("Available attributes:", [attr for attr in dir(launch_result) if not attr.startswith('_')])