# -*- coding: utf-8 -*-
from langgraph.graph import StateGraph, START, END
from agent.nodes import planner_node, reporter_node, background_investigation_node, paper_filter_node, paper_search_node, \
    paper_rerank_download_node, self_reflection_node, State

# 添加节点
graph_builder = StateGraph(State)
graph_builder.add_edge(START, "planner")
# graph_builder.add_node("background_investigation_node", background_investigation_node)
graph_builder.add_node("planner", planner_node)
graph_builder.add_node("paper_search", paper_search_node)
graph_builder.add_node("paper_filter", paper_filter_node)
graph_builder.add_node("paper_rerank_download", paper_rerank_download_node)
graph_builder.add_node("self_reflection", self_reflection_node)
graph_builder.add_node("reporter", reporter_node)
graph_builder.add_edge("reporter", END)

# 编译状态图
graph = graph_builder.compile()
