from langgraph.graph import StateGraph, START, END
from state import State
from nodes import background_investigation_node, planner_node, paper_search_node, reporter_node


def build_base_graph():
    # 构建节点图
    graph_builder = StateGraph(State)
    graph_builder.add_edge(START, "background_investigation_node")
    graph_builder.add_node("background_investigation_node", background_investigation_node)
    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("paper_search", paper_search_node)
    graph_builder.add_node("reporter", reporter_node)
    graph_builder.add_edge("reporter", END)
    return graph_builder.compile()


if __name__ == '__main__':
    user_input = "脂滴如何保护肝癌细胞抵抗铁死亡"  # THBS2在肿瘤免疫治疗的潜力
    graph = build_base_graph()
    print(graph.invoke({"messages": [{"role": "user", "content": user_input}]})["final_report"])
