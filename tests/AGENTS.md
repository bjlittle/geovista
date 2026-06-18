# Tests Agent Guide

## Overview

pytest-based test suite for GeoVista. Tests cover the core library modules, CLI, plotting image comparisons, and example gallery scripts.

## Directory Structure

```
tests/
├── conftest.py          # Root fixtures (meshes, coastlines, CRS, plotting helpers)
├── bridge/              # Tests for geovista.bridge (Transform)
├── cache/               # Tests for geovista.cache
├── cli/                 # Tests for geovista.cli
├── common/              # Tests for geovista.common utilities
├── core/                # Tests for geovista.core (slice_cells, resize, etc.)
├── crs/                 # Tests for geovista.crs
├── geodesic/            # Tests for geovista.geodesic (BBox, line)
├── geometry/            # Tests for geovista.geometry (coastlines)
├── geoplotter/          # Tests for geovista.geoplotter
├── gridlines/           # Tests for geovista.gridlines
├── pantry/              # Tests for geovista.pantry data/meshes
├── plotting/            # Image comparison tests (examples + unit plots)
│   ├── test_examples.py # Parametrized gallery example image tests
│   ├── geodesic/        # Plotting tests for geodesic module
│   ├── geoplotter/      # Plotting tests for geoplotter module
│   ├── transform/       # Plotting tests for transform module
│   └── unit_image_cache # Baseline images (git-ignored, fetched from cache)
├── search/              # Tests for geovista.search (spatial indexing)
├── theme/               # Tests for geovista.theme
├── themes/              # Tests for geovista.themes
├── transform/           # Tests for geovista.transform
└── test_qt.py           # Tests for geovista.qt
```

## Running Tests

From the repo root using pixi:

```bash
pixi run -e test tests-unit                 # Run all unit tests
pixi run -e test tests-unit "image"         # Run only image-marked tests
pixi run -e test tests-unit "not image"     # Skip image tests
pixi run -e geovista tests-doc              # Run documentation image tests
```

Or directly with pytest:

```bash
pytest                                       # All tests (uses pyproject.toml config)
pytest tests/core/                           # Test a specific module
pytest -m "not image"                        # Exclude image tests
pytest -k "test_slice_cells"                 # Run by name pattern
```

## Configuration

All pytest configuration is in `pyproject.toml` under `[tool.pytest.ini_options]`:

- **Import mode**: `importlib` (no `sys.path` manipulation)
- **Strict config/markers**: unrecognized markers and config errors are failures
- **Doctests**: enabled via `--doctest-modules` (runs doctests in `src/`)
- **Warnings**: treated as errors, with explicit allowlist for known third-party warnings
- **xfail_strict**: `true` — unexpectedly passing xfail tests are failures

### Markers

| Marker | Purpose |
|--------|---------|
| `example` | Gallery image tests |
| `image` | Plotting image comparison tests |

### Required Plugins

- `pytest-mock` — mocking support
- `pytest_pyvista` — image comparison and off-screen rendering

## Conventions

### Test File Naming

- Files: `test_<function_or_class>.py` (one test file per public function/class)
- Functions: `test_<scenario>` (descriptive of the behaviour being verified)

### Copyright Header

Every test file must begin with:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.
```

### Imports

All test files must include `from __future__ import annotations` (enforced by ruff ISC rule).

### Fixtures

- Shared fixtures live in `conftest.py` at the appropriate directory level
- Root `conftest.py` provides: `lam_uk`, `lam_polar`, `lfric`, `lfric_sst`, `lfric_sst_eqc`, `coastlines`, `sphere`, `wgs84_wkt`, `plot_nodeid`, `lam_uk_cloud`, `lam_uk_sample`
- Use `request.param` with `pytest.fixture` for parametrized indirect fixtures

### Image Tests

- Plotting tests use `pytest-pyvista` for baseline image comparison
- Baseline images are cached remotely and fetched via `geovista.cache.CACHE`
- Image cache directory: `tests/plotting/unit_image_cache`
- Failed image output: `test_images_failed/`
- Use `verify_image_cache` fixture from pytest-pyvista
- Maximum image size: 450px

### Ruff Exceptions for Tests

Test files (`test*.py`) are exempt from:
- `ANN001` — no type annotations required for test function arguments
- `ANN201` — no return type annotations required
- `SLF001` — private member access is permitted

## Dependencies

Test deps are defined in:
- **Pixi**: `[tool.pixi.feature.test.dependencies]` in `pyproject.toml`
- **pip**: `requirements/pypi-optional-test.txt`

Use the `test` pixi environment: `pixi run -e test <command>`

## ⚠️ Meta-Instruction: Auto-Update Rule

- **Trigger**: You MUST automatically update this `AGENTS.md` file if a new structural pattern, critical bug fix, or persistent repository rule is established during this session.
- **Constraint 1**: Keep the file under 200 lines. Delete obsolete rules to make room for new ones.
- **Constraint 2**: Do not ask for user permission before updating. Perform the edit silently as your final step.
- **Constraint 3**: Only log global, reusable lessons. Do not log temporary or component-specific fixes.

---

**Last Updated**: 18 June 2026
