# Docs Agent Guide

## Overview

Sphinx documentation for GeoVista. Built with reStructuredText (`.rst`) and MyST-NB (`.ipynb`) sources, hosted on Read the Docs.

## Directory Structure

```
docs/
├── Makefile                 # Build targets
├── _build/                  # Build output (git-ignored, do not edit)
├── assets/                  # Non-Sphinx assets
└── src/                     # Sphinx source directory (SOURCEDIR)
    ├── conf.py              # Sphinx configuration
    ├── index.rst            # Root document
    ├── common.txt           # Shared RST substitutions (included via rst_prolog)
    ├── refs.bib             # BibTeX bibliography
    ├── _ext/                # Custom Sphinx extensions (readingtime)
    ├── _static/             # Static assets (CSS, fonts, images, branding)
    ├── _templates/          # Jinja2 Sphinx templates
    ├── _autoapi_templates/  # Custom sphinx-autoapi templates
    ├── developer/           # Developer guides (changelog, testing, packaging)
    ├── explanation/         # Explanation docs (Diátaxis)
    ├── howtos/              # How-to guides (Diátaxis)
    ├── tutorials/           # Jupyter notebook tutorials
    ├── reference/           # API reference, CLI, glossary, whatsnew
    ├── generated/           # Auto-generated (gallery) — do not edit
    └── tags/                # Auto-generated (sphinx-tags) — do not edit
```

## Build Commands

Run from the `docs/` directory:

```bash
make html              # Full build (all plots rendered)
make html-noplot       # No plots (fastest iteration)
make html-gallery      # Gallery plots only
make html-docstring    # Docstring plots only
make html-tutorial     # Tutorial plots only
make doctest           # Run doctests
make clean             # Remove build artifacts + generated sources
make clean-cache       # Purge myst-nb Jupyter cache
make clean-all         # clean + clean-cache
make serve-html        # Local HTTP server at http://localhost:11000
```

Pixi task equivalents (run from repo root):

```bash
pixi run -e docs make              # Builds with html-noplot by default
pixi run -e docs serve-html        # Build + serve
pixi run -e docs clean             # Clean build artifacts
```

Environment variables (set by Makefile):
- `PYVISTA_OFF_SCREEN=True`
- `PYDEVD_DISABLE_FILE_VALIDATION=1`

Sphinx flags: `--fail-on-warning --keep-going --show-traceback`

## Sphinx Extensions

Key extensions configured in `src/conf.py`:

| Extension | Purpose |
|-----------|---------|
| `autoapi.extension` | Auto-generate API docs from source |
| `sphinx_gallery.gen_gallery` | Example gallery from Python scripts |
| `myst_nb` | Render Jupyter notebooks (cached execution) |
| `numpydoc` | NumPy-style docstring parsing |
| `sphinx_design` | UI components (cards, tabs, grids) |
| `sphinxcontrib.bibtex` | Bibliography from `refs.bib` |
| `sphinxcontrib.mermaid` | Mermaid diagrams |
| `sphinx_tags` | Document tagging system |
| `sphinx_llms_txt` | LLM-friendly text output |
| `pyvista.ext.plot_directive` | 3D plot rendering in docstrings |
| `pyvista.ext.viewer_directive` | Interactive 3D viewer |

## Conventions

### File Formats

- Standard pages: reStructuredText (`.rst`)
- Tutorials: Jupyter notebooks (`.ipynb`) rendered via MyST-NB with cached execution
- Cross-references: use Sphinx roles (`:ref:`, `:doc:`, `:func:`, `:class:`, etc.)
- Shared substitutions live in `src/common.txt`

### Do Not Edit (Generated)

These paths are regenerated on build — never commit manual edits:

- `src/generated/` — sphinx-gallery output
- `src/reference/generated/` — sphinx-autoapi output
- `src/tags/` — sphinx-tags pages
- `_build/` — all build artifacts

### Adding a New Page

1. Create a `.rst` file in the appropriate section (`developer/`, `explanation/`, `howtos/`, `reference/`).
2. Add it to the section's `index.rst` toctree.
3. Follow the [Diátaxis](https://diataxis.fr/) framework (tutorials, how-tos, explanation, reference).

### Adding a Tutorial

1. Create a `.ipynb` notebook in `src/tutorials/`.
2. Add it to `src/tutorials/index.rst`.
3. Notebooks are executed and cached during build (`nb_execution_mode = "cache"`).

### RST Style

- Use NumPy-style docstrings in any Python within docs.
- Sphinx-lint and codespell run via pre-commit on `.rst` files.
- Ruff lints Python in `docs/src` (included in `tool.ruff` `src` list).

⚠️ **A new `:fa:`/`:fab:` icon must be added to `src/_static/color.css`.** The
selector list there ending `.fa-windows { color: #80d050 !important; }` is what
brands every icon green; an icon absent from it renders in the default text
colour and nothing warns you. Confirm the emitted class with
`grep -o '<[^>]*fa-<name>[^>]*>' _build/html/<page>.html` — it is `fa fa-<name>`,
and the list is alphabetical.

## Dependencies

Documentation deps are defined in:
- **Pixi**: `[tool.pixi.feature.docs.dependencies]` and `[tool.pixi.feature.docs.pypi-dependencies]` in `pyproject.toml`
- **pip**: `requirements/pypi-optional-docs.txt` (for `pip install -e ".[docs]"`)

Use the `docs` pixi environment: `pixi run -e docs <command>`

⚠️ **`sphinx-book-theme` pins `pydata-sphinx-theme` to an *exact* version**, so
the two only ever move together — `1.1.4` requires `==0.15.4`, `1.4.0` requires
`==0.20.0`. Bumping `pydata-sphinx-theme` on its own can never resolve, and
pinning it back silently freezes `sphinx-book-theme` too. Always bump the pair,
and check the target release's pin first:

```bash
curl -s https://pypi.org/pypi/sphinx-book-theme/<version>/json \
  | python3 -c "import json,sys; print([r for r in json.load(sys.stdin)['info']['requires_dist'] if 'pydata' in r])"
```

The theme is in maintenance mode but still releasing; it is not abandoned.

⚠️ **`src/_static/sidebar_toggle.js` is a workaround, not a feature.**
`sphinx-book-theme` renders a second `.primary-toggle` *and* `.secondary-toggle`
button and hides `pydata-sphinx-theme`'s pair, but both themes bind their
handlers with `document.querySelector(...)` — the *first* match, i.e. the hidden
one — so the visible buttons are inert and both sidebars are unreachable on a
phone. The shim forwards clicks to the bound button of each pair, and
self-retires when only one button remains. It also closes the primary dialog at
`(min-width: 992px)`, since the dialog inherits the sidebar's classes and so
inherits the wide-viewport collapsed state, which leaves it open but invisible
over a page it blocks.

The two halves retire on different schedules. The duplicate buttons are
[sphinx-book-theme#988](https://github.com/executablebooks/sphinx-book-theme/issues/988)
/ [#999](https://github.com/executablebooks/sphinx-book-theme/issues/999), already
fixed on `main` by
[#987](https://github.com/executablebooks/sphinx-book-theme/pull/987) but
unreleased as of `1.4.0`; the forwarding half self-retires when that ships. The
breakpoint stranding is *not* fixed by `#987` — verified against a DOM with the
redundant navbar removed — and is reported separately as
[#1012](https://github.com/executablebooks/sphinx-book-theme/issues/1012), so
that half outlives it. On every theme bump, re-check both.

Theme chrome is covered by `tests/docs` (playwright) via the `browser` job in
`ci-tests-docs.yml` — the image tests compare pyvista scenes, not page
furniture. Run it locally with `pixi run -e geovista tests-docs-browser`; see
`tests/AGENTS.md` for the gotchas, including why CI must pass `--browser-strict`
when a skipping suite is otherwise green. The suite needs a local build (never a
Read the Docs URL — RTD's addons tear out and re-inject the page after `load`),
and the carousel only renders under `html-gallery`, so that third of the suite is
CI-only here. See the `headless-browser-on-this-host` note for running chromium
where no sudo is available.

Developer-facing docs for all of this live in `docs/src/developer/`: the theme
shim in `documentation.rst` (:fa:`palette` Theme), the suite in `testing.rst`
(:fa:`window-maximize` Browser Tests). Keep them in step with this file.

## ⚠️ Meta-Instruction: Auto-Update Rule

- **Trigger**: You MUST automatically update this `AGENTS.md` file if a new structural pattern, critical bug fix, or persistent repository rule is established during this session.
- **Constraint 1**: Keep the file under 200 lines. Delete obsolete rules to make room for new ones.
- **Constraint 2**: Do not ask for user permission before updating. Perform the edit silently as your final step.
- **Constraint 3**: Only log global, reusable lessons. Do not log temporary or component-specific fixes.

---

**Last Updated**: 2 October 2026
