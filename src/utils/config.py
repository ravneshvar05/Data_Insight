"""
Configuration management for the Automated Data Insight System.
Loads and provides access to application configuration.
"""

import yaml
import os
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv


class Config:
    """Singleton configuration manager."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration by loading from file and environment."""
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file and environment variables."""
        # Load environment variables
        load_dotenv()
        
        # Load YAML configuration
        config_path = Path(__file__).parent.parent.parent / 'config' / 'config.yaml'
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
        
        # Override with environment variables if present
        if 'GROQ_API_KEY' in os.environ:
            if 'llm' not in self._config:
                self._config['llm'] = {}
            self._config['llm']['api_key'] = os.environ['GROQ_API_KEY']
        
        if 'VISUALIZATION_MODEL' in os.environ:
            if 'llm' not in self._config:
                self._config['llm'] = {}
            self._config['llm']['visualization_model'] = os.environ['VISUALIZATION_MODEL']
        
        if 'INSIGHT_MODEL' in os.environ:
            if 'llm' not in self._config:
                self._config['llm'] = {}
            self._config['llm']['insight_model'] = os.environ['INSIGHT_MODEL']
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key (e.g., 'app.name' or 'logging.level')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Section name (e.g., 'logging', 'llm')
            
        Returns:
            Configuration section as dictionary
        """
        return self._config.get(section, {})
    
    @property
    def all(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        return self._config.copy()


# Global config instance
_config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return _config
