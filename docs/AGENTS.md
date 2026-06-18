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

## Dependencies

Documentation deps are defined in:
- **Pixi**: `[tool.pixi.feature.docs.dependencies]` and `[tool.pixi.feature.docs.pypi-dependencies]` in `pyproject.toml`
- **pip**: `requirements/pypi-optional-docs.txt` (for `pip install -e ".[docs]"`)

Use the `docs` pixi environment: `pixi run -e docs <command>`

## ⚠️ Meta-Instruction: Auto-Update Rule

- **Trigger**: You MUST automatically update this `AGENTS.md` file if a new structural pattern, critical bug fix, or persistent repository rule is established during this session.
- **Constraint 1**: Keep the file under 200 lines. Delete obsolete rules to make room for new ones.
- **Constraint 2**: Do not ask for user permission before updating. Perform the edit silently as your final step.
- **Constraint 3**: Only log global, reusable lessons. Do not log temporary or component-specific fixes.

---

**Last Updated**: 18 June 2026
