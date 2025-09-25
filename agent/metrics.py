# -*- coding: utf-8 -*-
import asyncio, time, functools
import threading
from typing import Callable
from logger import get_logger
logger = get_logger(__name__)

_summary_lock = threading.Lock()
_node_times: dict[str, float] = {}

# 一键清零时间
def reset_time_stats():
    global _node_times
    with _summary_lock:
        _node_times.clear()

# ================= 运行时间测量 =================
# 函数装饰器，用于记录函数的运行时间
def node_monitor(func: Callable) -> Callable:
    """既可用于 sync 也可用于 async 节点"""
    name = func.__name__

    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def _async_wrapper(*args, **kwargs):
            st = time.perf_counter()
            result = await func(*args, **kwargs)          # 这里是 await
            cost = time.perf_counter() - st
            with _summary_lock:
                _node_times[name] = _node_times.get(name, 0.0) + cost
            return result
        return _async_wrapper
    else:
        @functools.wraps(func)
        def _sync_wrapper(*args, **kwargs):
            st = time.perf_counter()
            result = func(*args, **kwargs)
            cost = time.perf_counter() - st
            with _summary_lock:
                _node_times[name] = _node_times.get(name, 0.0) + cost
            return result
        return _sync_wrapper

# 记录各个节点的总结
def dump_summary():
    with _summary_lock:
        total = sum(_node_times.values())
        logger.info("========== 汇总 ==========")
        logger.info(f"总时长: {total:.3f}s")
        for n, t in _node_times.items():
            logger.info(f"  {n}: {t:.3f}s")

# ================= token测量 =================
from langchain.callbacks.base import BaseCallbackHandler
class TokenCounter(BaseCallbackHandler):
    def __init__(self):
        self.prompt_tokens   = 0
        self.completion_tokens = 0

    def on_llm_end(self, response, **kwargs) -> None:
        # OpenAI / ChatOpenAI 的 response.llm_output 格式
        usage = response.llm_output.get('token_usage', {})
        self.prompt_tokens   += usage.get('prompt_tokens', 0)
        self.completion_tokens += usage.get('completion_tokens', 0)

    def total(self):
        return self.prompt_tokens + self.completion_tokens

    def reset(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0

token_cb = TokenCounter()

# 清零token
def reset_token_stats():
    token_cb.reset()