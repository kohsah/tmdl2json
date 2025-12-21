import os
import argparse
import glob
import json
from config_loader import ConfigLoader
from tmdl_parser import TmdlParser

class PbipParser:
    def __init__(self, pbip_folder_path, config_path="pbip_definition.json"):
        self.pbip_folder_path = pbip_folder_path
        self.config_loader = ConfigLoader(config_path)
        self.model_data = {}

    def parse(self):
        # 0. Validate PBIP structure
        pbip_file_pattern = self.config_loader.get_pbip_file_pattern()
        if pbip_file_pattern:
            found_pbip_files = glob.glob(os.path.join(self.pbip_folder_path, pbip_file_pattern))
            if not found_pbip_files:
                print(f"Warning: No PBIP file found matching '{pbip_file_pattern}' in '{self.pbip_folder_path}'")
        
        report_folder_pattern = self.config_loader.get_report_folder_pattern()
        if report_folder_pattern:
             found_report_folders = glob.glob(os.path.join(self.pbip_folder_path, report_folder_pattern))
             if not found_report_folders:
                 print(f"Warning: No Report folder found matching '{report_folder_pattern}' in '{self.pbip_folder_path}'")

        # 1. Find the Semantic Model folder
        model_pattern = self.config_loader.get_model_folder_pattern()
        search_path = os.path.join(self.pbip_folder_path, model_pattern)
        found_models = glob.glob(search_path)

        if not found_models:
            print(f"No Semantic Model folder found matching pattern '{model_pattern}' in '{self.pbip_folder_path}'")
            return None
        
        # Assuming one model per PBIP folder for now, but usually true
        semantic_model_path = found_models[0]
        
        # 2. Locate definition folder
        def_folder_name = self.config_loader.get_definition_folder_name()
        definition_path = os.path.join(semantic_model_path, def_folder_name)
        
        if not os.path.exists(definition_path):
            print(f"Definition folder not found at: {definition_path}")
            return None

        # 3. Parse specific files defined in config
        files_config = self.config_loader.get_definition_files()
        
        # Parse database.tmdl
        if "database_tmdl" in files_config:
            self._parse_file(definition_path, files_config["database_tmdl"], "database")

        # Parse model.tmdl
        if "model_tmdl" in files_config:
            self._parse_file(definition_path, files_config["model_tmdl"], "model")

        # Parse relationships.tmdl
        if "relationships_tmdl" in files_config:
            self._parse_file(definition_path, files_config["relationships_tmdl"], "relationships")

        # Parse expressions.tmdl
        if "expressions_tmdl" in files_config:
            self._parse_file(definition_path, files_config["expressions_tmdl"], "expressions")

        # 4. Parse folders defined in config
        folders_config = self.config_loader.get_definition_folders()
        
        # Parse tables folder
        if "tables" in folders_config:
            tables_path = os.path.join(definition_path, folders_config["tables"])
            if os.path.exists(tables_path):
                self._parse_tables_folder(tables_path)

        return self.model_data

    def _parse_file(self, base_path, filename, key):
        file_path = os.path.join(base_path, filename)
        if os.path.exists(file_path):
            parser = TmdlParser(file_path)
            parsed_content = parser.parse()
            # If the parser returns a list (like for relationships), store it directly
            # If it returns a dict, store it under the key
            
            # Special handling based on typical TmdlParser output
            # TmdlParser.parse() returns a dict representing the root element
            
            if key == "relationships":
                 # Relationships might be at the root or inside 'relationships' key depending on implementation
                 # Based on recent changes, they are in 'relationships' key of the returned dict
                 if 'relationships' in parsed_content:
                     self.model_data['relationships'] = parsed_content['relationships']
                 else:
                     # Fallback if parser returns something else
                     self.model_data[key] = parsed_content
            else:
                self.model_data[key] = parsed_content

    def _parse_tables_folder(self, tables_path):
        tables = []
        # Find all .tmdl files in the tables directory
        tmdl_files = glob.glob(os.path.join(tables_path, "*.tmdl"))
        
        for tmdl_file in tmdl_files:
            parser = TmdlParser(tmdl_file)
            parsed_content = parser.parse()
            tables.append(parsed_content)
        
        self.model_data['tables'] = tables

def main():
    parser = argparse.ArgumentParser(description="Parse a PBIP report folder and convert TMDL to JSON.")
    parser.add_argument("pbip_folder", help="Path to the PBIP report folder")
    parser.add_argument("--output", help="Path to output JSON file (optional)", default=None)
    
    args = parser.parse_args()
    
    pbip_parser = PbipParser(args.pbip_folder)
    result = pbip_parser.parse()
    
    if result:
        json_output = json.dumps(result, indent=4)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"Output written to {args.output}")
        else:
            print(json_output)

if __name__ == "__main__":
    main()
