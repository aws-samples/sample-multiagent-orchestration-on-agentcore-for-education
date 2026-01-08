#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Sample: Multi-Agent Educational Assistant - Deployment Script
# This script automates the complete deployment of the AgentCore multi-agent system

set -e  # Exit on error

# Load environment variables from .env file first
if [ -f ".env" ]; then
    # Export variables from .env file
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    
    # Set AWS_DEFAULT_REGION from .env if AWS_REGION is defined
    if [ ! -z "$AWS_REGION" ]; then
        export AWS_DEFAULT_REGION=$AWS_REGION
        echo "🌍 Using AWS Region from .env: $AWS_REGION"
    fi
fi

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Banner
echo "=========================================="
echo "  Octank Edu Multi-Agent Orchestrator"
echo "  Deployment Script"
echo "=========================================="
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

if ! command_exists aws; then
    print_error "AWS CLI is not installed. Please install AWS CLI."
    exit 1
fi

if ! command_exists bedrock-agentcore; then
    print_warning "Bedrock AgentCore CLI is not installed. Installing..."
    pip install bedrock-agentcore
fi

print_success "All prerequisites are met."
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from .env.example..."
    cp .env.example .env
    print_warning "Please edit .env file with your configuration before continuing."
    read -p "Press Enter to continue after editing .env file..."
fi

# Check if knowledge base helper exists
if [ ! -f "knowledge_base_helper.py" ]; then
    print_error "knowledge_base_helper.py not found. This file is required for Knowledge Base deployment."
    exit 1
fi

# Check if knowledge base documents directory exists
if [ ! -d "utils/knowledge_base_docs" ]; then
    print_warning "utils/knowledge_base_docs directory not found. Creating empty directory..."
    mkdir -p utils/knowledge_base_docs
    print_warning "Please add your knowledge base documents (.txt files) to utils/knowledge_base_docs/"
fi

# Check if Lambda deployment script exists
if [ ! -f "src/lambda_sns_eum/update_lambda_env.sh" ]; then
    print_error "src/lambda_sns_eum/update_lambda_env.sh not found. This file is required for Lambda deployment."
    exit 1
fi

# Make sure Lambda deployment script is executable
chmod +x src/lambda_sns_eum/update_lambda_env.sh

# Get AWS account and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

print_info "AWS Account ID: $AWS_ACCOUNT_ID"
print_info "AWS Region: $AWS_REGION"

# Check if demo phone numbers are configured
if [ -z "$DEMO_ADMIN_PHONE" ] || [ -z "$DEMO_PROFESSOR_PHONE" ] || [ -z "$DEMO_STUDENT_PHONE" ]; then
    print_warning "Demo phone numbers not configured in .env file."
    print_warning "Please add DEMO_ADMIN_PHONE, DEMO_PROFESSOR_PHONE, and DEMO_STUDENT_PHONE"
    print_warning "Default phone numbers will be used for demo users."
fi
echo ""

# Step 1: Deploy Knowledge Base
print_info "Step 1/4: Deploying Knowledge Base..."
python3 deploy_knowledge_base.py

if [ $? -eq 0 ]; then
    print_success "Knowledge Base deployed successfully"
else
    print_error "Failed to deploy Knowledge Base"
    exit 1
fi
echo ""

# Wait for knowledge base to be ready
print_info "Waiting for knowledge base to be ready..."
sleep 10

# Step 2: Deploy AgentCore Memory
print_info "Step 2/4: Deploying AgentCore Memory..."
python3 deploy_agentcore_memory.py

if [ $? -eq 0 ]; then
    print_success "AgentCore Memory deployed successfully"
else
    print_error "Failed to deploy AgentCore Memory"
    exit 1
fi
echo ""

# Wait for memory to be ready
print_info "Waiting for memory to be ready..."
sleep 5

# Step 3: Deploy AgentCore Gateway
print_info "Step 3/4: Deploying AgentCore Gateway..."
python3 deploy_agentcore_gateway.py

if [ $? -eq 0 ]; then
    print_success "AgentCore Gateway deployed successfully"
else
    print_error "Failed to deploy AgentCore Gateway"
    exit 1
fi
echo ""

# Wait for gateway to be ready
print_info "Waiting for gateway to be ready..."
sleep 10

# Step 4: Deploy AgentCore Runtime
print_info "Step 4/6: Deploying AgentCore Runtime..."
python3 deploy_agentcore_runtime_with_gw.py

if [ $? -eq 0 ]; then
    print_success "AgentCore Runtime deployed successfully"
else
    print_error "Failed to deploy AgentCore Runtime"
    exit 1
fi
echo ""

# Wait for runtime to be ready
print_info "Waiting for AgentCore Runtime to be ready..."
sleep 15

# Step 5: Deploy Cognito User Pool
print_info "Step 5/6: Deploying Cognito User Pool..."
python3 deploy_cognito_user_pool.py

if [ $? -eq 0 ]; then
    print_success "Cognito User Pool deployed successfully"
else
    print_error "Failed to deploy Cognito User Pool"
    exit 1
fi
echo ""

# Wait for user pool to be ready
print_info "Waiting for Cognito User Pool to be ready..."
sleep 5

# Step 6: Deploy Lambda Functions
print_info "Step 6/6: Deploying Lambda Functions..."

# Deploy WhatsApp SNS Handler Lambda
print_info "Deploying WhatsApp SNS Handler Lambda..."
cd src/lambda_sns_eum
./update_lambda_env.sh

if [ $? -eq 0 ]; then
    print_success "WhatsApp SNS Handler Lambda deployed successfully"
else
    print_error "Failed to deploy WhatsApp SNS Handler Lambda"
    cd ../..
    exit 1
fi

# Return to root directory
cd ../..
echo ""

# Deployment summary
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
print_success "All components have been deployed successfully."
echo ""
print_info "Deployment Summary:"
echo "  - Knowledge Base: Deployed"
echo "  - AgentCore Memory: Deployed"
echo "  - AgentCore Gateway: Deployed"
echo "  - AgentCore Runtime: Deployed"
echo "  - Cognito User Pool: Deployed"
echo "  - Lambda Functions: Deployed"
echo ""
print_info "🎯 System Ready for Testing:"
echo "  1. WhatsApp integration is configured"
echo "  2. Demo users are created in Cognito"
echo "  3. AgentCore Runtime is running"
echo "  4. Knowledge Base is populated"
echo ""
print_info "📱 Demo Users for WhatsApp Testing:"
echo "  - Administrator: ${DEMO_ADMIN_PHONE:-+5511987654321}"
echo "  - Professor: ${DEMO_PROFESSOR_PHONE:-+551146731805}"
echo "  - Student: ${DEMO_STUDENT_PHONE:-+5511123456789}"
echo ""
print_info "🔑 Demo Password: OctankDemo123!"
echo ""
print_info "Next Steps:"
echo "  1. Test WhatsApp integration with demo phone numbers"
echo "  2. View logs in CloudWatch"
echo "  3. Monitor in AWS Console"
echo "  4. Test agent using: python3 tests/invoke_agent.py"
echo ""
print_info "To clean up resources, run: ./scripts/cleanup.sh"
echo ""
