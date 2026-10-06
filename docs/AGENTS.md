# Docs Agent Guide

## Overview

Sphinx documentation for GeoVista. Built with reStructuredText (`.rst`) and MyST-NB (`.ipynb`) sources, hosted on Read the Docs.

## Directory Structure

```
docs/
├── Makefile                 # Build targets
├── assets/                  # Non-Sphinx assets
├── _build/                  # Build output (git-ignored, do not edit)
└── src/                     # Sphinx source directory (SOURCEDIR)
    ├── conf.py index.rst    # Sphinx configuration; root document
    ├── common.txt refs.bib  # Shared RST substitutions (included); bibliography
    ├── _ext/ _inventory/    # Custom extensions; vendored .inv — do not hand-edit
    ├── _static/             # CSS, fonts, branding, and vendored js/ and icons/
    ├── _templates/ _autoapi_templates/   # Jinja2 templates
    ├── developer/ explanation/ howtos/ tutorials/ reference/  # Diátaxis
    └── generated/ tags/ reference/generated/  # Auto-generated — do not edit
```

## Build Commands

Run from the `docs/` directory:

```bash
make html        # full; also html-noplot (fastest), html-gallery/-docstring/-tutorial
make doctest     # run doctests
make clean       # build + generated sources; also clean-cache (myst-nb), clean-all
make serve-html  # local HTTP server at http://localhost:11000
```

Each has a pixi task of the same name, run from the repo root as
`pixi run -e docs <task>`; `make` builds `html-noplot`.

The Makefile sets `PYVISTA_OFF_SCREEN=True` and `PYDEVD_DISABLE_FILE_VALIDATION=1`,
and passes sphinx `--fail-on-warning --keep-going --show-traceback`.

## Sphinx Extensions

Key extensions configured in `src/conf.py`:

| Extension | Purpose |
|-----------|---------|
| `autoapi.extension` | Auto-generate API docs from source |
| `sphinx_gallery.gen_gallery` | Example gallery from Python scripts |
| `myst_nb` | Render Jupyter notebooks (cached execution) |
| `numpydoc` | NumPy-style docstring parsing |
| `sphinx_design` | UI components (cards, tabs, grids) |
| `sphinxcontrib.bibtex` / `.mermaid` | Bibliography from `refs.bib`; mermaid diagrams |
| `sphinx_tags` | Document tagging system |
| `sphinx_llms_txt` | LLM-friendly text output |
| `pyvista.ext.plot_directive` / `.viewer_directive` | 3D plots in docstrings; interactive viewer |

⚠️ **A new `intersphinx_mapping` entry needs a vendored inventory.** Add the URL
to `INTERSPHINX_URLS` in `src/conf.py` — the single source of truth, read by
`.github/scripts/inventories.py` — then run `pixi run -e docs fetch-inventories`
and commit the `_inventory/*.inv` it writes. Without one, an outage at that site
falls through to `intersphinx_resilience`, which saves the build by disabling
`nitpicky` for the rest of it. See the root `AGENTS.md` and issue #2517.

⚠️ **An extension's default asset URLs are a network dependency too**, and they
bite at *read* time, so no build log ever shows them. `sphinx-tippy` defaulted
`tippy_js` to two floating-major `unpkg` URLs on 148 of 173 pages until #2549
vendored the bundles under `src/_static/js/` (not `_static/tippy/`, which the
extension owns, nor `_static/vendor/`, the theme's), each beside its upstream MIT
notice as `<bundle>.LICENSE.txt`. Audit with `grep -rho '<script[^>]*src="https[^"]*"'
_build/html` — though that sees the *loader*, not what it then fetches: the
`sphinx-iconify` script on 171 pages resolved each icon against `api.iconify.design`
from inside the bundle, so vendoring it would have cleaned the grep and fixed
nothing. #2559 dropped it for SVGs under `_static/icons/`, gated by `test_assets.py`.

⚠️ **`tippy_skip_urls` matches the raw `href`, which comes in two shapes.**
`re.match` sees the href as written: bare between sibling pages (`clouds.html`)
and directory-prefixed from anywhere else (`../generated/gallery/domain/clouds.html`),
so a pattern for one shape silently matches nothing from the other, unwarned. Its
sibling `tippy_skip_anchor_classes` *replaces* the defaults
`headerlink`/`sd-stretched-link` rather than extending them, and applies in the
browser, so dropping one leaves the build unchanged. `test_tooltips.py` gates both.

⚠️ **Nothing type-checks `src/_ext`:** the `mypy` hook is `pass_filenames: false`,
so it only sees `[tool.mypy] files = ["src/geovista"]`, and `numpydoc-validation`
is `files: "^src/"` — #2551 found `PATTERN: re.Match` and a `-> None` `setup()`
returning a dict. That `setup()` must also return `parallel_read_safe` and
`parallel_write_safe`, or `--jobs` warns twice and reads serially, failing
`--fail-on-warning`; and must `env.note_dependency(__file__)` for anything it
bakes into a doctree, its own modules being no source sphinx watches.

⚠️ **`sphinx-llms-txt` concatenates `_sources/*` verbatim** — page *source*, so
`llms-full.txt` carries `.. readingtime::` rather than the banner, and no
directive output can appear there. Check rendering with the `text` builder.

## Conventions

### File Formats

Pages are reStructuredText; tutorials are Jupyter notebooks. Cross-reference with
Sphinx roles (`:ref:`, `:doc:`, `:func:`), and keep substitutions in `src/common.txt`.

### Do Not Edit (Generated)

Regenerated on build, never commit manual edits: `src/generated/` (sphinx-gallery),
`src/reference/generated/` (sphinx-autoapi), `src/tags/` (sphinx-tags), `_build/`.

### Adding a New Page or Tutorial

Create the `.rst` in the appropriate section (`developer/`, `explanation/`,
`howtos/`, `reference/`) or the `.ipynb` in `src/tutorials/`, then add it to that
section's `index.rst` toctree, following [Diátaxis](https://diataxis.fr/).
Notebooks are executed and cached on build (`nb_execution_mode = "cache"`).

⚠️ **It also needs a reading-time banner, or an exemption.** Every page read
start to finish opens with `.. readingtime::` at column 0, after the title and
before the first section — exactly one; a directive lower down is a
demonstration. A page *navigated* rather than read (landing page, generated
body, lookup table, or an `.. include::` of a page that carries one) goes in
`EXEMPT` in `tests/docs/test_readingtime_coverage.py` **with its reason**. That
gate derives its corpus from `src`, so a new page is governed the day it lands;
the build stays silent and the test is what tells you. On a MyST page wrap it in
an `{eval-rst}` fence or use the native `{readingtime}` one — a bare
`.. readingtime::` line there renders as prose, unwarned. Reserve a literal
`.. readingtime:: <n>` for an estimate the word count cannot make, such as a
tutorial whose reader runs every snippet.

⚠️ **A `.md` page is built the day it lands.** `myst_parser` registers `.md` itself,
whatever `source_suffix` names, so it warns `toc.not_included` and fails the build
unless a toctree holds it, a page `.. include::`s it, or it sets `orphan: true` (#2564).

### RST Style

NumPy-style docstrings in any Python within docs; sphinx-lint and codespell run
on `.rst` via pre-commit, and ruff lints Python in `docs/src`.

⚠️ **A reformat silently desyncs `:emphasize-lines:`.** The `black` 26 reflow in
#2557 left `testing.rst` pointing past a now 3-line block; only the build sees it.

⚠️ **A new `:fa:`/`:fab:` icon must be added to `src/_static/color.css`.** The
selector list there ending `.fa-windows { color: #80d050 !important; }` brands every
icon green; one absent from it renders in the default text colour, unwarned. Confirm
the emitted class with `grep -o '<[^>]*fa-<name>[^>]*>' _build/html/<page>.html` — it
is `fa fa-<name>`, and the list is alphabetical.

## Dependencies

Deps live in `[tool.pixi.feature.docs.dependencies]` / `.pypi-dependencies` in
`pyproject.toml`, and in `requirements/pypi-optional-docs.txt` for
`pip install -e ".[docs]"`. Use `pixi run -e docs <command>`.

⚠️ **`sphinx-book-theme` pins `pydata-sphinx-theme` to an *exact* version** — the two
only move together (`1.4.0` requires `==0.20.0`). Bumping either alone can never
resolve, and pinning one back silently freezes the other. Always bump the pair, checking
the target release's pin in its PyPI JSON. It is in maintenance mode, not abandoned.

⚠️ **A `contextlib.suppress(ModuleNotFoundError)` extension guard outlives its
reason.** `sphinx-tippy`'s predated its conda-forge package and, by #2549, let a
missing extension drop every tooltip while the build still exited 0. Check
conda-forge before adding one, and again before keeping one.

⚠️ **`src/_static/sidebar_toggle.js` is a workaround, not a feature.**
`sphinx-book-theme` renders a second `.primary-toggle`/`.secondary-toggle` pair
and hides `pydata-sphinx-theme`'s, but both themes bind with
`document.querySelector(...)` — the *first* match, i.e. the hidden one — so the
visible buttons are inert and both sidebars are unreachable on a phone. The shim
forwards clicks to the bound button of each pair, self-retires when only one
remains, and closes the primary dialog at `(min-width: 992px)`, where it
inherits the sidebar's collapsed state and sits open but invisible over a page
it blocks.

The two halves retire separately. The duplicate buttons are sphinx-book-theme
[#988](https://github.com/executablebooks/sphinx-book-theme/issues/988) /
[#999](https://github.com/executablebooks/sphinx-book-theme/issues/999), fixed on
`main` by [#987](https://github.com/executablebooks/sphinx-book-theme/pull/987)
but unreleased as of `1.4.0`. The breakpoint stranding is *not* fixed by it
(verified against a DOM with the redundant navbar removed) and is
[#1012](https://github.com/executablebooks/sphinx-book-theme/issues/1012), so
outlives it. Re-check both on every theme bump.

Theme chrome is covered by `tests/docs` (playwright) via the `browser` job in
`ci-tests-docs.yml` — the image tests compare pyvista scenes, not page furniture.
Run `pixi run -e geovista tests-docs-browser`; `tests/AGENTS.md` has the gotchas,
including why CI must pass `--browser-strict`. The suite needs a *local* build,
never a Read the Docs URL — RTD's addons re-inject the page after `load`.

Developer-facing docs live in `docs/src/developer/`: the theme shim and tooltips
in `documentation.rst` (:fa:`palette` Theme, :fa:`comments` Tooltips), the suite
in `testing.rst` (:fa:`window-maximize` Browser Tests). Keep them in step.

## ⚠️ Meta-Instruction: Auto-Update Rule

- **Trigger**: You MUST automatically update this `AGENTS.md` file if a new structural pattern, critical bug fix, or persistent repository rule is established during this session.
- **Constraint 1**: Keep the file under 200 lines. Delete obsolete rules to make room for new ones.
- **Constraint 2**: Do not ask for user permission before updating. Perform the edit silently as your final step.
- **Constraint 3**: Only log global, reusable lessons. Do not log temporary or component-specific fixes.

---

**Last Updated**: 6 October 2026
