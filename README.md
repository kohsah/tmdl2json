# TMDL to JSON Converter

A Python3 utility to convert Tabular Model Definition Language (TMDL) files into JSON format. This tool parses the indentation-based TMDL syntax and outputs a structured JSON representation, making it easier to process or analyze Power BI/Analysis Services semantic models programmatically.

For a detailed breakdown of supported features and extraction capabilities, please refer to the [Technical Specification](TECHNICAL_SPEC.md).

## Features

- **TMDL Parsing**: Correctly handles nested structures like tables, columns, partitions, and annotations.
- **Multi-line Support**: Handles multi-line expressions (e.g., M scripts in partitions) by stripping common indentation.
- **Batch Processing**: Can convert a single file or an entire directory of `.tmdl` files.
- **Flexible Output**: Supports outputting to console, a specific file, or a dedicated output directory.

## Project Structure

```
.
├── tmdl/                   # Example TMDL files
├── tmdl_parser.py          # Main converter script
├── test_tmdl_parser.py     # Unit tests
└── README.md
```

## Usage

### 1. Convert a single file

**Print to console:**
```bash
python tmdl_parser.py tmdl/DimCountry.tmdl
```

**Save to a specific JSON file:**
```bash
python tmdl_parser.py tmdl/DimCountry.tmdl -o output.json
```

### 2. Convert a directory

Convert all `.tmdl` files in a directory and save them to an output folder:

```bash
python tmdl_parser.py tmdl -o json_output
```
*Note: If `json_output` does not exist, it will be created.*

### 3. Help

View all available options:

```bash
python tmdl_parser.py --help
```

## Testing

Unit tests are provided to verify the parser's functionality. Run them from the `code` directory:

```bash
python test_tmdl_parser.py
```
