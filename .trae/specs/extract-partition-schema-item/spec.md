# Partition Schema/Item Extraction Spec

## Why
Partition M expressions often reference a concrete SQL object via `Source{[Schema="...",Item="..."]}[Data]`. Exposing those values in the parsed JSON makes lineage and ERD generation more reliable.

## What Changes
- Parse each partition `source` (M expression) and extract:
  - `Schema="..."` as `schema`
  - `Item="..."` as `item`
- Emit extracted values in the partition JSON under `sourceDetails` as objects: `{ "schema": "...", "item": "..." }`.
- Promote extracted values to table-level fields:
  - `table.schema`: the extracted schema name
  - `table.table_item`: the extracted item name (table/view)
  - Values are derived from the first partition of the table that contains a `{[Schema="...",Item="..."]}` occurrence.
- Preserve existing parsing behavior (e.g., `source` captured as a normalized multi-line string).

## Impact
- Affected specs: TMDL table parsing, partition parsing enrichment
- Affected code: `tmdl_parser.py` (partition `source` handling), unit tests

## ADDED Requirements
### Requirement: Partition Schema/Item Extraction
When a TMDL partition contains an M expression `source` block, the system SHALL extract the schema name and table name from any occurrence of the M record pattern `{[Schema="...",Item="..."]}`.

#### Scenario: Extract schema and item from Sql.Database source
- **GIVEN** a partition `source` containing `Source{[Schema="inhcm",Item="HRLocations"]}[Data]`
- **WHEN** the TMDL is parsed to JSON
- **THEN** the partition output SHALL contain `sourceDetails` with an entry `{ "schema": "inhcm", "item": "HRLocations" }`.

### Requirement: Table-Level Schema/Item Fields
When schema/item values are extracted for a table, the system SHALL save the schema and item individually on the table JSON object as `schema` and `table_item`.

#### Scenario: Table-level fields present for HRLocations
- **GIVEN** the table `inhcm HRLocations` has a partition `source` containing `Source{[Schema="inhcm",Item="HRLocations"]}[Data]`
- **WHEN** the TMDL is parsed to JSON
- **THEN** the table object SHALL include `"schema": "inhcm"` and `"table_item": "HRLocations"`.

#### Scenario: Table-level fields present for CurrentLocationFull
- **GIVEN** the table `qapi vw_CurrentLocationFull_MasterData` has a partition `source` containing `Source{[Schema="qapi",Item="vw_CurrentLocationFull_MasterData"]}[Data]`
- **WHEN** the TMDL is parsed to JSON
- **THEN** the table object SHALL include `"schema": "qapi"` and `"table_item": "vw_CurrentLocationFull_MasterData"`.

#### Scenario: No schema/item present in any partition source
- **GIVEN** a table has no `{[Schema="...",Item="..."]}` occurrence in any partition `source`
- **WHEN** the TMDL is parsed to JSON
- **THEN** the table object SHALL NOT include `schema` and `table_item`.

#### Scenario: Extract schema and item for a view-like item name
- **GIVEN** a partition `source` containing `Source{[Schema="qapi",Item="vw_CurrentLocationFull_MasterData"]}[Data]`
- **WHEN** the TMDL is parsed to JSON
- **THEN** the partition output SHALL contain `sourceDetails` with an entry `{ "schema": "qapi", "item": "vw_CurrentLocationFull_MasterData" }`.

#### Scenario: Multiple schema/item occurrences
- **GIVEN** a partition `source` containing multiple `{[Schema="...",Item="..."]}` occurrences
- **WHEN** the TMDL is parsed to JSON
- **THEN** the partition `sourceDetails` SHALL include an entry for each occurrence in source order.

## MODIFIED Requirements
### Requirement: Partition Source Capture
The system SHALL continue to capture the partition `source` as a normalized multi-line string and SHALL NOT alter the semantics of non-`source` partition properties.

## REMOVED Requirements
None.
