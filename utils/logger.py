import logging
import os
import sys
import io
from logging.handlers import RotatingFileHandler
from config import Config

def setup_logger(name='harbor-backend'):
    """配置日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    logger.propagate = False
    try:
        logger.handlers.clear()
    except Exception:
        logger.handlers = []
    
    class SafeConsoleHandler(logging.StreamHandler):
        def emit(self, record):
            try:
                super().emit(record)
            except UnicodeEncodeError:
                try:
                    msg = self.format(record)
                    safe = msg.encode('ascii', 'replace').decode('ascii')
                    self.stream.write(safe + self.terminator)
                    self.flush()
                except Exception:
                    pass

    # 尝试将控制台编码设置为 UTF-8，不可用时自动降级为 ASCII 替换
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        stdout_stream = sys.stdout
    except Exception:
        try:
            stdout_stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except Exception:
            stdout_stream = sys.stdout
    console_handler = None
    
    # 文件处理器
    try:
      os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
    except Exception:
      pass
    file_handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    if not logger.handlers:
        if console_handler:
            logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger
