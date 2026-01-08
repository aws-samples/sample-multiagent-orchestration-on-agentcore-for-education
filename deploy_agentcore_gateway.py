import os
import boto3
import zipfile

boto_session = boto3.Session()
region = boto_session.region_name

import utils

#### Create ZIP file dynamically from lambda_function.py
def create_lambda_zip():
    """
    Cria lambda_function_code.zip com o código da Lambda
    """
    zip_filename = 'lambda_function_code.zip'
    
    # Remover ZIP existente se houver
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
        print(f"🗑️ {zip_filename} existente removido")
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Adicionar lambda_function.py ao ZIP
            if os.path.exists('lambda_function.py'):
                zipf.write('lambda_function.py', 'lambda_function.py')
                print("✅ lambda_function.py adicionado ao ZIP")
            else:
                raise FileNotFoundError("❌ Arquivo lambda_function.py não encontrado!")
            
            # Adicionar outros arquivos necessários se existirem
            additional_files = ['requirements.txt', 'utils.py']
            for file in additional_files:
                if os.path.exists(file):
                    zipf.write(file, file)
                    print(f"✅ {file} adicionado ao ZIP")
        
        print(f"📦 ZIP criado: {zip_filename}")
        return zip_filename
        
    except Exception as e:
        # Limpar arquivo em caso de erro
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
        raise e

# Criar ZIP dinamicamente
print("🚀 Criando lambda_function_code.zip dinamicamente...")
lambda_zip_path = create_lambda_zip()

#### Create AWS Lambda function using the dynamically created ZIP
lambda_resp = utils.create_gateway_lambda(lambda_zip_path)

if lambda_resp is not None:
    if lambda_resp['exit_code'] == 0:
        print("Lambda function created with ARN: ", lambda_resp['lambda_function_arn'])
    else:
        print("Lambda function creation failed with message: ", lambda_resp['lambda_function_arn'])


lambda_arn =  lambda_resp['lambda_function_arn']
#### Create an IAM role for the Gateway to assume
agentcore_gateway_iam_role = utils.create_agentcore_gateway_role("agentcore-lambdagateway")
print("Agentcore gateway role ARN: ", agentcore_gateway_iam_role['Role']['Arn'])


# Creating Cognito User Pool 
import os
import boto3
import requests
import time
from botocore.exceptions import ClientError

USER_POOL_NAME = "octank-gateway-pool"
RESOURCE_SERVER_ID = "octank-gateway-id"
RESOURCE_SERVER_NAME = "octank-gateway-name"
CLIENT_NAME = "octank-gateway-client"
SCOPES = [
    {"ScopeName": "gateway:read", "ScopeDescription": "Read access"},
    {"ScopeName": "gateway:write", "ScopeDescription": "Write access"}
]
scopeString = f"{RESOURCE_SERVER_ID}/gateway:read {RESOURCE_SERVER_ID}/gateway:write"
utils.put_ssm_parameter("/app/octank/agentcore/scope", scopeString)

cognito = boto3.client("cognito-idp", region_name=region)

print("Creating or retrieving Cognito resources...")
user_pool_id = utils.get_or_create_user_pool(cognito, USER_POOL_NAME)
print(f"User Pool ID: {user_pool_id}")
utils.put_ssm_parameter("/app/octank/agentcore/user_pool_id", user_pool_id)

utils.get_or_create_resource_server(cognito, user_pool_id, RESOURCE_SERVER_ID, RESOURCE_SERVER_NAME, SCOPES)
print("Resource server ensured.")

client_id, client_secret  = utils.get_or_create_m2m_client(cognito, user_pool_id, CLIENT_NAME, RESOURCE_SERVER_ID)
print(f"Client ID: {client_id}")
utils.put_ssm_parameter("/app/octank/agentcore/client_id", client_id)
utils.put_ssm_parameter("/app/octank/agentcore/client_secret", client_secret)

# Get discovery URL  
cognito_discovery_url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration'
print(cognito_discovery_url)

# CreateGateway with Cognito authorizer without CMK. Use the Cognito user pool created in the previous step
gateway_client = boto3.client('bedrock-agentcore-control', region_name = region)
auth_config = {
    "customJWTAuthorizer": { 
        "allowedClients": [client_id],  # Client MUST match with the ClientId configured in Cognito. Example: 7rfbikfsm51j2fpaggacgng84g
        "discoveryUrl": cognito_discovery_url
    }
}

gateway_name = 'octankforLambda'
try:
    create_response = gateway_client.create_gateway(
        name=gateway_name,
        roleArn=agentcore_gateway_iam_role['Role']['Arn'],
        protocolType='MCP',
        authorizerType='CUSTOM_JWT',
        authorizerConfiguration=auth_config,
        description='AgentCore Gateway with AWS Lambda target type'
    )
    print(create_response)
    # Retrieve the GatewayID used for GatewayTarget creation
    gatewayID = create_response["gatewayId"]
    gatewayURL = create_response["gatewayUrl"]
    print(gatewayID)
    utils.put_ssm_parameter("/app/octank/agentcore/gatewayID", gatewayID)
    utils.put_ssm_parameter("/app/octank/agentcore/gatewayURL", gatewayURL)
except gateway_client.exceptions.ConflictException:
    print(f"Gateway '{gateway_name}' already exists. Using existing gateway.")
    gatewayID = utils.get_ssm_parameter("/app/octank/agentcore/gatewayID")
    gatewayURL = utils.get_ssm_parameter("/app/octank/agentcore/gatewayURL")
# Replace the AWS Lambda function ARN below
print("O ARN é: " + lambda_arn)
#print("O ARN 2 é: " + lambda_resp)
lambda_target_config = {
    "mcp": {
        "lambda": {
            "lambdaArn": lambda_arn,  # String direta, não set
            "toolSchema": {
                "inlinePayload": [
                    {
                        "name": "send_whatsapp_message",
                        "description": "Envia mensagem de texto WhatsApp via AWS End User Messaging Social. Use esta ferramenta para enviar respostas aos usuários via WhatsApp.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "phone_number": {
                                    "type": "string",
                                    "description": "Número WhatsApp do destinatário (formato: +5511999999999)"
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Texto da mensagem a ser enviada"
                                }
                            },
                            "required": ["phone_number", "message"]
                        }
                    }
                ]
            }
        }
    }
}


credential_config = [ 
    {
        "credentialProviderType" : "GATEWAY_IAM_ROLE"
    }
]

# Adicionar timestamp para evitar conflitos de nome
import time
timestamp = int(time.time())
targetname = f'WppLambdaFunction-{timestamp}'

print(f"🎯 Creating gateway target: {targetname}")

try:
    response = gateway_client.create_gateway_target(
        gatewayIdentifier=gatewayID,
        name=targetname,
        description='Lambda Target using SDK',
        targetConfiguration=lambda_target_config,
        credentialProviderConfigurations=credential_config)
    
    print(f"✅ Gateway target created successfully: {targetname}")
    print(response)
    
except gateway_client.exceptions.ConflictException:
    print(f"⚠️ Target '{targetname}' already exists. Using existing target.")
except Exception as e:
    print(f"❌ Error creating gateway target: {e}")
    raise