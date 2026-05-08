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

product_spec_path = os.path.join(os.path.dirname(__file__), "Product-Spec-Email-Router.txt")
with open(product_spec_path, "r", encoding="utf-8") as f:
    product_spec = f.read()

knowledge_action_planning = (
    "Stories are defined from a product spec by identifying a "
    "persona, an action, and a desired outcome for each story. "
    "Each story represents a specific functionality of the product "
    "described in the specification.\n"
    "Features are defined by grouping related user stories.\n"
    "Tasks are defined for each story and represent the engineering "
    "work required to develop the product.\n"
    "A development plan for a product contains user stories, features, and engineering tasks."
)

action_planning_agent = ActionPlanningAgent(
    openai_api_key=openai_api_key,
    knowledge=knowledge_action_planning,
)

persona_product_manager = "You are a Product Manager, you are responsible for defining the user stories for a product."
knowledge_product_manager = (
    "Stories are defined by writing sentences with a persona, an action, and a desired outcome. "
    "The sentences always start with: As a "
    "Write several user stories for the product specification below, where the personas are the different users of the product. "
    "Return only user stories. "
    + product_spec
)

product_manager_knowledge_agent = KnowledgeAugmentedPromptAgent(
    openai_api_key=openai_api_key,
    persona=persona_product_manager,
    knowledge=knowledge_product_manager,
)

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

persona_program_manager = "You are a Program Manager, you are responsible for defining the features for a product."
knowledge_program_manager = (
    "Features of a product are defined by organizing similar user stories into cohesive groups. "
    "When given a product specification and user stories, return product features only. "
    "Each feature must follow this structure:\n"
    "Feature Name: ...\n"
    "Description: ...\n"
    "Key Functionality: ...\n"
    "User Benefit: ...\n"
    + product_spec
)

program_manager_knowledge_agent = KnowledgeAugmentedPromptAgent(
    openai_api_key=openai_api_key,
    persona=persona_program_manager,
    knowledge=knowledge_program_manager,
)

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

persona_dev_engineer = "You are a Development Engineer, you are responsible for defining the development tasks for a product."
knowledge_dev_engineer = (
    "Development tasks are defined by identifying what needs to be built to implement each user story and feature. "
    "When given a product specification, user stories, and product features, return engineering tasks only. "
    "Each task must follow this structure:\n"
    "Task ID: ...\n"
    "Task Title: ...\n"
    "Related User Story: ...\n"
    "Description: ...\n"
    "Acceptance Criteria: ...\n"
    "Estimated Effort: ...\n"
    "Dependencies: ...\n"
    + product_spec
)

development_engineer_knowledge_agent = KnowledgeAugmentedPromptAgent(
    openai_api_key=openai_api_key,
    persona=persona_dev_engineer,
    knowledge=knowledge_dev_engineer,
)

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


def product_manager_support_function(query):
    evaluation_result = product_manager_evaluation_agent.evaluate(query)
    return evaluation_result["final_response"]


def program_manager_support_function(query):
    evaluation_result = program_manager_evaluation_agent.evaluate(query)
    return evaluation_result["final_response"]


def development_engineer_support_function(query):
    evaluation_result = development_engineer_evaluation_agent.evaluate(query)
    return evaluation_result["final_response"]


routes = [
    {
        "name": "Product Manager",
        "description": "Responsible for defining user stories only. Creates stories in the format As a [type of user], I want [an action or feature] so that [benefit/value].",
        "func": lambda x: product_manager_support_function(x),
    },
    {
        "name": "Program Manager",
        "description": "Responsible for defining product features only. Groups related user stories into cohesive features and returns Feature Name, Description, Key Functionality, and User Benefit.",
        "func": lambda x: program_manager_support_function(x),
    },
    {
        "name": "Development Engineer",
        "description": "Responsible for defining engineering tasks only. Converts approved user stories and product features into detailed implementation tasks.",
        "func": lambda x: development_engineer_support_function(x),
    },
]

routing_agent = RoutingAgent(
    openai_api_key=openai_api_key,
    agents=routes,
)

print("\n*** Workflow execution started ***\n")

workflow_prompt = (
    "Generate a complete project plan for the Email Router product, including "
    "user stories, product features, and detailed engineering tasks."
)

print(f"Task to complete in this workflow, workflow prompt = {workflow_prompt}")
print("\nDefining workflow steps from the workflow prompt")

planned_steps = action_planning_agent.extract_steps_from_prompt(workflow_prompt)

workflow_steps = []

if any("stor" in step.lower() for step in planned_steps):
    workflow_steps.append("Define user stories for the Email Router product.")
if any("feature" in step.lower() for step in planned_steps):
    workflow_steps.append("Define product features for the Email Router product.")
if any("task" in step.lower() for step in planned_steps):
    workflow_steps.append("Define engineering tasks for the Email Router product.")

if not any("user stories" in step.lower() for step in workflow_steps):
    workflow_steps.append("Define user stories for the Email Router product.")
if not any("product features" in step.lower() for step in workflow_steps):
    workflow_steps.append("Define product features for the Email Router product.")
if not any("engineering tasks" in step.lower() for step in workflow_steps):
    workflow_steps.append("Define engineering tasks for the Email Router product.")

ordered_workflow_steps = []
for canonical_step in [
    "Define user stories for the Email Router product.",
    "Define product features for the Email Router product.",
    "Define engineering tasks for the Email Router product.",
]:
    if canonical_step in workflow_steps and canonical_step not in ordered_workflow_steps:
        ordered_workflow_steps.append(canonical_step)

workflow_steps = ordered_workflow_steps

print("\nWorkflow steps:")
for step in workflow_steps:
    print(step)

generated_user_stories = ""
generated_features = ""
generated_tasks = ""
completed_steps = []

for step in workflow_steps:
    print(f"\nExecuting workflow step: {step}")

    if "user stories" in step.lower():
        current_query = (
            "Create user stories for the Email Router product based on the following product specification.\n\n"
            f"{product_spec}\n\n"
            "Return only user stories in the format: "
            "As a [type of user], I want [an action or feature] so that [benefit/value]."
        )
        step_result = routing_agent.route(current_query)
        generated_user_stories = step_result

    elif "product features" in step.lower():
        current_query = (
            "Create product features for the Email Router product.\n\n"
            "Use the following approved user stories and the product specification.\n\n"
            "USER STORIES:\n"
            f"{generated_user_stories}\n\n"
            "PRODUCT SPECIFICATION:\n"
            f"{product_spec}\n\n"
            "Return only product features in this format:\n"
            "Feature Name: ...\n"
            "Description: ...\n"
            "Key Functionality: ...\n"
            "User Benefit: ..."
        )
        step_result = routing_agent.route(current_query)
        generated_features = step_result

    elif "engineering tasks" in step.lower():
        current_query = (
            "Create engineering tasks for the Email Router product.\n\n"
            "Use the following approved user stories, product features, and the product specification.\n\n"
            "USER STORIES:\n"
            f"{generated_user_stories}\n\n"
            "PRODUCT FEATURES:\n"
            f"{generated_features}\n\n"
            "PRODUCT SPECIFICATION:\n"
            f"{product_spec}\n\n"
            "Return only engineering tasks in this format:\n"
            "Task ID: ...\n"
            "Task Title: ...\n"
            "Related User Story: ...\n"
            "Description: ...\n"
            "Acceptance Criteria: ...\n"
            "Estimated Effort: ...\n"
            "Dependencies: ..."
        )
        step_result = routing_agent.route(current_query)
        generated_tasks = step_result

    else:
        step_result = routing_agent.route(step)

    completed_steps.append(
        {
            "step": step,
            "result": step_result,
        }
    )

    print(f"\nResult of step:\n{step_result}")

final_output = (
    "\n=== FINAL EMAIL ROUTER PROJECT PLAN ===\n\n"
    "=== USER STORIES ===\n"
    f"{generated_user_stories}\n\n"
    "=== PRODUCT FEATURES ===\n"
    f"{generated_features}\n\n"
    "=== ENGINEERING TASKS ===\n"
    f"{generated_tasks}\n"
)

print("\n*** Workflow completed ***\n")
print(final_output)

output_path = os.path.join(os.path.dirname(__file__), "Outputs", "workflow_output.txt")

os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(final_output)