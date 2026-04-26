import json
import os

class ConfigLoader:
    def __init__(self, config_path="pbip_definition.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """Loads the JSON configuration file."""
        config_path = self.config_path
        if not os.path.exists(config_path) and not os.path.isabs(config_path):
            candidate = os.path.join(os.path.dirname(__file__), config_path)
            if os.path.exists(candidate):
                config_path = candidate
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_pbip_file_pattern(self):
        return self.config.get("pbip_file_pattern")

    def get_report_folder_pattern(self):
        return self.config.get("report_folder_pattern")

    def get_model_folder_pattern(self):
        return self.config.get("model_folder_pattern")

    def get_definition_folder_name(self):
        return self.config.get("content", {}).get("definition_folder")

    def get_definition_files(self):
        return self.config.get("definition_folder_structure", {}).get("content", {}).get("files", {})

    def get_definition_folders(self):
        return self.config.get("definition_folder_structure", {}).get("content", {}).get("folders", {})
