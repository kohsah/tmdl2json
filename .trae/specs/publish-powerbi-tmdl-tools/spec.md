# Publish powerbi-tmdl-tools to PyPI Spec

## Why
Publishing this repository as a PyPI package enables simple installation (`pip install powerbi-tmdl-tools`) and exposes stable CLIs for converting TMDL/PBIP to JSON and generating Mermaid ERDs.

## What Changes
- Add packaging metadata and build configuration for the PyPI distribution name **powerbi-tmdl-tools**.
- Add Apache-2.0 licensing artifacts and declare license metadata in the package.
- Ship the existing modules as installable Python modules.
- Provide 3 console entry points:
  - `tmdl-to-json` (TMDL/PBIP → JSON)
  - `pbip-to-json` (PBIP folder → JSON)
  - `tmdl-erd` (JSON → Mermaid ERD, optional PNG export)
- Keep runtime dependencies minimal; make PNG rendering dependencies optional where possible.

## Impact
- Affected specs: packaging/distribution, CLI UX
- Affected code: `pyproject.toml` (new), `LICENSE` (new), possibly small CLI wrappers, tests for entry points

## ADDED Requirements
### Requirement: PyPI Build Metadata
The repository SHALL include a `pyproject.toml` that can build an sdist and wheel for a PyPI release named `powerbi-tmdl-tools`.

#### Scenario: Build artifacts
- **WHEN** the maintainer runs `python -m build`
- **THEN** an sdist and wheel SHALL be produced successfully.

### Requirement: License
The package SHALL be published under the Apache-2.0 license.

#### Scenario: License artifacts
- **WHEN** a wheel or sdist is built
- **THEN** the distribution SHALL include the Apache-2.0 license text and declare Apache-2.0 in metadata.

### Requirement: Console Entry Points
The installed package SHALL expose 3 console scripts.

#### Scenario: tmdl-to-json CLI
- **WHEN** a user runs `tmdl-to-json --help`
- **THEN** the help text SHALL display successfully and reflect the current `tmdl_parser` CLI.

#### Scenario: pbip-to-json CLI
- **WHEN** a user runs `pbip-to-json --help`
- **THEN** the help text SHALL display successfully and reflect the current `pbip_parser` CLI.

#### Scenario: tmdl-erd CLI
- **WHEN** a user runs `tmdl-erd --help`
- **THEN** the help text SHALL display successfully and reflect the current `erd_generator` CLI.

### Requirement: Optional PNG Dependencies
The package SHALL keep core parsing usable without optional PNG rendering dependencies.

#### Scenario: Install without extras
- **GIVEN** the user installs `powerbi-tmdl-tools` without extras
- **WHEN** they run `tmdl-to-json` and `pbip-to-json`
- **THEN** commands SHALL work without requiring Mermaid CLI or Python `mermaid-cli`.

## MODIFIED Requirements
None.

## REMOVED Requirements
None.

