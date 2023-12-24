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

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import sys                                # noqa: ERA001
# sys.path.insert(0, os.path.abspath('.'))  # noqa: ERA001
from __future__ import annotations

import datetime
from importlib.metadata import version as get_version
import os
from pathlib import Path

import pyvista
from pyvista.plotting.utilities.sphinx_gallery import DynamicScraper
from sphinx_gallery.sorting import ExampleTitleSortKey

# -- General configuration ---------------------------------------------------
# See https://www.sphinx-doc.org/en/master/config.html#general-configuration

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    #    "jupyter_sphinx",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_gallery.gen_gallery",
    "pyvista.ext.viewer_directive",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


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

# src base directory
base_dir = Path(__file__).absolute().parent


# The name of the Pygments (syntax highlighting) style to use.
# https://pygments.org/styles/
pygments_style = "friendly"


# -- Options for HTML output -------------------------------------------------
# See https://www.sphinx-doc.org/en/master/config.html#options-for-html-output

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

html_logo = "_static/logo.png"

html_context = {
    "github_url": "https://github.com",
    "github_user": "bjlittle",
    "github_repo": "geovista",
    "github_version": "main",
    "doc_path": "docs/src",
}

html_theme_options = {
    "github_url": "https://github.com/bjlittle/geovista",
    "show_prev_next": False,
    "use_edit_page_button": True,
    "icon_links": [
        {
            "name": "Twitter",
            "url": "https://twitter.com/geovista_devs",
            "icon": "fab fa-twitter-square",
        },
        {
            "name": "Discussions",
            "url": "https://github.com/bjlittle/geovista/discussions",
            "icon": "fa fa-comments fa-fw",
        },
    ],
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_sidebars = {"**": ["sidebar-nav-bs", "sidebar-ethical-ads.html"]}


# -- Options for the linkcheck builder ---------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-the-linkcheck-builder

linkcheck_ignore = []
linkcheck_retries = 3


# -- Configuration: intersphinx ----------------------------------------------
intersphinx_mapping = {
    "cartopy": ("https://scitools.org.uk/cartopy/docs/latest/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "pyvista": ("https://docs.pyvista.org/", None),
}


# -- Configuration: copybutton -----------------------------------------------
# See https://sphinx-copybutton.readthedocs.io/en/latest/

copybutton_prompt_text = r">>> |\.\.\. "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"


# -- Configuration: doctest --------------------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html#configuration

doctest_global_setup = "import geovista"


# -- Configuration: extlinks -------------------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html

extlinks = {
    "issue": ("https://github.com/bjlittle/geovista/issues/%s", "Issue #%s"),
    "pull": ("https://github.com/bjlittle/geovista/pull/%s", "PR #%s"),
}


# -- Configuration: pyvista --------------------------------------------------

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
images_dir = base_dir / "generated" / "images"
pyvista.FIGURE_PATH = str(images_dir)
if not images_dir.exists():
    images_dir.mkdir(parents=True, exist_ok=True)

# We also need to start this on CI services and GitHub Actions has a CI env var
if on_rtd or os.environ.get("CI"):
    pyvista.start_xvfb()
    scraper = DynamicScraper()
else:
    scraper = "pyvista"


# -- Configuration: sphinx gallery -------------------------------------------
sphinx_gallery_conf = {
    "filename_pattern": "/.*",
    "ignore_pattern": "(__init__)|(fesom)|(synthetic)",
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
