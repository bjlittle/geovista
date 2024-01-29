# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html

Notes
-----
.. versionadded:: 0.1.0

"""

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with api docs) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import sys                                # noqa: ERA001
# sys.path.insert(0, os.path.abspath('.'))  # noqa: ERA001
from __future__ import annotations

import datetime
from importlib.metadata import version as get_version
import ntpath
import os
from pathlib import Path

import pyvista
from pyvista.plotting.utilities.sphinx_gallery import DynamicScraper
from sphinx_gallery.sorting import ExampleTitleSortKey


def autolog(message: str) -> None:
    """Write useful output to stdout, prefixing the source."""
    print(f"[{ntpath.basename(__file__)}] {message}")  # noqa: T201


# -- General configuration ---------------------------------------------------
# See https://www.sphinx-doc.org/en/master/config.html#general-configuration

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    #    "jupyter_sphinx",
    "autoapi.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_gallery.gen_gallery",
    "sphinx.ext.napoleon",
    "pyvista.ext.viewer_directive",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "**.ipynb_checkpoints",
    ".DS_Store",
    "_build",
    "Thumbs.db",
    "reference/generated/api/index.rst",
]

# The file extensions of source files.
source_suffix = {
    ".rst": "restructuredtext",
}

# The master toctree document.
root_doc = "index"

# If true, 'todo' and 'todoList' produce output, else they produce nothing.
todo_include_todos = False


# -- Project information -----------------------------------------------------
# See https://www.sphinx-doc.org/en/master/config.html#project-information

project = "GeoVista"
copyright_years = f"2021 - {datetime.datetime.now(datetime.UTC).year}"
copyright = f"{copyright_years}, {project} Contributors"  # noqa: A001
author = f"{project} Contributors"
on_rtd = os.environ.get("READTHEDOCS")

if on_rtd:
    # https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#including-content-based-on-tags
    # https://www.sphinx-doc.org/en/master/usage/configuration.html#conf-tags
    tags.add("on_rtd")  # noqa: F821

# The full version, including alpha/beta/rc tags
release = get_version("geovista")
if release.endswith("+dirty"):
    release = release[: -len("+dirty")]

# docs src directory
src_dir = Path(__file__).absolute().parent
root_dir = src_dir.parents[1]
package_dir = root_dir / "src"

autolog(f"[general] {src_dir=}")
autolog(f"[general] {root_dir=}")
autolog(f"[general] {package_dir=}")


# -- napoleon options --------------------------------------------------------
# See https://sphinxcontrib-napoleon.readthedocs.io/en/latest/sphinxcontrib.napoleon.html

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True  # includes dunders in api doc
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_keyword = True
napoleon_custom_sections = None


# -- autoapi options ---------------------------------------------------------
# See https://sphinx-autoapi.readthedocs.io/en/latest/how_to.html#how-to-include-type-annotations-as-types-in-rendered-docstrings
autodoc_typehints = "description"


# -- autoapi options ---------------------------------------------------------
# See https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html
#     https://github.com/readthedocs/sphinx-autoapi
#

autoapi_type = "python"
autoapi_dirs = [
    package_dir,
]
autoapi_root = "reference/generated/api"
autoapi_ignore = [
    str(package_dir / "geovista/examples/*"),
]
autoapi_member_order = "alphabetical"
autoapi_options = [
    "members",
    # "inherited-members",
    "undoc-members",
    # "private-members",
    # "special-members",
    "show-inheritance",
    # "show-inheritance-diagram",
    "show-module-summary",
    "imported-members",
]

autoapi_python_class_content = "both"
autoapi_keep_files = True
autoapi_add_toctree_entry = False

autolog(f"[autoapi] {autoapi_dirs=}")
autolog(f"[autoapi] {autoapi_ignore=}")
autolog(f"[autoapi] {autoapi_root=}")


# -- internationalization options --------------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-internationalization

language = "en"


# -- pygments options --------------------------------------------------------
# See https://pygments.org/styles/
# See https://pygments.org/docs/lexers/#lexers-for-python-and-related-languages

# The name of the Pygments (syntax highlighting) style to use.
highlight_language = "python"
highlight_options = {
    "default": "python",
    "bash": "powershell",
    "python": "python",
}
pygments_style = "friendly"


# -- HTML output options -----------------------------------------------------
# See https://www.sphinx-doc.org/en/master/config.html#options-for-html-output

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "sphinx_book_theme"
html_logo = "_static/logo.png"

html_context = {
    "github_url": "https://github.com",
    "github_user": "bjlittle",
    "github_repo": "geovista",
    "github_version": "main",
    "doc_path": "docs/src",
}

html_theme_options = {
    "home_page_in_toc": True,
    "icon_links": [
        {
            "name": "GitHub Discussions",
            "url": "https://github.com/bjlittle/geovista/discussions",
            "icon": "fa fa-comments fa-fw",
        },
        {
            "name": "GitHub Issues",
            "url": "https://github.com/bjlittle/geovista/issues",
            "icon": "fa-brands fa-square-github fa-fw",
        },
        {
            "name": "GitHub Pulls",
            "url": "https://github.com/bjlittle/geovista/pulls",
            "icon": "fa-brands fa-github-alt fa-fw",
        },
        {
            "name": "X (formally Twitter)",
            "url": "https://twitter.com/geovista_devs",
            "icon": "fa-brands fa-twitter",
        },
    ],
    "navigation_with_keys": False,
    "path_to_docs": "docs/src",
    "repository_branch": "main",
    "repository_url": "https://github.com/bjlittle/geovista",
    "show_prev_next": True,
    "show_toc_level": 4,
    "toc_title": "On this page",
    "use_download_button": True,
    "use_edit_page_button": False,
    "use_fullscreen_button": True,
    "use_issues_button": False,
    "use_repository_button": True,
    "use_sidenotes": True,
    "use_source_button": False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = [
    "_static",
]
html_css_files = [
    "style.css",
    "theme_overrides.css",
]


# -- linkcheck builder options -----------------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-the-linkcheck-builder

linkcheck_ignore = []
linkcheck_retries = 3


# -- intersphinx options -----------------------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html

intersphinx_mapping = {
    "cartopy": ("https://scitools.org.uk/cartopy/docs/latest/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pooch": ("https://www.fatiando.org/pooch/latest/", None),
    "pyproj": ("https://pyproj4.github.io/pyproj/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "pyvista": ("https://docs.pyvista.org/", None),
}


# -- copybutton options ------------------------------------------------------
# See https://sphinx-copybutton.readthedocs.io/en/latest/

copybutton_prompt_text = r">>> |\.\.\. "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"


# -- doctest options ---------------------------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html#configuration

doctest_global_setup = "import geovista"


# -- extlinks options --------------------------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html

extlinks = {
    "issue": ("https://github.com/bjlittle/geovista/issues/%s", "Issue #%s"),
    "pull": ("https://github.com/bjlittle/geovista/pull/%s", "PR #%s"),
}


# -- pyvista options ---------------------------------------------------------

# Manage errors
pyvista.set_error_output_file("errors.txt")

# Ensure that off-screen rendering is used for docs generation
pyvista.OFF_SCREEN = True

# Preferred plotting style for documentation
pyvista.set_plot_theme("document")
pyvista.global_theme.window_size = [1024, 768]
pyvista.global_theme.font.size = 22
pyvista.global_theme.font.label_size = 22
pyvista.global_theme.font.title_size = 22
pyvista.global_theme.return_cpos = False
pyvista.BUILDING_GALLERY = True
os.environ["PYVISTA_BUILDING_GALLERY"] = "true"

# Save figures in specified directory
images_dir = src_dir / "generated" / "images"
pyvista.FIGURE_PATH = str(images_dir)
if not images_dir.exists():
    images_dir.mkdir(parents=True, exist_ok=True)

# We also need to start this on CI services and GitHub Actions has a CI env var
if on_rtd or os.environ.get("CI"):
    pyvista.start_xvfb()

scraper = DynamicScraper()


# -- sphinx-gallery options --------------------------------------------------
# See https://sphinx-gallery.github.io/stable/configuration.html

sphinx_gallery_conf = {
    "filename_pattern": "/.*",
    "ignore_pattern": "(__init__)|(clouds)|(fesom)|(synthetic)",
    "examples_dirs": "../../src/geovista/examples",
    "gallery_dirs": "generated/gallery",
    "matplotlib_animations": True,
    "plot_gallery": True,
    "doc_module": ("geovista"),
    "image_scrapers": (scraper, "matplotlib"),
    "download_all_examples": False,
    "remove_config_comments": True,
    "within_subsection_order": ExampleTitleSortKey,
    "reference_url": {
        "geovista": None,
    },
}
