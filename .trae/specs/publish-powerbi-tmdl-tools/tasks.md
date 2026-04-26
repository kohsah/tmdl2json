# Tasks
- [x] Add packaging config and metadata
  - [x] Create `pyproject.toml` for `powerbi-tmdl-tools` using setuptools
  - [x] Define versioning approach (explicit version field; update for releases)
  - [x] Use `README.md` as long description and include package metadata (authors, classifiers, python requires)
- [x] Add Apache-2.0 license artifacts
  - [x] Add `LICENSE` file (Apache-2.0 text)
  - [x] Ensure license is included in sdist/wheel metadata
- [x] Add console entry points
  - [x] Implement stable callable entrypoints for `tmdl_parser`, `pbip_parser`, `erd_generator`
  - [x] Wire console scripts: `tmdl-to-json`, `pbip-to-json`, `tmdl-erd`
- [x] Restructure dependencies for optional PNG support
  - [x] Make core install dependency-free (stdlib only)
  - [x] Add optional extras for PNG rendering modes (e.g. `png-python`, `png-local`)
  - [x] Update docs to describe extras and install options
- [x] Packaging validation
  - [x] Build: `python -m build`
  - [x] Metadata validation: `twine check dist/*`
  - [x] Smoke test install the wheel and run `--help` for each console script

# Task Dependencies
- Console entry points depends on entrypoint wrappers being callable
- Packaging validation depends on packaging config + license + entry points
