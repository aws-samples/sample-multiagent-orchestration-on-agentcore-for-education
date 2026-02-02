# Sample: Multi-Agent Educational Assistant with Amazon Bedrock AgentCore

This sample demonstrates how to build a sophisticated multi-agent educational system using **Amazon Bedrock AgentCore Runtime**. The system features specialized AI agents for student support, teacher assistance, financial management, and administrative operations, with optional WhatsApp integration via AWS End User Messaging Social.

> **🎯 PRIMARY FOCUS**: This sample demonstrates **Amazon Bedrock AgentCore** capabilities including multi-agent orchestration, memory management, and MCP tool integration. The WhatsApp integration is an **optional add-on** to showcase real-world messaging scenarios and is **not part of the core AgentCore demonstration**.

> **📱 WhatsApp Prerequisites**: The WhatsApp functionality requires pre-existing AWS End User Messaging Social and WhatsApp Business Account (WABA) setup, which is **outside the scope of this sample**. The core AgentCore system works fully without WhatsApp integration.

## ⚠️ Important Disclaimers

> **🚨 SAMPLE CODE ONLY**: This is a **demonstration and learning sample**. It is **NOT intended for production use** without significant modifications, security hardening, and proper testing.

> **🔒 SECURITY NOTICE**: This sample includes demo users with hardcoded passwords, simplified authentication, and basic error handling. **Do not deploy to production environments** without implementing proper security measures.

> **📚 EDUCATIONAL PURPOSE**: Use this sample to learn AgentCore concepts, architecture patterns, and integration techniques. Adapt and secure the code according to your production requirements.

## Architecture

![Architecture Diagram](static/Final_Agentcore_Demo-Art_of_Possible-Arquitetura.drawio.png)

The system follows a hub-and-spoke architecture where the orchestrator agent acts as the central coordinator, routing requests to specialized agents based on query intent and user persona.

### Key Components

1. **Orchestrator Agent** - Central coordinator that routes requests to specialized agents
2. **Specialized Agents** - Five domain-specific agents (Educational, Teacher, Financial, Secretary, General)
3. **AgentCore Memory** - Persistent conversation context and user preferences
4. **Knowledge Base** - Document retrieval for enhanced responses
5. **MCP Gateway** - Tool integration via Model Context Protocol
6. **WhatsApp Integration** (Optional) - Real-world messaging via AWS End User Messaging Social

## What You'll Learn

This sample demonstrates:

- **Multi-agent orchestration** using the "Agents as Tools" pattern
- **AgentCore Memory integration** for conversation persistence
- **Persona-based access control** and routing
- **Knowledge Base integration** for RAG (Retrieval Augmented Generation)
- **MCP (Model Context Protocol)** tool integration
- **AWS service integration** (Cognito, Lambda, S3, Systems Manager)
- **Optional WhatsApp messaging** via AWS End User Messaging Social

## Prerequisites

### AWS Account Requirements

- AWS Account with permissions for:
  - Amazon Bedrock (with model access to `openai.gpt-oss-20b-1:0`)
  - Amazon Bedrock AgentCore Runtime
  - AWS Lambda, Amazon Cognito, Amazon S3
  - AWS Systems Manager (Parameter Store)
  - AWS IAM

### System Requirements

- **Python**: 3.11 or higher
- **AWS CLI**: Latest version, configured with credentials
- **Operating System**: macOS, Linux, or Windows with WSL

### Required Tools

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Bedrock AgentCore starter toolkit
pip install bedrock-agentcore-starter-toolkit

# Install Python dependencies
pip install -r requirements.txt
```

### AWS Permissions

Your AWS user/role needs permissions for:
- Bedrock model invocation and AgentCore operations
- Lambda function creation and management
- Cognito User Pool management
- S3 bucket operations
- IAM role creation and policy attachment
- Systems Manager Parameter Store access

### Optional: WhatsApp Integration Requirements

**📱 OPTIONAL FEATURE**: The core AgentCore functionality works without WhatsApp. This integration is provided to demonstrate real-world messaging scenarios.

**⚠️ IMPORTANT**: For **optional** WhatsApp functionality, you must have the following configured **before** deploying this application:

#### 1. AWS End User Messaging Social Setup
- **Service**: AWS End User Messaging Social must be configured in your AWS account
- **Documentation**: [Getting Started with WhatsApp on AWS End User Messaging Social](https://docs.aws.amazon.com/social-messaging/latest/userguide/getting-started-whatsapp.html)
- **Requirements**:
  - End User Messaging Social service enabled in your AWS region
  - SNS topic configured for WhatsApp webhook events
  - Phone number registered and verified

#### 2. WhatsApp Business Account (WABA) Setup
- **Service**: WhatsApp Business Account must be configured and linked to AWS
- **Documentation**: [Managing WhatsApp Business Accounts](https://docs.aws.amazon.com/social-messaging/latest/userguide/managing-whatsapp-waba.html)
- **Requirements**:
  - Valid WhatsApp Business Account
  - Phone number verification completed
  - Business verification (if required)
  - WABA linked to AWS End User Messaging Social

#### 3. Configuration Parameters
After setting up the above services, you'll need these values for your `.env` file:
- `WHATSAPP_PHONE_NUMBER_ID`: Phone number ID from End User Messaging Social
- `END_USER_MESSAGING_TOPIC`: SNS Topic ARN for WhatsApp webhook events

**Note**: Without proper WABA and End User Messaging Social setup, the WhatsApp integration will not function. The core multi-agent system will still work via direct API calls, but WhatsApp messaging will fail.

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/aws-samples/sample-multiagent-orchestration-on-agentcore-for-education.git
cd sample-bedrock-agentcore-whatsapp-assistant

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your AWS configuration
```

### 2. Deploy with One Command

```bash
# Deploy entire system
./scripts/deploy.sh
```

This deploys:
1. Knowledge Base with document upload
2. AgentCore Memory for conversation context
3. AgentCore Gateway with MCP tools
4. AgentCore Runtime with all agents
5. Cognito User Pool with demo users
6. Lambda functions for WhatsApp integration (optional)

**Deployment time**: ~10-15 minutes

### 3. Test the System

```bash
# Test core AgentCore functionality
python3 tests/invoke_agent.py

# Test with different personas
python3 tests/invoke_agent.py --persona student --query "What are my pending tasks?"
python3 tests/invoke_agent.py --persona professor --query "Show my course metrics"
```

### 4. Optional: Test WhatsApp Integration

If you configured WhatsApp Business API:
- Send messages to your configured WhatsApp number from demo phones:
  - Administrator: +55119999999
  - Professor: +551199999999 
  - Student: +551199999999
### 5. Cleanup When Done

```bash
# Remove all deployed resources
./scripts/cleanup.sh
```

## Configuration

### Environment Variables

Edit `.env` file with your configuration:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# AgentCore Memory (auto-populated by deployment)
MEMORY_ID=OctankEduMultiAgentMemory-XXXXXXXXXX

# AgentCore Runtime (auto-populated by deployment)
USER_POOL_ID=us-east-1_XXXXXXXXX
AGENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:XXXXXXXXXXXX:runtime/octank_edu_orchestrator-XXXXXXXXXX

# Optional: WhatsApp Integration
WHATSAPP_PHONE_NUMBER_ID=phone-number-id-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
END_USER_MESSAGING_TOPIC=arn:aws:sns:us-east-1:XXXXXXXXXXXX:endUserMssTopic

# Demo Users (for testing)
DEMO_ADMIN_PHONE=+551199999999
DEMO_PROFESSOR_PHONE=+5511999999
DEMO_STUDENT_PHONE=+551110099999
```

### Knowledge Base Documents

Add educational documents to `utils/knowledge_base_docs/`:

```bash
mkdir -p utils/knowledge_base_docs
# Add .txt files with educational content
# Examples: course_catalog.txt, policies.txt, procedures.txt
```

## Project Structure

```
sample-bedrock-agentcore-whatsapp-assistant/
├── LICENSE                              # MIT-0 License
├── NOTICE                               # Copyright notice
├── THIRD-PARTY-LICENSES                 # Third-party dependency licenses
├── CODE_OF_CONDUCT.md                   # Code of conduct
├── CONTRIBUTING.md                      # Contributing guidelines
├── README.md                            # This file
├── .env.example                         # Environment template
├── requirements.txt                     # Python dependencies
├── src/
│   ├── agents/                          # Agent implementations
│   │   ├── orchestrator_agentcore_runtime_gateway.py  # Main orchestrator
│   │   ├── educational_assistant_agent.py             # Student queries
│   │   ├── teacher_assistant_agent.py                 # Professor queries
│   │   ├── financial_assistant_agent.py               # Payment queries
│   │   ├── virtual_secretary_agent.py                 # Admin queries
│   │   ├── general_questions_agent.py                 # General queries
│   │   └── mock_data_generator.py                     # Test data
│   └── lambda_sns_eum/                  # WhatsApp Lambda functions
│       ├── lambda_sns_handler.py                      # SNS handler
│       └── update_lambda_env.sh                       # Deployment script
├── scripts/
│   ├── deploy.sh                        # Complete deployment
│   └── cleanup.sh                       # Complete cleanup
├── tests/
│   ├── invoke_agent.py                  # Agent testing
│   └── test_tool.py                     # Tool testing
├── utils/
│   └── knowledge_base_docs/             # Knowledge base documents
├── static/
│   └── Agentcore_Demo-Art_of_Possible-Arquitetura.drawio(1).png
└── deploy_*.py                          # Individual deployment scripts
```

## How It Works

### 1. Multi-Agent Orchestration

The orchestrator agent coordinates five specialized agents:

- **Educational Assistant**: Handles student academic queries (tasks, courses, grades)
- **Teacher Assistant**: Manages teacher operations (metrics, student performance)
- **Financial Assistant**: Processes payment and financial queries
- **Virtual Secretary**: Administrative operations (reports, school-wide data)
- **General Questions**: Fallback for general policies and procedures

### 2. Persona-Based Access Control

Users are automatically identified by phone number (WhatsApp) or session attributes:

- **Student**: Access to Educational + Financial agents
- **Professor**: Access to Teacher + Financial agents  
- **Administrator**: Full access to all agents

### 3. Memory System

AgentCore Memory provides three types of persistence:

- **User Preferences**: Long-term settings and preferences
- **User Facts**: Factual information about users
- **Session Context**: Short-term conversation history

### 4. Knowledge Base Integration

Documents in `utils/knowledge_base_docs/` are automatically:
- Uploaded to S3
- Indexed in Bedrock Knowledge Base
- Available for retrieval during agent responses

## Testing

### Demo Users

The system creates demo users for testing:

| Persona | Username | Phone | Password | Access |
|---------|----------|-------|----------|---------|
| Administrator | `admin_demo` | `+551199999999` | `OctankDemo123!` | All agents |
| Professor | `professor_demo` | `+551199999999` | `OctankDemo123!` | Professor + Financial |
| Student | `student_demo` | `+5511123456789` | `OctankDemo123!` | Educational + Financial |

> **⚠️ DEMO ONLY**: These users have hardcoded passwords for demonstration. Never use in production.

### Test Commands

```bash
# Test different personas
python3 tests/invoke_agent.py --persona student --query "What are my pending tasks?"
python3 tests/invoke_agent.py --persona professor --query "Show my course metrics"
python3 tests/invoke_agent.py --persona administrator --query "Generate operational report"

# Test WhatsApp (if configured)
# Send messages to configured WhatsApp number from demo phones
```

## Deployment Options

### Option 1: Automated (Recommended)

```bash
./scripts/deploy.sh
```

### Option 2: Step-by-Step

```bash
# 1. Deploy Knowledge Base
python3 deploy_knowledge_base.py

# 2. Deploy AgentCore Memory
python3 deploy_agentcore_memory.py

# 3. Deploy AgentCore Gateway
python3 deploy_agentcore_gateway.py

# 4. Deploy AgentCore Runtime
python3 deploy_agentcore_runtime_with_gw.py

# 5. Deploy Cognito User Pool
python3 deploy_cognito_user_pool.py

# 6. Deploy Lambda for handling SNS and EUM social
cd src/lambda_sns_eum
./update_lambda_env.sh
```

## Troubleshooting

### Common Issues

**Issue**: `Memory ID not found`
- **Solution**: Run `python3 deploy_agentcore_memory.py` first

**Issue**: `Cognito authentication failed`
- **Solution**: Verify OAuth2 credentials in SSM Parameter Store

**Issue**: `WhatsApp messages not working`
- **Solution**: 
  1. Verify WABA is properly configured
  2. Check End User Messaging Social setup
  3. Ensure phone numbers match exactly (including +)

### Logs

```bash
# View AgentCore Runtime logs
aws logs tail /aws/bedrock-agentcore/runtimes/<runtime-id> --follow

# View Lambda logs
aws logs tail /aws/lambda/send_message_tool --follow
```

## Security Considerations

### ⚠️ Production Security Requirements

**This sample is NOT production-ready. For production deployment, implement:**

- [ ] Replace demo users with proper user management
- [ ] Implement strong password policies and MFA
- [ ] Add rate limiting and abuse protection
- [ ] Encrypt sensitive data at rest and in transit
- [ ] Use VPC with private subnets
- [ ] Add comprehensive logging and monitoring
- [ ] Regular security assessments

## Cost Considerations

- **Bedrock Model Usage**: Pay per token (input/output)
- **AgentCore Runtime**: Pay per invocation and compute time
- **Lambda Functions**: Pay per invocation
- **S3 Storage**: Pay for document storage
- **Cognito**: Pay per monthly active user

Estimated cost for development/testing: $10-50/month depending on usage.

## Cleanup

### Automated Cleanup

```bash
./scripts/cleanup.sh
```

This removes:
- AgentCore Runtime and all agents
- AgentCore Gateway and MCP tools
- Lambda functions
- Cognito User Pool
- Knowledge Base and S3 bucket
- AgentCore Memory
- All SSM parameters
- IAM roles and policies

## Next Steps

After exploring this sample:

1. **Customize Agents**: Modify agent prompts and behaviors for your use case
2. **Add Knowledge**: Upload your own documents to the Knowledge Base
3. **Extend Tools**: Add new MCP tools via the Gateway
4. **Security Hardening**: Implement production security measures
5. **Scale**: Consider multi-region deployment and auto-scaling

## Dependencies

### AWS Services

| Service | Purpose | Required |
|---------|---------|----------|
| Amazon Bedrock | LLM model hosting | ✅ |
| Bedrock AgentCore Runtime | Agent hosting | ✅ |
| AWS Lambda | Tool functions | ✅ |
| Amazon Cognito | Authentication | ✅ |
| Amazon S3 | Document storage | ✅ |
| AWS Systems Manager | Configuration | ✅ |
| AWS End User Messaging Social | WhatsApp integration | 📱 Optional |

### Python Packages

See `requirements.txt` for complete list. Key dependencies:
- `boto3` - AWS SDK
- `bedrock-agentcore` - Amazon Bedrock AgentCore SDK
- `bedrock-agentcore-starter-toolkit` - AgentCore starter toolkit
- `strands-agents` - Agent framework
- `requests` - HTTP client
- `python-dotenv` - Environment management

## Support

For issues and questions:
- Review the [troubleshooting section](#troubleshooting)
- Check existing [GitHub issues](../../issues)
- Create a new issue with detailed information
- Refer to AWS Bedrock AgentCore documentation

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Code of Conduct

This project has adopted the [Amazon Open Source Code of Conduct](https://aws.github.io/code-of-conduct). 
For more information see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## References

- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [AWS End User Messaging Social User Guide](https://docs.aws.amazon.com/social-messaging/latest/userguide/)
- [WhatsApp Business Platform Documentation](https://developers.facebook.com/docs/whatsapp)

## License

This sample code is provided under the MIT-0 License. See the [LICENSE](LICENSE) file for details.

**Third-Party Dependencies**: This sample uses third-party dependencies with their own licenses. See [THIRD-PARTY-LICENSES](THIRD-PARTY-LICENSES) for details.

---

**Sample Code**: This is sample code and not intended for production use without significant modifications.
