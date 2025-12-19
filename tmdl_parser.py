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
            while self.stack[-1][1] >= indent:
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
        elif content.startswith('column '):
            self._handle_column(content, parent, indent)
        elif content.startswith('partition '):
            self._handle_partition(content, parent, indent)
        elif content.startswith('annotation '):
            self._handle_annotation(content, parent)
        elif content.startswith('measure '):
            self._handle_measure(content, parent, indent)
        else:
            self._handle_property(content, parent, indent)

    def _handle_table(self, content):
        table_name = content.split(' ', 1)[1]
        self.root['name'] = table_name
        self.root['type'] = 'table'
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
            parent[key] = value
        elif content.endswith(' ='):
            key = content[:-2]
            self._handle_multiline_block(key, parent, indent)
        elif '=' in content:
            key, value = [x.strip() for x in content.split('=', 1)]
            parent[key] = value

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

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert TMDL file to JSON.')
    parser.add_argument('input', help='Path to TMDL file or directory')
    parser.add_argument('-o', '--output', help='Path to output JSON file or directory')
    
    args = parser.parse_args()
    
    tmdl_input = args.input
    output_target = args.output
    
    if os.path.isdir(tmdl_input):
        # Process all tmdl files in directory
        if output_target:
             if os.path.exists(output_target) and not os.path.isdir(output_target):
                 print(f"Error: Output path '{output_target}' exists and is not a directory. Cannot output multiple files to a single file.")
                 sys.exit(1)
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
        if output_target:
            # Check if output_target is a directory
            if os.path.isdir(output_target):
                filename = os.path.basename(tmdl_input)
                json_filename = filename.replace('.tmdl', '.json')
                out_path = os.path.join(output_target, json_filename)
                print(convert_tmdl_to_json(tmdl_input, out_path))
            else:
                # Assume it's a file path
                print(convert_tmdl_to_json(tmdl_input, output_target))
        else:
            print(convert_tmdl_to_json(tmdl_input))
