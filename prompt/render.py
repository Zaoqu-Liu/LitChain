from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

from langgraph.prebuilt.chat_agent_executor import AgentState

env = Environment(
    loader=FileSystemLoader(os.path.dirname(__file__)),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def get_plan_prompt(
        state: AgentState,
) -> list:
    # Convert state to dict for template rendering
    state_vars = {
        "CURRENT_TIME": datetime.now(),
    }
    # Add configurable variables

    try:
        template = env.get_template(f"plan_system.md")
        system_prompt = template.render(**state_vars)
        return [{"role": "system", "content": system_prompt}]
    except Exception as e:
        raise ValueError(f"Error applying template plan: {e}")


def get_paper_filter_prompt(
    state: AgentState,papers,format_str
) -> list:
    # Convert state to dict for template rendering
    current_step_index = state["current_plan_index"]
    state_vars = {
        "User_Query": state["messages"][0].content,
        "Steps": state["current_plan"]["steps"],
        "Current_Step": state["current_plan"]["steps"][current_step_index],
        "Papers": papers
    }
    # Add configurable variables

    try:
        system_template = env.get_template(f"paper_filter_system.md")
        system_prompt = system_template.render(**state_vars)
        user_template = env.get_template(f"paper_filter_user.md")
        user_prompt = user_template.render(**state_vars)
        return [{"role": "system", "content": system_prompt}]+[
        {
            "role": "user",
            "content": user_prompt
        }
    ]
    except Exception as e:
        raise ValueError(f"Error applying template paper_filter: {e}")


def get_self_reflection_prompt(
    state: AgentState,format_str
) -> list:
    current_step_index = state["current_plan_index"]
    state_vars = {
        "User_Query": state["messages"][0].content,
        "Steps": state["current_plan"]["steps"],
        "Current_Step": state["current_plan"]["steps"][current_step_index],
    }
    try:
        system_template = env.get_template(f"self_reflection_system.md")
        system_prompt = system_template.render(**state_vars)
        user_template = env.get_template(f"self_reflection_user.md")
        user_prompt = user_template.render(**state_vars)+f"\n\n{format_str}"

        return [{"role": "system", "content": system_prompt}] + [
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    except Exception as e:
        raise ValueError(f"Error applying template self_reflection: {e}")

def get_paper_read_prompt(user_query,verification_Point,purpose,paper_content
) -> list:
    state_vars = {
        "user_query":user_query,
        "Verification_Point": verification_Point,
        "purpose": purpose,
        "paper_content":paper_content
    }
    try:
        system_template = env.get_template(f"paper_read_system.md")
        system_prompt = system_template.render(**state_vars)
        user_template = env.get_template(f"paper_read_user.md")
        user_prompt = user_template.render(**state_vars)
        return [{"role": "system", "content": system_prompt}] + [{"role": "user", "content": user_prompt}]
    except Exception as e:
        raise ValueError(f"Error applying template paper_read: {e}")

def get_paper_merge_prompt(user_query,verification_Point,purpose,papers_content
) -> list:
    state_vars = {
        "user_query":user_query,
        "Verification_Point": verification_Point,
        "purpose": purpose,
        "papers_content":papers_content
    }
    try:
        system_template = env.get_template(f"paper_merge_system.md")
        system_prompt = system_template.render(**state_vars)
        user_template = env.get_template(f"paper_merge_user.md")
        user_prompt = user_template.render(**state_vars)
        return [{"role": "system", "content": system_prompt}] + [{"role": "user", "content": user_prompt}]
    except Exception as e:
        raise ValueError(f"Error applying template paper_merge: {e}")

def get_report_prompt(plan,content,user_query
) -> list:
    try:
        system_template = env.get_template(f"reporter_system.md")
        system_prompt = system_template.render()
        user_template = env.get_template(f"reporter_user.md")
        user_prompt = user_template.render(user_query=user_query,
                      items=zip(plan, content))
        return [{"role": "system", "content": system_prompt}] + [{"role": "user", "content": user_prompt}]
    except Exception as e:
        raise ValueError(f"Error applying template report: {e}")