# -*- coding: utf-8 -*-
import asyncio
from concurrent.futures import ThreadPoolExecutor
from prompt.render import get_paper_read_prompt, get_paper_merge_prompt
from langchain_community.document_loaders import UnstructuredPDFLoader

# 全局线程池，按需调大小
executor = ThreadPoolExecutor(max_workers=8)


async def _deal_pdf_async(file_path) -> str:
    loader = UnstructuredPDFLoader(
        file_path=file_path,
        mode="elements",
        strategy="fast"
    )
    # 在线程池里执行阻塞的 loader.load()
    loop = asyncio.get_running_loop()
    docs = await loop.run_in_executor(None, loader.load)
    # 过滤 + 拼接
    text_docs = [d for d in docs if d.metadata.get("category") == "NarrativeText"]
    full_text = "\n".join(d.page_content for d in text_docs)
    return full_text


async def _read_one_paper(query,step: dict, file_path: str, llm) -> str:
    """并发提取文本 + 并发调用大模型"""
    # 1. 提取文本（异步）
    pdf_text = await _deal_pdf_async(file_path)

    # 2. 构造 prompt
    messages = get_paper_read_prompt(
        user_query=query,
        verification_Point=step["Verification_Point"],
        purpose=step["purpose"],
        paper_content=pdf_text
    )

    # 3. 把阻塞的 llm.invoke 扔到线程池
    loop = asyncio.get_running_loop()
    answer = await loop.run_in_executor(executor, llm.invoke, messages)
    return answer.content


async def _read_many_papers(query,step, files_list, llm):
    """steps_and_files = [(step, file_path), ...]"""
    tasks = [_read_one_paper(query,step, fp, llm) for fp in files_list]
    return await asyncio.gather(*tasks)


async def _process_one_step(query,step, paper_list, abs_list, llm):
    """处理单个 step 的全部逻辑"""
    # 1. 解析字段
    save_paths = [p['save_path'] for p in paper_list]
    urls = [p['URL'] for p in paper_list]
    titles = [p['Title'] for p in paper_list]

    # 2. 并发读论文
    paper_content_list = await _read_many_papers(query,step, save_paths, llm)

    # 3. 组装 prompt
    papers_content = [
        {"content": c, "url": u, "Title": t}
        for c, u, t in zip(paper_content_list, urls, titles)
    ]
    papers_content.extend(abs_list)

    messages = get_paper_merge_prompt(
        user_query=query,
        verification_Point=step["Verification_Point"],
        purpose=step["purpose"],
        papers_content=papers_content
    )

    # 4. 调用 LLM
    result = await llm.ainvoke(messages)
    return result.content


async def run_all_steps(query,plan, paper_read_list, abs_read_list, llm):
    """并发跑完所有 step"""
    tasks = [
        _process_one_step(query,step, plist, alist, llm)
        for step, plist, alist in zip(plan["steps"], paper_read_list, abs_read_list)
    ]
    # 按原始顺序收集结果
    return await asyncio.gather(*tasks)


# def main():
#     # 设置模型名称（可在环境变量中切换）
#     model = "claude-3-7-sonnet-20250219"
#     # model = "claude-sonnet-4-20250514"
#     # 从环境变量获取API密钥和基础URL
#     api_key = os.getenv('OPENAI_API_KEY')
#     base_url = os.getenv("OPENAI_API_BASE")
#     llm = ChatOpenAI(model=model, api_key=api_key, base_url=base_url)
#     content = asyncio.run(run_all_steps(plan, paper_read_list, abs_read_list, llm))
#     messages = get_report_prompt(plan=plan["steps"], content=content,user_query=query)
#     result = llm.invoke(messages).content
#     save_markdown(result, "ai_output.md")
# print(result)


# if __name__ == '__main__':
#     # file_path = r"D:\project\paperagent\papers\test\10.1016_j.neuron.2022.09.021.pdf"
#     # step = plan["steps"][0]
#     # paper_read(step,file_path)
#     start_time = time.time()
#     main()
#     print(time.time()-start_time)
