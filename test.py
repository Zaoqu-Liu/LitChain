import json
import logging
from typing import Annotated, Literal
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import Command
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage
from prompt.render import apply_prompt_template
from tools.pubmed_search import search_pubmed
import os
from util.json_util import repair_json_output

# 基础配置
model = "gpt-4o-2024-11-20"
api_key = "sk-Xx2Ix6Gz7MkkXDiH5b8d3bF0963a4a869c8303B077Da65A5"
base_url = "https://api.bltcy.ai/v1"
logger = logging.getLogger(__name__)
# 设置环境变量
os.environ["TAVILY_API_KEY"] = "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"

llm = ChatOpenAI(model=model, api_key=api_key, base_url=base_url)


class Plan(BaseModel):
    has_enough_context: bool
    thought: str
    title: str
    steps: list

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "has_enough_context": False,
                    "thought": (
                        "To understand the current market trends in AI, we need to gather comprehensive information."
                    ),
                    "title": "AI Market Research Plan",
                    "steps": [
                        {
                            "Research objectives": "Current AI Market Analysis",
                            "entities": ["AI", ""]
                        }
                    ],
                }
            ]
        }


class State(TypedDict):
    messages: Annotated[list, add_messages]
    background_investigation_results: list
    final_report: str = ""
    current_plan: Plan | str = None


def reporter_node(state: State):
    print("Reporter Node is running.")
    current_plan = state["current_plan"]
    prompt = apply_prompt_template("reporter",state)
    prompt.append(
        HumanMessage(
            content="IMPORTANT: Structure your report according to the format in the prompt. Remember to include:\n\n1. Key Points - A bulleted list of the most important findings\n2. Overview - A brief introduction to the topic\n3. Detailed Analysis - Organized into logical sections\n4. Survey Note (optional) - For more comprehensive reports\n5. Key Citations - List all references at the end\n\nFor citations, DO NOT include inline citations in the text. Instead, place all citations in the 'Key Citations' section at the end using the format: `- [Source Title](URL)`. Include an empty line between each citation for better readability.\n\nPRIORITIZE USING MARKDOWN TABLES for data presentation and comparison. Use tables whenever presenting comparative data, statistics, features, or options. Structure tables with clear headers and aligned columns. Example table format:\n\n| Feature | Description | Pros | Cons |\n|---------|-------------|------|------|\n| Feature 1 | Description 1 | Pros 1 | Cons 1 |\n| Feature 2 | Description 2 | Pros 2 | Cons 2 |",
            name="system",
        )
    )
    for step in current_plan["steps"]:
        prompt.append(
            HumanMessage(
                content=f"Below are some research objectives and papers for the research task:\n\n{step['Research objectives']}\n\n{step['papers']}",
                name="observation",
            )
        )
    llm_response = llm.invoke(prompt).content

    return Command(
        update={
            "final_report":llm_response
        }
    )


# 定义背景调研节点
def background_investigation_node(state: State) -> Command[Literal["planner"]]:
    print("Background Investigation Node is running.")
    query = state["messages"][-1].content
    tool = TavilySearch(max_results=1)
    searched_content = tool.invoke({"query": query})
    background_investigation_results = searched_content['results']
    if isinstance(searched_content, list):
        background_investigation_results = [
            {"title": elem["title"], "content": elem["content"]}
            for elem in searched_content
        ]

    return Command(
        update={
            "background_investigation_results": json.dumps(
                background_investigation_results, ensure_ascii=False
            )
        },
        goto="planner",
    )


# 定义LL节点
def planner_node(
        state: State
) -> Command[Literal["paper_search", "reporter"]]:
    print("Planner Node is running.")
    messages = apply_prompt_template("planner",state)
    messages += [
        {
            "role": "user",
            "content": (
                    "background investigation results of user query:\n"
                    + state["background_investigation_results"]
                    + "\n"
            ),
        }
    ]
    response = llm.invoke(messages).content
    # response = response.model_dump_json(indent=4, exclude_none=True)
    try:
        curr_plan = json.loads(repair_json_output(response))
    except json.JSONDecodeError:
        logger.warning("Planner response is not a valid JSON")
        return Command(goto="reporter")

    if curr_plan.get("has_enough_context"):
        logger.info("Planner response has enough context.")
        new_plan = Plan.model_validate(curr_plan)
        return Command(
            update={
                "messages": [AIMessage(content=response, name="planner")],
                "current_plan": new_plan,
            },
            goto="reporter",
        )
    return Command(
        update={
            "messages": [AIMessage(content=response, name="planner")],
            "current_plan": curr_plan,
        },
        goto="paper_search",
    )


def paper_search_node(
        state: State
) -> Command[Literal["reporter"]]:
    print("Paper Search Node is running.")
    current_plan = state.get("current_plan")
    plans = current_plan["steps"]
    # 查找论文
    for index, value in enumerate(plans):
        papers = []
        entities = value["entities"]
        for query in entities:
            papers.extend(search_pubmed([query],max_results=1))
        plans[index]["papers"] = papers
    current_plan["steps"] = plans
    return Command(
        update={
            "current_plan": current_plan,
        },
        goto="reporter",
    )
# 构建节点图
graph_builder = StateGraph(State)
graph_builder.add_edge(START, "background_investigation_node")
graph_builder.add_node("background_investigation_node", background_investigation_node)
graph_builder.add_node("planner", planner_node)
graph_builder.add_node("paper_search", paper_search_node)
graph_builder.add_node("reporter", reporter_node)
graph_builder.add_edge("reporter", END)
graph = graph_builder.compile()

if __name__ == '__main__':
    user_input = "脂滴如何保护肝癌细胞抵抗铁死亡"  # THBS2在肿瘤免疫治疗的潜力
    print(graph.invoke({"messages": [{"role": "user", "content": user_input}]})["final_report"])
