# -*- coding: utf-8 -*-
import requests
import re
import os
from europe_pmc import EuropePMC
import ssl
import PyPDF2
from pathlib import Path
from sympy import resultant
ssl._create_default_https_context = ssl._create_unverified_context
email = "z2654697613@gmail.com"
# save_dir = "./papers"

# 删除无法打开的pdf文档
def _safe_delete(path) -> None:
    """静默删除文件，忽略不存在或权限错误。"""
    try:
        os.remove(path)
    except (FileNotFoundError, PermissionError):
        pass


# 验证论文pdf是否下载成功
def is_valid_pdf(filepath: str) -> bool:
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return len(reader.pages) > 0  # 能解析出至少一页
    except Exception as e:
        _safe_delete(filepath)
        raise ValueError(f"无法打开pdf文件: {e}")


def download_unpaywall(doi, filename,save_dir):
    """
        Unpaywall下载论文。
    """
    filename = os.path.join(save_dir, filename)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    # 1. 通过Unpaywall API获取PDF链接
    api_url = f"https://api.unpaywall.org/v2/{doi}?email={email}"  # 修正URL空格问题
    response = requests.get(api_url, headers=headers, timeout=30)
    response.raise_for_status()  # 检查HTTP错误

    data = response.json()
    pdf_url = None

    # 2. 解析最佳PDF链接
    if data.get('best_oa_location'):
        oa_loc = data['best_oa_location']
        pdf_url = oa_loc.get('url_for_pdf') or oa_loc.get('url')

    if not pdf_url:
        raise ValueError(f"No PDF found via Unpaywall for DOI: {doi}")

    # 3. 下载PDF内容
    pdf_response = requests.get(pdf_url, headers=headers, timeout=60)
    pdf_response.raise_for_status()

    # 4. 保存文件
    with open(filename, 'wb') as f:
        f.write(pdf_response.content)
    # 验证pdf的可读性
    result = is_valid_pdf(filename)
    print(f"unpaywall downloading to:{filename}")
    return result


def download_sci_hub(doi, filename,save_dir):
    """
    sci_hub下载论文。
    """
    filename = os.path.join(save_dir, filename)
    scihub_url = (f''
                  f''
                  f'')  # 修正URL空格问题
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"
    }
    r = requests.get(scihub_url, headers=headers)
    r.raise_for_status()

    # 检查内容是否为PDF（防止下载到错误页面）
    if not r.headers.get('Content-Type', '').lower().startswith('application/pdf'):
        raise ValueError("Sci-Hub returned non-PDF content")
    # 保存文件（使用统一路径）
    with open(filename, 'wb') as f:
        f.write(r.content)
    result = is_valid_pdf(filename)
    print(f"sci_hub downloading to:{filename}")
    return result


def download_europe_pmc(PMCID,filename,save_dir):
    """
        利用europe_pmc下载论文。
    """

    paper = EuropePMC().fetch(PMCID)
    paper.save(outfile=filename, outdir=save_dir)
    filename = os.path.join(save_dir, filename)
    result = is_valid_pdf(filename)
    print(f"europe_pmc downloading to:{filename}")
    return result


def make_pdf_filename(title: str) -> str:
    """
    根据论文标题生成 pdf 文件名（前 50 字符，不足则全保留）。
    """
    # 1. 清理非法字符
    safe = re.sub(r'[<>:\"/\\|?*\x00-\x1f]', '', title.strip())
    safe = re.sub(r'\s+', '_', safe)          # 空格→下划线
    # 2. 截取或全保留
    safe = safe[:50] if len(safe) > 50 else safe
    # 3. 拼接扩展名
    return f"{safe}.pdf"


def sanitize_id(doi: str) -> str:
    """把 DOI 或 arXiv ID 转成安全文件名"""
    return re.sub(r'[^\w\-_.]', '_', doi)+'.pdf'


def download_paper(paper,save_dir):
    """
    综合下载器：优先 Europe PMC → 其次 Unpaywall → 最后 Sci-Hub
    """

    # 提取论文ID
    doi = ''
    PMCID = ''
    if 'DOI' in paper:
        doi = paper['DOI']
    if 'PMCID' in paper:
        PMCID = paper['PMCID']
    if not doi and not PMCID:
        return False,None

    # 文件名清理
    filename = sanitize_id(paper['DOI'])
    # 判断是否已经下载，若已经下载了，直接返回True
    save_path = Path(os.path.join(save_dir,filename))
    if save_path.is_file():
        return True,save_path
    # 1) 有 PMCID 就优先尝试 Europe PMC
    if PMCID:
        try:
            result = download_europe_pmc(PMCID,filename,save_dir)
            return result,save_path
        except Exception as e:
            # print(f"europe_pmc failed: {str(e)}. Trying Unpaywall...")
            pass  # 失败就继续下一步

    # 2) 用 Unpaywall
    try:
        result = download_unpaywall(doi,filename,save_dir)
        return result,save_path
    except Exception as e:
        # print(f"Unpaywall failed: {str(e)}. Trying sci_hub...")
        pass  # 失败就继续下一步
        # 3) 兜底：Sci-Hub
    try:
        result = download_sci_hub(doi,filename,save_dir)
        return result,save_path
    except Exception as e:
        # print(f"Both methods failed for paper {doi}: {str(e)}")
        pass
        # 全部失败
    return False,None


