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
    ├── _ext/                # Custom Sphinx extensions (readingtime, intersphinx_resilience)
    ├── _inventory/          # Vendored intersphinx fallbacks — do not hand-edit
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
make html              # full build; also html-noplot (fastest iteration),
                       # html-gallery, html-docstring, html-tutorial
make doctest           # run doctests
make clean             # build artifacts + generated sources; also
                       # clean-cache (purge myst-nb), clean-all
make serve-html        # local HTTP server at http://localhost:11000
```

Pixi task equivalents (run from repo root):

```bash
pixi run -e docs make              # Builds with html-noplot by default
pixi run -e docs serve-html        # Build + serve
pixi run -e docs clean             # Clean build artifacts
```

The Makefile sets `PYVISTA_OFF_SCREEN=True` and
`PYDEVD_DISABLE_FILE_VALIDATION=1`, and passes sphinx
`--fail-on-warning --keep-going --show-traceback`.

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
_build/html`; `sphinx-iconify` still loads `code.iconify.design` on 171 pages.

⚠️ **`tippy_skip_urls` matches the raw `href`, which comes in two shapes.**
`re.match` is applied to the href exactly as written into the page: bare between
sibling pages (`clouds.html`) and directory-prefixed from anywhere else
(`../generated/gallery/domain/clouds.html`), so a pattern for one shape silently
matches nothing from the other and nothing warns. Its sibling
`tippy_skip_anchor_classes` *replaces* the defaults `headerlink`/`sd-stretched-link`
rather than extending them, and is applied in the browser, so dropping one leaves
the build output unchanged. `tests/docs/test_tooltips.py` gates both.

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

### Adding a New Page or Tutorial

Create the `.rst` in the appropriate section (`developer/`, `explanation/`,
`howtos/`, `reference/`) or the `.ipynb` in `src/tutorials/`, then add it to that
section's `index.rst` toctree, following [Diátaxis](https://diataxis.fr/).
Notebooks are executed and cached on build (`nb_execution_mode = "cache"`).

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

Deps live in `[tool.pixi.feature.docs.dependencies]` / `.pypi-dependencies` in
`pyproject.toml`, and in `requirements/pypi-optional-docs.txt` for
`pip install -e ".[docs]"`. Use `pixi run -e docs <command>`.

⚠️ **`sphinx-book-theme` pins `pydata-sphinx-theme` to an *exact* version**, so
the two only ever move together — `1.1.4` requires `==0.15.4`, `1.4.0` requires
`==0.20.0`. Bumping `pydata-sphinx-theme` on its own can never resolve, and
pinning it back silently freezes `sphinx-book-theme` too. Always bump the pair,
checking the target release's pin first with `curl -s
https://pypi.org/pypi/sphinx-book-theme/<version>/json | grep -o
'pydata-sphinx-theme[^"]*'`. The theme is in maintenance mode but still
releasing; it is not abandoned.

⚠️ **A `contextlib.suppress(ModuleNotFoundError)` extension guard outlives its
reason.** `sphinx-tippy`'s was written when conda-forge had no package; by #2549
it did, and the guard let a missing extension drop every tooltip while the build
still exited 0. Check conda-forge before adding one, and again before keeping one.

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

The two halves retire separately. The duplicate buttons are sphinx-book-theme
[#988](https://github.com/executablebooks/sphinx-book-theme/issues/988) /
[#999](https://github.com/executablebooks/sphinx-book-theme/issues/999), fixed on
`main` by [#987](https://github.com/executablebooks/sphinx-book-theme/pull/987)
but unreleased as of `1.4.0`. The breakpoint stranding is *not* fixed by it —
verified against a DOM with the redundant navbar removed — and is
[#1012](https://github.com/executablebooks/sphinx-book-theme/issues/1012), so
that half outlives it. Re-check both on every theme bump.

Theme chrome is covered by `tests/docs` (playwright) via the `browser` job in
`ci-tests-docs.yml` — the image tests compare pyvista scenes, not page furniture.
Run it with `pixi run -e geovista tests-docs-browser`; see `tests/AGENTS.md` for
the gotchas, including why CI must pass `--browser-strict` when a skipping suite
is otherwise green. The suite needs a local build (never a Read the Docs URL —
RTD's addons tear out and re-inject the page after `load`), and the carousel only
renders under `html-gallery`, so that third of the suite is CI-only here. See the
`headless-browser-on-this-host` note for running chromium without sudo.

Developer-facing docs live in `docs/src/developer/`: the theme shim and tooltips
in `documentation.rst` (:fa:`palette` Theme, :fa:`comments` Tooltips), the suite
in `testing.rst` (:fa:`window-maximize` Browser Tests). Keep them in step.

## ⚠️ Meta-Instruction: Auto-Update Rule

- **Trigger**: You MUST automatically update this `AGENTS.md` file if a new structural pattern, critical bug fix, or persistent repository rule is established during this session.
- **Constraint 1**: Keep the file under 200 lines. Delete obsolete rules to make room for new ones.
- **Constraint 2**: Do not ask for user permission before updating. Perform the edit silently as your final step.
- **Constraint 3**: Only log global, reusable lessons. Do not log temporary or component-specific fixes.

---

**Last Updated**: 5 October 2026
