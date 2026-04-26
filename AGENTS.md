# Agent Guide

**Purpose:** This file is a *curated* index for agents to quickly locate the most important parts of this repository without traversing every folder.

**How to use (only for agents):**

- Read this file first.
- Only open the linked files/dirs relevant to the task.
- Avoid scanning the full repo tree unless the task explicitly requires it.
- **Always** check with the user that the model_architecture, model_config and module paths are correct. Only when the requested task/question(in chat or agent mode) is not obvious as to which architecture the user is requesting about you can ask about clarification before proceeding.

This repository is designed to be run from the `code/` directory and uses an in-repo virtual environment.

## Key Paths
- `README.md` (usage and CLI entry points)
- `docs/TECHNICAL_SPEC.md` (supported inputs and JSON outputs)
- `tmdl_parser.py` (TMDL parsing implementation)
- `pbip_parser.py` (PBIP parsing entry point)
- `config_loader.py` and `pbip_definition.json` (PBIP structure discovery/config)
- `erd_generator.py` (Mermaid ERD generation, optional PNG export)
- `test_tmdl_parser.py` and `test_pbip_parser.py` (tests)
- Windows venv Python: `../env/Scripts/python.exe`

## Conventions & Determinism Expectations
- Run commands from `code/`.
- Use the in-repo virtual environment Python (`../env/Scripts/python.exe` on Windows, or `../env/python` if you use a shim).
- TMDL parsing assumes tab-indented input; keep tests and fixtures consistent with tabs.
- Prefer deterministic behavior:
  - Avoid changes that introduce time-, locale-, machine-, or path-dependent output.
  - Keep network-dependent operations optional; PNG rendering uses `mermaid.ink`, while Mermaid text output remains deterministic for a given JSON input.

## Safe Change Guidelines (for agents and contributors)
- Keep edits scoped to the requested file(s); avoid repo-wide reformatting or broad search/replace.
- Do not add credentials or secrets; keep examples generic and safe to share.
- Validate changes:
  - For code changes: run `../env/Scripts/python.exe -m unittest` from `code/`.
  - For doc changes: verify referenced files exist and relative links resolve.

## Working Directory
- Run all commands with `code/` as the current working directory.

## Python Environment
- Use the repository virtual environment Python:
  - Windows venv: `../env/Scripts/python.exe`
  - If you have a shim: `../env/python`

## Documentation Layout
- Entry point: `README.md`
- Technical documentation: `docs/TECHNICAL_SPEC.md`

## Common Commands

### Convert TMDL to JSON
```bash
../env/Scripts/python.exe tmdl_parser.py path\to\file.tmdl -o output.json
```

### Parse a PBIP Folder to JSON
```bash
../env/Scripts/python.exe pbip_parser.py path\to\Report.pbip --output model.json
```

### Generate an ERD (Mermaid)
```bash
../env/Scripts/python.exe erd_generator.py model.json --output diagram.md
```

## Tests
Run all unit tests:
```bash
../env/Scripts/python.exe -m unittest
```

## Maintenance (Keeping This Current)
- Update this file when adding new entrypoints, moving config paths, or introducing a new canonical model variant.
- If the repo grows, add an explicit "Ignore Unless Needed" section listing heavy/rarely-used directories.
- Don't update all the architecture files, always focus on the architecture file in scope.
