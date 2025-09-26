# -*- coding: utf-8 -*-
from matplotlib import image as mpimg, pyplot as plt
import io

from util.save_markdown import save_markdown
from agent.gragh import graph
from agent.metrics import dump_summary, token_cb
import asyncio
import dotenv
import time
from logger import get_logger

import warnings

warnings.filterwarnings("ignore")

logger = get_logger(__name__)
# 读取env配置
dotenv.load_dotenv()

PROGRAM_T0 = time.perf_counter()  # 程序级开始时间


# 展示图结构
def show_workflow(workflow):
    img_bytes = workflow.get_graph().draw_mermaid_png()
    img = mpimg.imread(io.BytesIO(img_bytes), format='png')
    plt.imshow(img)
    plt.axis('off')
    plt.show()


# ================= 主函数 =================
async def main(user_input, file_save):
    """运行主函数"""
    # show_workflow(graph)  # 显示gragh的结构
    # 示例查询
    user_input = user_input
    # 初始化状态并运行图
    result = await graph.ainvoke({
        "messages": [{
            "role": "user",
            "content": user_input
        }],
        "current_plan_index": 0,
        "num_self_reflection": 0,
        "papers_filtered": [],
        "paper_pdf_dir": [],
        "paper_abs_read": [],
        "step_paper_content": []

    }, {"recursion_limit": 100})
    logger.info("prompt (输入) : %s", token_cb.prompt_tokens)
    logger.info("completion (输出): %s", token_cb.completion_tokens)
    logger.info("total (总) : %s", token_cb.total())
    dump_summary()
    report = result["final_report"]
    save_markdown(report, file_save)
    return report


if __name__ == '__main__':
    # 异步运行主函数
    # config = ConfigManager()
    question = "Investigate Sema3c's role in cancer metastasis: current molecular mechanisms, expression patterns across cancer types, and potential as therapeutic target."
    file_save = "ai_output.md"
    asyncio.run(main(user_input=question, file_save=file_save))
