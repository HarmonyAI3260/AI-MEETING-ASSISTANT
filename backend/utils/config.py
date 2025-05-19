"""
Configuration Utilities

Handles configuration loading, environment variables, and settings management.
"""

import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the AI Meeting Assistant"""
    
    def __init__(self):
        """Initialize configuration with default values"""
        # Default configuration
        self.defaults = {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "reload": True,
                "log_level": "INFO"
            },
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "chunk_size": 1024,
                "vad_aggressiveness": 3
            },
            "openai": {
                "model": "gpt-4o",
                "transcription_model": "whisper-1",
                "max_tokens": 150,
                "temperature": 0.7
            },
            "platforms": {
                "zoom": {
                    "enabled": False,
                    "sdk_key": ""
                },
                "teams": {
                    "enabled": False,
                    "client_id": ""
                },
                "meet": {
                    "enabled": False,
                    "credentials_file": ""
                }
            }
        }
        
        # Actual configuration (will be populated with defaults and overrides)
        self.config = {}
        
        # Load the configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables and config files"""
        # Start with defaults
        self.config = self.defaults.copy()
        
        # Load environment variables
        self._load_from_env()
        
        # Load from config file if it exists
        config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        if os.path.exists(config_file):
            self._load_from_file(config_file)
            
        logger.info("Configuration loaded")
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # OpenAI API Key
        if "OPENAI_API_KEY" in os.environ:
            self.config["openai"]["api_key"] = os.environ["OPENAI_API_KEY"]
        
        # Server settings
        if "HOST" in os.environ:
            self.config["server"]["host"] = os.environ["HOST"]
        if "PORT" in os.environ:
            self.config["server"]["port"] = int(os.environ["PORT"])
        if "LOG_LEVEL" in os.environ:
            self.config["server"]["log_level"] = os.environ["LOG_LEVEL"]
        
        # Audio settings
        if "SAMPLE_RATE" in os.environ:
            self.config["audio"]["sample_rate"] = int(os.environ["SAMPLE_RATE"])
    
    def _load_from_file(self, file_path: str):
        """Load configuration from a JSON file"""
        try:
            with open(file_path, 'r') as file:
                file_config = json.load(file)
                
            # Recursively update config
            self._update_config(self.config, file_config)
            logger.info(f"Loaded configuration from {file_path}")
        except Exception as e:
            logger.error(f"Error loading configuration file: {str(e)}")
    
    def _update_config(self, target: Dict, source: Dict):
        """Recursively update nested dictionaries"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_config(target[key], value)
            else:
                target[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using a dot-notation path
        
        Args:
            key_path: Dot-notation path to the config value (e.g., "server.port")
            default: Default value to return if the path is not found
            
        Returns:
            Configuration value or default
        """
        parts = key_path.split('.')
        config = self.config
        
        try:
            for part in parts:
                config = config[part]
            return config
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Set a configuration value using a dot-notation path
        
        Args:
            key_path: Dot-notation path to the config value (e.g., "server.port")
            value: Value to set
        """
        parts = key_path.split('.')
        config = self.config
        
        # Navigate to the nested dict containing the target key
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]
        
        # Set the value
        config[parts[-1]] = value
    
    def save(self, file_path: Optional[str] = None):
        """
        Save the current configuration to a file
        
        Args:
            file_path: Path to save the configuration file, if None uses the default path
        """
        if not file_path:
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write config excluding sensitive values
            safe_config = self._create_safe_config()
            with open(file_path, 'w') as file:
                json.dump(safe_config, file, indent=2)
                
            logger.info(f"Configuration saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def _create_safe_config(self) -> Dict:
        """Create a copy of the config without sensitive values like API keys"""
        # Deep copy the config
        safe_config = json.loads(json.dumps(self.config))
        
        # Remove sensitive values
        sensitive_keys = [
            ("openai", "api_key"),
            ("platforms", "zoom", "sdk_key"),
            ("platforms", "teams", "client_id"),
            ("platforms", "teams", "client_secret")
        ]
        
        for key_path in sensitive_keys:
            # Navigate to the containing dict
            current = safe_config
            for part in key_path[:-1]:
                if part in current:
                    current = current[part]
                else:
                    break
            
            # Remove the sensitive key if it exists
            if key_path[-1] in current:
                current[key_path[-1]] = "***"
        
        return safe_config
    
    def has_api_key(self) -> bool:
        """Check if OpenAI API key is configured"""
        return "api_key" in self.config.get("openai", {}) and bool(self.config["openai"]["api_key"])

# Global configuration instance
config = Config()
