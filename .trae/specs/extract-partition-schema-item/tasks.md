# Tasks
- [x] Confirm current parser output for schema/item extraction on the two provided TMDL fixtures
  - [x] Parse `inhcm HRLocations.tmdl` and validate partition output includes `{schema: inhcm, item: HRLocations}`
  - [x] Parse `qapi vw_CurrentLocationFull_MasterData.tmdl` and validate partition output includes `{schema: qapi, item: vw_CurrentLocationFull_MasterData}`
- [x] Confirm table-level fields are present when schema/item are extracted
  - [x] For `inhcm HRLocations`, validate table JSON includes `schema=inhcm` and `table_item=HRLocations`
  - [x] For `qapi vw_CurrentLocationFull_MasterData`, validate table JSON includes `schema=qapi` and `table_item=vw_CurrentLocationFull_MasterData`
- [x] Add/adjust unit tests if required to cover both fixtures and edge cases (multiple occurrences)
- [x] Run `python -m unittest` and ensure all tests pass

# Task Dependencies
- Confirm table-level fields depends on confirming current parser output
- Add/adjust unit tests depends on confirming current parser output
