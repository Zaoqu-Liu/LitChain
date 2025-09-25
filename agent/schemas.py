# -*- coding: utf-8 -*-
from openai.lib.azure import API_KEY_SENTINEL
from pydantic import BaseModel, Field
from typing import List
from typing import Type, TypeVar, Generic, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

# ================plan节点================
class Step(BaseModel):
    relationship: str = Field(
        description="The logical relationship between this step and the previous step and the logical chain"
    )
    purpose: str = Field(
        description="What is the purpose of this step? Why is this step necessary"
    )
    Verification_Point: str = Field(
        description="The points that need to be verified in this step, "
                    "for example, whether there is any literature indicating the relationship between molecule 1 and molecule 2"
    )
    Step_query: str = Field(
        description='Verification points correspond to queries. The query format requires connecting entities using logical operators; do not replace entities with synonyms, for example: molecule 1 AND molecule 2. Query can only include important entities, not secondary entities such as "relationships" or "environments"'
    )

class LogicalChain_model(BaseModel):
    thought: str = Field(
        description="How to generate a qualified logical chain based on user questions, "
                    "and why this logical chain is the best"
    )
    Logical_chain: str = Field(
        description="The content of logical chain"
    )
    steps: List[Step] = Field(
        description="Steps that need to be verified"
    )

# ================paper filter 节点================
class PaperLevel(BaseModel):
    reason: str = Field(description="The reason for classifying the paper into this level")
    level: int = Field(description="The level of the paper: 1, 2, or 3")

    title: str = Field(description="The title of the paper")

class Papers_model(BaseModel):
    Papers: List[PaperLevel] = Field(description="The level of all papers")


T = TypeVar("T", bound=BaseModel)

class StructuredRetryLLM(Generic[T]):
    """
    包装任意 ChatOpenAI，做结构化输出 + 自动重试
    """
    def __init__(
        self,
        llm: ChatOpenAI,
        output_model: Type[T],
        max_retry: int = 3,
        system_rollback_prompt: Optional[str] = None,
    ):
        self.llm = llm
        self.output_model = output_model
        self.max_retry = max_retry
        self.system_rollback_prompt = system_rollback_prompt or (
            "You are a helpful assistant. "
            "The JSON you just generated did not pass the Pydantic validation. "
            "Below are the validation error(s) and the original JSON. "
            "Please fix all issues and return a new valid JSON object."
        )

    def invoke(self, user_query: str) -> T:
        """单次入口，返回校验通过的 Pydantic 对象"""
        structured_llm = self.llm.with_structured_output(
            self.output_model, include_raw=True
        )

        last_json: Optional[str] = None
        for attempt in range(1, self.max_retry + 1):
            raw_resp = structured_llm.invoke(user_query)
            last_json = raw_resp["raw"].content

            try:
                # 直接让 Pydantic 再解析一次，确保 100% 合规
                return self.output_model.model_validate_json(last_json)
            except ValidationError as e:
                if attempt == self.max_retry:
                    raise RuntimeError(
                        f"Still invalid after {self.max_retry} retries. "
                        f"Last error: {e}"
                    ) from e

                # 构造 rollback 消息
                rollback_messages = [
                    SystemMessage(content=self.system_rollback_prompt),
                    HumanMessage(
                        content=f"Validation error:\n{e}\n\n"
                                f"Original JSON:\n{last_json}\n\n"
                                f"Please provide a corrected JSON object."
                    ),
                ]
                # 用普通 invoke 拿到修正后的 JSON
                correction = self.llm.invoke(rollback_messages)
                user_query = correction.content   # 把修正后的 JSON 当成新的“用户输入”继续循环

        # 理论上不会走到这里
        raise RuntimeError("Unexpected retry loop exit.")


if __name__ == '__main__':
    import os
    base_url = os.getenv("OPENAI_API_BASE")
    api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, base_url=base_url, temperature=0)

    retry_llm = StructuredRetryLLM(llm, LogicalChain_model, max_retry=3)
    result = retry_llm.invoke(
        "Investigate Sema3c's role in cancer metastasis: current molecular mechanisms, "
        "expression patterns across cancer types, and potential as therapeutic target."
    )
    print(result.model_dump_json(indent=2))
