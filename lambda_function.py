
import json
import os
import boto3
from botocore.exceptions import ClientError

WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')

def lambda_handler(event, context):
    """
    Lambda handler para enviar mensagens WhatsApp via AgentCore Gateway
    """
    print(f"📥 Event recebido: {json.dumps(event)}")
    
    # Extrai informações do contexto do Gateway
    client_context = context.client_context
    if client_context:
        custom = client_context.custom
        tool_name = custom.get('bedrockagentcoreToolName', 'unknown')
        session_id = custom.get('bedrockagentcoreSessionId', 'unknown')
        print(f"🔧 Tool: {tool_name}, Session: {session_id}")
    
    try:
        # Parse do input
        if isinstance(event, str):
            event = json.loads(event)
        
        phone_number = event.get('phone_number')
        message = event.get('message')
        
        if not phone_number or not message:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'phone_number e message são obrigatórios'
                })
            }
        
        # Limpa formato do número
        clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
        
        # Cliente AWS End User Messaging
        socialmessaging_client = boto3.client('socialmessaging', region_name='us-east-1')
        
        # Mensagem no formato WhatsApp API
        meta_message = {
            "messaging_product": "whatsapp",
            "to": f"+{clean_phone}",
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        print(f"📤 Enviando mensagem para +{clean_phone}...")
        
        response = socialmessaging_client.send_whatsapp_message(
            originationPhoneNumberId=WHATSAPP_PHONE_NUMBER_ID,
            message=json.dumps(meta_message),
            metaApiVersion='v20.0'
        )
        
        whatsapp_msg_id = response.get('messageId', '')
        
        print(f"✅ Mensagem enviada: {whatsapp_msg_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message_id': whatsapp_msg_id,
                'recipient': f"+{clean_phone}",
                'message_sent': message
            })
        }
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        
        print(f"❌ Erro AWS: {error_code} - {error_message}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f"{error_code}: {error_message}"
            })
        }
    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
