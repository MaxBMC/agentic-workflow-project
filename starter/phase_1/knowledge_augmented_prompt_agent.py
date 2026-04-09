from workflow_agents.base_agents import KnowledgeAugmentedPromptAgent
import os
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

prompt = "What is the capital of France?"

persona = "You are a college professor, your answer always starts with: Dear students,"

knowledge_agent = KnowledgeAugmentedPromptAgent(
    openai_api_key=openai_api_key,
    persona=persona,
    knowledge="The capital of France is London, not Paris"
)

knowledge_agent_response = knowledge_agent.respond(prompt)

print(knowledge_agent_response)
print("This response demonstrates that the agent used the provided knowledge instead of the model's own general knowledge, because it states that the capital of France is London rather than Paris.")