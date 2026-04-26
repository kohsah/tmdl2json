# Support PBIP Report Root Input Spec

## Why
The current `tmdl_parser.py` CLI accepts a `.tmdl` file or a directory of `.tmdl` files, but PBIP exports are typically a *report root folder* containing a `.pbip` file that references a `.Report` folder, which then references the dataset semantic model folder. Accepting the report root folder as input removes manual path hunting and makes the tool easier to use on real PBIP projects.

## What Changes
- Extend `code/tmdl_parser.py` input handling to accept:
  - A PBIP report root folder containing a single `.pbip` file, or
  - A `.pbip` file path directly
- When given a PBIP report root, resolve the semantic model definition folder using:
  - `<root>/*.pbip` → `artifacts[].report.path` → `<root>/<report-folder>/definition.pbir` → `datasetReference.byPath.path` → `<semantic-model-folder>/definition`
- Parse the semantic model definition folder into a single aggregated JSON document (similar to `pbip_parser.py` output, but rooted from the report root resolution).
- Add tests covering PBIP-root resolution using the existing `code/test_inputs/duty_stations_report/` sample.

## Impact
- Affected specs: CLI input interpretation for `tmdl_parser.py`.
- Affected code: `code/tmdl_parser.py` (primary), tests under `code/`.
- No breaking changes for existing `.tmdl` file and directory modes.

## ADDED Requirements
### Requirement: PBIP Root Folder Input
`tmdl_parser.py` SHALL accept a PBIP report root folder as the input argument and produce an aggregated JSON representation of the referenced semantic model.

#### Scenario: Parse report root folder (success)
- **WHEN** the user runs `tmdl_parser.py` with the path `code/test_inputs/duty_stations_report/`
- **AND** that folder contains `Duty Stations Report.pbip` referencing `Duty Stations Report.Report/definition.pbir`
- **AND** `definition.pbir` contains `"datasetReference": { "byPath": { "path": "../Duty Stations Report.SemanticModel" } }`
- **THEN** the tool resolves the semantic model definition folder at `Duty Stations Report.SemanticModel/definition`
- **AND** outputs aggregated JSON with at least:
  - `database` parsed from `database.tmdl`
  - `model` parsed from `model.tmdl`
  - `relationships` parsed from `relationships.tmdl`
  - `tables` parsed from `tables/*.tmdl`
  - `cultures` parsed from `cultures/*.tmdl` (if present)

#### Scenario: Parse .pbip file path (success)
- **WHEN** the user runs `tmdl_parser.py` with the path `.../Duty Stations Report.pbip`
- **THEN** the tool treats the `.pbip` file’s parent directory as the PBIP report root folder and proceeds as in the previous scenario.

### Requirement: Deterministic Resolution
PBIP resolution SHALL be deterministic:
- If the input is a folder containing **exactly one** `.pbip` file, that file is used.
- If the input folder contains **zero** or **more than one** `.pbip` files, the tool SHALL fail with a clear error message indicating the ambiguity.

### Requirement: Robust Path Resolution
The tool SHALL correctly resolve relative paths containing spaces (e.g. `Duty Stations Report.Report`) on Windows.

## MODIFIED Requirements
### Requirement: Directory Input
If the input is a directory, `tmdl_parser.py` SHALL interpret it as:
- PBIP report root mode, if it contains a `.pbip` file, otherwise
- Existing “directory of `.tmdl` files” mode.

## REMOVED Requirements
None.
