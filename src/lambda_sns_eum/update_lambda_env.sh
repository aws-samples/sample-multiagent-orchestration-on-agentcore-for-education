#!/bin/bash

# Script para criar ou atualizar função Lambda usando valores do .env

set -e  # Exit on any error

FUNCTION_NAME="octank-edu-whatsapp-sns-handler"
ROLE_NAME="octank-edu-whatsapp-lambda-role"

echo "🔧 Configurando função Lambda: $FUNCTION_NAME"

# Verificar se arquivo .env existe
if [ ! -f "../../.env" ]; then
    echo "❌ Arquivo .env não encontrado em ../../.env"
    exit 1
fi

# Ler valores do arquivo .env
echo "📖 Carregando variáveis do arquivo .env..."
export $(cat ../../.env | grep -v '^#' | xargs)

# Verificar se variáveis obrigatórias estão definidas
if [ -z "$AWS_REGION" ] || [ -z "$AGENT_RUNTIME_ARN" ] || [ -z "$USER_POOL_ID" ] || [ -z "$WHATSAPP_PHONE_NUMBER_ID" ]; then
    echo "❌ Variáveis obrigatórias não encontradas no .env:"
    echo "   AWS_REGION: $AWS_REGION"
    echo "   AGENT_RUNTIME_ARN: $AGENT_RUNTIME_ARN"
    echo "   USER_POOL_ID: $USER_POOL_ID"
    echo "   WHATSAPP_PHONE_NUMBER_ID: $WHATSAPP_PHONE_NUMBER_ID"
    exit 1
fi

# Criar ZIP do código
echo "📦 Criando pacote de deployment..."
zip -q lambda_deployment.zip lambda_sns_handler.py

# Verificar se a função Lambda existe
echo "🔍 Verificando se função Lambda existe..."
if aws lambda get-function --function-name $FUNCTION_NAME >/dev/null 2>&1; then
    echo "✅ Função existe. Atualizando..."
    
    # Atualizar código
    echo "🚀 Atualizando código da função..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda_deployment.zip
    
    # Atualizar variáveis de ambiente
    echo "🔧 Atualizando variáveis de ambiente..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment "Variables={AGENT_RUNTIME_ARN=$AGENT_RUNTIME_ARN,USER_POOL_ID=$USER_POOL_ID,WHATSAPP_PHONE_NUMBER_ID=$WHATSAPP_PHONE_NUMBER_ID}"
    
    echo "✅ Função atualizada com sucesso!"
    
else
    echo "❌ Função não existe. Criando nova função..."
    
    # Obter ARN da role (assumindo que já existe)
    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>/dev/null || echo "")
    
    if [ -z "$ROLE_ARN" ]; then
        echo "❌ Role $ROLE_NAME não encontrada. Criando role..."
        
        # Criar role se não existir
        TRUST_POLICY='{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }'
        
        aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document "$TRUST_POLICY" \
            --description "Role for WhatsApp SNS Handler Lambda"
        
        # Anexar políticas básicas
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        
        # Criar política inline combinada para AgentCore, Cognito e Social Messaging
        COMBINED_POLICY='{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AgentCoreInvokeAccess",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:InvokeAgentRuntime"
                    ],
                    "Resource": "arn:aws:bedrock-agentcore:*:*:runtime/*"
                },
                {
                    "Sid": "CognitoUserPoolReadAccess",
                    "Effect": "Allow",
                    "Action": [
                        "cognito-idp:ListUsers"
                    ],
                    "Resource": "arn:aws:cognito-idp:*:*:userpool/*"
                },
                {
                    "Sid": "SocialMessagingAccess",
                    "Effect": "Allow",
                    "Action": [
                        "social-messaging:SendWhatsAppMessage",
                        "social-messaging:PostWhatsAppMessageMedia",
                        "social-messaging:GetWhatsAppMessageMedia"
                    ],
                    "Resource": "*"
                }
            ]
        }'
        
        aws iam put-role-policy \
            --role-name $ROLE_NAME \
            --policy-name "WhatsAppLambdaPolicy" \
            --policy-document "$COMBINED_POLICY"
        
        # Aguardar role ser criada
        echo "⏳ Aguardando role ser criada..."
        sleep 10
        
        ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
    fi
    
    echo "🚀 Criando função Lambda..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.12 \
        --role $ROLE_ARN \
        --handler lambda_sns_handler.lambda_handler \
        --zip-file fileb://lambda_deployment.zip \
        --description "Handles WhatsApp messages from SNS and invokes AgentCore Runtime" \
        --timeout 300 \
        --memory-size 512 \
        --environment "Variables={AGENT_RUNTIME_ARN=$AGENT_RUNTIME_ARN,USER_POOL_ID=$USER_POOL_ID,WHATSAPP_PHONE_NUMBER_ID=$WHATSAPP_PHONE_NUMBER_ID}"
    
    echo "✅ Função criada com sucesso!"
fi

# Mostrar configuração final
echo ""
echo "📋 Configuração da função:"
aws lambda get-function-configuration --function-name $FUNCTION_NAME --query '{
    FunctionName: FunctionName,
    Runtime: Runtime,
    Handler: Handler,
    Timeout: Timeout,
    MemorySize: MemorySize,
    Environment: Environment.Variables
}' --output table

echo ""
echo "✅ Deploy concluído com sucesso!"