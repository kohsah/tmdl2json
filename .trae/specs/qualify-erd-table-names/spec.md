# Qualified ERD Table Names Spec

## Why
Power BI table names often differ from their physical SQL objects. When schema and table/view name are available, showing entities as `schema.item` makes ERDs easier to align with the source system.

## What Changes
- In Mermaid ERD output, when a table has both `schema` and `table_item`, render the entity name as `schema.table_item`.
- Apply the same mapping to relationships so relationship endpoints match the rendered entity names.
- Preserve existing behavior for tables without `schema`/`table_item`, and for relationship endpoints that refer to tables not present in `tables`.

## Impact
- Affected specs: ERD generation from model JSON
- Affected code: `erd_generator.py`, unit tests

## ADDED Requirements
### Requirement: Qualified Entity Names
The ERD generator SHALL render a table entity name as `schema.table_item` when the table object includes both `schema` and `table_item` fields.

#### Scenario: Render qualified entity name
- **GIVEN** a table with `"name": "inhcm HRLocations"`, `"schema": "inhcm"`, and `"table_item": "HRLocations"`
- **WHEN** an ERD is generated
- **THEN** the entity name SHALL be rendered as `"inhcm.HRLocations"`.

#### Scenario: Leave entity name unchanged when metadata missing
- **GIVEN** a table without `schema` or without `table_item`
- **WHEN** an ERD is generated
- **THEN** the entity name SHALL be rendered using the table’s `"name"` as it is today.

### Requirement: Relationship Endpoint Mapping
When a relationship references a table by name (e.g., `fromTable`/`toTable`), the ERD generator SHALL map that table name to the same rendered entity name used in the table definitions (qualified or unqualified).

#### Scenario: Relationship uses qualified endpoints
- **GIVEN** a relationship with `fromTable="qapi vw_CurrentLocationFull_MasterData"` and the referenced table has `schema="qapi"` and `table_item="vw_CurrentLocationFull_MasterData"`
- **WHEN** an ERD is generated
- **THEN** the relationship line SHALL reference `"qapi.vw_CurrentLocationFull_MasterData"` for that endpoint.

#### Scenario: Relationship table missing from tables list
- **GIVEN** a relationship references a table name that is not present in the `tables` array
- **WHEN** an ERD is generated
- **THEN** the relationship endpoint SHALL remain the original table name (no mapping).

## MODIFIED Requirements
### Requirement: ERD Output Determinism
The ERD generator SHALL remain deterministic for a given JSON input (no extra network calls or time-dependent data).

## REMOVED Requirements
None.

