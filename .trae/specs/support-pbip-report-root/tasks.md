# Tasks
- [x] Task 1: Implement PBIP report-root input detection in `tmdl_parser.py`
  - [x] Add logic to detect PBIP root mode when input is a directory containing `.pbip`
  - [x] Add logic to accept an explicit `.pbip` file path and treat its parent as the root
  - [x] Keep existing `.tmdl` file and `.tmdl` directory behavior unchanged

- [x] Task 2: Implement PBIP resolution chain (root → report → dataset → semantic model definition)
  - [x] Parse the `.pbip` JSON and extract `artifacts[].report.path`
  - [x] Read `<report-folder>/definition.pbir` and extract `datasetReference.byPath.path`
  - [x] Resolve the semantic model folder path and locate its `definition/` folder
  - [x] Provide clear, deterministic errors for missing/ambiguous files or unsupported schema (e.g., `byConnection`)

- [x] Task 3: Aggregate definition folder TMDL into one JSON document
  - [x] Parse `database.tmdl`, `model.tmdl`, `relationships.tmdl` if present
  - [x] Parse all `tables/*.tmdl` into `tables: []` if the folder exists
  - [x] Parse all `cultures/*.tmdl` into `cultures: []` if the folder exists
  - [x] Ensure aggregation output is stable and predictable (ordering, keys)

- [x] Task 4: Add tests for PBIP-root resolution
  - [x] Add tests that run the resolution against `code/test_inputs/duty_stations_report/`
  - [x] Assert that output includes keys `database`, `model`, `relationships`, `tables`
  - [x] Assert that cultures are included when present
  - [x] Add negative tests for ambiguous `.pbip` discovery (0 or >1)

- [x] Task 5: Verification
  - [x] Run `../env/python -m unittest` from `code/`
  - [x] Manually validate parsing with the provided sample PBIP root and confirm the output is produced without requiring users to locate the semantic model folder themselves

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 3
- Task 5 depends on Task 4
