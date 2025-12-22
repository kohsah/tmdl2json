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
├── tmdl_parser.py          # Main TMDL to JSON converter script
├── erd_generator.py        # ERD generator script
├── test_tmdl_parser.py     # Unit tests
├── TECHNICAL_SPEC.md       # Technical documentation
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

## ERD Generation

The `erd_generator.py` utility allows you to generate Entity Relationship Diagrams (ERD) from the JSON output produced by the TMDL parser.

### Features

- **Mermaid Syntax**: Generates standard Mermaid ERD diagrams compatible with GitHub, Notion, and other tools.
- **Smart Filtering**: Automatically excludes system tables (`DateTableTemplate`, `LocalDateTable`) to focus on your business logic.
- **Clean Output**: Trims DAX formulas from column names for better readability.
- **PNG Export**: Can export diagrams directly to PNG images using the mermaid.ink API (requires internet access).

### Usage

**1. Generate Mermaid Markdown:**

```bash
python erd_generator.py input.json --output diagram.md
```

**2. Generate PNG Image:**

```bash
python erd_generator.py input.json --png-output diagram.png
```

**3. Generate both Markdown and PNG:**

```bash
python erd_generator.py input.json --output diagram.md --png-output diagram.png
```

### Options

- `input_file`: Path to the JSON input file (output from `tmdl_parser.py`).
- `--output`, `-o`: Path to output Mermaid file (e.g. `output.md`). If ending in `.md`, wraps content in a mermaid code block.
- `--png-output`: Path to output PNG file. Fetches the rendered image from mermaid.ink.
