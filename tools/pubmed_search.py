import asyncio

from Bio import Entrez
import ssl
import os
import pandas as pd

_api_key = os.getenv("PUBMED_API_KEY")

ssl._create_default_https_context = ssl._create_unverified_context

# 全局缓存，避免每次查找IF都重新读文件
_journal_if_map = None


async def pubmed_search(query, max_results=10, sort="relevance"):
    """
    根据用户输入查询pubmed论文
    :param query：用户搜索关键词（字符串）
    :param max_results：返回结果数量（默认 3）
    :param sort：查询方式（默认 relevance）
    :return: 包含论文信息的字典列表
    """
    # 设置邮箱和API key（NCBI要求）
    Entrez.email = "z2654697613@gmail.com"  # 请替换为你的邮箱
    Entrez.api_key = _api_key

    # 第一步：搜索PubMed获取ID列表,返回最相关的数据
    with Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort=sort) as handle:
        record = Entrez.read(handle)
        id_list = record["IdList"]
    if not id_list:
        print("未找到相关论文")
        print(query)
        return []
    # 第二步：获取论文详细信息
    with Entrez.efetch(db="pubmed", id=id_list, rettype="pdf", retmode="xml") as handle:
        records = Entrez.read(handle)

    papers = []
    for record in records['PubmedArticle']:
        article = record['MedlineCitation']['Article']
        # 获取论文出版日期
        # 根据不同的情况获取论文出版日期
        article_date = ''
        if article["ArticleDate"]:
            article_date = article_date + str(article["ArticleDate"][0]["Year"]) + '-' + str(
                article["ArticleDate"][0]["Month"]) + '-' + \
                           str(article["ArticleDate"][0]["Day"])
        elif article["Journal"]["JournalIssue"]["PubDate"]:
            pub_date = article["Journal"]["JournalIssue"]["PubDate"]

            if "Month" in pub_date:
                article_date = article_date + str(pub_date["Year"]) + '-' + _convert_to_month_number(
                    str(pub_date["Month"]))
                if "Day" in pub_date:
                    article_date = article_date + '-' + str(pub_date["Day"])
        article_id_list = record["PubmedData"]["ArticleIdList"]
        # 获取论文相关ID
        PMID = ''
        PMCID = ''
        doi = ''
        for id in  article_id_list:
            if id.attributes.get('IdType') == 'pubmed':
                PMID = str(id)
            elif  id.attributes.get('IdType') == 'pmc':
                PMCID = str(id)
            elif id.attributes.get('IdType') ==  'doi' :
                doi = str(id)
        # print(f"PMID:{PMID},PMCID:{PMCID}.\n")
        # issn的提取
        # 某些情况下是没有issn的，比如当一篇文章是来自预印本时。'Journal_Title': 'medRxiv : the preprint server for health sciences'
        issn = article['Journal'].get("ISSN",'N/A')
        # 提取论文其他的信息
        paper_info = {
            "Title": str(article.get('ArticleTitle', 'N/A')),  # 论文题目
            "Abstract": str(article.get('Abstract', {}).get('AbstractText', ['N/A'])[0]),  # 论文摘要
            "PMID": PMID, # 论文PMID
            "PMCID": PMCID, #论文PMCID
            "DOI": doi,  #论文DOI
            "Journal_Title": str(article['Journal']["Title"]),  # 论文出版期刊全称
            "ISO_Abbreviation": str(article['Journal']["ISOAbbreviation"]),  # 论文出版期刊简称
            "Journal_Score": str(_get_impact_factor(issn)),  # 论文出版期刊综合分数
            "ISSN": str(issn),  # 论文出版期刊ISSN
            "ArticleDate": str(article_date),  # 论文出版时间
            "URL": str(_get_pubmed_url(record['MedlineCitation']['PMID'])),  # 论文访问地址

        }
        papers.append(paper_info)
    return papers


def _get_pubmed_url(pmid):
    """通过 PMID 返回 PubMed 论文的完整 URL"""
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def _convert_to_month_number(abbr):
    """将月份简称转化为对应数字"""
    if abbr:
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }
        # 处理大小写
        return month_map.get(abbr.capitalize(), "Invalid month abbreviation")
    else:
        return "None"


def _get_impact_factor(journal_name: str, excel_path: str = r"./data/journal_scores.xlsx") -> str | None:
    """
    根据期刊名返回对应的 IF（Impact Factor）。

    参数
    ----
    journal_name : str
        要查询的期刊名。
    excel_path : str, optional
        CSV 文件路径，默认 "./2024JCR.xlsx"。

    返回
    ----
    str | None
        对应期刊的 IF；若未找到则返回 None。
    """
    global _journal_if_map

    # 首次调用时加载并缓存
    if _journal_if_map is None:
        df = pd.read_excel(excel_path)
        # 自动识别列名（允许中英文）
        journal_col = "eISSN"
        if_col = "Score"
        # 创建小写去空格后的映射
        _journal_if_map = {
            str(k).strip().lower(): str(v)
            for k, v in zip(df[journal_col], df[if_col])
        }

    key = str(journal_name).strip().lower()
    return _journal_if_map.get(key)


if __name__ == "__main__":
    user_query = "depression AND geographic variation"
    papers = asyncio.run(pubmed_search(user_query, max_results=10))
    print(papers)
