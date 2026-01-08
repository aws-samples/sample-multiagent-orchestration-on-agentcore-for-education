#!/bin/bash

# Octank Edu Multi-Agent Orchestrator - Cleanup Script
# This script removes all deployed resources

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "=========================================="
echo "  Octank Edu Multi-Agent Orchestrator"
echo "  Cleanup Script"
echo "=========================================="
echo ""

print_warning "This script will delete all deployed resources."
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    print_info "Cleanup cancelled."
    exit 0
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

AWS_REGION=${AWS_REGION:-us-east-1}
print_info "AWS Region: $AWS_REGION"
echo ""

# Function to get SSM parameter
get_ssm_parameter() {
    aws ssm get-parameter --name "$1" --query 'Parameter.Value' --output text 2>/dev/null || echo ""
}

# Function to delete SSM parameter
delete_ssm_parameter() {
    local param_name=$1
    if aws ssm get-parameter --name "$param_name" >/dev/null 2>&1; then
        aws ssm delete-parameter --name "$param_name" >/dev/null 2>&1
        print_success "Deleted SSM parameter: $param_name"
    fi
}

# Step 1: Delete AgentCore Runtime
print_info "Step 1/8: Deleting AgentCore Runtime..."

RUNTIME_ID=$(get_ssm_parameter "/app/octank_edu_multi_agent/runtime_id")
if [ -n "$RUNTIME_ID" ]; then
    bedrock-agentcore delete-runtime --runtime-id "$RUNTIME_ID" 2>/dev/null || true
    print_success "AgentCore Runtime deleted"
else
    print_warning "Runtime ID not found in SSM"
fi
echo ""

# Step 2: Delete AgentCore Gateway
print_info "Step 2/8: Deleting AgentCore Gateway..."

GATEWAY_ID=$(get_ssm_parameter "/app/octank/agentcore/gatewayID")
if [ -n "$GATEWAY_ID" ]; then
    # Delete gateway targets first
    print_info "Deleting gateway targets..."
    TARGETS=$(aws bedrock-agentcore-control list-gateway-targets \
        --gateway-identifier "$GATEWAY_ID" \
        --query 'items[].targetId' \
        --output text 2>/dev/null || echo "")
    
    for target in $TARGETS; do
        aws bedrock-agentcore-control delete-gateway-target \
            --gateway-identifier "$GATEWAY_ID" \
            --target-id "$target" 2>/dev/null || true
        print_success "Deleted gateway target: $target"
    done
    
    # Delete gateway
    aws bedrock-agentcore-control delete-gateway \
        --gateway-identifier "$GATEWAY_ID" 2>/dev/null || true
    print_success "AgentCore Gateway deleted"
else
    print_warning "Gateway ID not found in SSM"
fi
echo ""

# Step 3: Delete Lambda Functions
print_info "Step 3/8: Deleting Lambda Functions..."

LAMBDA_FUNCTIONS=(
    "send_message_tool"
    "octank-edu-whatsapp-sns-handler"
    "octank-whatsapp-tool"
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    if aws lambda get-function --function-name "$func" >/dev/null 2>&1; then
        aws lambda delete-function --function-name "$func" 2>/dev/null || true
        print_success "Deleted Lambda function: $func"
    else
        print_info "Lambda function not found: $func"
    fi
done

# Delete Lambda IAM roles
LAMBDA_ROLES=(
    "octank-edu-whatsapp-lambda-role"
    "gateway_lambda_iamrole"
)

for role in "${LAMBDA_ROLES[@]}"; do
    if aws iam get-role --role-name "$role" >/dev/null 2>&1; then
        # Detach managed policies
        POLICIES=$(aws iam list-attached-role-policies \
            --role-name "$role" \
            --query 'AttachedPolicies[].PolicyArn' \
            --output text 2>/dev/null || echo "")
        
        for policy in $POLICIES; do
            aws iam detach-role-policy \
                --role-name "$role" \
                --policy-arn "$policy" 2>/dev/null || true
        done
        
        # Delete inline policies
        INLINE_POLICIES=$(aws iam list-role-policies \
            --role-name "$role" \
            --query 'PolicyNames' \
            --output text 2>/dev/null || echo "")
        
        for policy in $INLINE_POLICIES; do
            aws iam delete-role-policy \
                --role-name "$role" \
                --policy-name "$policy" 2>/dev/null || true
        done
        
        # Delete role
        aws iam delete-role --role-name "$role" 2>/dev/null || true
        print_success "Deleted Lambda IAM role: $role"
    fi
done
echo ""

# Step 4: Delete Cognito Resources
print_info "Step 4/8: Deleting Cognito Resources..."

# Check for User Pool ID in environment variables first (from our deployment)
USER_POOL_ID=${USER_POOL_ID:-$(get_ssm_parameter "/app/octank/agentcore/user_pool_id")}

# Also check for OctankEduMultiAgentPool by name
if [ -z "$USER_POOL_ID" ]; then
    USER_POOL_ID=$(aws cognito-idp list-user-pools --max-results 60 \
        --query 'UserPools[?Name==`OctankEduMultiAgentPool`].Id' \
        --output text 2>/dev/null || echo "")
fi

if [ -n "$USER_POOL_ID" ] && [ "$USER_POOL_ID" != "None" ]; then
    print_info "Found User Pool ID: $USER_POOL_ID"
    # Delete app clients
    print_info "Deleting Cognito app clients..."
    CLIENTS=$(aws cognito-idp list-user-pool-clients \
        --user-pool-id "$USER_POOL_ID" \
        --query 'UserPoolClients[].ClientId' \
        --output text 2>/dev/null || echo "")
    
    for client in $CLIENTS; do
        aws cognito-idp delete-user-pool-client \
            --user-pool-id "$USER_POOL_ID" \
            --client-id "$client" 2>/dev/null || true
        print_success "Deleted Cognito client: $client"
    done
    
    # Delete resource servers
    print_info "Deleting Cognito resource servers..."
    RESOURCE_SERVERS=$(aws cognito-idp list-resource-servers \
        --user-pool-id "$USER_POOL_ID" \
        --query 'ResourceServers[].Identifier' \
        --output text 2>/dev/null || echo "")
    
    for server in $RESOURCE_SERVERS; do
        aws cognito-idp delete-resource-server \
            --user-pool-id "$USER_POOL_ID" \
            --identifier "$server" 2>/dev/null || true
        print_success "Deleted resource server: $server"
    done
    
    # Delete domain
    DOMAIN=$(aws cognito-idp describe-user-pool \
        --user-pool-id "$USER_POOL_ID" \
        --query 'UserPool.Domain' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "None" ]; then
        aws cognito-idp delete-user-pool-domain \
            --user-pool-id "$USER_POOL_ID" \
            --domain "$DOMAIN" 2>/dev/null || true
        print_success "Deleted Cognito domain: $DOMAIN"
    fi
    
    # Delete user pool
    aws cognito-idp delete-user-pool --user-pool-id "$USER_POOL_ID" 2>/dev/null || true
    print_success "Deleted Cognito User Pool"
else
    print_warning "User Pool ID not found in SSM"
fi
echo ""

# Step 5: Delete IAM Roles
print_info "Step 5/8: Deleting IAM Roles..."

IAM_ROLES=(
    "agentcore-orchestrator-role"
    "agentcore-lambdagateway-role"
    "gateway_lambda_iamrole"
)

for role in "${IAM_ROLES[@]}"; do
    if aws iam get-role --role-name "$role" >/dev/null 2>&1; then
        # Detach managed policies
        POLICIES=$(aws iam list-attached-role-policies \
            --role-name "$role" \
            --query 'AttachedPolicies[].PolicyArn' \
            --output text 2>/dev/null || echo "")
        
        for policy in $POLICIES; do
            aws iam detach-role-policy \
                --role-name "$role" \
                --policy-arn "$policy" 2>/dev/null || true
        done
        
        # Delete inline policies
        INLINE_POLICIES=$(aws iam list-role-policies \
            --role-name "$role" \
            --query 'PolicyNames' \
            --output text 2>/dev/null || echo "")
        
        for policy in $INLINE_POLICIES; do
            aws iam delete-role-policy \
                --role-name "$role" \
                --policy-name "$policy" 2>/dev/null || true
        done
        
        # Delete role
        aws iam delete-role --role-name "$role" 2>/dev/null || true
        print_success "Deleted IAM role: $role"
    fi
done
echo ""

# Step 6: Delete Knowledge Base and S3 Resources
print_info "Step 6/8: Deleting Knowledge Base and S3 Resources..."

# Delete Knowledge Base
KB_ID=$(get_ssm_parameter "/app/octank_assistant/agentcore/kb_id")
if [ -n "$KB_ID" ]; then
    # Get data sources first
    DATA_SOURCES=$(aws bedrock-agent list-data-sources \
        --knowledge-base-id "$KB_ID" \
        --query 'dataSourceSummaries[].dataSourceId' \
        --output text 2>/dev/null || echo "")
    
    # Delete data sources
    for ds_id in $DATA_SOURCES; do
        aws bedrock-agent delete-data-source \
            --knowledge-base-id "$KB_ID" \
            --data-source-id "$ds_id" 2>/dev/null || true
        print_success "Deleted data source: $ds_id"
    done
    
    # Delete knowledge base
    aws bedrock-agent delete-knowledge-base \
        --knowledge-base-id "$KB_ID" 2>/dev/null || true
    print_success "Knowledge Base deleted"
else
    print_warning "Knowledge Base ID not found in SSM"
fi

# Delete S3 bucket
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
if [ -n "$AWS_ACCOUNT_ID" ]; then
    BUCKET_NAME="agentcore-workshop-${AWS_REGION}-${AWS_ACCOUNT_ID}"
    
    if aws s3api head-bucket --bucket "$BUCKET_NAME" >/dev/null 2>&1; then
        # Empty bucket first
        aws s3 rm "s3://$BUCKET_NAME" --recursive 2>/dev/null || true
        # Delete bucket
        aws s3api delete-bucket --bucket "$BUCKET_NAME" 2>/dev/null || true
        print_success "Deleted S3 bucket: $BUCKET_NAME"
    fi
fi
echo ""

# Step 7: Delete AgentCore Memory
print_info "Step 7/8: Deleting AgentCore Memory..."

# Try multiple possible memory ID locations
MEMORY_ID=$(get_ssm_parameter "/app/octankedu/agentcore/memory_id")
if [ -z "$MEMORY_ID" ]; then
    MEMORY_ID=$(get_ssm_parameter "/app/octank_edu_assistant/agentcore/memory_id")
fi
if [ -z "$MEMORY_ID" ]; then
    MEMORY_ID=$(get_ssm_parameter "/app/octank_edu_memory/agentcore/memory_id")
fi

if [ -n "$MEMORY_ID" ]; then
    # Clean up the memory ID (remove any formatting issues)
    MEMORY_ID=$(echo "$MEMORY_ID" | tr -d ' \n\r')
    print_info "Found Memory ID: $MEMORY_ID"
    aws bedrock-agentcore-control delete-memory \
        --memory-identifier "$MEMORY_ID" 2>/dev/null || true
    print_success "AgentCore Memory deleted"
else
    print_warning "Memory ID not found in any SSM parameter"
fi
echo ""

# Step 8: Delete SSM Parameters
print_info "Step 8/8: Deleting SSM Parameters..."

SSM_PARAMETERS=(
    "/app/octankedu/agentcore/memory_id"
    "/app/octank_edu_assistant/agentcore/memory_id"
    "/app/octank_edu_memory/agentcore/memory_id"
    "/app/octank_edu_multi_agent/memory_id"
    "/app/octank_edu_multi_agent/runtime_id"
    "/app/octank/agentcore/user_pool_id"
    "/app/octank/agentcore/client_id"
    "/app/octank/agentcore/client_secret"
    "/app/octank/agentcore/scope"
    "/app/octank/agentcore/gatewayID"
    "/app/octank/agentcore/gatewayURL"
    "/app/octank_assistant/agentcore/kb_id"
)

for param in "${SSM_PARAMETERS[@]}"; do
    delete_ssm_parameter "$param"
done
echo ""

# Cleanup summary
echo "=========================================="
echo "  Cleanup Complete!"
echo "=========================================="
echo ""
print_success "All resources have been deleted successfully."
echo ""
print_info "Cleanup Summary:"
echo "  - AgentCore Runtime: Deleted"
echo "  - AgentCore Gateway: Deleted"
echo "  - Lambda Functions: Deleted"
echo "  - Cognito User Pool: Deleted"
echo "  - IAM Roles: Deleted"
echo "  - Knowledge Base: Deleted"
echo "  - S3 Bucket: Deleted"
echo "  - AgentCore Memory: Deleted"
echo "  - SSM Parameters: Deleted"
echo ""
print_warning "Note: Some resources may take a few minutes to be fully deleted."
print_info "To redeploy the system, run: ./scripts/deploy.sh"
echo ""
