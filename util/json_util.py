import logging
import json
import json_repair
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)


def repair_json_output(content: str) -> str:
    """
    Repair and normalize JSON output.

    Args:
        content (str): String content that may contain JSON

    Returns:
        str: Repaired JSON string, or original content if not JSON
    """
    content = content.strip()
    if content.startswith(("{", "[")) or "```json" in content or "```ts" in content:
        try:
            # If content is wrapped in ```json code block, extract the JSON part
            if content.startswith("```json"):
                content = content.removeprefix("```json")

            if content.startswith("```ts"):
                content = content.removeprefix("```ts")

            if content.endswith("```"):
                content = content.removesuffix("```")

            # Try to repair and parse JSON
            repaired_content = json_repair.loads(content)
            return json.dumps(repaired_content, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"JSON repair failed: {e}")
    return content


def validate_logical_chain(data: Dict[str, Any]) -> bool:
    """
    验证JSON结构是否符合logical_chain接口规范
    """
    try:
        # 检查顶层字段
        if not all(key in data for key in ['thought', 'Logical_chain', 'steps']):
            return False

        # 检查字段类型
        if not isinstance(data['thought'], str) or not isinstance(data['Logical_chain'], str):
            return False

        # 检查steps数组
        steps = data['steps']
        if not isinstance(steps, list):
            return False

        # 检查每个step对象
        for step in steps:
            if not all(k in step for k in ['relationship', 'purpose', 'Verification_Point', 'Step_query']):
                return False
            if not all(
                    isinstance(step[k], str) for k in ['relationship', 'purpose', 'Verification_Point', 'Step_query']):
                return False

        return True
    except Exception:
        return False


def validate_papers(papers_list: list) -> bool:
    """验证论文分级JSON结构"""
    try:
        # 检查顶层字段
        if not all(key in papers_list for key in ['Papers']):
            return False
        papers = papers_list["Papers"]
        if not isinstance(papers, list):
            return False
        # 检查每篇论文
        for paper in papers:
            if not all(k in paper for k in ['reason', 'level', 'title']):
                return False
            if not isinstance(paper['reason'], str) or not isinstance(paper['title'], str):
                return False
            if not isinstance(paper['level'], int) or paper['level'] not in [1, 2, 3]:
                return False
        return True
    except Exception:
        return False


def get_validated_response(llm, messages, validator: Callable, max_retries=5) -> Dict[str, Any]:
    """
    通用验证响应获取函数
    - llm: 大模型实例
    - messages: 输入消息
    - validator: 验证函数 (validate_logical_chain 或 validate_papers)
    - max_retries: 最大重试次数
    """
    for attempt in range(max_retries):
        raw_content = ""
        try:
            # 获取大模型原始响应
            raw_content = llm.invoke(messages).content
            # print(raw_content)
            # 修复JSON格式
            repaired_json = repair_json_output(raw_content)

            # 尝试解析JSON
            parsed_data = json.loads(repaired_json)

            # 验证数据结构
            if validator(parsed_data):
                return parsed_data
            else:
                print(f"验证失败 (尝试 #{attempt + 1}/{max_retries})")
                # print(f"问题数据: {json.dumps(parsed_data, indent=2)[:500]}...")
                # print(messages)
                # print("========")
                # print(raw_content)# 打印部分问题数据
        except (json.JSONDecodeError, TypeError) as e:
            print(f"JSON解析错误: {str(e)}，尝试 #{attempt + 1}/{max_retries}")
            print(f"原始响应片段: {raw_content[:200]}...")

    raise ValueError(f"无法获取有效JSON格式的响应，超过最大重试次数{max_retries}")