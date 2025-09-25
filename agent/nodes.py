# -*- coding: utf-8 -*-
import json
from typing import Annotated, Literal
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langchain_tavily import TavilySearch
from langgraph.graph.message import add_messages
from langgraph.types import Command
from pydantic import BaseModel
from prompt.render import get_plan_prompt, get_paper_filter_prompt, get_self_reflection_prompt, get_report_prompt
from util.json_util import validate_papers, validate_logical_chain, get_validated_response
from tools.paper_report import run_all_steps
from tools.paper_rerank import process_all_paper
import asyncio
from tools.pubmed_search import pubmed_search
from tools.biorxiv_search import biorxiv_search
from tools.medrxiv_search import medrxiv_search
import time
import concurrent.futures
from threading import Lock
from util.filter_dicts_with_stats import filter_dicts_with_stats
from config import get_cfg
from logger import get_logger
from langchain.output_parsers import PydanticOutputParser
from agent.schemas import Papers_model, LogicalChain_model, StructuredRetryLLM
from agent.metrics import node_monitor, token_cb


# 配置文件加载
cfg = get_cfg()

# logger设置
logger = get_logger(__name__)

# 并发的max_workers设置
max_workers = cfg.max_workers

# ================= 大模型定义 =================
api_key = cfg.openai_api_key
base_url = cfg.openai_api_base
text_model_name = cfg.text_model  # 内容生成大模型
json_model_name = cfg.json_model  # json格式生成大模型

text_model = ChatOpenAI(model=text_model_name, api_key=api_key, base_url=base_url, max_retries=3, callbacks=[token_cb])

json_model = ChatOpenAI(model=json_model_name, api_key=api_key, base_url=base_url, max_retries=3, callbacks=[token_cb],
                        temperature=0)


# ================= 数据结构定义 =================
# 定义的Plan对象类
class Plan(BaseModel):
    """规划步骤的数据结构"""
    thought: str
    Logical_chain: str
    steps: list


class State(TypedDict):
    """智能体状态数据结构"""
    messages: Annotated[list, add_messages]  # 消息历史
    background_investigation_results: list  # 背景调研结果
    final_report: str  # 最终报告
    current_plan: Plan | str  # 当前执行计划
    current_plan_index: int  # 当前计划步骤索引
    step: list  # 步骤列表
    papers: dict  # 检索到的论文
    papers_filtered: list  # 过滤后的论文
    num_self_reflection: int  # 自我反思次数计数器
    paper_pdf_dir: list  # 论文pdf保存路径
    paper_abs_read: list  # 筛选出那些论文只需要读摘要
    step_paper_content: list  # 每一步总结的论文内容


# ================= 节点函数定义 =================
@node_monitor
def background_investigation_node(state: State) -> Command[Literal["planner"]]:
    """背景调研节点（当前未启用）"""
    node_config = cfg.get_node_params("background_investigation_node")
    logger.info("Background Investigation Node is running.")
    query = state["messages"][-1].content

    # 使用Tavily搜索引擎进行搜索
    tool = TavilySearch(max_results=node_config["max_results"], time_range='year')
    searched_content = tool.invoke({"query": query})
    logger.debug(searched_content)
    # print(searched_content)
    # 处理搜索结果
    background_investigation_results = searched_content['results']
    if isinstance(searched_content, list):
        background_investigation_results = [
            {"title": elem["title"], "content": elem["content"]}
            for elem in searched_content
        ]
    # 更新状态并跳转到规划节点
    return Command(
        update={
            "background_investigation_results": json.dumps(
                background_investigation_results, ensure_ascii=False
            )
        },
        goto="planner",
    )


@node_monitor
def planner_node(
        state: State
) -> Command[Literal["paper_search"]]:
    """规划节点：生成研究计划"""
    logger.info("=" * 80)
    logger.info(f"User_Query:{state["messages"][-1].content}")
    logger.info(f"Text Model:{text_model_name}")
    logger.info(f"Json Model:{json_model_name}")
    logger.info("Planner Node is running.")
    # 获取规划提示模板并添加用户查询
    parser = PydanticOutputParser(pydantic_object=LogicalChain_model)
    format_str = parser.get_format_instructions()
    messages = get_plan_prompt(state)
    messages += [
        {
            "role": "user",
            "content": "user query:\n" + state["messages"][-1].content + "\n\n" + format_str
        }
    ]
    try:
        # 使用了两种方式进行json验证：
        # 一种是基于schema+重写ChatOpenAI类的方法 这种方法需要大模型支持function calling
        # 第二种是手工验证的方法
        # 两种方法都可以使用，目前还是使用的手工验证的方法，因为该方法经过了在pubmedQA上后测试之后的优化，基本上没有错误了
        # retry_llm = StructuredRetryLLM(llm, LogicalChain_model, max_retry=3)
        # curr_plan = retry_llm.invoke(messages)
        curr_plan = get_validated_response(
            json_model,
            messages,
            validate_logical_chain
        )
        logger.debug(json.dumps(curr_plan, indent=2, ensure_ascii=False))
    except ValueError as e:
        print(f"逻辑链获取失败: {str(e)}")

    # 更新状态并跳转到论文搜索节点
    return Command(
        update={
            "current_plan": curr_plan,
        },
        goto="paper_search",
    )


@node_monitor
async def paper_search_node(
        state: State
) -> Command[Literal["paper_rerank_download", "paper_filter"]]:
    """论文搜索节点：并行搜索多个数据库"""
    logger.info("Paper Search Node is running.")
    # 加载节点的配置
    node_config = cfg.get_node_params("paper_search_node")
    # print("Paper Search Node is running.")
    current_plan = state.get("current_plan")
    plans = current_plan["steps"]
    current_plan_index = state.get("current_plan_index")
    logger.info(f"当前的处理到的step:{current_plan_index}")
    # 检查是否完成所有搜索步骤 若已经完成，则调到paper_rerank_download节点
    if current_plan_index == len(plans):
        return Command(
            goto="paper_rerank_download",
        )
    else:
        # 获取当前步骤的查询
        query = plans[current_plan_index]["Step_query"]
        # 创建并行搜索任务
        # 记录开始时间
        start_time = time.perf_counter()
        tasks = [
            asyncio.create_task(biorxiv_search(query, max_results=node_config["max_results"])),
            asyncio.create_task(medrxiv_search(query, max_results=node_config["max_results"])),
            asyncio.create_task(pubmed_search(query, max_results=node_config["max_results"]))
        ]
        # 并行执行所有搜索任务
        results = await asyncio.gather(*tasks)
        # 记录结束时间
        end_time = time.perf_counter()
        total_time = end_time - start_time
        # logger.info(f"论文搜索总执行时间: {total_time:.4f} 秒")
        # 整理结果到字典
        retrieval_papers = {
            "pubmed": results[2],
            "biorxiv": results[0],
            "medrxiv": results[1],
        }
        # 打印各数据库搜索结果
        # for source, paper in retrieval_papers.items():
        #     # logger.debug()
        #     print(f"\n{source.upper()} found {len(paper)} papers:")
        #     for p in paper:
        #         print(f" - {p}".encode('gbk', errors='ignore').decode('gbk'))
        # 更新状态并跳转到论文过滤节点
        return Command(
            update={
                "papers": retrieval_papers,
            },
            goto="paper_filter",
        )


# 定义paper filter节点 通过使用大模型过滤论文
@node_monitor
def paper_filter_node(
        state: State
) -> Command[Literal["paper_search", "self_reflection"]]:
    """论文过滤节点：使用大模型评估论文质量"""
    logger.info("Paper Filter Node is running.")
    # print("Paper Filter Node is running.")

    current_step_index = state["current_plan_index"]
    num_self_reflection = state["num_self_reflection"]
    retrieval_papers = state["papers"]
    papers_filtered = state["papers_filtered"]
    f_papers = {
        source: [
            {"Title": paper["Title"], "Abstract": paper["Abstract"]}
            for paper in papers
        ]
        for source, papers in retrieval_papers.items()
        if papers  # 只保留长度不为0的 results[]
    }
    # 并发对三个数据库的论文进行过滤，加速代码运行时间
    level = {}
    result_lock = Lock()
    # 单个线程的工作函数
    def _process_one_source(source: str, papers):
        """
        针对单个 source 的处理逻辑。
        """
        parser = PydanticOutputParser(pydantic_object=Papers_model)
        format_str = parser.get_format_instructions()
        messages = get_paper_filter_prompt(state, papers, format_str)
        try:
            paper_level = get_validated_response(
                json_model,
                messages,
                validate_papers
            )
            paper_level = paper_level["Papers"]
            # 线程安全地写回
            with result_lock:
                level[source] = paper_level
                logger.debug(json.dumps(paper_level, indent=2, ensure_ascii=False))
        except ValueError as e:
            # 异常仅打印，也可以收集到队列里再统一处理
            print(f"论文level获取失败 (source={source}): {str(e)}")

    # 并行执行
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 启动所有任务
        future_to_source = {
            executor.submit(_process_one_source, src, paps): src
            for src, paps in f_papers.items()
        }
        # 等待全部完成
        for fut in concurrent.futures.as_completed(future_to_source):
            # fut.result() 会把线程内的异常抛出来，这里不处理就吞掉
            try:
                fut.result()
            except Exception as e:
                src = future_to_source[fut]
                print(f"线程异常 (source={src}): {e}")

    # for source, papers in f_papers.items():
    # # 获取过滤提示并调用大模型
    #     messages = get_paper_filter_prompt(state,papers)
    #     try:
    #         paper_level = get_validated_response(
    #             llm,
    #             messages,
    #             validate_papers
    #         )
    #         result[source] =paper_level
    #         logger.debug(json.dumps(paper_level, indent=2, ensure_ascii=False))
    #     except ValueError as e:
    #         print(f"论文level获取失败: {str(e)}")

    # 根据大模型的结果，过滤论文
    filtered_dict, result, num_papers = filter_dicts_with_stats(retrieval_papers, level)
    logger.debug(result)
    # 滤掉所有搜索到的论文，则跳到self_reflection节点
    if num_papers == 0 and num_self_reflection < 2:
        return Command(
            goto="self_reflection",
        )

    # 更新状态并继续下一个Step
    papers_filtered.append(filtered_dict)
    return Command(
        update={
            "num_self_reflection": 0,  # 重置反思计数器
            "current_plan_index": current_step_index + 1,  # 移至下一步
            "papers_filtered": papers_filtered,  # 保存过滤结果
        },
        goto="paper_search",  # 返回论文搜索节点
    )


@node_monitor
def self_reflection_node(state: State) -> Command[Literal["paper_search"]]:
    """自我反思节点：调整研究计划"""
    logger.info("Self Reflection Node is running.")
    # print("Self Reflection Node is running.")
    # 获取反思提示并调用大模型
    parser = PydanticOutputParser(pydantic_object=LogicalChain_model)
    format_str = parser.get_format_instructions()
    self_reflection_prompt = get_self_reflection_prompt(state, format_str)
    try:
        curr_plan = get_validated_response(
            json_model,
            self_reflection_prompt,
            validate_logical_chain
        )
        logger.debug(json.dumps(curr_plan, indent=2, ensure_ascii=False))
    except ValueError as e:
        print(f"逻辑链获取失败: {str(e)}")
    # 使用新的plan进行论文搜索，跳到论文搜索节点
    return Command(
        update={
            "current_plan": curr_plan,
        },
        goto="paper_search",
    )


@node_monitor
def paper_rerank_download_node(state: State) -> Command[Literal["reporter"]]:
    """筛选出值得阅读的论文，并下载论文的pdf"""
    logger.info("Paper Rerank and Download is running.")
    # 加载节点的配置
    node_config = cfg.get_node_params("paper_rerank_download_node")

    # print("Paper Rerank is running.")
    papers = state["papers_filtered"]
    # 并行处理所有步骤的论文，包括了论文排序和论文下载
    paper_read_path, abs_read = process_all_paper(papers, node_config)
    # 跳到reporter节点
    return Command(
        update={
            "paper_pdf_dir": paper_read_path,
            "paper_abs_read": abs_read,
        },
        goto="reporter",
    )


@node_monitor
def reporter_node(state: State):
    """报告生成节点"""
    logger.info("Reporter Node is running.")
    plan = state["current_plan"]
    paper_read_list = state["paper_pdf_dir"]
    abs_read_list = state["paper_abs_read"]
    query = state["messages"][-1].content
    # 并行阅读所有步骤的内容：先对每个步骤中下载好的论文进行paper read得到一小段总结的内容，然后和其他的、需要阅读摘要的内容总结为当前step的内容
    content = asyncio.run(run_all_steps(query, plan, paper_read_list, abs_read_list, text_model))
    # 总结所有step的内容.
    messages = get_report_prompt(plan=plan["steps"], content=content, user_query=query)
    result = text_model.invoke(messages).content
    # save_markdown(result, "ai_output.md")
    return Command(
        update={
            "final_report": result
        }
    )
