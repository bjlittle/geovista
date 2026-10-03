# Tests Agent Guide

## Overview

pytest-based test suite for GeoVista. Tests cover the core library modules, CLI, plotting image comparisons, and example gallery scripts.

## Directory Structure

One directory per `geovista` module — `bridge/`, `cache/`, `cli/`, `common/`,
`core/`, `crs/`, `geodesic/`, `geometry/`, `geoplotter/`, `gridlines/`,
`pantry/`, `search/`, `theme/`, `themes/`, `transform/` — plus `test_qt.py`.
The exceptions:

```
tests/
├── conftest.py          # Root fixtures (meshes, coastlines, CRS, plotting helpers)
├── docs/                # Browser and sphinx configuration tests of the docs
└── plotting/            # Image comparison tests (examples + unit plots)
    ├── test_examples.py # Parametrized gallery example image tests
    ├── geodesic/ geoplotter/ transform/  # Plotting tests per module
    └── unit_image_cache # Baseline images (git-ignored, fetched from cache)
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
| `browser` | Documentation theme chrome tests |
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

⚠️ **Baselines live in a second repo.** `bjlittle/geovista-data` holds the PNGs
under `assets/`; `src/geovista/cache/registry.txt` lists `<path> <sha256>` and
`DATA_VERSION` (`src/geovista/cache/__init__.py`) names the **git tag** to fetch
from. Changing a baseline is therefore a two-repo dance: land the asset PR
there, let it release, then bump `DATA_VERSION` *and* the registry together — a
bump to a tag that does not exist yet fails the whole suite at collection, not
just the image tests. `registry.txt` is **hand-maintained**: grouped by blank
lines and only roughly sorted, so edit the affected lines in place. Never
rewrite or re-sort it.

⚠️ **Never hand-edit `version.txt` in `geovista-data`, and never tag it by
hand.** Its `ci-release.yml` does both automatically on merge to `main`: it
derives `YYYY.MM` from the current date and sets the serial to `0`, *unless*
`version.txt` already carries the current month, in which case it increments the
serial. So a manual bump to the version you want is self-defeating — it pushes
the release one serial past it. Predict the tag from the date and what is on
`main`, then bake that into `DATA_VERSION`.

### Documentation Tests

`tests/docs` covers what no other Python test can reach: a headless chromium
driven over a built site with playwright for the theme chrome — the sidebar
toggles, the dialogs they open, the gallery carousel — and the sphinx
configuration itself, by building throwaway documentation sets in-process.

```bash
pixi run -e geovista tests-docs-browser-install   # one-off, fetches chromium
pixi run -e geovista tests-docs-browser           # build + test
pixi run -e geovista tests-docs-browser html-gallery  # include the carousel
pixi run -e geovista tests-docs-browser html-gallery strict  # what CI runs
```

Every prerequisite **skips** rather than fails — no playwright, no chromium, no
build, no carousel — so a plain `pytest` run is unaffected. The task selects the
whole of `tests/docs`, not the `browser` marker, so the sphinx configuration
tests beside them are covered by the same CI job and the same guard.

⚠️ **A skipping suite is green, so CI must run `--browser-strict`.** CI installs
every prerequisite and builds the gallery deliberately; without the option, a
regression that stops the carousel being generated skips its three tests and the
job still passes, having silently lost the coverage it exists to provide. The
option turns each unmet prerequisite into a failure, and the second `strict`
argument of the pixi task passes it. Note that pytest honours `pytest_addoption`
only in the test-root `tests/conftest.py`, so that is where it is registered —
not in `tests/docs/`, which consumes it.

⚠️ **Only the first `Sphinx` application in a process builds cleanly.** docutils
registers nodes, directives and roles in a *global* registry, so every later
application re-registers them and sphinx warns once apiece — some 57 warnings
that fail any `warningiserror=True` build for reasons of the harness alone.
They are typed, so a generated `conf.py` can carry `suppress_warnings = ["app"]`
to be rid of them; the intersphinx inventory failure, by contrast, has no type
and so cannot be suppressed that way.

⚠️ **The default `html-noplot` build has no carousel.** `plot_gallery=False`
leaves `geovista_carousel` with nothing to render, so the carousel tests skip.
Only `html-gallery` (or another plotting target) covers them, and rendering the
thumbnails needs a display — so, exactly like the image tests, the carousel is
only meaningfully exercised in CI.

⚠️ **Never settle the page with a fixed delay.** Both themes inject their
toggles from JavaScript *after* load, so the chrome is not final when the page
is ready. `conftest.py` polls until the toggle count stops changing; a sleep
tuned on a developer machine is apt to be too short on a loaded CI runner.

⚠️ **`sd-stretched-link` covers its card through an `::after` overlay**, so the
anchor's own bounding rect is just its text. Click coverage must be checked by
hit-testing with `elementFromPoint`, not by comparing rectangles. A carousel
also deliberately hangs cards past its own edge, so only cards lying wholly
inside the clipping rect can be hit-tested — assert that some card qualifies,
or the test passes vacuously.

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

**Last Updated**: 2 October 2026
