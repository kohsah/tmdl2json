# Align Table Source Item Field Spec

## Why
The extracted physical source object name is already stored under `partition.sourceDetails[].item`. The table-level field name should align with that terminology to avoid confusion.

## What Changes
- When extracting `{[Schema="...",Item="..."]}` from a partition `source`, save table-level fields as:
  - `table.schema`
  - `table.item` (same meaning as `partition.sourceDetails[].item`)
- Keep existing `table.table_item` as a backward-compatible alias for now (same value as `table.item`).
- Update ERD generation to prefer `table.item` (fallback to `table.table_item`) when rendering `schema.item`.

## Impact
- Affected specs: TMDL partition enrichment, ERD generation from model JSON
- Affected code: `tmdl_parser.py`, `erd_generator.py`, unit tests

## ADDED Requirements
### Requirement: Table-Level Source Fields
When schema/item values are extracted for a table from a partition `source`, the system SHALL save them on the table JSON object as `schema` and `item`.

#### Scenario: Table item aligns with sourceDetails item
- **GIVEN** a partition `sourceDetails` entry `{ "schema": "qapi", "item": "vw_CurrentLocationFull_MasterData" }`
- **WHEN** the TMDL is parsed to JSON
- **THEN** the table object SHALL include `"schema": "qapi"` and `"item": "vw_CurrentLocationFull_MasterData"`.

### Requirement: Backward-Compatible Alias
If the table object includes `item`, the system SHALL also include `table_item` with the same value for backward compatibility.

## MODIFIED Requirements
### Requirement: Qualified Entity Names
When generating Mermaid ERD, the generator SHALL render a table entity name as `schema.item` when `schema` and `item` are present; it MAY fall back to `schema.table_item` when `item` is not present.

## REMOVED Requirements
None.

