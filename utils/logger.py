# utils/logger.py
"""Logging configuration for AVCS DNA Industrial Monitor"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

# Try to import settings, but don't fail if not available
try:
    from modules.config import settings
    LOG_FILE = settings.LOG_FILE if hasattr(settings, 'LOG_FILE') else "logs/app.log"
    LOG_LEVEL = settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO"
except (ImportError, AttributeError):
    LOG_FILE = "logs/app.log"
    LOG_LEVEL = "INFO"

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # Colors for different log levels
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add timestamp
        record.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add color for console output
        if hasattr(record, 'color') and record.color:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

def setup_logger(name: str = "avcs_dna", log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup application logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory
    log_path = Path(log_file or LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    file_formatter = CustomFormatter(
        '%(timestamp)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_formatter = CustomFormatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler (with rotation)
    try:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}")
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    logger.addHandler(console_handler)
    
    return logger

# Create default logger instance
logger = setup_logger()

class LoggerMixin:
    """Mixin class to add logging capability to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger
    
    def log_debug(self, msg: str, *args, **kwargs):
        """Log debug message"""
        self.logger.debug(msg, *args, **kwargs)
    
    def log_info(self, msg: str, *args, **kwargs):
        """Log info message"""
        self.logger.info(msg, *args, **kwargs)
    
    def log_warning(self, msg: str, *args, **kwargs):
        """Log warning message"""
        self.logger.warning(msg, *args, **kwargs)
    
    def log_error(self, msg: str, *args, **kwargs):
        """Log error message"""
        self.logger.error(msg, *args, **kwargs)
    
    def log_critical(self, msg: str, *args, **kwargs):
        """Log critical message"""
        self.logger.critical(msg, *args, **kwargs)

# Context manager for temporary log level changes
class log_level:
    """Context manager to temporarily change log level"""
    
    def __init__(self, logger_name: str, level: int):
        self.logger = logging.getLogger(logger_name)
        self.old_level = self.logger.level
        self.new_level = level
    
    def __enter__(self):
        self.logger.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)

# Decorator for logging function calls
def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise
    return wrapper
