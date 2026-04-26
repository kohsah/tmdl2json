# Tasks
- [x] Update TMDL parser table-level fields to use `item` (and keep `table_item` as alias)
- [x] Update ERD generator to prefer `schema` + `item` when rendering `schema.item` (fallback to `table_item`)
- [x] Update/extend unit tests for:
  - [x] table-level `schema` + `item`
  - [x] alias `table_item`
  - [x] ERD rendering uses `schema.item`
- [x] Run `python -m unittest` and ensure all tests pass
