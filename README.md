# TMDL to JSON Converter

A Python3 utility to convert Tabular Model Definition Language (TMDL) files into JSON format. This tool parses the indentation-based TMDL syntax and outputs a structured JSON representation, making it easier to process or analyze Power BI/Analysis Services semantic models programmatically.

For contributor and tooling conventions, see [AGENTS.md](AGENTS.md). For a detailed breakdown of supported features and extraction capabilities, see [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md).

## Features

- **TMDL Parsing**: Handles root objects (`table`, `database`, `model`) and nested elements like columns, partitions, measures, annotations, and relationships.
- **Relationship Enrichment**: Derives `fromTable`/`fromColumnName` and `toTable`/`toColumnName` from `fromColumn`/`toColumn`.
- **Multi-line Support**: Normalizes multi-line blocks (e.g., partition `source` M scripts, measure expressions) by stripping common indentation.
- **Partition Source Enrichment**: Extracts `{[Schema="...",Item="..."]}` references and attempts base64 decode/decompression for `Binary.FromText(..., BinaryEncoding.Base64)`.
- **Batch Processing**: Converts a single file or an entire directory of `.tmdl` files.
- **PBIP Parsing**: Parses a `.pbip` folder structure and aggregates model definition files into one JSON document.
- **ERD Generation**: Produces Mermaid ER diagrams from JSON output, with optional PNG export via mermaid.ink.

## Project Structure

```
.
├── AGENTS.md
├── README.md
├── config_loader.py
├── erd_generator.py
├── pbip_definition.json
├── pbip_parser.py
├── tmdl_parser.py
├── test_pbip_parser.py
├── test_tmdl_parser.py
└── docs/
    └── TECHNICAL_SPEC.md
```

## Usage

Run commands from the `code` directory using the in-repo virtual environment Python (`../env/Scripts/python.exe` on Windows, or `../env/python` if you use a shim).

### 1. Convert a single TMDL file

**Print to console:**
```bash
../env/Scripts/python.exe tmdl_parser.py tmdl/DimCountry.tmdl
```

**Save to a specific JSON file:**
```bash
../env/Scripts/python.exe tmdl_parser.py tmdl/DimCountry.tmdl -o output.json
```

### 2. Convert a directory of `.tmdl` files

Convert all `.tmdl` files in a directory and save them to an output folder:

```bash
../env/Scripts/python.exe tmdl_parser.py tmdl -o json_output
```
*Note: If `json_output` does not exist, it will be created.*

### 3. Parse a PBIP folder

Parse a `.pbip` folder and write the aggregated model JSON:

```bash
../env/Scripts/python.exe pbip_parser.py path\to\Report.pbip --output model.json
```

### 4. Help

View all available options:

```bash
../env/Scripts/python.exe tmdl_parser.py --help
```

## Testing

Unit tests are provided to verify parser functionality. Run them from the `code` directory:

```bash
../env/Scripts/python.exe -m unittest
```

## ERD Generation

The `erd_generator.py` utility generates Entity Relationship Diagrams (ERD) from the JSON output produced by `tmdl_parser.py` or `pbip_parser.py`.

### Features

- **Mermaid Syntax**: Generates standard Mermaid ERD diagrams compatible with GitHub, Notion, and other tools.
- **Smart Filtering**: Automatically excludes system tables (`DateTableTemplate`, `LocalDateTable`) to focus on your business logic.
- **Clean Output**: Trims DAX formulas from column names for better readability.
- **PNG Export**: Can export diagrams directly to PNG images using the mermaid.ink API (requires internet access).

### Usage

**1. Generate Mermaid Markdown:**

```bash
../env/Scripts/python.exe erd_generator.py input.json --output diagram.md
```

**2. Generate PNG Image:**

```bash
../env/Scripts/python.exe erd_generator.py input.json --png-output diagram.png
```

**3. Generate both Markdown and PNG:**

```bash
../env/Scripts/python.exe erd_generator.py input.json --output diagram.md --png-output diagram.png
```

### Options

- `input_file`: Path to the JSON input file (output from `tmdl_parser.py`).
- `--output`, `-o`: Path to output Mermaid file (e.g. `output.md`). If ending in `.md`, wraps content in a mermaid code block.
- `--png-output`: Path to output PNG file. Fetches the rendered image from mermaid.ink.
