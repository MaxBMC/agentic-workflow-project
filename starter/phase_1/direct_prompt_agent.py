from workflow_agents.base_agents import DirectPromptAgent
import os
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

prompt = "What is the Capital of France?"

direct_agent = DirectPromptAgent(openai_api_key=openai_api_key)
direct_agent_response = direct_agent.respond(prompt)

print(direct_agent_response)

print("Knowledge source: The agent used the general knowledge contained in the selected LLM model, because no additional external knowledge or custom context was provided.")