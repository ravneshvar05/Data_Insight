"""
Logging configuration for the Automated Data Insight System.
Provides centralized logging with rotating file handlers.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from typing import Optional


class Logger:
    """Singleton logger factory for the application."""
    
    _loggers = {}
    _initialized = False
    
    @classmethod
    def setup(cls, config: dict) -> None:
        """
        Set up the logging system with configuration.
        
        Args:
            config: Logging configuration dictionary
        """
        if cls._initialized:
            return
            
        # Create logs directory if it doesn't exist
        log_dir = Path(config.get('log_dir', 'logs'))
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        log_level = getattr(logging, config.get('level', 'INFO'))
        log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # File handler with rotation
        log_file = log_dir / 'app.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.get('max_bytes', 10485760),  # 10MB
            backupCount=config.get('backup_count', 5)
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        cls._initialized = True
        
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance for the specified name.
        
        Args:
            name: Logger name (typically __name__ of the module)
            
        Returns:
            Logger instance
        """
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger instance.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Logger instance
    """
    return Logger.get_logger(name)
