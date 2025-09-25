import os
import yaml
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict

class ConfigManager:
    def __init__(self, cfg_path: Path = None):
        # 默认读取项目根目录下的 config.yaml
        if cfg_path is None:
            cfg_path = Path(__file__).parent.parent / "config.yaml"
        with open(cfg_path, "r", encoding="utf-8") as f:
            raw_yaml = yaml.safe_load(f) or {}

        # 扁平化后再与环境变量合并，实现「YAML 为空 → 读环境变量」
        self._cfg = self._merge_env(raw_yaml)

    # ---------- 对外快捷属性 ----------
    @property
    def openai_api_base(self) -> str:
        return self._cfg.get("OPENAI_API_BASE") or os.getenv("OPENAI_API_BASE", "")

    @property
    def openai_api_key(self) -> str:
        return self._cfg.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "")

    @property
    def text_model(self) -> str:
        return self._cfg.get("text_model")

    @property
    def json_model(self) -> str:
        return self._cfg.get("json_model")

    @property
    def max_workers(self) -> int:
        return self._cfg.get("max_workers") or os.getenv("MAX_WORKERS", 10)

    @property
    def log_dir(self) -> str:
        log_cfg = self._cfg.get("LOG", {})
        return log_cfg.get("log_dir") or os.getenv("LOG_LOG_DIR", "paperagent.log")

    # ---------- 节点参数 ----------
    def get_node_params(self, node: str) -> Dict[str, Any]:
        node_cfg = self._cfg.get("nodes", {}).get(node, {})
        # 节点级环境变量：RETRIEVER_TOP_K=10 ...
        return self._merge_env(node_cfg, prefix=node.upper())

    # ---------- 通用合并工具 ----------
    def _merge_env(self, d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        递归合并环境变量：
          - 扁平键：OPENAI_API_BASE
          - 嵌套键：LOG_LOG_DIR
          - 节点键：RETRIEVER_TOP_K
        """
        out = {}
        for k, v in d.items():
            env_key = f"{prefix}_{k}".upper() if prefix else k.upper()
            if isinstance(v, dict):
                out[k] = self._merge_env(v, prefix=env_key)
            else:
                # YAML 为空/None → 读环境变量 → 仍为空则保持 None
                val = v if v is not None else os.getenv(env_key)
                out[k] = val
        return out

# 对外接口
@lru_cache
def get_cfg() -> ConfigManager:
    return ConfigManager()