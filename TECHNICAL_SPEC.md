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

## 6. ERD Generation

The tool includes a dedicated module (`erd_generator.py`) to visualize the semantic model structure.

### 6.1 Logic and Rules
- **Mermaid Syntax**: Output follows the standard Mermaid `erDiagram` syntax.
- **Table Exclusion**: 
  - Automatically filters out internal system tables to reduce noise.
  - **Exclusion Pattern**: Tables containing `DateTableTemplate` or `LocalDateTable` (case-insensitive) are skipped.
  - **Relationship Filtering**: Any relationship involving an excluded table is also removed.
- **Column Name Sanitization**:
  - **Formula Trimming**: Detects columns with DAX formulas (containing `=`) and truncates the name at the first `=` sign.
  - **Character Cleanup**: Removes quotes and replaces spaces with underscores to ensure valid Mermaid identifiers.
- **Data Type Mapping**: Maps TMDL data types to generic ERD types:
  - `int64` -> `int`
  - `double`, `decimal` -> `float` / `decimal`
  - `dateTime` -> `datetime`
  - `binary` -> `blob`
- **Relationships**:
  - Cardinality defaults to `}o--||` (Many-to-One) unless specified otherwise.
  - Labels are formatted as `"FromColumn to ToColumn"`.

### 6.2 PNG Export
- **Mechanism**: Generates PNGs by sending the Mermaid definition to the `mermaid.ink` API.
- **Implementation**:
  - Encodes the Mermaid Markdown string to UTF-8.
  - Converts the byte stream to a URL-safe Base64 string.
  - Constructs the URL: `https://mermaid.ink/img/<Base64String>`.
  - Downloads the binary content via `urllib` and saves it to the specified path.
- **Dependencies**: Uses only standard Python libraries (`base64`, `urllib`), ensuring zero external dependencies.

## Annex: Understanding LocalDateTable Files

### What are they?
Files named `LocalDateTable_*.tmdl` are automatically generated by Power BI because the **"Auto Date/Time"** feature is enabled in the report settings.

### Why do they exist?
1.  **One Table per Date Column**: When "Auto Date/Time" is on, Power BI scans the entire data model. For **every single column** formatted as a Date or DateTime, it automatically creates a hidden calculated table (a `LocalDateTable`) to handle time intelligence for that specific column.
    *   Example: If there are 10 different tables with a "ModifiedDate" column, Power BI creates 10 separate hidden `LocalDateTable` files.
    *   The GUIDs (e.g., `84ab9a85-bfee...`) are unique identifiers linking these hidden tables to their respective source columns.

2.  **Automatic Hierarchies**: These tables allow Power BI to provide the automatic "Year > Quarter > Month > Day" hierarchy when dragging a date field into a visual.

3.  **Hidden & Internal**:
    *   These files typically contain `isHidden` and `showAsVariationsOnly` properties, confirming they are internal structures.
    *   `DateTableTemplate_*.tmdl` files often exist alongside them, serving as the blueprint for creating these local tables.

### Best Practice
For production-grade models, it is widely considered a best practice to **disable "Auto Date/Time"** (File > Options > Current File > Data Load). These hidden tables can significantly bloat model size and clutter the TMDL folder structure. Instead, a single, dedicated Date dimension table (e.g., `DimDate`) is recommended.
