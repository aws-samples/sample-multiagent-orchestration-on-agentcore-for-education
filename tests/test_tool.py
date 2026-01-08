from strands.models import BedrockModel
from mcp.client.streamable_http import streamablehttp_client 
from strands.tools.mcp.mcp_client import MCPClient
from strands import Agent
import utils
import logging

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", 
    handlers=[logging.StreamHandler()]
)

# Get Cognito token
token = utils.get_cognito_token()

def create_streamable_http_transport():
    return streamablehttp_client(
        utils.get_ssm_parameter("/app/octank/agentcore/gatewayURL"),
        headers={"Authorization": f"Bearer {token}"}
    )

client = MCPClient(create_streamable_http_transport)

## The IAM credentials configured in ~/.aws/credentials should have access to Bedrock model
yourmodel = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    temperature=0.7,
)

with client:
    # Call the listTools 
    tools = client.list_tools_sync()
    # Create an Agent with the model and tools
    agent = Agent(model=yourmodel,tools=tools) ## you can replace with any model you like
    print(f"Tools loaded in the agent are {agent.tool_names}")
    #print(f"Tools configuration in the agent are {agent.tool_config}")
    # Invoke the agent with the sample prompt. This will only invoke  MCP listTools and retrieve the list of tools the LLM has access to. The below does not actually call any tool.
    response1 = agent("Hi , can you list all tools available to you")
    print(f"\n=== Response 1 ===\n{response1}\n")
    
    # Invoke the agent with sample prompt, invoke the tool and display the response
    response2 = agent("Envie uma mensagem WhatsApp para +551146731805 dizendo 'Olá! Esta é uma mensagem de teste do AgentCore Gateway.'")
    print(f"\n=== Response 2 ===\n{response2}\n")
    
    # Call the MCP tool explicitly. The MCP Tool name and arguments must match with your AWS Lambda function
    # Uncomment to test direct tool call:
    # targetname = "GetCreditCheckLambda"  # Replace with your target name
    # result = client.call_tool_sync(
    #     tool_use_id="send_whatsapp_message_1",
    #     name=targetname+"___send_whatsapp_message",
    #     arguments={"phone_number": "+551146731805", "message": "Teste direto"}
    # )
    # print(f"\n=== Tool Call result ===\n{result['content'][0]['text']}\n")
