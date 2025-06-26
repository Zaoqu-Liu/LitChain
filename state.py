from langgraph.graph import MessagesState
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from typing import Annotated, Literal
from prompt.planner_model import Plan


class State(TypedDict):
    messages: Annotated[list, add_messages]
    background_investigation_results: list
    final_report: str = ""
    current_plan: Plan | str = None
