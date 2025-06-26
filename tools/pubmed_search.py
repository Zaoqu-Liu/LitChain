from Bio import Entrez
import datetime
import ssl
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
import os
import time

ssl._create_default_https_context = ssl._create_unverified_context


def search_pubmed(keywords, operator="AND", max_results=3):
    """
    根据用户输入查询pubmed论文
    :param user_query：用户搜索关键词（字符串）
    :param subject_category：学科分类代码（字符串）
    :param date_filter：日期过滤对象（需包含 if_filter 属性和 build_query_string 方法）
    :param max_results：返回结果数量（默认 3）
    :return: 包含论文信息的字典列表
    """
    # 设置邮箱（NCBI要求）
    Entrez.email = "1625015135@qq.com"  # 请替换为你的邮箱
    # download_dir = "./pubmed_paper"
    # 构建full_query
    full_query = f"({operator})".join(keywords)
    # print(full_query)
    try:
        # 第一步：搜索PubMed获取ID列表,返回最相关的前三条数据
        with Entrez.esearch(db="pubmed", term=full_query, retmax=max_results, sort="relevance") as handle:
            record = Entrez.read(handle)
            id_list = record["IdList"]

        if not id_list:
            print("未找到相关论文")
            return []
        # 下载论文
        # for pmc_id in id_list:
        #     download_pdf(pmc_id,download_dir)
        # 第二步：获取论文详细信息
        with Entrez.efetch(db="pubmed", id=id_list, rettype="pdf", retmode="xml") as handle:
            records = Entrez.read(handle)

        papers = []
        for record in records['PubmedArticle']:
            article = record['MedlineCitation']['Article']
            journal = article['Journal']

            # 提取论文信息
            paper_info = {
                "Title": article.get('ArticleTitle', 'N/A'),
                "Abstract": article.get('Abstract', {}).get('AbstractText', ['N/A'])[0],
                "URL": get_pubmed_url(record['MedlineCitation']['PMID'])
            }
            papers.append(paper_info)
        # print(papers)
        return papers

    except Exception as e:
        print(f"搜索过程中出错: {e}")
        return []


def get_pubmed_url(pmid):
    """通过 PMID 返回 PubMed 论文的完整 URL"""
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


if __name__ == "__main__":
    user_query = ["THBS2", "tumor immune therapy"]  # 'lung cancer'
    search_pubmed(user_query)
