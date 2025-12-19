# Technical Specification: TMDL to JSON Converter

This document details the capabilities of the TMDL (Tabular Model Definition Language) to JSON converter tool. It outlines the supported TMDL elements, parsing logic, and metadata extraction features.

## 1. Overview
The tool parses TMDL files (`.tmdl`), which use an indentation-based syntax to define Power BI/Tabular models, and converts them into a structured JSON format. It handles nested structures, multi-line code blocks, and specific Power BI metadata patterns.

## 2. Supported Top-Level Elements

### 2.1 Tables
- **Syntax**: `table <TableName>`
- **Extraction**:
  - `name`: Extracted from the declaration line.
  - `type`: Set to `"table"`.
  - Properties (e.g., `lineageTag`, `ordinal`) are extracted as key-value pairs.

### 2.2 Columns
- **Syntax**: `column <ColumnName>` (nested under `table`)
- **Extraction**:
  - `name`: Extracted from the declaration line.
  - `type`: Set to `"column"`.
  - **Properties**:
    - `dataType`: Data type of the column (e.g., `string`, `int64`, `dateTime`).
    - `summarizeBy`: Aggregation method (e.g., `sum`, `none`).
    - `sourceColumn`: Name of the column in the source.
    - `formatString`: Formatting string.
    - `lineageTag`: Unique identifier.
    - `relationship`: Relationship ID (if applicable).
    - `defaultHierarchy`: Hierarchy reference (if applicable).

### 2.3 Partitions
- **Syntax**: `partition <PartitionName> = <Type>`
- **Extraction**:
  - `name`: Extracted from declaration.
  - `partitionType`: The type of partition (e.g., `m`).
  - `type`: Set to `"partition"`.
  - `mode`: Data import mode (e.g., `import`).
  - `source`: The M script source definition (handled as a multi-line block).

### 2.4 Measures
- **Syntax**: `measure '<MeasureName>' = <Expression>`
- **Extraction**:
  - `name`: Extracted from declaration (quotes are stripped).
  - `type`: Set to `"measure"`.
  - `expression`: The DAX formula.
    - Supports **Inline Expressions**: `measure 'X' = SUM(A)`
    - Supports **Delimited Blocks**: `measure 'X' = ``` ... ``` `
    - Supports **Implicit Indented Blocks**: `measure 'X' = \n\t\tVAR ...`
  - **Properties**: `formatString`, `displayFolder`, `lineageTag`, etc.

### 2.5 Annotations
- **Syntax**: `annotation <Key> = <Value>`
- **Extraction**:
  - Stored as a list of objects under the `annotations` key.
  - Structure: `{"name": "<Key>", "value": "<Value>"}`.

## 3. Advanced Metadata Extraction

### 3.1 M Script Source Parsing
The tool analyzes the `source` property within partitions to extract structured metadata.

#### 3.1.1 Schema and Item Extraction
- **Pattern**: `{[Schema="<SchemaName>",Item="<ItemName>"]}`
- **Target**: Extracts source database objects (tables/views) used in the M script.
- **Output**:
  ```json
  "sourceDetails": [
    {
      "schema": "dbo",
      "item": "DimCountry"
    }
  ]
  ```

#### 3.1.2 Base64 Encoded Content
- **Pattern**: `Binary.FromText("...", BinaryEncoding.Base64)`
- **Functionality**:
  1. Detects Base64 encoded strings in the M script.
  2. Decodes the Base64 string.
  3. Attempts decompression (Inflate/Deflate) often used by Power BI for embedded JSON.
- **Output**:
  ```json
  "sourceDetails": [
    {
      "contentType": "decompressed_json",
      "content": "..." // Decoded string (e.g., JSON content)
    }
  ]
  ```

### 3.2 Multi-line Block Normalization
- **Logic**:
  - Detects indentation of the block.
  - Strips common leading whitespace (tabs) to preserve relative formatting while removing structural indentation.
  - Ensures clean extraction of DAX and M scripts.

## 4. Usage Modes

### 4.1 Single File
- Converts a single `.tmdl` file to JSON.
- Output: Print to stdout or save to file.

### 4.2 Batch Processing
- Input: A directory containing `.tmdl` files.
- Output:
  - If output path is not specified: Prints all JSONs to stdout.
  - If output path is a directory: Saves individual `.json` files for each input `.tmdl` file.

## 5. JSON Output Structure
The output is a hierarchical JSON object:
```json
{
  "name": "TableName",
  "type": "table",
  "lineageTag": "...",
  "columns": [
    {
      "name": "ColumnName",
      "type": "column",
      "dataType": "...",
      "annotations": [...]
    }
  ],
  "partitions": [
    {
      "name": "PartitionName",
      "source": "...",
      "sourceDetails": [...]
    }
  ],
  "measures": [
    {
      "name": "MeasureName",
      "expression": "...",
      "formatString": "..."
    }
  ],
  "annotations": [...]
}
```
