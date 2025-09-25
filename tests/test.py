# -*- coding: utf-8 -*-
import os
from typing import List

from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

# 2. 把 TS 接口翻译成 Pydantic 模型
class PaperLevel(BaseModel):
    reason: str = Field(description="The reason for classifying the paper into this level")
    level: int = Field(description="The level of the paper: 1, 2, or 3")
    title: str = Field(description="The title of the paper")

class Papers(BaseModel):
    Papers: List[PaperLevel] = Field(description="The level of all papers")

# # 3. 初始化大模型
# llm = ChatOpenAI(
#     openai_api_key=os.getenv("OPENAI_API_KEY"),
#     model="gpt-4-turbo-preview",
#     temperature=0
# )

# 4. 创建 Parser：负责
#    - 生成格式说明（JSON Schema + 中文提示）
#    - 解析 LLM 输出并自动校验
parser = PydanticOutputParser(pydantic_object=Papers)

print(parser.get_format_instructions())

# # 5. 组装 Prompt：把“格式要求”注入模板
# prompt = PromptTemplate(
#     template="请根据用户提供的论文信息，按下面格式返回 JSON 结果。\n{format_instructions}\n\n用户输入：{query}\n",
#     input_variables=["query"],
#     partial_variables={"format_instructions": parser.get_format_instructions()}
# )
#
# # 6. 构建链
# chain = prompt | llm | parser
#
# # 7. 调用示例
# if __name__ == "__main__":
#     user_input = """
#     论文1：标题《Graph Neural Networks for Social Recommendation》，创新一般，引用 120 次。
#     论文2：标题《Attention Is All You Need》，突破性工作，引用 5 万+。
#     论文3：标题《A Survey on Deep Learning》，综述文章，引用 2000 次。
#     """
#     result: Papers = chain.invoke({"query": user_input})
#     print("结构化结果：", result)
#     # 访问单条数据
#     for p in result.Papers:
#         print(p.title, "-> 等级", p.level, "原因：", p.reason)