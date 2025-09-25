# -*- coding: utf-8 -*-
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from config import get_cfg

# logger配置
_cfg = get_cfg()
_log_cfg = _cfg._cfg.get("logging", {})

# ----------- 基础参数 -----------
LOG_LEVEL = _log_cfg.get("level", "INFO").upper()
LOG_DIR   = Path(_log_cfg.get("log_dir", "logs")).resolve()
LOG_FILE  = LOG_DIR / _log_cfg.get("filename", "paperagent.log")
MAX_BYTES = int(_log_cfg.get("max_bytes", 10_000_000))
BACKUP    = int(_log_cfg.get("backup_count", 5))
CONSOLE   = bool(_log_cfg.get("console", True))
FMT       = _log_cfg.get("format",
            "%(asctime)s [%(levelname)s] %(name)s | %(message)s")

# ----------- 初始化 -----------
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 根 logger
root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)

# 避免重复添加 handler（reload 时）
for h in root_logger.handlers[:]:
    root_logger.removeHandler(h)

# 文件 handler（按大小滚动）
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP, encoding="utf-8")
file_handler.setFormatter(logging.Formatter(FMT))
root_logger.addHandler(file_handler)

# 控制台 handler（可选彩色）
if CONSOLE:
    try:
        import coloredlogs
        coloredlogs.install(level=LOG_LEVEL, fmt=FMT)
    except ImportError:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter(FMT))
        root_logger.addHandler(console)

# ----------- 对外 API -----------
def get_logger(name: str) -> logging.Logger:
    """
    任何地方：
        from logger import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)