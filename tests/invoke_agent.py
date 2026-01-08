#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Script para invocar o AgentCore Runtime e testar o orchestrator.

Usage:
    python3 tests/invoke_agent.py
    python3 tests/invoke_agent.py --persona student --query "What are my pending tasks?"
    python3 tests/invoke_agent.py --persona professor --query "Show my course metrics"

Payload Parameters:
    - inputText (required): User's query
    - persona (required): "student", "teacher", or "administrator"
    - user_id (required): Unique user identifier
    - persona_id (optional): Persona-specific ID (e.g., STU-001)
    - whatsapp_phone_number (optional): Phone number for WhatsApp integration
    - memory_id (optional): Memory ID (defaults to SSM parameter)
"""

import boto3
import json
import uuid
import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Invoke AgentCore Runtime for testing')
    parser.add_argument('--persona', 
                       choices=['student', 'teacher', 'professor', 'administrator'], 
                       default='student',
                       help='User persona (default: student)')
    parser.add_argument('--query', 
                       default='Olá! Por favor, liste todas as ferramentas (tools) que você tem disponíveis para usar. Descreva cada uma delas brevemente.',
                       help='Query to send to the agent')
    
    args = parser.parse_args()
    
    # Map professor to teacher for compatibility
    persona = 'teacher' if args.persona == 'professor' else args.persona
    
    # Get runtime ARN from environment or use default
    RUNTIME_ARN = os.getenv('AGENT_RUNTIME_ARN', 'arn:aws:bedrock-agentcore:us-east-1:831782568328:runtime/Octank_edu_assistant-iGSP5IGDGF')
    REGION = os.getenv('AWS_REGION', 'us-east-1')

    # Cliente do AgentCore
    client = boto3.client('bedrock-agentcore', region_name=REGION)

    print("🤖 Invocando o agente AgentCore...")
    print(f"📍 Runtime ARN: {RUNTIME_ARN}")
    print(f"👤 Persona: {args.persona}")
    print(f"💬 Query: {args.query}")
    print()

    try:
        # Gerar um session ID único (mínimo 33 caracteres)
        session_id = str(uuid.uuid4()) + str(uuid.uuid4())[:5]
        
        print(f"🔑 Session ID: {session_id}")
        print()
        
        # Generate persona-specific user details
        persona_configs = {
            'student': {
                'user_id': 'test_student_123',
                'persona_id': 'STU-001',
                'whatsapp_phone_number': '+5511123456789'
            },
            'teacher': {
                'user_id': 'test_teacher_456', 
                'persona_id': 'TEA-001',
                'whatsapp_phone_number': '+551146731805'
            },
            'administrator': {
                'user_id': 'test_admin_789',
                'persona_id': 'ADM-001', 
                'whatsapp_phone_number': '+5511987654321'
            }
        }
        
        config = persona_configs[persona]
        
        # Preparar o payload com todos os parâmetros necessários
        payload = json.dumps({
            "inputText": args.query,
            "persona": persona,
            "user_id": config['user_id'],
            "persona_id": config['persona_id'],
            "whatsapp_phone_number": config['whatsapp_phone_number']
        })
        
        # Invocar o agente
        response = client.invoke_agent_runtime(
            agentRuntimeArn=RUNTIME_ARN,
            runtimeSessionId=session_id,
            payload=payload,
            qualifier="DEFAULT"
        )
        
        print("✅ Resposta recebida!")
        print("=" * 80)
        
        # Ler a resposta
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        
        # Mostrar a resposta formatada
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
        print("=" * 80)
        print()
        print("✨ Invocação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao invocar o agente: {str(e)}")
        print(f"   Tipo: {type(e).__name__}")
        
        # Mostrar detalhes do erro se disponível
        if hasattr(e, 'response'):
            error_response = e.response
            if 'Error' in error_response:
                print(f"   Código: {error_response['Error'].get('Code', 'N/A')}")
                print(f"   Mensagem: {error_response['Error'].get('Message', 'N/A')}")
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
