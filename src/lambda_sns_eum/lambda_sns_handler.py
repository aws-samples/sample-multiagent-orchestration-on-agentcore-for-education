"""
Lambda Function: WhatsApp SNS Handler

Recebe eventos SNS do End User Messaging Social (mensagens do WhatsApp)
e invoca o AgentCore Runtime orchestrator.
"""
import boto3
import json
import os

# Get AWS region from environment (with fallback)
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize clients
agent_core_client = boto3.client('bedrock-agentcore', region_name=AWS_REGION)
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)

# Configuration from environment variables (required)
AGENT_RUNTIME_ARN = os.environ.get('AGENT_RUNTIME_ARN')
if not AGENT_RUNTIME_ARN:
    raise Exception("AGENT_RUNTIME_ARN environment variable is required")

USER_POOL_ID = os.environ.get('USER_POOL_ID')
if not USER_POOL_ID:
    raise Exception("USER_POOL_ID environment variable is required")

WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
if not WHATSAPP_PHONE_NUMBER_ID:
    raise Exception("WHATSAPP_PHONE_NUMBER_ID environment variable is required")

def markAsRead(msg_id):
    """
    Marca mensagem como lida no WhatsApp
    """
    try:
        print(f"📖 Marcando mensagem como lida: {msg_id}")
        
        # Inicializar cliente do End User Messaging Social
        socialmessaging_client = boto3.client('socialmessaging', region_name=AWS_REGION)
        
        # Preparar payload para marcar como lida
        meta_message = {
            "messaging_product": "whatsapp",
            "message_id": msg_id,
            "status": "read"
        }
        
        # Enviar confirmação de leitura
        response = socialmessaging_client.send_whatsapp_message(
            originationPhoneNumberId=WHATSAPP_PHONE_NUMBER_ID,
            metaApiVersion='v20.0',
            message=json.dumps(meta_message)
        )
        
        print(f"✅ Mensagem marcada como lida: {msg_id}")
        return response
        
    except Exception as e:
        print(f"❌ Erro ao marcar mensagem como lida: {str(e)}")
        # Não falhar o processamento se não conseguir marcar como lida
        return None

def get_user_persona_by_phone(phone_number):
    """
    Busca a persona do usuário no Cognito User Pool usando o número de telefone.
    
    Args:
        phone_number (str): Número de telefone do usuário (com ou sem +)
    
    Returns:
        str: Persona do usuário ('student', 'professor', 'administrator') ou 'student' como padrão
    """
    try:
        # Normalizar o número de telefone para o formato usado no Cognito
        # Garantir que tenha o '+' no início
        if not phone_number.startswith('+'):
            phone_number = f'+{phone_number}'
        
        print(f"🔍 Buscando usuário com telefone: {phone_number}")
        
        # Listar todos os usuários da User Pool
        # Nota: Para otimização em produção, considere usar filtros ou indexação
        paginator = cognito_client.get_paginator('list_users')
        
        for page in paginator.paginate(UserPoolId=USER_POOL_ID):
            for user in page['Users']:
                # Verificar se o usuário tem o atributo phone_number
                phone_attr = None
                persona_attr = None
                
                for attr in user.get('Attributes', []):
                    if attr['Name'] == 'phone_number':
                        phone_attr = attr['Value']
                    elif attr['Name'] == 'custom:persona':
                        persona_attr = attr['Value']
                
                # Comparar números de telefone
                if phone_attr and phone_attr == phone_number:
                    print(f"✅ Usuário encontrado: {user.get('Username', 'N/A')}")
                    print(f"📱 Telefone: {phone_attr}")
                    print(f"👤 Persona: {persona_attr}")
                    
                    # Retornar a persona encontrada ou 'student' como padrão
                    return persona_attr if persona_attr else 'student'
        
        print(f"⚠️ Usuário não encontrado para o telefone: {phone_number}")
        return 'student'  # Persona padrão
        
    except Exception as e:
        print(f"❌ Erro ao buscar usuário no Cognito: {str(e)}")
        import traceback
        traceback.print_exc()
        return 'student'  # Persona padrão em caso de erro


def lambda_handler(event, context):
    """
    Lambda function que recebe eventos SNS do End User Messaging Social
    e invoca o AgentCore Runtime orchestrator.
    
    Event format:
    {
        "Records": [{
            "Sns": {
                "Message": "{...JSON do End User Messaging Social...}"
            }
        }]
    }
    """
    print(f"📨 Evento SNS recebido")
    print(f"📨 Número de records: {len(event.get('Records', []))}")
    
    try:
        # Parse SNS message
        for record in event['Records']:
            sns_message = json.loads(record['Sns']['Message'])
            
            print(f"📨 SNS Message: {json.dumps(sns_message, indent=2)}")
            
            # Extract WhatsApp webhook entry
            whatsapp_entry_str = sns_message.get('whatsAppWebhookEntry', '{}')
            whatsapp_entry = json.loads(whatsapp_entry_str)
            
            print(f"📱 WhatsApp Entry: {json.dumps(whatsapp_entry, indent=2)}")
            
            # Extract message details
            changes = whatsapp_entry.get('changes', [])
            if not changes:
                print("⚠️ Nenhuma mudança encontrada no evento")
                continue
            
            value = changes[0].get('value', {})
            
            # Check if this is a message status update (skip these)
            if 'statuses' in value:
                print("ℹ️ Status update recebido, ignorando...")
                continue
            
            messages = value.get('messages', [])
            
            if not messages:
                print("⚠️ Nenhuma mensagem encontrada no evento")
                continue
            
            # Get first message
            message = messages[0]
            message_type = message.get('type', 'text')
            sender_phone = message.get('from', '')
            message_id = message.get('id', '')
            
            # Marcar mensagem como lida imediatamente
            markAsRead(message_id)
            
            # Extract message content based on type
            if message_type == 'text':
                user_message = message.get('text', {}).get('body', '')
            elif message_type == 'image':
                user_message = "[Usuário enviou uma imagem]"
            elif message_type == 'audio':
                user_message = "[Usuário enviou um áudio]"
            elif message_type == 'video':
                user_message = "[Usuário enviou um vídeo]"
            elif message_type == 'document':
                user_message = "[Usuário enviou um documento]"
            else:
                user_message = f"[Usuário enviou {message_type}]"
            
            # Get contact info
            contacts = value.get('contacts', [])
            user_name = contacts[0].get('profile', {}).get('name', 'Usuário') if contacts else 'Usuário'
            
            print(f"📱 Mensagem de: {user_name} ({sender_phone})")
            print(f"💬 Tipo: {message_type}")
            print(f"💬 Conteúdo: {user_message}")
            
            # Buscar persona do usuário no Cognito
            user_persona = get_user_persona_by_phone(sender_phone)
            
            # Mapear "professor" para "teacher" para compatibilidade com AgentCore
            if user_persona == "professor":
                user_persona = "teacher"
            
            print(f"👤 Persona identificada: {user_persona}")
            
            # Confirmação de leitura já foi enviada via markAsRead()
            # Não é necessário enviar mensagem de ACK adicional
            # Generate session ID (use phone number as base for continuity)
            # Session ID precisa ter no mínimo 33 caracteres
            # Remove '+' do número pois AgentCore Memory não aceita
            clean_phone = sender_phone.replace('+', '').replace('-', '').replace(' ', '')
            
            # Usar hash do número para manter consistência entre sessões do mesmo usuário
            import hashlib
            from datetime import datetime
            
            phone_hash = hashlib.sha256(sender_phone.encode()).hexdigest()
            
            # Gerar timestamp por hora (YYYY-MM-DD-HH) para renovar sessão a cada hora
            hour_timestamp = datetime.utcnow().strftime('%Y-%m-%d-%H')
            
            session_id = f"whatsapp-{clean_phone}-{hour_timestamp}-{phone_hash[:8]}"
            
            # Prepare payload for AgentCore Runtime
            payload = json.dumps({
                "inputText": user_message,
                "persona": user_persona,  # Persona obtida do Cognito
                "user_id": clean_phone,  # Sem '+' para AgentCore Memory
                "persona_id": clean_phone,
                # Adicionar contexto do WhatsApp para a tool send_whatsapp_message
                "whatsapp_phone_number": sender_phone  # Com '+' para enviar WhatsApp
            }).encode()
            
            print(f"🚀 Invocando AgentCore Runtime...")
            print(f"   Agent ARN: {AGENT_RUNTIME_ARN}")
            print(f"   Session ID: {session_id}")
            
            # Invoke AgentCore Runtime
            response = agent_core_client.invoke_agent_runtime(
                agentRuntimeArn=AGENT_RUNTIME_ARN,
                runtimeSessionId=session_id,
                payload=payload
            )
            
            print(f"✅ AgentCore Runtime invocado com sucesso")
            print(f"   Content Type: {response.get('contentType', 'unknown')}")
            
            # Process streaming response
            if "text/event-stream" in response.get("contentType", ""):
                content = []
                for line in response["response"].iter_lines(chunk_size=10):
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            line = line[6:]
                            content.append(line)
                
                agent_response = "\n".join(content)
                print(f"✅ Resposta do AgentCore (streaming): {agent_response[:200]}...")
                
            elif response.get("contentType") == "application/json":
                content = []
                for chunk in response.get("response", []):
                    content.append(chunk.decode('utf-8'))
                
                agent_response = json.loads(''.join(content))
                print(f"✅ Resposta do AgentCore (JSON): {agent_response}")
            
            # A resposta do agente já deve ter usado a tool send_whatsapp_message
            # para enviar a mensagem de volta ao WhatsApp
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Mensagem processada com sucesso'
            })
        }
    
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
