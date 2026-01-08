from strands.models import BedrockModel
from strands import Agent
import logging

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", 
    handlers=[logging.StreamHandler()]
)

# Configuração do Runtime
RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:831782568328:runtime/Octank_edu_assistant-iGSP5IGDGF"

print("🤖 Invocando o agente AgentCore via Strands...")
print(f"📍 Runtime ARN: {RUNTIME_ARN}")
print()

try:
    # Criar o modelo apontando para o runtime
    model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        temperature=0.7,
    )
    
    # Criar o agente com o runtime ARN
    agent = Agent(
        model=model,
        runtime_arn=RUNTIME_ARN
    )
    
    print("✅ Agente criado com sucesso!")
    print()
    
    # Verificar as tools disponíveis
    if hasattr(agent, 'tool_names'):
        print("🔧 Tools disponíveis no agente:")
        for tool_name in agent.tool_names:
            print(f"   - {tool_name}")
        print()
    
    # Invocar o agente
    print("💬 Enviando mensagem ao agente...")
    print("=" * 80)
    
    response = agent("Olá! Por favor, liste todas as ferramentas (tools) que você tem disponíveis para usar. Descreva cada uma delas.")
    
    print()
    print("=" * 80)
    print()
    print("📝 Resposta do agente:")
    print(response)
    print()
    print("✨ Invocação concluída com sucesso!")
    
except Exception as e:
    print(f"❌ Erro ao invocar o agente: {str(e)}")
    print(f"   Tipo: {type(e).__name__}")
    import traceback
    traceback.print_exc()
