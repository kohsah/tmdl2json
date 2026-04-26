# Offline Mermaid PNG Export Spec

## Why
`erd_generator.py` currently exports PNG via the hosted mermaid.ink service. This requires network access and may be undesirable for offline workflows or locked-down environments. The project needs a completely local/offline way to render Mermaid ERD text into PNG.

## What Changes
- Add a local/offline PNG rendering mode to `code/erd_generator.py` that invokes a locally installed Mermaid renderer (Mermaid CLI).
- Introduce a CLI switch to choose rendering mode:
  - `--png-mode local` for fully offline rendering (no HTTP calls)
  - `--png-mode remote` to use the existing mermaid.ink behavior
- Add an additional CLI rendering mode:
  - `--png-mode python` to render locally using the Python `mermaid-cli` library (no HTTP calls)
- Add an optional override for the Mermaid CLI executable path (e.g., `--mmdc-path`), otherwise discover it from `PATH`.
- Allow providing the Mermaid CLI executable path via an environment variable (in addition to `--mmdc-path`).
- Add `code/requirements.txt` including the Python `mermaid-cli` dependency required for `--png-mode python`.
- Improve error messaging when local prerequisites are missing (e.g., Mermaid CLI not installed).

## Impact
- Affected specs: ERD PNG export behavior and CLI options.
- Affected code: `code/erd_generator.py`, tests under `code/`, documentation describing the new options.

## ADDED Requirements
### Requirement: Fully Offline PNG Export
When `--png-output` is provided with `--png-mode local`, the system SHALL generate a PNG from the Mermaid ERD definition **without any network dependency**.

#### Scenario: Offline export succeeds
- **WHEN** the user runs `erd_generator.py input.json --png-output out.png --png-mode local`
- **AND** the Mermaid CLI executable is available (via `--mmdc-path`, environment variable, or on `PATH`)
- **THEN** the tool renders the Mermaid ERD to `out.png` locally
- **AND** does not attempt any HTTP request

#### Scenario: Offline prerequisites missing
- **WHEN** the user runs with `--png-mode local`
- **AND** Mermaid CLI is not available
- **THEN** the tool fails with a clear error explaining how to install/provide Mermaid CLI

### Requirement: Python Mermaid-CLI Rendering Mode
When `--png-output` is provided with `--png-mode python`, the system SHALL generate a PNG from the Mermaid ERD definition using the Python `mermaid-cli` library **without any network calls**.

#### Scenario: Python mode export succeeds
- **WHEN** the user runs `erd_generator.py input.json --png-output out.png --png-mode python`
- **AND** the Python dependency `mermaid-cli` is installed (from `code/requirements.txt`)
- **THEN** the tool renders the Mermaid ERD to `out.png` locally
- **AND** does not attempt any HTTP request

#### Scenario: Python mode prerequisites missing
- **WHEN** the user runs with `--png-mode python`
- **AND** the `mermaid-cli` Python library is not installed or cannot be imported
- **THEN** the tool fails with a clear error explaining how to install dependencies

### Requirement: Requirements File
The repository SHALL include `code/requirements.txt` listing the Python dependency for `--png-mode python`.

### Requirement: Mermaid CLI Path via Environment Variable
When running with `--png-mode local`, the system SHALL allow specifying the Mermaid CLI executable path via an environment variable.

#### Scenario: Environment variable provides Mermaid CLI path
- **WHEN** the user sets `MMDC_PATH` to the Mermaid CLI executable path
- **AND** the user runs `erd_generator.py input.json --png-output out.png --png-mode local`
- **THEN** the tool uses `MMDC_PATH` as the Mermaid CLI executable path

#### Scenario: Precedence
- **WHEN** `--mmdc-path` is provided
- **THEN** it takes precedence over `MMDC_PATH`
- **AND** `MMDC_PATH` takes precedence over `PATH` discovery

### Requirement: Backward-Compatible Default
The exporter SHALL preserve existing behavior by default:
- `erd_generator.py <input_json> --png-output <path>` continues to use the current remote mermaid.ink approach unless `--png-mode local` is explicitly requested.

## MODIFIED Requirements
### Requirement: Error Handling
If the PNG export cannot be generated, the tool SHALL fail with a clear, actionable error message including:
- Whether the failure was local prerequisite related, local rendering failure, or network/HTTP related (remote mode)
- The selected `--png-mode` and (when applicable) the endpoint or executable used

## REMOVED Requirements
None.
