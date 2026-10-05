# Tests Agent Guide

## Overview

pytest-based test suite for GeoVista. Tests cover the core library modules, CLI, plotting image comparisons, and example gallery scripts.

## Directory Structure

One directory per `geovista` module — `bridge/`, `cache/`, `cli/`, `common/`,
`core/`, `crs/`, `geodesic/`, `geometry/`, `geoplotter/`, `gridlines/`,
`pantry/`, `search/`, `themes/`, `transform/` — plus `test_qt.py` and the root
`conftest.py` of shared fixtures. Two directories are not modules: `docs/`
tests the built documentation, and `plotting/` holds the image comparisons —
gallery examples in `test_examples.py`, per-module plots under `geodesic/`,
`geoplotter/` and `transform/`, baselines fetched into `unit_image_cache/`
(git-ignored).

## Running Tests

```bash
pixi run -e test tests-unit    # all unit tests; also "image", "not image"
pixi run -e geovista tests-doc # documentation image tests
pytest tests/core/             # direct; also -m "not image", -k "test_slice_cells"
```

The pixi tasks run from the repo root; pytest reads `pyproject.toml` either way.

## Configuration

All pytest configuration is in `pyproject.toml` under `[tool.pytest.ini_options]`:
import mode `importlib` (no `sys.path` manipulation), strict config and markers,
doctests on via `--doctest-modules`, `xfail_strict`, and warnings as errors with
an explicit allowlist for known third-party ones. Required plugins are
`pytest-mock` and `pytest_pyvista` (image comparison, off-screen rendering).

### Markers

| Marker | Purpose |
|--------|---------|
| `browser` | Documentation theme chrome tests |
| `example` | Gallery image tests |
| `image` | Plotting image comparison tests |

Apply `browser` module-wide with a `pytestmark` global. `tests/docs/test_tooltips.py`
mixes static and browser checks, so it marks per-test instead, which keeps
`-m "not browser"` selecting the static half.

## Conventions

### Naming and Preamble

One file per public function or class, named `test_<function_or_class>.py`, with
functions named `test_<scenario>` for the behaviour verified. Every file begins
with the copyright header given in the root `AGENTS.md`, followed by
`from __future__ import annotations` (both enforced by ruff). A name outside
pytest's `python_files` default is collected by nothing and warns about nothing:
`tests/themes/test.py` sat dead from #2259 until #2558 renamed it.

⚠️ **`tests/plotting/__init__.py` rewrites global `pyvista` state at import** —
the testing theme over `pv.global_theme`, plus `OFF_SCREEN` and
`GEOVISTA_IMAGE_TESTING`. That is *collection*, so `-m "not image"` is no
escape, and a test reading global theme state passes on its own directory and
fails in a full run. Restore it in a fixture: `copy.deepcopy` round-trips.

### Fixtures

- Shared fixtures live in `conftest.py` at the appropriate directory level
- Root `conftest.py` provides: `lam_uk`, `lam_polar`, `lfric`, `lfric_sst`, `lfric_sst_eqc`, `coastlines`, `sphere`, `wgs84_wkt`, `plot_nodeid`, `lam_uk_cloud`, `lam_uk_sample`
- Use `request.param` with `pytest.fixture` for parametrized indirect fixtures

### Image Tests

- Plotting tests use `pytest-pyvista` baseline comparison through the
  `verify_image_cache` fixture; maximum image size 450px
- Baselines are fetched via `geovista.cache.CACHE` into
  `tests/plotting/unit_image_cache`; failures land in `test_images_failed/`

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

`tests/docs` covers what no other Python test reaches: a headless chromium driven
over a built site with playwright for the theme chrome — sidebar toggles, dialogs,
carousel, tooltips — the sphinx configuration read off the built HTML or a
throwaway in-process build, and the off-site assets no page may load (#2559).

```bash
pixi run -e geovista tests-docs-browser-install   # one-off, fetches chromium
pixi run -e geovista tests-docs-browser           # build + test
pixi run -e geovista tests-docs-browser html-gallery  # include the carousel
pixi run -e geovista tests-docs-browser html-gallery strict  # what CI runs
```

Every prerequisite **skips** rather than fails — no playwright, no chromium, no
build, no carousel — so a plain `pytest` run is unaffected. The task selects the
whole of `tests/docs`, not the `browser` marker, so the sphinx configuration
tests beside them share the same CI job and the same guard.

⚠️ **A source-tree policy gate has nothing to skip on, and must not acquire
one.** `test_readingtime_coverage.py` reads `docs/src` as *text* and
`test_python_support.py` reads `pyproject.toml` beside the workflow matrices, so
neither needs sphinx, a build nor a browser. Both *derive* what they govern from
the tree rather than listing it, so a new page or `pyXYZ` feature is covered the
day it lands and an exemption must be declared with its reason. Guard such a gate
on nothing: a skip retires the rule in silence. The `reading` fixture comes from
`tests/docs/conftest.py`, shared with `test_readingtime.py`.

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
to be rid of them; the intersphinx inventory failure has no type and so cannot.

⚠️ **Register a path-loaded module in `sys.modules` before `exec_module`.**
`spec_from_file_location` does not, and a `@dataclass` under `from __future__
import annotations` resolves annotations through `sys.modules[cls.__module__]` —
so it raises `AttributeError: 'NoneType' object has no attribute '__dict__'` at
class creation. `docs/src/_ext` is not an importable package, so this is the only
way its modules reach a test.

⚠️ **The default `html-noplot` build has no carousel.** `plot_gallery=False`
leaves `geovista_carousel` nothing to render, so its tests skip. Only
`html-gallery` covers them, and rendering thumbnails needs a display, so like
the image tests the carousel is only meaningfully exercised in CI.

⚠️ **A setting applied in emitted JavaScript is invisible to the build.**
`tippy_skip_anchor_classes` is consulted in the browser as a tooltip is
*attached*, so a skipped anchor still has one *generated* into the page payload:
drop a class and nothing under `_build/html` changes. Only a browser sees it.
Its sibling `tippy_skip_urls` is applied as the tooltip is generated, so that
half *is* checkable statically. Gate a two-halved config with both kinds of
test, and be clear which half any given assertion covers.

⚠️ **Never let a generated artefact set a test's scope.** `sphinx_tippy` stamps
each payload with a UUID and its stale-payload cleanup globs the wrong path
part, so superseded payloads pile up beside the live one — resolve the live one
from the `<script src>` of the page. It writes an *empty* payload for a page it
tipped nothing on, so an empty file is data, not a failure; and gathering only
the pages that *have* payloads leaves a check vacuous on any page that loses
one. Enumerate every page and exclude by name.

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

`test*.py` is exempt from `ANN001`/`ANN201` (no annotations needed on test
functions) and `SLF001` (private member access is permitted).

## Dependencies

Test deps live in `[tool.pixi.feature.test.dependencies]` in `pyproject.toml`
and in `requirements/pypi-optional-test.txt`. Use `pixi run -e test <command>`.

## ⚠️ Meta-Instruction: Auto-Update Rule

- **Trigger**: You MUST automatically update this `AGENTS.md` file if a new structural pattern, critical bug fix, or persistent repository rule is established during this session.
- **Constraint 1**: Keep the file under 200 lines. Delete obsolete rules to make room for new ones.
- **Constraint 2**: Do not ask for user permission before updating. Perform the edit silently as your final step.
- **Constraint 3**: Only log global, reusable lessons. Do not log temporary or component-specific fixes.

---

**Last Updated**: 5 October 2026
