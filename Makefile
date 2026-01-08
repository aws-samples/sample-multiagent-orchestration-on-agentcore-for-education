.PHONY: help install setup deploy deploy-kb deploy-memory deploy-gateway deploy-runtime deploy-cognito deploy-lambda test test-coverage lint format clean cleanup demo check-env logs-runtime logs-lambda status

help:
	@echo "Octank Educational Multi-Agent System - Available Commands"
	@echo "============================================================"
	@echo ""
	@echo "🚀 DEPLOYMENT COMMANDS:"
	@echo "  deploy           - Complete automated deployment"
	@echo "  deploy-kb        - Deploy Knowledge Base only"
	@echo "  deploy-memory    - Deploy AgentCore Memory only"
	@echo "  deploy-gateway   - Deploy AgentCore Gateway only"
	@echo "  deploy-runtime   - Deploy AgentCore Runtime only"
	@echo "  deploy-cognito   - Deploy Cognito User Pool only"
	@echo "  deploy-lambda    - Deploy Lambda functions only"
	@echo ""
	@echo "🧹 CLEANUP COMMANDS:"
	@echo "  cleanup          - Remove all deployed resources"
	@echo "  clean            - Clean up local generated files"
	@echo ""
	@echo "🔧 DEVELOPMENT COMMANDS:"
	@echo "  install          - Install Python dependencies"
	@echo "  setup            - Setup development environment"
	@echo "  check-env        - Validate environment configuration"
	@echo ""
	@echo "🧪 TESTING COMMANDS:"
	@echo "  test             - Run unit tests"
	@echo "  test-coverage    - Run tests with coverage report"
	@echo "  demo             - Run demo agent invocation"
	@echo ""
	@echo "📝 CODE QUALITY COMMANDS:"
	@echo "  lint             - Run linting checks (ruff)"
	@echo "  format           - Format code (black)"

# =============================================================================
# DEPLOYMENT COMMANDS
# =============================================================================

deploy:
	@echo "🚀 Starting complete deployment..."
	./scripts/deploy.sh

deploy-kb:
	@echo "📚 Deploying Knowledge Base..."
	python3 deploy_knowledge_base.py

deploy-memory:
	@echo "🧠 Deploying AgentCore Memory..."
	python3 deploy_agentcore_memory.py

deploy-gateway:
	@echo "🌐 Deploying AgentCore Gateway..."
	python3 deploy_agentcore_gateway.py

deploy-runtime:
	@echo "⚡ Deploying AgentCore Runtime..."
	python3 deploy_agentcore_runtime_with_gw.py

deploy-cognito:
	@echo "👥 Deploying Cognito User Pool..."
	python3 deploy_cognito_user_pool.py

deploy-lambda:
	@echo "λ Deploying Lambda functions..."
	cd src/lambda_sns_eum && ./update_lambda_env.sh

# =============================================================================
# CLEANUP COMMANDS
# =============================================================================

cleanup:
	@echo "🧹 Cleaning up all deployed resources..."
	./scripts/cleanup.sh

clean:
	@echo "🧹 Cleaning up local files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.zip" -not -path "./venv/*" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/ .ruff_cache/

# =============================================================================
# DEVELOPMENT COMMANDS
# =============================================================================

install:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully"

setup: install check-env
	@echo "🔧 Setting up development environment..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env from template..."; \
		cp .env.example .env; \
		echo "⚠️  Please edit .env file with your configuration"; \
	fi
	@echo "✅ Development environment ready"

check-env:
	@echo "🔍 Checking environment configuration..."
	@python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); \
	required = ['AWS_REGION', 'DEMO_ADMIN_PHONE', 'DEMO_PROFESSOR_PHONE', 'DEMO_STUDENT_PHONE']; \
	missing = [v for v in required if not os.getenv(v)]; \
	print('✅ Environment configuration valid') if not missing else print(f'❌ Missing variables: {missing}') or exit(1)"

# =============================================================================
# TESTING COMMANDS
# =============================================================================

test:
	@echo "🧪 Running unit tests..."
	pytest tests/ -v

test-coverage:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=src --cov-report=html --cov-report=term tests/
	@echo "📊 Coverage report generated in htmlcov/"

demo:
	@echo "🎮 Running demo agent invocation..."
	python3 tests/invoke_agent.py

# =============================================================================
# CODE QUALITY COMMANDS
# =============================================================================

lint:
	@echo "🔍 Running linting checks..."
	ruff check src/ tests/ *.py

format:
	@echo "✨ Formatting code..."
	black src/ tests/ *.py --line-length 100
	@echo "✅ Code formatted successfully"

# =============================================================================
# UTILITY COMMANDS
# =============================================================================

logs-runtime:
	@echo "📋 Showing AgentCore Runtime logs..."
	@RUNTIME_ID=$$(aws ssm get-parameter --name "/app/octank_edu_multi_agent/runtime_id" --query 'Parameter.Value' --output text 2>/dev/null || echo ""); \
	if [ -n "$$RUNTIME_ID" ]; then \
		aws logs tail /aws/bedrock-agentcore/runtimes/$$RUNTIME_ID --follow; \
	else \
		echo "❌ Runtime ID not found in SSM"; \
	fi

logs-lambda:
	@echo "📋 Showing Lambda logs..."
	aws logs tail /aws/lambda/octank-edu-whatsapp-sns-handler --follow

status:
	@echo "📊 Checking deployment status..."
	@echo "Memory ID: $$(aws ssm get-parameter --name "/app/octank_edu_multi_agent/memory_id" --query 'Parameter.Value' --output text 2>/dev/null || echo 'Not deployed')"
	@echo "Runtime ID: $$(aws ssm get-parameter --name "/app/octank_edu_multi_agent/runtime_id" --query 'Parameter.Value' --output text 2>/dev/null || echo 'Not deployed')"
	@echo "Gateway ID: $$(aws ssm get-parameter --name "/app/octank/agentcore/gatewayID" --query 'Parameter.Value' --output text 2>/dev/null || echo 'Not deployed')"
	@echo "KB ID: $$(aws ssm get-parameter --name "/app/octank_assistant/agentcore/kb_id" --query 'Parameter.Value' --output text 2>/dev/null || echo 'Not deployed')"
