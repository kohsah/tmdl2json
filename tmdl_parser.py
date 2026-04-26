import json
import re
import sys
import os
import base64
import zlib

class TmdlParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.lines = []
        self.current_line_index = 0
        self.root = {}
        self.stack = [(self.root, -1)] # (current_dict, indent_level)

    def parse(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()
        
        self.current_line_index = 0
        while self.current_line_index < len(self.lines):
            line = self.lines[self.current_line_index].rstrip()
            if not line.strip():
                self.current_line_index += 1
                continue

            indent = self._get_indent(line)
            content = line.strip()

            # Adjust stack
            while len(self.stack) > 1 and self.stack[-1][1] >= indent:
                self.stack.pop()
            
            parent = self.stack[-1][0]

            self._process_line(content, parent, indent)
            self.current_line_index += 1
        
        return self.root

    def _get_indent(self, line):
        return len(line) - len(line.lstrip('\t'))

    def _process_line(self, content, parent, indent):
        if content.startswith('table '):
            self._handle_table(content)
        elif content.startswith('database '):
            self._handle_root_object(content, 'database')
        elif content.startswith('model '):
            self._handle_root_object(content, 'model')
        elif content.startswith('column '):
            self._handle_column(content, parent, indent)
        elif content.startswith('partition '):
            self._handle_partition(content, parent, indent)
        elif content.startswith('annotation '):
            self._handle_annotation(content, parent)
        elif content.startswith('measure '):
            self._handle_measure(content, parent, indent)
        elif content.startswith('relationship '):
            self._handle_relationship(content, parent, indent)
        else:
            self._handle_property(content, parent, indent)

    def _handle_relationship(self, content, parent, indent):
        rel_def = content.split(' ', 1)[1]
        new_rel = {'name': rel_def, 'type': 'relationship'}
        
        # Relationships are top-level in relationships.tmdl, but let's check structure.
        # Usually they are at the root level in that file.
        if 'relationships' not in self.root:
            self.root['relationships'] = []
            
        self.root['relationships'].append(new_rel)
        # Relationship properties are indented under it, so we push to stack
        self.stack.append((new_rel, indent))

    def _handle_table(self, content):
        table_name = content.split(' ', 1)[1]
        self.root['name'] = table_name
        self.root['type'] = 'table'
        # Reset stack for root properties
        self.stack = [(self.root, 0)]

    def _handle_root_object(self, content, type_name):
        obj_name = content.split(' ', 1)[1]
        self.root['name'] = obj_name
        self.root['type'] = type_name
        # Reset stack for root properties
        self.stack = [(self.root, 0)]
    
    def _handle_column(self, content, parent, indent):
        col_name = content.split(' ', 1)[1]
        new_col = {'name': col_name, 'type': 'column'}
        if 'columns' not in parent:
            parent['columns'] = []
        parent['columns'].append(new_col)
        self.stack.append((new_col, indent))

    def _handle_partition(self, content, parent, indent):
        part_def = content.split(' ', 1)[1]
        if '=' in part_def:
            part_name, part_type = [x.strip() for x in part_def.split('=', 1)]
            new_part = {'name': part_name, 'partitionType': part_type, 'type': 'partition'}
        else:
            new_part = {'name': part_def, 'type': 'partition'}
            
        if 'partitions' not in parent:
            parent['partitions'] = []
        parent['partitions'].append(new_part)
        self.stack.append((new_part, indent))

    def _handle_annotation(self, content, parent):
        if '=' in content:
            key_part = content.split(' ', 1)[1]
            key, value = [x.strip() for x in key_part.split('=', 1)]
            if 'annotations' not in parent:
                parent['annotations'] = []
            parent['annotations'].append({'name': key, 'value': value})

    def _handle_measure(self, content, parent, indent):
        if '=' not in content:
             return

        name_part, expression_part = content.split('=', 1)
        name_part = name_part.strip()
        expression_part = expression_part.strip()
        
        # Remove 'measure ' prefix
        measure_name = name_part[len('measure '):].strip()
        
        if measure_name.startswith("'") and measure_name.endswith("'"):
            measure_name = measure_name[1:-1]
        
        new_measure = {
            'name': measure_name,
            'type': 'measure',
            'expression': ''
        }
        
        if expression_part == '```':
            # Case 1: Delimited block
            block_lines = []
            self.current_line_index += 1
            while self.current_line_index < len(self.lines):
                line = self.lines[self.current_line_index]
                if line.strip() == '```':
                    break 
                block_lines.append(line.rstrip())
                self.current_line_index += 1
            new_measure['expression'] = self._normalize_block(block_lines)

        elif not expression_part:
            # Case 3: Implicit block (indented)
            # Peek next line to verify indentation
            if self.current_line_index + 1 < len(self.lines):
                next_line = self.lines[self.current_line_index + 1]
                next_indent = self._get_indent(next_line)
                
                # If next line is indented deeper than the measure (and likely deeper than properties at indent+1)
                # We assume properties are at indent+1. Expression block should be at indent+2 usually,
                # but let's be flexible and say if it's > indent+1 it's definitely a block.
                # In the example: Measure at 1. Properties at 2. Expression at 3.
                if next_indent > indent + 1:
                     self._handle_multiline_block('expression', new_measure, indent + 1)
        else:
            # Case 2: Inline expression
            new_measure['expression'] = expression_part

        if 'measures' not in parent:
            parent['measures'] = []
        parent['measures'].append(new_measure)
        self.stack.append((new_measure, indent))

    def _handle_property(self, content, parent, indent):
        if ': ' in content:
            key, value = content.split(': ', 1)
            if key in ('fromColumn', 'toColumn'):
                self._handle_column_reference(key, value, parent)
            else:
                parent[key] = value
        elif content.endswith(' ='):
            key = content[:-2]
            self._handle_multiline_block(key, parent, indent)
        elif '=' in content:
            key, value = [x.strip() for x in content.split('=', 1)]
            parent[key] = value

    def _handle_column_reference(self, key, value, parent):
        parent[key] = value
        
        # Breakdown into table and column
        if '.' in value:
            # Split by the last dot to separate column from table (in case table has dots, though rare/quoted)
            # Standard TMDL format is Table.Column
            table_part, col_part = value.rsplit('.', 1)
            
            # Helper to strip quotes if present
            def strip_quotes(s):
                s = s.strip()
                if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
                    return s[1:-1]
                return s

            table_name = strip_quotes(table_part)
            col_name = strip_quotes(col_part)
            
            # Add breakdown fields
            # We use key + "Table" and key + "Column" (e.g. fromColumnTable, fromColumnColumn)
            # Or simplified: fromTable, fromColumnName?
            # To be safe and explicit:
            prefix = "from" if key == "fromColumn" else "to"
            
            parent[f"{prefix}Table"] = table_name
            parent[f"{prefix}ColumnName"] = col_name


    def _handle_multiline_block(self, key, parent, indent):
        block_lines = []
        self.current_line_index += 1
        
        # Look ahead
        while self.current_line_index < len(self.lines):
            next_line = self.lines[self.current_line_index]
            if not next_line.strip():
                block_lines.append('')
                self.current_line_index += 1
                continue
            
            next_indent = self._get_indent(next_line)
            if next_indent <= indent:
                self.current_line_index -= 1 # Backtrack
                break
            
            block_lines.append(next_line.rstrip())
            self.current_line_index += 1
            
        # Normalize
        normalized_block = self._normalize_block(block_lines)
        parent[key] = normalized_block
        
        # If this is a 'source' block in a partition, try to extract Schema and Item
        if key == 'source' and parent.get('type') == 'partition':
            self._extract_schema_item(normalized_block, parent)
            self._extract_base64_content(normalized_block, parent)

    def _current_table_object(self):
        for obj, _indent in reversed(self.stack):
            if isinstance(obj, dict) and obj.get('type') == 'table':
                return obj
        return None

    def _extract_base64_content(self, source_code, parent):
        # Look for pattern: Binary.FromText("...", BinaryEncoding.Base64)
        pattern = re.compile(r'Binary\.FromText\(\s*"([^"]+)"\s*,\s*BinaryEncoding\.Base64\s*\)')
        
        matches = pattern.findall(source_code)
        
        if matches:
            extracted_info = []
            for b64_str in matches:
                try:
                    # Decode Base64
                    decoded_bytes = base64.b64decode(b64_str)
                    
                    # Try to decompress (usually it's Deflate/Raw Deflate)
                    try:
                        # -15 for raw deflate (no header), which is common in M scripts
                        decompressed_bytes = zlib.decompress(decoded_bytes, -15)
                        content = decompressed_bytes.decode('utf-8')
                        content_type = 'decompressed_json' # Often it's JSON
                    except Exception:
                        try:
                            # Try standard zlib
                            decompressed_bytes = zlib.decompress(decoded_bytes)
                            content = decompressed_bytes.decode('utf-8')
                            content_type = 'decompressed_json'
                        except Exception:
                            # If decompression fails, treat as plain text or failed decompression
                            content = "Decompression failed or not compressed"
                            content_type = 'raw_decoded'
                    
                    extracted_info.append({
                        'contentType': content_type,
                        'content': content
                    })
                except Exception as e:
                    extracted_info.append({
                        'error': f"Failed to decode: {str(e)}"
                    })
            
            if extracted_info:
                if 'sourceDetails' not in parent:
                    parent['sourceDetails'] = []
                parent['sourceDetails'].extend(extracted_info)

    def _extract_schema_item(self, source_code, parent):
        # Look for pattern: {[Schema="Value",Item="Value"]} or similar variations
        # Note: M code can be complex, this regex targets the specific pattern seen in examples
        
        # Pattern matches: {[Schema="...",Item="..."]}
        # It handles potential spaces around comma and brackets
        # Capture groups: 1=Schema, 2=Item
        pattern = re.compile(r'\{\s*\[\s*Schema\s*=\s*"([^"]+)"\s*,\s*Item\s*=\s*"([^"]+)"\s*\]\s*\}')
        
        matches = pattern.findall(source_code)
        
        if matches:
            extracted_info = []
            for schema, item in matches:
                extracted_info.append({
                    'schema': schema,
                    'item': item
                })
            
            parent['sourceDetails'] = extracted_info
            table_obj = self._current_table_object()
            if table_obj is not None and extracted_info:
                table_obj.setdefault('schema', extracted_info[0]['schema'])
                table_obj.setdefault('item', extracted_info[0]['item'])
                table_obj.setdefault('table_item', table_obj.get('item'))

    def _normalize_block(self, block_lines):
        if not block_lines:
             return ""
        
        non_empty_lines = [line for line in block_lines if line.strip()]
        if non_empty_lines:
             min_indent = min(len(line) - len(line.lstrip('\t')) for line in non_empty_lines)
             cleaned_lines = []
             for line in block_lines:
                 if not line.strip():
                     cleaned_lines.append('')
                 elif line.startswith('\t' * min_indent):
                     cleaned_lines.append(line[min_indent:])
                 else:
                     cleaned_lines.append(line.lstrip('\t'))
             return '\n'.join(cleaned_lines)
        return '\n'.join(block_lines)

def parse_tmdl(file_path):
    parser = TmdlParser(file_path)
    return parser.parse()

def convert_tmdl_to_json(tmdl_path, output_path=None):
    data = parse_tmdl(tmdl_path)
    json_output = json.dumps(data, indent=2)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_output)
        return f"JSON saved to {output_path}"
    else:
        return json_output

def _read_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _find_single_pbip_file(root_dir):
    pbip_files = [f for f in os.listdir(root_dir) if f.lower().endswith('.pbip') and os.path.isfile(os.path.join(root_dir, f))]
    pbip_files.sort(key=lambda s: s.lower())
    if len(pbip_files) != 1:
        raise ValueError(f"Expected exactly 1 .pbip file in '{root_dir}', found {len(pbip_files)}")
    return os.path.join(root_dir, pbip_files[0])

def _resolve_report_folder_from_pbip(pbip_path):
    pbip_root = os.path.dirname(pbip_path)
    pbip_json = _read_json_file(pbip_path)
    artifacts = pbip_json.get('artifacts', [])
    report_paths = []
    for artifact in artifacts:
        report = (artifact or {}).get('report')
        if isinstance(report, dict) and isinstance(report.get('path'), str):
            report_paths.append(report['path'])
    report_paths = [p for p in report_paths if p]
    report_paths = list(dict.fromkeys(report_paths))
    if len(report_paths) != 1:
        raise ValueError(f"Expected exactly 1 report path in '{pbip_path}', found {len(report_paths)}")
    report_folder = os.path.normpath(os.path.join(pbip_root, report_paths[0]))
    if not os.path.isdir(report_folder):
        raise FileNotFoundError(f"Report folder not found: {report_folder}")
    return report_folder

def _resolve_semantic_model_folder_from_report(report_folder):
    definition_path = os.path.join(report_folder, 'definition.pbir')
    if not os.path.isfile(definition_path):
        raise FileNotFoundError(f"Report definition not found: {definition_path}")
    report_def = _read_json_file(definition_path)
    dataset_ref = report_def.get('datasetReference') or {}
    by_path = dataset_ref.get('byPath')
    by_connection = dataset_ref.get('byConnection')
    if by_connection:
        raise ValueError("datasetReference.byConnection is not supported")
    if not isinstance(by_path, dict) or not isinstance(by_path.get('path'), str) or not by_path.get('path'):
        raise ValueError("datasetReference.byPath.path is missing or invalid")
    semantic_model_folder = os.path.normpath(os.path.join(report_folder, by_path['path']))
    if not os.path.isdir(semantic_model_folder):
        raise FileNotFoundError(f"Semantic model folder not found: {semantic_model_folder}")
    return semantic_model_folder

def parse_semantic_model_definition(definition_folder):
    if not os.path.isdir(definition_folder):
        raise FileNotFoundError(f"Definition folder not found: {definition_folder}")

    result = {}

    database_path = os.path.join(definition_folder, 'database.tmdl')
    if os.path.isfile(database_path):
        result['database'] = TmdlParser(database_path).parse()

    model_path = os.path.join(definition_folder, 'model.tmdl')
    if os.path.isfile(model_path):
        result['model'] = TmdlParser(model_path).parse()

    relationships_path = os.path.join(definition_folder, 'relationships.tmdl')
    if os.path.isfile(relationships_path):
        parsed = TmdlParser(relationships_path).parse()
        if isinstance(parsed, dict) and 'relationships' in parsed:
            result['relationships'] = parsed['relationships']
        else:
            result['relationships'] = parsed

    tables_folder = os.path.join(definition_folder, 'tables')
    if os.path.isdir(tables_folder):
        tables = []
        for filename in sorted(os.listdir(tables_folder), key=lambda s: s.lower()):
            if filename.lower().endswith('.tmdl'):
                tables.append(TmdlParser(os.path.join(tables_folder, filename)).parse())
        result['tables'] = tables

    cultures_folder = os.path.join(definition_folder, 'cultures')
    if os.path.isdir(cultures_folder):
        cultures = []
        for filename in sorted(os.listdir(cultures_folder), key=lambda s: s.lower()):
            if filename.lower().endswith('.tmdl'):
                cultures.append(TmdlParser(os.path.join(cultures_folder, filename)).parse())
        result['cultures'] = cultures

    return result

def parse_pbip_report_root(root_path):
    if os.path.isfile(root_path) and root_path.lower().endswith('.pbip'):
        pbip_path = root_path
        pbip_root = os.path.dirname(pbip_path)
    else:
        if not os.path.isdir(root_path):
            raise FileNotFoundError(f"PBIP root folder not found: {root_path}")
        pbip_root = root_path
        pbip_path = _find_single_pbip_file(pbip_root)

    report_folder = _resolve_report_folder_from_pbip(pbip_path)
    semantic_model_folder = _resolve_semantic_model_folder_from_report(report_folder)
    definition_folder = os.path.join(semantic_model_folder, 'definition')
    return parse_semantic_model_definition(definition_folder)

def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description='Convert TMDL (or PBIP report root) to JSON.')
    parser.add_argument('input', help='Path to a .tmdl file, a folder of .tmdl files, a PBIP report root folder, or a .pbip file')
    parser.add_argument('-o', '--output', help='Path to output JSON file or directory')

    args = parser.parse_args(argv)

    tmdl_input = args.input
    output_target = args.output

    if os.path.isdir(tmdl_input):
        pbip_candidates = [f for f in os.listdir(tmdl_input) if f.lower().endswith('.pbip') and os.path.isfile(os.path.join(tmdl_input, f))]
        if pbip_candidates:
            data = parse_pbip_report_root(tmdl_input)
            json_output = json.dumps(data, indent=2)
            if output_target:
                if os.path.isdir(output_target):
                    pbip_path = _find_single_pbip_file(tmdl_input)
                    base = os.path.splitext(os.path.basename(pbip_path))[0]
                    out_path = os.path.join(output_target, f"{base}.json")
                else:
                    out_path = output_target
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                print(f"JSON saved to {out_path}")
            else:
                print(json_output)
        else:
            if output_target:
                if os.path.exists(output_target) and not os.path.isdir(output_target):
                    print(f"Error: Output path '{output_target}' exists and is not a directory. Cannot output multiple files to a single file.")
                    return 1
                if not os.path.exists(output_target):
                    os.makedirs(output_target)

            for filename in os.listdir(tmdl_input):
                if filename.endswith(".tmdl"):
                    full_path = os.path.join(tmdl_input, filename)

                    if output_target:
                        json_filename = filename.replace('.tmdl', '.json')
                        out_path = os.path.join(output_target, json_filename)
                        print(convert_tmdl_to_json(full_path, out_path))
                    else:
                        print(f"--- {filename} ---")
                        print(convert_tmdl_to_json(full_path))
                        print("\n")
    else:
        if tmdl_input.lower().endswith('.pbip'):
            data = parse_pbip_report_root(tmdl_input)
            json_output = json.dumps(data, indent=2)
            if output_target:
                if os.path.isdir(output_target):
                    base = os.path.splitext(os.path.basename(tmdl_input))[0]
                    out_path = os.path.join(output_target, f"{base}.json")
                else:
                    out_path = output_target
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                print(f"JSON saved to {out_path}")
            else:
                print(json_output)
        else:
            if output_target:
                if os.path.isdir(output_target):
                    filename = os.path.basename(tmdl_input)
                    json_filename = filename.replace('.tmdl', '.json')
                    out_path = os.path.join(output_target, json_filename)
                    print(convert_tmdl_to_json(tmdl_input, out_path))
                else:
                    print(convert_tmdl_to_json(tmdl_input, output_target))
            else:
                print(convert_tmdl_to_json(tmdl_input))

    return 0

if __name__ == "__main__":
    sys.exit(main())
