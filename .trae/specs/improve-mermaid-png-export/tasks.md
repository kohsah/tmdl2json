# Tasks
- [x] Task 1: Add local/offline PNG export mode in `erd_generator.py`
  - [x] Add `--png-mode {remote,local}` (default: remote to preserve current behavior)
  - [x] Add `--mmdc-path` to optionally specify Mermaid CLI executable
  - [x] Implement local rendering by invoking Mermaid CLI (no HTTP requests in local mode)
  - [x] Keep existing remote mermaid.ink export for remote mode
  - [x] Improve error handling for missing prerequisites and subprocess failures

- [x] Task 4: Support Mermaid CLI path via environment variable
  - [x] Read Mermaid CLI path from `MMDC_PATH` for `--png-mode local`
  - [x] Define precedence: `--mmdc-path` > `MMDC_PATH` > `PATH`
  - [x] Add unit tests covering the environment-variable resolution behavior

- [x] Task 2: Add unit tests for local/offline mode behavior
  - [x] Add a `unittest` module that mocks Mermaid CLI discovery and subprocess invocation
  - [x] Verify that local mode errors clearly when Mermaid CLI is missing
  - [x] Verify that local mode invokes Mermaid CLI with the expected arguments and writes the requested PNG path

- [x] Task 3: Verification
  - [x] Run `../env/python -m unittest` from `code/`
  - [x] (Optional manual) Run `erd_generator.py` with `--png-output` using both:
    - `--png-mode remote` (when network is available)
    - `--png-mode local` (when Mermaid CLI is installed locally)

- [ ] Task 5: Add Python `mermaid-cli` rendering option and dependencies
- [x] Task 5: Add Python `mermaid-cli` rendering option and dependencies
  - [x] Extend `--png-mode` to support `python`
  - [x] Implement Python-mode PNG export using the `mermaid-cli` library (no HTTP calls)
  - [x] Add `code/requirements.txt` including `mermaid-cli` (and any required transitive prerequisites needed at runtime)
  - [x] Add unit tests that validate Python mode behavior without requiring network access

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 2
- Task 5 depends on Task 4
