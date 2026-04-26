# Technical Specification: TMDL/PBIP to JSON Tooling

This document describes the current behavior and outputs of the scripts in `code/` that parse Power BI/Tabular semantic model artifacts into JSON, and the optional ERD generator.

## 1. Overview

The repository provides:
- `tmdl_parser.py`: Parses a single `.tmdl` file (or a directory of `.tmdl` files) into JSON.
- `pbip_parser.py`: Parses a `.pbip` folder structure, discovers the semantic model definition files, and aggregates them into a single JSON document.
- `erd_generator.py`: Generates a Mermaid `erDiagram` from the aggregated JSON (from either parser) and can optionally render a PNG via mermaid.ink.

All parsing is indentation-based and expects tab-indented TMDL files.

## 2. TMDL Parsing (`tmdl_parser.py`)

### 2.1 Root Objects

The parser recognizes the following root-level declarations:

#### 2.1.1 Table
- **Syntax**: `table <TableName>`
- **Output**: Root object with:
  - `name`: `<TableName>`
  - `type`: `table`
  - Additional properties extracted as key/value pairs

#### 2.1.2 Database
- **Syntax**: `database <DatabaseName>`
- **Output**: Root object with:
  - `name`: `<DatabaseName>`
  - `type`: `database`
  - Additional properties extracted as key/value pairs

#### 2.1.3 Model
- **Syntax**: `model <ModelName>`
- **Output**: Root object with:
  - `name`: `<ModelName>`
  - `type`: `model`
  - Additional properties extracted as key/value pairs

#### 2.1.4 Relationships File
- **Syntax**: `relationship <RelationshipId>`
- **Output**: Root object with:
  - `relationships`: list of relationship objects (see 2.3)

### 2.2 Nested Elements

Nested elements attach to the current parent object based on indentation.

#### 2.2.1 Column
- **Syntax**: `column <ColumnName>` (typically under `table`)
- **Output**:
  - `name`: `<ColumnName>`
  - `type`: `column`
  - Properties extracted from `key: value` and `key = value` forms (examples: `dataType`, `summarizeBy`, `formatString`, `sourceColumn`, `lineageTag`)

#### 2.2.2 Partition
- **Syntax**:
  - `partition <PartitionName>`
  - `partition <PartitionName> = <PartitionType>` (e.g. `m`)
- **Output**:
  - `name`: `<PartitionName>`
  - `type`: `partition`
  - `partitionType`: `<PartitionType>` when present
  - Partition properties (examples: `mode`)
  - `source`: extracted from a multi-line block when defined as `source =` (see 2.4)
  - Optional enrichment under `sourceDetails` (see 2.5)

#### 2.2.3 Measure
- **Syntax**: `measure '<MeasureName>' = <Expression>`
- **Output**:
  - `name`: `<MeasureName>` (outer single quotes stripped when present)
  - `type`: `measure`
  - `expression`: extracted from one of:
    - Inline form: `measure 'X' = SUM(T[Col])`
    - Delimited block form: `measure 'X' = ``` ... ````
    - Implicit indented block form: `measure 'X' =` followed by a deeper-indented expression block
  - Additional measure properties are captured from subsequent lines (examples: `formatString`, `displayFolder`, `lineageTag`)

#### 2.2.4 Annotation
- **Syntax**: `annotation <Key> = <Value>`
- **Output**:
  - Appended to `annotations` as objects: `{"name": "<Key>", "value": "<Value>"}`

### 2.3 Relationship Parsing

Relationships are captured when parsing a file that contains `relationship ...` entries.

- **Syntax**: `relationship <RelationshipId>`
- **Output per relationship**:
  - `name`: `<RelationshipId>`
  - `type`: `relationship`
  - Relationship properties are captured from nested lines (examples: `joinOnDateBehavior`, `isActive`, `toCardinality`)

Column references inside relationship entries are captured and enriched:
- **Input**:
  - `fromColumn: DimTable.DimKey`
  - `toColumn: FactTable.FactKey`
- **Output**:
  - `fromColumn`: original string
  - `toColumn`: original string
  - `fromTable`: derived table name
  - `fromColumnName`: derived column name
  - `toTable`: derived table name
  - `toColumnName`: derived column name

The derivation splits on the last `.` and strips surrounding single/double quotes from the table/column parts when present.

### 2.4 Multi-line Block Normalization

Multi-line blocks are captured for:
- Partition `source` blocks defined as `source =` followed by deeper-indented lines
- Measure expressions defined as either a delimited triple-backtick block or an implicit indented block

Normalization behavior:
- Computes the minimum common leading tab indentation among non-empty lines in the block.
- Strips that common indentation so the extracted text preserves relative formatting without structural indentation.

### 2.5 Partition `source` Enrichment (`sourceDetails`)

When a partition contains a multi-line `source` block, the parser attempts additional extraction:

#### 2.5.1 Schema/Item Extraction
- **Pattern**: `{[Schema="dbo",Item="Table1"]}` (whitespace tolerant)
- **Output**:
  - Adds `sourceDetails` with entries like:
    - `{"schema": "dbo", "item": "Table1"}`

If multiple matches exist, multiple entries are produced.

#### 2.5.2 Base64 Decode + Decompression Attempt
- **Pattern**: `Binary.FromText("...", BinaryEncoding.Base64)`
- **Behavior**:
  - Base64-decodes the string
  - Attempts decompression (raw deflate first, then standard zlib)
- **Output**:
  - Adds `sourceDetails` entries like:
    - `{"contentType": "decompressed_json", "content": "<decoded text>"}`
  - On failure, emits an error entry for that match.

## 3. PBIP Parsing (`pbip_parser.py`)

### 3.1 Purpose

PBIP parsing aggregates a Power BI Project (`.pbip`) folder into one JSON document by locating the semantic model definition folder and parsing specific TMDL files and folders.

### 3.2 Configuration (`pbip_definition.json`)

`pbip_parser.py` uses `pbip_definition.json` (via `config_loader.py`) to determine:
- PBIP file naming patterns to validate expected structure
- Semantic model folder discovery pattern
- Definition folder name (commonly `definition`)
- Which definition files to parse (e.g. `database.tmdl`, `model.tmdl`, `relationships.tmdl`, `expressions.tmdl`)
- Which definition folders to parse (e.g. a `tables/` folder containing one `.tmdl` per table)

### 3.3 Aggregated JSON Output Shape

The aggregated JSON is a dictionary that may include:
- `database`: parsed output from `database.tmdl`
- `model`: parsed output from `model.tmdl`
- `relationships`: list of relationship objects parsed from `relationships.tmdl`
- `expressions`: parsed output from `expressions.tmdl` (as produced by the TMDL parser for the given file)
- `tables`: list of parsed table objects, one per `.tmdl` file under the configured tables folder

## 4. ERD Generation (`erd_generator.py`)

### 4.1 Inputs

The ERD generator expects JSON shaped like the PBIP aggregate output:
- `tables`: list of table objects with `name` and optional `columns`
- `relationships`: list of relationship objects with `fromTable`, `toTable`, `fromColumnName`, `toColumnName`

### 4.2 Table and Column Rules
- Excludes tables whose names contain `DateTableTemplate` or `LocalDateTable` (case-insensitive).
- Writes Mermaid entities using quoted table names.
- Writes attributes as `type name`, where:
  - The type is mapped from TMDL types (`int64` -> `int`, `dateTime` -> `datetime`, `binary` -> `blob`, etc.).
  - The attribute name is sanitized:
    - Truncates at the first `=` (to remove DAX-like suffixes)
    - Replaces spaces with `_`
    - Removes single/double quotes

### 4.3 Relationship Rules
- Relationships involving excluded tables are skipped.
- Cardinality defaults to Many-to-One: `}o` on the left and `||` on the right.
- If `toCardinality` is `many`, the right side uses `o{`.
- Connector style depends on activity:
  - `isActive: true` (or missing): uses `--`
  - `isActive: false`: uses `..`
- Relationship label is `"fromColumnName to toColumnName"`.

## Annex: Understanding LocalDateTable Files

### What are they?
Files named `LocalDateTable_*.tmdl` are automatically generated by Power BI when **Auto Date/Time** is enabled.

### Why do they exist?
1. **One table per date column**: Power BI can generate a hidden date table for each Date/DateTime column to support automatic hierarchies.
2. **Automatic hierarchies**: Enables the built-in `Year > Quarter > Month > Day` experience.
3. **Hidden & internal**: These tables are internal model artifacts and often include properties like `isHidden`.

### Best practice
For production models, disable Auto Date/Time and use a single explicit date dimension (e.g., `DimDate`) to avoid model bloat and clutter.
