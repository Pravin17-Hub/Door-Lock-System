"""
FaceSecure - Configuration Manager
Handles persistence and retrieval of application settings in JSON format.
"""

import os
import json
from utils.logger import setup_logger

logger = setup_logger("ConfigManager")

CONFIG_PATH = os.path.join("data", "config.json")

DEFAULT_CONFIG = {
    "camera_index": 0,
    "camera_resolution": "640x480",
    "confidence_threshold": 0.65, # 65% match threshold
    "door_unlock_duration": 5,   # seconds
    "com_port": "AUTO",          # Auto-detect or specific COM port (e.g. COM3)
    "baud_rate": 9600,
    "theme": "Dark",             # Dark or Light
    "auto_lock": True,
    "sound_alerts": True,
}


class ConfigManager:
    def __init__(self, filepath: str = CONFIG_PATH):
        self.filepath = filepath
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self):
        """Loads settings from JSON file or creates default configuration."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data)
                logger.info("Configuration loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading configuration file: {e}. Using defaults.")
        else:
            self.save_config()

    def save_config(self):
        """Saves current settings to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuration saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def set(self, key: str, value):
        self.config[key] = value
        self.save_config()
