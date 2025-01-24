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

import ast
import contextlib
import datetime
from importlib.metadata import version as get_version
import os
from pathlib import Path
import re
import subprocess
import textwrap
from typing import TYPE_CHECKING
from urllib.parse import quote

import pyvista
from pyvista.plotting.utilities.sphinx_gallery import DynamicScraper
from sphinx.util import logging
from sphinx.util.console import colorize

if TYPE_CHECKING:
    from collections.abc import Iterable

    from autoapi.mappers.python.objects import (
        PythonAttribute,
        PythonData,
        PythonFunction,
        PythonMethod,
        PythonModule,
        PythonPackage,
        PythonProperty,
    )
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

    # type aliases.
    Mapper = (
        PythonAttribute
        | PythonData
        | PythonFunction
        | PythonMethod
        | PythonModule
        | PythonPackage
        | PythonProperty
    )


GALLERY_DIRS: str = "generated/gallery"
"""sphinx-gallery target output directory"""


def autolog(message: str, section: str | None = None, color: str | None = None) -> None:
    """Log the diagnostics `message` with optional `section` prefix.

    Parameters
    ----------
    message : str
        The diagnostics message.
    section : str, optional
        The prefix text for the diagnostics message.
    color : str, optional
        The color of the `section` prefix text.

    """
    if color is None:
        color = "brown"

    section = colorize(color, colorize("bold", f"[{section}] ")) if section else ""
    msg = f"{colorize(color, section)}{colorize('darkblue', f'{message}')}"
    logger.info(msg)


logger = logging.getLogger("sphinx-geovista")


# -- General configuration ---------------------------------------------------
# See https://www.sphinx-doc.org/en/master/config.html#general-configuration

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "numpydoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "autoapi.extension",
    "sphinx.ext.doctest",
    "sphinx.ext.duration",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_changelog",
    "sphinx_click",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_gallery.gen_gallery",
    "sphinx_tags",
    "sphinx_togglebutton",
    "pyvista.ext.plot_directive",
    "pyvista.ext.viewer_directive",
    "myst_nb",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "**.ipynb_checkpoints",
    ".DS_Store",
    "_autoapi_templates",
    "_build",
    "Thumbs.db",
    "reference/generated/api/index.rst",
    "generated/gallery/**/*.ipynb",
]

# The file extensions of source files.
source_suffix = {
    ".rst": "restructuredtext",
    ".ipynb": "myst-nb",
}

# The master toctree document.
root_doc = "index"

# Sphinx document translation with sphinx gettext feature uses these settings:
locale_dirs = ["locale/"]
gettext_compact = False


# -- Project information -----------------------------------------------------
# See https://www.sphinx-doc.org/en/master/config.html#project-information

project = "GeoVista"
now = datetime.datetime.now(datetime.UTC)
copyright_years = f"2021 - {now.year}"
copyright = f"{copyright_years}, {project} Contributors"  # noqa: A001
# Explicitly unset to save rendering by sphinx as an additional line on the
# page footer, thus minimising the footer footprint. Instead, append "author"
# to "copyright".
author = ""

on_rtd = os.environ.get("READTHEDOCS") == "True"
rtd_version = os.environ.get("READTHEDOCS_VERSION")

if rtd_version is not None:
    # Make rtd_version safe for use in shields.io badges.
    rtd_version = rtd_version.replace("_", "__")
    rtd_version = rtd_version.replace("-", "--")
    rtd_version = quote(rtd_version)

# branch, tag, external (for pull requests) or unknown.
rtd_version_type = os.environ.get("READTHEDOCS_VERSION_TYPE")

# get the short commit sha.
rev_parse = subprocess.run(  # noqa: S603
    ["git", "rev-parse", "--short", "HEAD"],  # noqa: S607
    capture_output=True,
    text=True,
    check=True,
)
commit_sha = rev_parse.stdout.strip()

if on_rtd:
    # https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#including-content-based-on-tags
    # https://www.sphinx-doc.org/en/master/usage/configuration.html#conf-tags
    tags.add("on_rtd")  # noqa: F821

# The full version, including alpha/beta/rc tags
version = release = get_version("geovista")

rst_epilog = f"""
.. |gv_version| replace:: v{version}
.. |build_date| replace:: ({now.strftime("%Y-%m-%d")})
"""

# docs src directory
docs_src_dir = Path(__file__).absolute().parent
docs_images_dir = docs_src_dir / "_static" / "images"
root_dir = docs_src_dir.parents[1]
package_src_dir = root_dir / "src"
package_dir = package_src_dir / "geovista"

autolog(f"{docs_src_dir=}", section="General")
autolog(f"{docs_images_dir=}", section="General")
autolog(f"{root_dir=}", section="General")
autolog(f"{package_src_dir=}", section="General")
autolog(f"{package_dir=}", section="General")


# sphinx-tippy options -------------------------------------------------------
# See https://github.com/sphinx-extensions2/sphinx-tippy

# optional dependency (unavailable on conda-forge)
with contextlib.suppress(ModuleNotFoundError):
    import sphinx_tippy  # noqa: F401

    extensions.append("sphinx_tippy")

tippy_enable_wikitips = False
tippy_enable_doitips = False
tippy_rtd_urls = [
    "https://www.sphinx-doc.org/en/master/",
    "https://geovista.readthedocs.io/en/latest/",
    "https://geovista.readthedocs.io/en/stable/",
    "http://localhost:11000",
    "http://0.0.0.0:11000",
    "http://127.0.0.1:11000",
    "http://localhost:8888",
    "http://0.0.0.0:8888",
    "http://127.0.0.1:8888",
    "https://matplotlib.org/stable/",
    "https://numpy.org/doc/stable/",
    "https://platformdirs.readthedocs.io/en/stable/",
    "https://rasterio.readthedocs.io/en/stable/",
    "https://requests.readthedocs.io/en/stable/",
]
tippy_skip_anchor_classes = ("headerlink", "sd-stretched-link")
tippy_anchor_parent_selector = "article.bd-article"
tippy_props = {"maxWidth": 700, "placement": "top-start", "theme": "light"}


# sphinx-tags options --------------------------------------------------------
# See https://sphinx-tags.readthedocs.io/en/latest/index.html

tags_badge_colors = {
    "component:*": "primary",  # coastlines, graticule, manifold, texture, vectors
    "domain:*": "secondary",  # oceanography, seismology, meteorology, orography
    "filter:*": "success",  # extrude, threshold, warp
    "load:*": "dark",  # rectilinear, curvilinear, unstructured, points, geotiff
    "projection:*": "warning",  # crs, transform
    "render": "danger",  # camera
    "style:*": "light",  # colormap, lighting, opacity, shading
    "widget:*": "info",  # checkbox, logo
}

tags_create_tags = True
tags_create_badges = True
tags_index_head = "Themed content tags:"  # tags landing page intro text
tags_intro_text = "Tags:"  # prefix text for a tags list
tags_overview_title = ":fa:`tags` Tags"  # title for the tags landing page
tags_output_dir = "tags"
tags_page_header = "Tagged content:"  # tag sub-page, header text
tags_page_title = ":fa:`tags` Tag"  # tag sub-page, title appended with the tag name


# sphinx-togglebutton options ------------------------------------------------
# See https://github.com/executablebooks/sphinx-togglebutton

togglebutton_hint = "Click to show"
togglebutton_hint_hide = "Click to hide"


# myst-nb options ------------------------------------------------------------
# See https://myst-nb.readthedocs.io/en/latest/configuration.html

nb_execution_mode = "cache"
nb_execution_raise_on_error = True
nb_execution_timeout = -1
nb_number_source_lines = True
nb_render_text_lexer = "python"


# nitpicky options -----------------------------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-nitpicky

nitpicky = True
nitpick_ignore_regex = [
    (r"py:.*", r"Corners"),  # TBD: geovista.geodesic.PANEL_BBOX_BY_IDX
    (r"py:.*", r"h3.get_res0_cells"),  # no uber/h3 sphinx docs available
    (r"py:.*", r"scooby.Report"),  # no scooby sphinx docs available
    (r"py:.*", r"pv"),  # TBD: geovista.geoplotter, geovista.gridlines (lazy import)
    (r"py:class", r"numpy.typing.ArrayLike"),  # TBD: geovista.pantry.data (lazy import)
    (r"py:mod", r"pyvista"),  # see https://github.com/pyvista/pyvista/issues/5663
    (r"py:mod", r"pyvistaqt"),  # no :mod:`pyvistaqt` inventory entry available
    (r"py:mod", r"vtk"),  # no :mod:`vtk` inventory entry available
]


# sphinx.ext.todo options ----------------------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/extensions/todo.html
todo_include_todos = False
todo_emit_warnings = False  # set to True, to discover todos in the code


# -- numpydoc options --------------------------------------------------------
# See https://numpydoc.readthedocs.io/en/latest/index.html

numpydoc_attributes_as_param_list = True
numpydoc_class_members_toctree = False
numpydoc_show_class_members = False
numpydoc_use_plots = True
numpydoc_xref_aliases = {
    "Actor": "pyvista.Actor",
    "ArrayLike": "numpy.typing.ArrayLike",
    "bool": ":class:`python:bool`",
    "CRSLike": "geovista.crs.CRSLike",
    "CloudPreference": "geovista.pantry.data.CloudPreference",
    "Corners": "geovista.geodesic.Corners",
    "Geod": "pyproj.geod.Geod",
    "Path": "pathlib.Path",
    "Preference": "geovista.common.Preference",
    "PolyData": "pyvista.PolyData",
    "Shape": "geovista.bridge.Shape",
    "Texture": "pyvista.Texture",
}
numpydoc_xref_ignore = {"optional", "default", "of"}
numpydoc_xref_param_type = True


# -- autodoc options ---------------------------------------------------------
# See https://sphinx-autoapi.readthedocs.io/en/latest/how_to.html#how-to-include-type-annotations-as-types-in-rendered-docstrings
#     https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"


# -- autoapi options ---------------------------------------------------------
# See https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html
#     https://github.com/readthedocs/sphinx-autoapi
#

autoapi_dirs = [
    package_src_dir,
]
autoapi_root = "reference/generated/api"
autoapi_template_dir = "_autoapi_templates"
autoapi_ignore = [
    str(package_dir / "_version.py"),
    str(package_dir / "__main__.py"),
    str(package_dir / "cli.py"),
    str(package_dir / "examples/*"),
]
autoapi_member_order = "groupwise"
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

autolog(f"{autoapi_dirs=}", section="AutoAPI")
autolog(f"{autoapi_ignore=}", section="AutoAPI")
autolog(f"{autoapi_root=}", section="AutoAPI")


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
    # sidebar-version
    "on_rtd": on_rtd,
    "rtd_version": rtd_version,
    "rtd_version_type": rtd_version_type,
    "commit_sha": commit_sha,
}

html_sidebars = {
    "**": [
        "navbar-logo.html",
        "sidebar-version.html",
        "icon-links.html",
        "search-button-field.html",
        "sbt-sidebar-nav.html",
    ]
}

html_theme_options = {
    "extra_footer": f"Made with ❤️ and ☕ on {now.strftime('%b %d %Y')}.",
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
            "name": "Bluesky",
            "url": "https://bsky.app/profile/geovista.bsky.social",
            "icon": "fa-brands fa-bluesky",
        },
        {
            "name": "YouTube",
            "url": "https://www.youtube.com/@geovista_devs/videos",
            "icon": "fa-brands fa-youtube",
        },
    ],
    "max_navbar_depth": 3,
    "navigation_with_keys": False,
    "path_to_docs": "docs/src",
    "repository_branch": "main",
    "repository_url": "https://github.com/bjlittle/geovista",
    "show_navbar_depth": 1,
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

if on_rtd and rtd_version == "latest":
    html_theme_options["announcement"] = """
        ⚠️ Viewing <b>latest</b> development version. Released
        <a href="https://geovista.readthedocs.io/en/stable/">stable</a>
        version also available."""

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

linkcheck_ignore = [
    "https://doi.org/10.5281/zenodo.7608302",
    "https://www.mtu.edu/geo/community/seismology/learn/earthquake-measure/magnitude/",
    "https://www.usgs.gov/programs/earthquake-hazards",
    "https://www.ncei.noaa.gov/products/optimum-interpolation-sst",
    "https://earthexplorer.usgs.gov",
    "https://www.fvcom.org",
]
linkcheck_retries = 3


# -- intersphinx options -----------------------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html

intersphinx_mapping = {
    "cartopy": ("https://scitools.org.uk/cartopy/docs/latest/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "platformdirs": ("https://platformdirs.readthedocs.io/en/stable/", None),
    "pooch": ("https://www.fatiando.org/pooch/latest/", None),
    "pyproj": ("https://pyproj4.github.io/pyproj/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "pyvista": ("https://docs.pyvista.org/version/stable/", None),
    "pyvistaqt": ("https://qtdocs.pyvista.org/", None),
    "rasterio": ("https://rasterio.readthedocs.io/en/stable/", None),
    "requests": ("https://requests.readthedocs.io/en/stable/", None),
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
    "issue": ("https://github.com/bjlittle/geovista/issues/%s", "#%s"),
    "pull": ("https://github.com/bjlittle/geovista/pull/%s", "#%s"),
    "user": ("https://github.com/%s", "@%s"),
}


# -- numfig options ----------------------------------------------------------
# See https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-numfig

numfig = True

numfig_format = {
    "code-block": "Listing %s:",
    "figure": "Fig. %s:",
    "section": "Section %s:",
    "table": "Table %s:",
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
pyvista_images_dir = docs_src_dir / "generated" / "images"
pyvista.FIGURE_PATH = str(pyvista_images_dir)
if not pyvista_images_dir.exists():
    pyvista_images_dir.mkdir(parents=True, exist_ok=True)

# We also need to start this on CI services and GitHub Actions has a CI env var
if on_rtd or os.environ.get("CI"):
    pyvista.start_xvfb()

scraper = DynamicScraper()


# -- sphinx-gallery options --------------------------------------------------
# See https://sphinx-gallery.github.io/stable/configuration.html

sphinx_gallery_conf = {
    "default_thumb_file": str(docs_images_dir / "gallery-thumb.png"),
    "filename_pattern": "/.*",
    "ignore_pattern": "(__init__)|(clouds)|(fesom)|(synthetic)",
    "examples_dirs": str(package_dir / "examples"),
    "gallery_dirs": GALLERY_DIRS,
    "min_reported_time": 90,
    "matplotlib_animations": True,
    # see https://github.com/sphinx-gallery/sphinx-gallery/pull/195
    "plot_gallery": "'True'",
    "doc_module": "geovista",
    "image_scrapers": (scraper, "matplotlib"),
    "download_all_examples": False,
    "remove_config_comments": True,
    "within_subsection_order": "ExampleTitleSortKey",
    "reference_url": {
        "geovista": None,
    },
}


# -- pyvista-plot directive options ------------------------------------------

DIRECTIVE_NAME = "pyvista-plot"
DIRECTIVE = f".. {DIRECTIVE_NAME}::\n\n"
PATTERN = r"""(?P<prefix>.*)
              (?P<rubric>\.\.\ rubric::\ Examples?\n\n)
              (?P<examples>.*)
              (?P<postfix>(\.\.\ rubric::)?.*)"""
REGEX = re.compile(PATTERN, flags=re.DOTALL | re.MULTILINE | re.VERBOSE)

plot_setup = """
from pyvista import set_plot_theme as __s_p_t
__s_p_t('document')
del __s_p_t
"""
plot_cleanup = plot_setup


def indent(block: str, amount: int = 3) -> str:
    """Indent the document text `block` by the specified amount.

    Honours indenting multi-lines within the `block`.

    """
    return "\n".join(
        " " * amount + line if line else line for line in block.split("\n")
    )


def geovista_skip_member(
    app: Sphinx,
    what: str,
    name: str,  # noqa: ARG001
    obj: Mapper,
    skip: bool,  # noqa: FBT001
    options: Iterable[str],  # noqa: ARG001
) -> bool:
    """Inject the ``pyvista-plot`` directive into the docstring.

    The directive will be injected between an ``Example`` or ``Examples`` rubric,
    and the associated text block of the rubric, which itself will be indented
    appropriately to belong to the scope of the injected directive.

    Note that, the directive will be at the same level as the rubric.

    """
    plot_docstring = app.builder.config.plot_docstring
    targets = ["class", "function", "method", "property", "module"]

    if not skip and plot_docstring and what in targets:
        match = REGEX.fullmatch(obj.docstring)
        if match is not None:
            examples = match.group("examples")
            if DIRECTIVE_NAME not in examples:
                prefix = match.group("prefix")
                rubric = match.group("rubric")
                postfix = match.group("postfix")
                new = f"{prefix}{rubric}{DIRECTIVE}{indent(examples)}{postfix}"
                obj.docstring = new

    return skip


def _bool_eval(arg: str | bool) -> bool:
    """Sanitise to a boolean only configuration."""
    if isinstance(arg, str):
        with contextlib.suppress(TypeError):
            arg = ast.literal_eval(arg.capitalize())

    return bool(arg)


def generate_carousel(
    app: Sphinx,
    fname: Path,
    ncards: int | None = None,
    margin: int | None = None,
    width: int | None = None,
) -> None:
    """Generate and write the gallery carousel RST file."""
    if ncards is None:
        ncards = 3

    if margin is None:
        margin = 4

    if width is None:
        width = "25%"

    base = Path(app.srcdir, *GALLERY_DIRS.split("/"))
    cards_by_link = {}

    card = r""".. card::
    :img-background: {image}
    :link: {link}
    :link-type: ref
    :width: {width}
    :margin: {margin}
"""

    # TODO @bjlittle: use Path.walk when python >=3.12
    for root, _, files in os.walk(str(base)):
        root = Path(root)  # noqa: PLW2901
        if root.name == "images":
            root_relative = root.relative_to(app.srcdir)
            link_relative = root.parent.relative_to(app.srcdir)

            for file in files:
                path = Path(file)
                if path.suffix == ".png":
                    # generate the card "img-background" filename
                    image = root_relative / path

                    # generate the card "link" reference
                    # remove numeric gallery image index e.g., "001"
                    parts = path.stem.split("_")[:-1]
                    link = parts[:2] + list(link_relative.parts) + parts[2:]
                    link = f"{'_'.join(link)}.py"

                    kwargs = {
                        "image": image,
                        "link": link,
                        "width": width,
                        "margin": margin,
                    }

                    cards_by_link[link] = card.format(**kwargs)

    # sort the cards by their link
    cards = [cards_by_link[link] for link in sorted(cards_by_link.keys())]
    cards = textwrap.indent("\n".join(cards), prefix=" " * 4)

    # now, create the card carousel
    carousel = f""".. card-carousel:: {ncards}

{cards}

.. rst-class:: center

    :fa:`images` Gallery Carousel

"""

    # finally, write the rst for the gallery carousel
    Path(app.srcdir, fname).write_text(carousel)


def geovista_builder_inited(app: Sphinx) -> None:
    """Configure geovista sphinx options."""
    plot_docstring = _bool_eval(app.builder.config.plot_docstring)
    plot_gallery = _bool_eval(app.builder.config.plot_gallery)
    plot_tutorial = _bool_eval(app.builder.config.plot_tutorial)

    # overwrite the myst-nb sphinx configuration option that controls the
    # notebook execution mode. this option has been pre-parsed by the sphinx
    # state machine from this file (conf.py) or set by the default myst-nb app
    # configuration. for further details see
    # https://www.sphinx-doc.org/en/master/extdev/event_callbacks.html
    if not plot_tutorial:
        # https://myst-nb.readthedocs.io/en/latest/configuration.html#execution
        app.config["nb_execution_mode"] = "off"

    # sanitise the config option from str to bool
    app.builder.config.plot_docstring = plot_docstring

    # report diagnostics
    autolog(f"{plot_docstring=}", section="GeoVista")
    autolog(f"{plot_gallery=}", section="GeoVista")
    autolog(f"{plot_tutorial=}", section="GeoVista")


def geovista_carousel(
    app: Sphinx,
    env: BuildEnvironment,  # noqa: ARG001
    docnames: list[str],  # noqa: ARG001
) -> None:
    """Create the gallery carousel."""
    # create empty or truncate existing file
    fname = Path(app.srcdir, "gallery_carousel.txt")

    with fname.open("w"):
        pass

    if _bool_eval(app.builder.config.plot_gallery):
        # only generate the carousel if we have a gallery
        generate_carousel(app, fname)


def setup(app: Sphinx) -> None:
    """Configure sphinx application."""
    # we require the output of this extension
    app.setup_extension("sphinx_gallery.gen_gallery")
    # register geovista options
    app.add_config_value(name="plot_docstring", default="True", rebuild="html")
    app.add_config_value(name="plot_tutorial", default="True", rebuild="html")
    # early configuration of geovista options, see
    # https://www.sphinx-doc.org/en/master/extdev/event_callbacks.html
    app.connect("builder-inited", geovista_builder_inited, priority=10)
    # register callback for the autoapi event
    app.connect("autoapi-skip-member", geovista_skip_member)
    # register callback to generate gallery carousel
    app.connect("env-before-read-docs", geovista_carousel)
