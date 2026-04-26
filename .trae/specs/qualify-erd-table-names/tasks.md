# Tasks
- [x] Add qualified-name mapping in ERD generation
  - [x] Build a table-name -> rendered-name map using `schema` + `table_item` when present
  - [x] Use rendered-name in table definitions
  - [x] Use rendered-name in relationship endpoints (from/to) when mapping exists
- [x] Add/adjust unit tests for qualified table names and relationship mapping
- [x] Run `python -m unittest` and ensure all tests pass

# Task Dependencies
- Tests depends on qualified-name mapping implementation
