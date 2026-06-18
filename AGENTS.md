# GeoVista Project Guidelines

## Overview

GeoVista is a cartographic rendering and mesh analytics library powered by PyVista. It transforms rectilinear, curvilinear, and unstructured geospatial data into geolocated PyVista meshes with CRS-aware projection and 3D visualization.

## Architecture

```
src/geovista/          # Library source (lazy-loaded modules)
├── bridge.py          # Transform data to PyVista meshes
├── core.py            # Mesh slicing, resizing, remeshing
├── crs.py             # Coordinate Reference System utilities
├── geodesic.py        # Geodesic BBox and line operations
├── geometry.py        # Coastline features
├── geoplotter.py      # Cartographic PyVista plotter
├── gridlines.py       # Graticule / grid lines
├── search.py          # Spatial indexing (pykdtree)
├── transform.py       # Mesh transformations
├── cache/             # Pooch-based data cache
├── pantry/            # Sample data loaders
├── examples/          # Gallery example scripts
├── cli.py             # Click CLI entry point
├── themes.py          # PyVista theme registration
└── filters.py         # VTK filter wrappers
tests/                 # pytest test suite (see tests/AGENTS.md)
docs/                  # Sphinx documentation (see docs/AGENTS.md)
changelog/             # Towncrier news fragments
requirements/          # pip requirement files
```

## Build and Test

Package manager: **pixi** (conda-forge). Environments defined in `pyproject.toml` under `[tool.pixi.*]`.

```bash
pixi run -e test tests-unit              # Run unit tests
pixi run -e test tests-unit "image"      # Image comparison tests only
pixi run -e test tests-unit "not image"  # Skip image tests
pixi run -e docs make                    # Build docs (html-noplot)
pixi run -e docs serve-html              # Build + serve docs locally
pixi run download                        # Fetch offline assets
```

Direct pytest (with pixi environment activated):

```bash
pytest                    # All tests
pytest tests/core/        # Specific module
pytest -m "not image"     # Exclude image tests
```

## Code Style

- **Formatter/Linter**: ruff (config in `pyproject.toml` under `[tool.ruff]`)
- **Type checking**: mypy strict mode (`[tool.mypy]`)
- **Docstrings**: NumPy style, validated by numpydoc
- **Line length**: 88 characters
- **Pre-commit**: hooks defined in `.pre-commit-config.yaml`

### Copyright Header

Every Python file must begin with:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.
```

### Required Import

All Python files must include `from __future__ import annotations` (enforced by ruff).

## Conventions

- **Versioning**: `setuptools-scm` (no manual version file edits)
- **Changelog**: towncrier fragments in `changelog/` — one `.rst` file per PR per change type, named `{PR_NUMBER}.{TYPE}.rst`. Use the `changelog-fragment` skill or see `pyproject.toml` `[tool.towncrier]` for valid types.
- **Dependencies**: core deps in `requirements/pypi-core.txt`; optional groups in `requirements/pypi-optional-*.txt`. Pixi deps mirrored in `pyproject.toml`.
- **License**: BSD-3-Clause

## Subdirectory Guides

- [docs/AGENTS.md](docs/AGENTS.md) — documentation build, Sphinx extensions, adding pages/tutorials
- [tests/AGENTS.md](tests/AGENTS.md) — test structure, fixtures, image tests, pytest config

## ⚠️ Meta-Instruction: Auto-Update Rule

- **Trigger**: You MUST automatically update this `AGENTS.md` file if a new structural pattern, critical bug fix, or persistent repository rule is established during this session.
- **Constraint 1**: Keep the file under 200 lines. Delete obsolete rules to make room for new ones.
- **Constraint 2**: Do not ask for user permission before updating. Perform the edit silently as your final step.
- **Constraint 3**: Only log global, reusable lessons. Do not log temporary or component-specific fixes.

---

**Last Updated**: 18 June 2026
