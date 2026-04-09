import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../phase_1")))

from workflow_agents.base_agents import (
    ActionPlanningAgent,
    KnowledgeAugmentedPromptAgent,
    EvaluationAgent,
    RoutingAgent,
)

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

with open("Product-Spec-Email-Router.txt", "r", encoding="utf-8") as f:
    product_spec = f.read()

# Instantiate all the agents

# Action Planning Agent
knowledge_action_planning = (
    "Stories are defined from a product spec by identifying a "
    "persona, an action, and a desired outcome for each story. "
    "Each story represents a specific functionality of the product "
    "described in the specification. \n"
    "Features are defined by grouping related user stories. \n"
    "Tasks are defined for each story and represent the engineering "
    "work required to develop the product. \n"
    "A development Plan for a product contains all these components"
)

action_planning_agent = ActionPlanningAgent(
    openai_api_key=openai_api_key,
    knowledge=knowledge_action_planning,
)

# Product Manager - Knowledge Augmented Prompt Agent
persona_product_manager = "You are a Product Manager, you are responsible for defining the user stories for a product."
knowledge_product_manager = (
    "Stories are defined by writing sentences with a persona, an action, and a desired outcome. "
    "The sentences always start with: As a "
    "Write several stories for the product spec below, where the personas are the different users of the product. "
    + product_spec
)

product_manager_knowledge_agent = KnowledgeAugmentedPromptAgent(
    openai_api_key=openai_api_key,
    persona=persona_product_manager,
    knowledge=knowledge_product_manager,
)

# Product Manager - Evaluation Agent
persona_product_manager_eval = "You are an evaluation agent that checks the answers of other worker agents"
evaluation_criteria_product_manager = (
    "The answer should be stories that follow the following structure: "
    "As a [type of user], I want [an action or feature] so that [benefit/value]."
)

product_manager_evaluation_agent = EvaluationAgent(
    openai_api_key=openai_api_key,
    persona=persona_product_manager_eval,
    evaluation_criteria=evaluation_criteria_product_manager,
    worker_agent=product_manager_knowledge_agent,
    max_interactions=10,
)

# Program Manager - Knowledge Augmented Prompt Agent
persona_program_manager = "You are a Program Manager, you are responsible for defining the features for a product."
knowledge_program_manager = "Features of a product are defined by organizing similar user stories into cohesive groups."

program_manager_knowledge_agent = KnowledgeAugmentedPromptAgent(
    openai_api_key=openai_api_key,
    persona=persona_program_manager,
    knowledge=knowledge_program_manager,
)

# Program Manager - Evaluation Agent
persona_program_manager_eval = "You are an evaluation agent that checks the answers of other worker agents."

evaluation_criteria_program_manager = (
    "The answer should be product features that follow the following structure:\n"
    "Feature Name: A clear, concise title that identifies the capability\n"
    "Description: A brief explanation of what the feature does and its purpose\n"
    "Key Functionality: The specific capabilities or actions the feature provides\n"
    "User Benefit: How this feature creates value for the user"
)

program_manager_evaluation_agent = EvaluationAgent(
    openai_api_key=openai_api_key,
    persona=persona_program_manager_eval,
    evaluation_criteria=evaluation_criteria_program_manager,
    worker_agent=program_manager_knowledge_agent,
    max_interactions=10,
)

# Development Engineer - Knowledge Augmented Prompt Agent
persona_dev_engineer = "You are a Development Engineer, you are responsible for defining the development tasks for a product."
knowledge_dev_engineer = "Development tasks are defined by identifying what needs to be built to implement each user story."

development_engineer_knowledge_agent = KnowledgeAugmentedPromptAgent(
    openai_api_key=openai_api_key,
    persona=persona_dev_engineer,
    knowledge=knowledge_dev_engineer,
)

# Development Engineer - Evaluation Agent
persona_dev_engineer_eval = "You are an evaluation agent that checks the answers of other worker agents."

evaluation_criteria_dev_engineer = (
    "The answer should be tasks following this exact structure:\n"
    "Task ID: A unique identifier for tracking purposes\n"
    "Task Title: Brief description of the specific development work\n"
    "Related User Story: Reference to the parent user story\n"
    "Description: Detailed explanation of the technical work required\n"
    "Acceptance Criteria: Specific requirements that must be met for completion\n"
    "Estimated Effort: Time or complexity estimation\n"
    "Dependencies: Any tasks that must be completed first"
)

development_engineer_evaluation_agent = EvaluationAgent(
    openai_api_key=openai_api_key,
    persona=persona_dev_engineer_eval,
    evaluation_criteria=evaluation_criteria_dev_engineer,
    worker_agent=development_engineer_knowledge_agent,
    max_interactions=10,
)


# Job function persona support functions
def product_manager_support_function(query):
    response_from_knowledge_agent = product_manager_knowledge_agent.respond(query)
    evaluation_result = product_manager_evaluation_agent.evaluate(response_from_knowledge_agent)
    return evaluation_result["final_response"]


def program_manager_support_function(query):
    response_from_knowledge_agent = program_manager_knowledge_agent.respond(query)
    evaluation_result = program_manager_evaluation_agent.evaluate(response_from_knowledge_agent)
    return evaluation_result["final_response"]


def development_engineer_support_function(query):
    response_from_knowledge_agent = development_engineer_knowledge_agent.respond(query)
    evaluation_result = development_engineer_evaluation_agent.evaluate(response_from_knowledge_agent)
    return evaluation_result["final_response"]


# Routing Agent
routes = [
    {
        "name": "Product Manager",
        "description": "Responsible for defining product personas and user stories only. Does not define features or tasks. Does not group stories.",
        "func": lambda x: product_manager_support_function(x),
    },
    {
        "name": "Program Manager",
        "description": "Responsible for defining product features only. Groups related user stories into cohesive features. Does not define user stories or engineering tasks.",
        "func": lambda x: program_manager_support_function(x),
    },
    {
        "name": "Development Engineer",
        "description": "Responsible for defining detailed engineering tasks only. Converts user stories into implementation tasks. Does not define stories or features.",
        "func": lambda x: development_engineer_support_function(x),
    },
]

routing_agent = RoutingAgent(
    openai_api_key=openai_api_key,
    agents=routes,
)

# Run the workflow

print("\n*** Workflow execution started ***\n")

workflow_prompt = "What would the development tasks for this product be?"

print(f"Task to complete in this workflow, workflow prompt = {workflow_prompt}")

print("\nDefining workflow steps from the workflow prompt")

workflow_steps = action_planning_agent.extract_steps_from_prompt(workflow_prompt)
completed_steps = []

for step in workflow_steps:
    print(f"\nExecuting workflow step: {step}")
    step_result = routing_agent.route(step)
    completed_steps.append(step_result)
    print(f"\nResult of step:\n{step_result}")

print("\n*** Workflow completed ***\n")
if completed_steps:
    print("Final output of the workflow:\n")
    print(completed_steps[-1])
else:
    print("No workflow steps were completed.")