# -*- coding: utf-8 -*-
from datetime import datetime
import os
from tests.DGG import paper
from tools.paper_download import download_paper
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def _parse_date(date_str):
    """
    解析三种格式的日期字符串：
    1. "YYYY-MM-DD" (完整日期)
    2. "YYYY-MM" (年月)
    3. "" (空字符串)

    返回datetime对象，无效日期或者空字符串返回2000-01-01
    """
    if not date_str:
        return datetime.strptime("2000-01-01", "%Y-%m-%d")

    # 尝试完整日期格式
    if len(date_str) == 10:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            pass

    # 尝试年月格式
    if len(date_str) == 7:
        try:
            # 将年月格式转换为该月的第一天
            return datetime.strptime(date_str + "-01", "%Y-%m-%d")
        except:
            pass

    # 尝试其他可能的格式
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        try:
            return datetime.strptime(date_str, "%Y-%m")
        except:
            return datetime.strptime("2000-01-01", "%Y-%m-%d")


def _sort_single_step(step):
    """
        处理单个步骤的论文排序，并打印排序摘要
        :param step: 包含三个来源论文列表的字典
        :return: 排序后的论文列表
        """
    # 合并所有来源的论文
    # print(step)
    all_papers = []
    for source in ['biorxiv', 'medrxiv', 'pubmed']:
        all_papers.extend(step.get(source, []))


    # 去重论文
    seen = {}
    for item in all_papers:
        title = item["Title"]
        if title not in seen:
            seen[title] = item
    all_papers = list(seen.values())
    # 按Level分组
    level1_papers = [p for p in all_papers if p['Level'] == 1]
    level2_papers = [p for p in all_papers if p['Level'] == 2]

    # 通用排序函数
    def paper_sort_key(paper):
        # 来源优先级：PubMed优先（1表示PubMed，0表示其他）
        source_priority = 1 if 'PMID' in paper else 0

        # 期刊分数处理
        score_str = paper.get('Journal_Score', '')
        try:
            score = float(score_str) if score_str else None
        except:
            score = None

        # 日期处理 - 使用新的parse_date函数
        date_str = paper.get('ArticleDate', '')
        date_obj = _parse_date(date_str)
        # 排序优先级:
        return (
            -source_priority,  # PubMed论文优先
            0 if score is not None else 1,  # 有分数优先
            -score if score is not None else float('inf'),  # 分数降序
            -date_obj.timestamp()  # 日期降序
        )

    # 执行排序
    sorted_level1 = sorted(level1_papers, key=paper_sort_key)
    sorted_level2 = sorted(level2_papers, key=paper_sort_key)
    sorted_papers = sorted_level1 + sorted_level2
    # 打印排序摘要
    # print_result(sorted_level1,sorted_level2,sorted_papers)
    return sorted_papers


# 创建pdf文档保存路径，增加时间戳
def _create_paper_folder(save_dir: str = None) -> str:
    """
    在项目根目录下的 papers 文件夹内创建一个带当天日期 + 时分秒时间戳的子目录，
    并返回其绝对路径。
    """
    # 1. 项目根目录：默认取当前脚本所在目录的父目录（.. 一级）
    if save_dir is None:
        save_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 2. 组装目标目录名
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H%M%S")
    folder_name = f"papers_{date_str}_{time_str}"
    target_dir = os.path.join(save_dir, "papers", folder_name)

    # 3. 创建目录（已存在则跳过）
    os.makedirs(target_dir, exist_ok=True)
    return target_dir


def paper_reRank_download(papers,save_dir,config,max_workers=10):
    papers = _sort_single_step(papers)
    READ_PAPER_NUM = config["READ_PAPER_NUM"]          # 最多成功下载 3 篇
    ABS_PAPER_NUM  = config["ABS_PAPER_NUM"]          # 额外保留 3 篇摘要
    paper_read = []
    abs_read = []
    # 线程池提交所有任务
    papers_to_try = papers[:READ_PAPER_NUM]
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_paper = {
            pool.submit(download_paper, paper, save_dir): paper
            for paper in papers_to_try
        }

        # 按完成顺序收集结果
        for future in as_completed(future_to_paper):
            paper = future_to_paper[future]
            try:
                result, save_path = future.result()
            except Exception as e:
                # 网络异常等
                result, save_path = False, None

            if result:
                paper_read.append({
                    "save_path": str(save_path),
                    "URL": paper["URL"],
                    "Title": paper["Title"]
                })
                # print(f"论文下载成功：{save_path}")
            else:
                abs_read.append({
                    "content": paper["Abstract"],
                    "url": paper["URL"],
                    "Title": paper["Title"]
                })
                # print(f"论文下载失败：{paper['DOI']}")

            # print("\n" + "=" * 50 + "\n")

            # 一旦成功下载了 READ_PAPER_NUM 篇，立即取消其余任务并跳出循环
            if len(paper_read) >= READ_PAPER_NUM:
                for f in future_to_paper:
                    f.cancel()
                break
    processed_urls = {p.get("Title") for p in paper_read + abs_read}
    remaining = [p for p in papers if p.get("Title") not in processed_urls]
    for paper in remaining:
        if len(abs_read) >= ABS_PAPER_NUM:
            break
        if len(abs_read) >0:
            seen_titles = {abs_read_paper["Title"] for abs_read_paper in abs_read}
        else:
            seen_titles ={}
        if paper["Title"] not in seen_titles:
            abs_read.append({
                "content": paper["Abstract"],
                "url": paper["URL"],
                "Title": paper["Title"]
            })

    # 摘要条数截断
    abs_read = abs_read[:ABS_PAPER_NUM]

    return paper_read, abs_read


def process_all_paper(papers,config):
    save_dir = _create_paper_folder(save_dir=config["paper_save_dir"])
    # print(save_dir)
    paper_read_path = []
    abs_read = []
    # 使用线程池并行下载
    with ThreadPoolExecutor() as executor:
        # 提交所有任务
        futures = [executor.submit(paper_reRank_download, paper, save_dir, config) for paper in papers]
        # 收集结果
        for future in as_completed(futures):
            paper_read, abs_read_single = future.result()
            paper_read_path.append(paper_read)
            abs_read.append(abs_read_single)

    return paper_read_path, abs_read

if __name__ == "__main__":
    from config import get_cfg
    cfg = get_cfg()
    node_config = cfg.get_node_params("paper_rerank_download_node")
    start_time = time.time()
    paper_read_path, abs_read = process_all_paper(paper,node_config)
    endtime= time.time()
    print("论文下载时间花费：",endtime-start_time)
    print(paper_read_path)
    print(abs_read)
    # 下载PMC全文（仅限开放获取）
