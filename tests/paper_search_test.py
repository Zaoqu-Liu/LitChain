import asyncio
from tools.pubmed_search import pubmed_search
from tools.biorxiv_search import biorxiv_search
from tools.medrxiv_search import medrxiv_search


async def parallel_search(query: str) -> dict:
    # 创建任务列表
    tasks = [
        asyncio.create_task(biorxiv_search(query)),
        asyncio.create_task(medrxiv_search(query)),
        asyncio.create_task(pubmed_search(query))
    ]

    # 并行执行并等待所有任务完成
    results = await asyncio.gather(*tasks)

    # 整理结果到字典
    return {
        "biorxiv": results[0],
        "medrxiv": results[1],
        "pubmed": results[2]
    }


# 执行示例
if __name__ == "__main__":
    query = "cancer immunotherapy"
    results = asyncio.run(parallel_search(query))

    print(f"Results for query: '{query}'")
    for source, papers in results.items():
        print(f"\n{source.upper()} found {len(papers)} papers:")
        for paper in papers:
            print(f" - {paper}")