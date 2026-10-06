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
pixi run -e geovista tests-docs-browser  # Browser tests of the docs chrome
pixi run download                        # Fetch offline assets
```

**`geovista` is the superset environment** — development, testing, docs and all.
Prefer `pixi run -e geovista ...` over hunting across `test`/`devs`/`docs`.

**Use `--frozen` to reproduce CI.** Every CI job installs with `frozen: true`
and runs `pixi run --frozen ...`, which resolves strictly from `pixi.lock`
rather than re-solving the manifest — so `pixi run --frozen -e <env> ...`
locally is the same environment CI gets. The corollary: after editing any
dependency, run `pixi lock` *first*, or `--frozen` will silently keep running
the previous environment.

⚠️ **But `pixi lock` alone will not raise a version ceiling.** It only
re-solves when the lock is *invalid*, and an already-locked version still
satisfies a widened max-pin — so bumping a ceiling and running `pixi lock`
leaves the old version in place, and the suite then silently tests nothing new.
Use `pixi update <pkg>`, and confirm with `pixi list -e <env> <pkg>`. The same
bump must also be applied to `requirements/pypi-*.txt`, which `pixi` neither
reads nor updates.

⚠️ **A max-pin cannot see a renamed distribution.** `vtk-xref` became
`sphinx-vtk-xref` (#2541): the old name stopped at 0.1.2, so `pixi update`
had nothing to offer and dependabot nothing to propose, while five months of
fixes landed under the new name. A long-still pin is a smell — check PyPI.

⚠️ **A conda-forge package of the same name is not always the Python one.**
Tools that ship both a Node and a Python distribution (`playwright` is the
case in point) are packaged on conda-forge as the *Node* CLI, with no Python
bindings at all — the conda package installs cleanly and `import <pkg>` then
raises `ModuleNotFoundError`. Check with `pixi list -e <env> <pkg>` plus an
actual import before assuming conda-forge availability settles it; such
packages belong in a feature's `pypi-dependencies`.

**Install the hooks and let them gate commits, not CI:**

```bash
pixi run -e devs pre-commit install                 # fires on every commit
pixi run -e devs pre-commit run --files <paths>     # check before pushing
```

⚠️ **`pre-commit run mypy` is the authoritative type check, not bare `mypy`.**
`mypy` is available in `devs`/`geovista`, but invoking it directly does *not*
reproduce CI: `.pre-commit-config.yaml` uses `mirrors-mypy`, whose isolated venv
has no third-party libraries, so `pyvista`/`numpy` collapse to `Any`. Inside a
pixi environment mypy sees their real types and reports hundreds of additional
strict-mode errors (mostly in `examples/`) that the hook never raises. Use bare
`mypy` to explore a single file; trust only the hook. Note too that `pyproj` is
largely untyped: returning a `pyproj` expression from a `-> bool` function trips
`no-any-return`, so bind an annotated local first.

⚠️ **Image tests segfault without a GPU/display**, so a green local run proves
nothing about them — they are only meaningfully exercised in CI. `pytest.ini`
sets `filterwarnings = ["error", ...]`, so *any* new `warnings.warn` in library
code can fail an image test even when unit tests pass. Warn only when the
condition is genuinely exceptional, and check CI before calling such work done.

⚠️ **A suite that skips is a suite that passes.** Where a test guards itself on
a prerequisite — a display, a browser, a built artefact — CI must *require* that
prerequisite rather than inherit the local skip, or a regression that removes it
silently drops the coverage and the job still exits 0. `tests/docs` does this
with `--browser-strict`; follow the pattern for any new guarded suite.

⚠️ **Every `docs` build task wipes the build first.** `make` and `doctest`
both `depends-on` `clean`, and `serve-html`, `tests-doc` and
`tests-docs-browser` all chain through `make` — so `pixi run -e docs make` is
never incremental, and running the browser tests destroys the build you were
inspecting. For an incremental rebuild, invoke sphinx directly:

```bash
cd docs && pixi run -e docs sphinx-build -b html \
  -D plot_docstring=False -D plot_gallery=False \
  -D plot_inline=False -D plot_tutorial=False \
  -d _build/doctrees src _build/html
```

⚠️ **`intersphinx` is no longer allowed to fail the build (#2517).** Each
mapping in `conf.py` is `(url, (None, "_inventory/<name>.inv"))`, so an
unreachable remote falls back on the vendored copy — sphinx logs an earlier
location's failure at `info` once a later one succeeds, leaving
`--fail-on-warning` green. Add a mapping and you **must** add its inventory:
`pixi run -e docs fetch-inventories`, which `ci-inventories.yml` also runs
monthly to raise a refresh PR. Should every location fail, the
`intersphinx_resilience` extension disables `nitpicky` for the rest of the
build rather than emitting the warning plus its cascade of hundreds of nitpick
misses — a degraded build is annotated, so check the job summary before
trusting a green docs run.

⚠️ **`nitpick_ignore_regex` entries are prefix matches.** Sphinx applies them
with `re.match`, anchored at the start only, so `(r"py:mod", r"pyvista")` also
silenced `pyvistaqt` and every other target sharing that prefix. An entry can
equally outlive its cause and silence nothing, while still masking a future
regression: drop it once the upstream inventory gains the target (#2555).

## Code Style

- **Formatter/Linter**: ruff (config in `pyproject.toml` under `[tool.ruff]`)
- **Type checking**: mypy strict mode (`[tool.mypy]`)
- **Docstrings**: NumPy style, validated by numpydoc. Record a new public API
  with `.. versionadded:: X.Y.Z` under `Notes`; the `.. versionchanged::`
  directive is **not** used in this project. Get the next version from
  `geovista.__version__` (setuptools-scm), not by guessing.
- **Line length**: 88 characters
- **Pre-commit**: hooks defined in `.pre-commit-config.yaml`
- **`__all__`**: the API documentation is generated by sphinx-autoapi, which
  honours a module's `__all__`. A new public name — **constants included**, not
  just classes and functions — must be added there or it will not be rendered.
  ruff (`RUF022`) enforces the sort order.

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
- **Changelog**: towncrier fragments in `changelog/` — one `.rst` file per PR per change type, named `{PR_NUMBER}.{TYPE}.rst`. Use the `changelog-fragment` skill or see `pyproject.toml` `[tool.towncrier]` for valid types. ⚠️ `ci-changelog.yml` requires one *touched* file to be named for **your** PR, so a PR that only edits pre-existing fragments fails it until you add the `skip-changelog` label. Run the same check locally with `pixi run -e docs python .github/scripts/changelog.py <PR> "<touched fragment paths>"`.
- **`agentic` label**: ⚠️ **every issue and pull-request you raise must carry
  it**, alongside the usual `type:` ones — `gh` runs as the repository owner, so
  nothing else tells agent-generated work apart. `ci-label.yml` adds it
  automatically only for branches named `agent*`/`ai*`, which the `docs/`,
  `deps/`, `tests/` prefixes used here never match — so pass `--label agentic`
  to `gh issue create` / `gh pr create`, or `gh issue edit <n> --add-label
  agentic` after the fact. It is **not** the `bot` label, which marks
  deterministic automation: dependabot, and the scheduled `ci-*.yml` workflows.
- **Python support**: SPEC 0 — drop a minor version three years after its
  release. Nine places declare it, so bump the trove classifiers first and let
  `tests/test_python_support.py` name whatever else must follow.
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

**Last Updated**: 6 October 2026
