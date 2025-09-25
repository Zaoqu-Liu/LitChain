# -*- coding: utf-8 -*-
import asyncio
from langchain_core.prompts import ChatPromptTemplate
import json
import os
from langchain_openai import ChatOpenAI

from agent.metrics import reset_time_stats, reset_token_stats
from run import main as reporter
from typing import Final
# ---------- 0. 参数 ----------
VALID_ANSWERS: Final[set[str]] = {"yes", "no", "maybe"}
MAX_RETRY: Final[int] = 3
INPUT_FILE   = r"D:\project\LitChain\pubmedQA_test\test_set.json"  # 原始文件
OUTPUT_FILE  = r"D:\project\LitChain\pubmedQA_test\k2_result.json"  # 结果文件
model = "kimi-k2-0711-preview"
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE")

model = ChatOpenAI(model=model, api_key=api_key, base_url=base_url, max_retries=3)

# prompt构造
ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a rigorous scientific QA judge. "
     "Based solely on the research report below, decide whether the original question can be answered "
     "with high confidence (yes), clearly negated (no), or remains uncertain (maybe). "
     "Answer only one word: yes/no/maybe."),
    ("user", "Research report:\n{report}\n\nOriginal question: {question}")
])

async def judge_answer(question: str,pid:str) -> str:
    """返回 yes / no / maybe"""

    save_dir = r"D:\project\LitChain\pubmedQA_test\result"
    filename =f"{pid}.md"
    report = await reporter(user_input=question,file_save=os.path.join(save_dir,filename))
    # report =""
    chain = ANSWER_PROMPT | model
    for attempt in range(1, MAX_RETRY + 1):
        resp = await chain.ainvoke({"report": report, "question": question})
        ans = resp.content.strip().lower()
        if ans in VALID_ANSWERS:
            return ans
        # 可选：打印日志
        # print(f"[WARN] 第 {attempt} 次回答非法: {ans!r}，重试…")
        await asyncio.sleep(0.2)          # 轻微延迟，避免瞬间爆打

    # 重试耗尽，降级为 maybe
    return "maybe"

async def main():
    # 读取输入
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 加载已有结果
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        results = {}

    # 异步处理并逐个保存
    count = 0
    for pid, v in data.items():
        count =count+1
        if count==41:
            break
        if pid in results:
            continue  # 已处理
        question = v.get("QUESTION")
        if not question:
            continue
        try:
            reset_time_stats()  # 每次任务开始前清零
            reset_token_stats()
            result = await judge_answer(question,pid)
            results[pid] = result

            #  安全写：每完成一个就写回
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[ERROR] 处理 {pid} 失败：{e}")
            continue  # 跳过当前，继续下一个

if __name__ == '__main__':
    # 读取原始文件
    asyncio.run(main())
