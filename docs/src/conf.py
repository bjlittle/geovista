# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import datetime
from importlib.metadata import version as get_version
import os

import pyvista

# -- General configuration ---------------------------------------------------
# See https://www.sphinx-doc.org/en/master/config.html#general-configuration

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "jupyter_sphinx",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx_copybutton",
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
copyright_years = f"2021 - {datetime.datetime.now().year}"
copyright = f"{copyright_years}, {project} Contributors"
author = f"{project} Contributors"

# The full version, including alpha/beta/rc tags
release = get_version("geovista")
if release.endswith("+dirty"):
    release = release[: -len("+dirty")]

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

html_sidebars = {"**": ["sidebar-ethical-ads.html"]}


# -- Options for the linkcheck builder ---------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-the-linkcheck-builder

linkcheck_ignore = []
linkcheck_retries = 3


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
# Ensure that offscreen rendering is used for docs generation
pyvista.OFF_SCREEN = True  # Not necessary - simply an insurance policy
# Preferred plotting style for documentation
pyvista.set_plot_theme("document")
pyvista.global_theme.window_size = [1024, 768]
pyvista.global_theme.font.size = 22
pyvista.global_theme.font.label_size = 22
pyvista.global_theme.font.title_size = 22
pyvista.global_theme.return_cpos = False
pyvista.set_jupyter_backend(None)
# Save figures in specified directory
pyvista.FIGURE_PATH = os.path.join(os.path.abspath("./images"), "auto-generated")
if not os.path.exists(pyvista.FIGURE_PATH):
    os.makedirs(pyvista.FIGURE_PATH)
