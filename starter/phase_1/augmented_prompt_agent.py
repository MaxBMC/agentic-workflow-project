from workflow_agents.base_agents import AugmentedPromptAgent
import os
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

prompt = "What is the capital of France?"
persona = "You are a college professor; your answers always start with: 'Dear students,'"

augmented_agent = AugmentedPromptAgent(
    openai_api_key=openai_api_key,
    persona=persona
)

augmented_agent_response = augmented_agent.respond(prompt)

print(augmented_agent_response)

print("The agent likely used the general knowledge contained in the underlying LLM to answer the prompt, because no external knowledge source or custom factual reference was provided. The system prompt influenced the style and framing of the response by making the agent adopt the college professor persona and begin its answer with 'Dear students,'.")