import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
DEBUG = bool(os.environ.get("DEBUG", False))


class loggingFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green  
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[41m",   # Red background
        "TIME": "\033[90m",       # Dark gray
        "MODULE": "\033[35m",     # Magenta
        "SEPARATOR": "\033[90m",  # Dark gray
        "HIGHLIGHT": "\033[1m",   # Bold
        "RESET": "\033[0m",
    }
    
    LEVEL_ICONS = {
        "DEBUG": "🔍",
        "INFO": "ℹ️ ",
        "WARNING": "⚠️ ",
        "ERROR": "❌",
        "CRITICAL": "💥"
    }

    def format(self, record):
        levelname = record.levelname
        
        # 取得適當的圖標和顏色
        icon = self.LEVEL_ICONS.get(levelname, "  ")
        
        if sys.stderr.isatty():
            color = self.COLORS.get(levelname, "")
            reset = self.COLORS["RESET"]
            time_color = self.COLORS["TIME"]
            module_color = self.COLORS["MODULE"]
            separator_color = self.COLORS["SEPARATOR"]
            
            # 格式化時間
            now = datetime.now().strftime("%H:%M:%S")
            
            # 格式化模組名稱
            module_name = record.name
            if len(module_name) > 25:
                module_name = "..." + module_name[-22:]
            
            # 格式化訊息
            message = record.getMessage()
            
            # 為特定類型的訊息添加特殊處理
            if "Portfolio response detail:" in message:
                icon = "📊"
            elif "User exists check:" in message:
                icon = "👤"
            elif "/register triggered" in message:
                icon = "📝"
            elif "/pvp triggered" in message:
                icon = "🎯"
            elif "/start triggered" in message:
                icon = "🚀"
            elif "returned status code" in message:
                icon = "🌐"
            elif "正在測試與後端的連線" in message:
                icon = "🔗"
            elif "後端連線成功" in message:
                icon = "✅"
            elif "後端 API 認證成功" in message:
                icon = "🔑"
            elif "初始化" in message:
                icon = "🤖"
                
            return (f"{icon} {color}{levelname.ljust(8)}{reset} "
                   f"{time_color}{now}{reset} "
                   f"{separator_color}│{reset} "
                   f"{module_color}{module_name.ljust(25)}{reset} "
                   f"{separator_color}│{reset} "
                   f"{message}")
        else:
            # 無色彩模式
            now = datetime.now().strftime("%H:%M:%S")
            module_name = record.name
            if len(module_name) > 25:
                module_name = "..." + module_name[-22:]
            
            return f"{icon} {levelname.ljust(8)} {now} | {module_name.ljust(25)} | {record.getMessage()}"


def setup_logger(name: str = None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(loggingFormatter())
        logger.addHandler(handler)

    return logger


def log_separator(logger, title: str = None):
    """添加美觀的分隔線到日誌"""
    if title:
        padding = (50 - len(title)) // 2
        logger.info("═" * padding + f" {title} " + "═" * padding)
    else:
        logger.info("─" * 60)
