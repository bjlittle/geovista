# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the ``readingtime`` sphinx extension.

The reading-time model is covered directly, as it imports nothing beyond the
standard library. The directive around it is covered by building a throwaway
documentation set in-process, which needs ``sphinx`` and so skips without it.

"""

from __future__ import annotations

import importlib.util
import io
import itertools
import math
from pathlib import Path
import re
import sys
from typing import TYPE_CHECKING, NamedTuple

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType
    from typing import NoReturn

try:
    from sphinx.application import Sphinx
except ImportError:
    Sphinx = None

#: The documentation source, carrying the extension and stylesheet under test.
DOCS = Path(__file__).parents[2] / "docs" / "src"

#: A minimal sphinx configuration loading the extension.
#:
#: Every application after the first in a process re-registers the docutils
#: nodes, directives and roles of each extension, and sphinx warns once per
#: registration - which would fail these builds for reasons of the harness
#: alone. Those warnings are typed, and so can simply be named here.
CONF = """
import sys

sys.path.insert(0, {ext!r})

extensions = ["readingtime"]
exclude_patterns = ["_build"]
suppress_warnings = ["app"]
html_theme = "basic"
"""

#: The published banner, whatever the builder rendered it with.
ESTIMATE = re.compile(r"Estimated reading time: (\d+) minutes?")

#: The classes the banner carries in the built HTML, which the stylesheet
#: selects on.
CLASSES = re.compile(r'<div class="([^"]*\breading-time\b[^"]*)"')

#: A custom property the stylesheet asks the theme for.
USED = re.compile(r"var\((--[\w-]+)\)")

#: A custom property a stylesheet defines.
DEFINED = re.compile(r"(--[\w-]+)\s*:")

#: Three words of prose under a one word title, counted at one word per minute
#: so that the published estimate is the word count itself.
PROSE = """
Title
=====

.. readingtime:: 1wpm

alpha beta gamma
"""

#: The same four words, buried in markup that a reader never reads. The source
#: of this page runs to three times the words of the one above; the page does
#: not, and it is the page that is being estimated.
MARKUP = """
Title
=====

.. readingtime:: 1wpm

.. a comment carrying a great many words that are never rendered anywhere at
   all, and so must not lengthen anybody's estimate of how long this page
   takes to read

.. _a-hyperlink-target-nobody-reads:

alpha beta gamma

.. raw:: html

   <div class="not-prose" data-nor-is-this="attributes are not words"></div>
"""

#: A page whose only body is code, which *is* counted: the rate is pitched low
#: precisely because these pages alternate prose with code and output.
CODE = """
Title
=====

.. readingtime:: 1wpm

.. code:: python

   alpha = beta
"""

#: A page whose body arrives from another file, and so exists only once the
#: page has been parsed.
INCLUDE = """
Title
=====

.. readingtime:: 1wpm

.. include:: included.txt
"""


class Build(NamedTuple):
    """A completed documentation build.

    Attributes
    ----------
    app : Sphinx
        The application that performed the build.
    rendered : str
        The built page.
    warning : str
        Everything the build reported to its warning stream.

    """

    app: Sphinx
    rendered: str
    warning: str


@pytest.fixture(scope="session")
def reading() -> ModuleType:
    """Load the reading-time model.

    It is loaded from its path rather than imported, as ``docs/src/_ext`` is on
    the path of a documentation build and of nothing else.

    Returns
    -------
    ModuleType
        The loaded module.

    """
    path = DOCS / "_ext" / "reading.py"
    spec = importlib.util.spec_from_file_location("reading", path)
    module = importlib.util.module_from_spec(spec)
    # registered before it is executed, as "dataclass" resolves the annotations
    # of a module compiled with "from __future__ import annotations" by looking
    # the module up by name
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


@pytest.fixture(scope="session")
def readingtime(require: Callable[[str], NoReturn]) -> ModuleType:
    """Load the directive, under a name of its own.

    Loaded rather than imported for the same reason as :func:`reading`, and
    under a private name so that a documentation build running in this process
    still loads its own copy off the path its ``conf.py`` sets.

    Parameters
    ----------
    require : Callable
        The guard for an unavailable prerequisite.

    Returns
    -------
    ModuleType
        The loaded module.

    """
    if Sphinx is None:
        require("sphinx is not installed")

    path = DOCS / "_ext" / "readingtime.py"
    spec = importlib.util.spec_from_file_location("readingtime_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


@pytest.fixture
def registered(readingtime: ModuleType, mocker) -> tuple[object, dict[str, object]]:
    """Set the extension up against a recording application.

    Parameters
    ----------
    readingtime : ModuleType
        The loaded directive.
    mocker : pytest_mock.MockerFixture
        The mock factory.

    Returns
    -------
    tuple
        The application the extension registered itself with, and the metadata
        it declared.

    """
    app = mocker.Mock()

    return app, readingtime.setup(app)


@pytest.fixture
def build(require: Callable[[str], NoReturn], tmp_path: Path) -> Callable[..., Build]:
    """Provide a factory building a single-page documentation set.

    Parameters
    ----------
    require : Callable
        The guard for an unavailable prerequisite.
    tmp_path : Path
        The temporary directory of the build.

    Returns
    -------
    Callable
        A factory taking the page source, any further files to write beside it,
        the builder to run, and whether a warning should fail the build.

    """
    if Sphinx is None:
        require("sphinx is not installed")

    serial = itertools.count()

    def factory(
        source: str,
        *,
        extra: dict[str, str] | None = None,
        builder: str = "html",
        strict: bool = True,
    ) -> Build:
        root = tmp_path / f"build{next(serial)}"
        src = root / "src"
        src.mkdir(parents=True)

        conf = CONF.format(ext=str(DOCS / "_ext"))
        (src / "conf.py").write_text(conf, encoding="utf-8")
        (src / "index.rst").write_text(source, encoding="utf-8")

        for name, text in (extra or {}).items():
            (src / name).write_text(text, encoding="utf-8")

        warning = io.StringIO()
        app = Sphinx(
            srcdir=str(src),
            confdir=str(src),
            outdir=str(root / "out"),
            doctreedir=str(root / "doctrees"),
            buildername=builder,
            status=io.StringIO(),
            warning=warning,
            warningiserror=strict,
            freshenv=True,
        )
        app.build()

        suffix = {"html": ".html", "text": ".txt"}[builder]
        rendered = (Path(app.outdir) / f"index{suffix}").read_text(encoding="utf-8")

        return Build(app, rendered, warning.getvalue())

    return factory


def published(rendered: str) -> int:
    """Read the estimate off a built page.

    Parameters
    ----------
    rendered : str
        The built page.

    Returns
    -------
    int
        The published estimate, in minutes.

    """
    match = ESTIMATE.search(rendered)

    assert match is not None, "no reading-time banner in the built page"

    return int(match.group(1))


def test_count_words__empty(reading):
    """Nothing to read is no words."""
    assert reading.count_words("") == 0


def test_count_words__prose(reading):
    """Words are runs of word characters, punctuation and all."""
    assert reading.count_words("alpha, beta; gamma!") == 3


def test_count_words__dotted(reading):
    """A dotted name counts as its parts.

    Inherited from the original directive and kept deliberately, so that no
    published estimate moves for two reasons at once. Pinned here so that
    changing it is a decision rather than an accident.

    """
    assert reading.count_words("geovista.bridge.Transform") == 3


@pytest.mark.parametrize(
    ("words", "wpm", "expected"),
    [
        (0, 150, 1),
        (1, 150, 1),
        (150, 150, 1),
        (151, 150, 2),
        (300, 150, 2),
        (301, 150, 3),
        (1000, 1000, 1),
    ],
)
def test_estimate_minutes(reading, words, wpm, expected):
    """The estimate rounds up, and a page that was opened costs a minute."""
    assert reading.estimate_minutes(words, wpm) == expected


def test_estimate_minutes__default(reading):
    """The default rate is the one the documentation quotes."""
    assert reading.WPM == 150
    assert reading.estimate_minutes(reading.WPM) == 1


@pytest.mark.parametrize(
    ("argument", "minutes", "wpm"),
    [
        (None, None, 150),
        ("30", 30, 150),
        ("1", 1, 150),
        ("200wpm", None, 200),
        ("200WPM", None, 200),
        ("  200wpm  ", None, 200),
        ("1wpm", None, 1),
    ],
)
def test_parse_argument__accepted(reading, argument, minutes, wpm):
    """Every documented spelling of the argument is read."""
    parsed = reading.parse_argument(argument)

    assert parsed.minutes == minutes
    assert parsed.wpm == wpm


@pytest.mark.parametrize(
    "argument",
    ["", "thirty", "0", "0wpm", "-5", "-5wpm", "1.5", "5min", "wpm", "30 wpm", "wpm30"],
)
def test_parse_argument__refused(reading, argument):
    """Anything else is refused rather than quietly estimated."""
    with pytest.raises(ValueError, match="expected no argument"):
        reading.parse_argument(argument)


def test_doctree__counted_not_source(build):
    """The estimate must come from the page, not from the markup behind it.

    Counting the source inflates every estimate by whatever the author spent on
    directives, options, link targets and comments - which on these pages is
    between a third and half of the file.

    """
    plain = published(build(PROSE).rendered)
    marked = published(build(MARKUP).rendered)

    # "Title" plus "alpha beta gamma", at one word per minute
    assert plain == 4
    assert marked == plain


def test_doctree__counts_code(build):
    """Code is read, so code is counted."""
    assert published(build(CODE).rendered) == 3


def test_doctree__counts_generated_bodies(build):
    """A body another directive produced is part of the page."""
    rendered = build(
        INCLUDE, extra={"included.txt": "delta epsilon zeta eta theta\n"}
    ).rendered

    assert published(rendered) == 6


def test_argument__duration_quoted(build):
    """A literal duration is published as given, however long the page is."""
    source = PROSE.replace(".. readingtime:: 1wpm", ".. readingtime:: 7")

    assert published(build(source).rendered) == 7


def test_argument__rate_overrides(build):
    """A rate override changes the estimate and nothing else."""
    source = PROSE.replace(".. readingtime:: 1wpm", ".. readingtime:: 2wpm")

    assert published(build(source).rendered) == math.ceil(4 / 2)


def test_argument__absent_uses_default(build, reading):
    """With no argument, a short page still costs the reader a minute."""
    source = PROSE.replace(".. readingtime:: 1wpm", ".. readingtime::")
    rendered = build(source).rendered

    assert published(rendered) == reading.estimate_minutes(4)
    # and reads as English while it is at it
    assert "1 minute" in rendered
    assert "1 minutes" not in rendered


def test_argument__invalid_fails(build):
    """A misspelled argument must fail the build, not fall back on a default.

    Estimating the page anyway would publish a number the author never asked
    for, and the only notice of it would be the number itself.

    """
    source = PROSE.replace(".. readingtime:: 1wpm", ".. readingtime:: thirty")
    app, rendered, warning = build(source, strict=False)

    assert app._warncount > 0
    assert "expected no argument" in warning
    assert ESTIMATE.search(rendered) is None


def test_banner__survives_a_non_html_builder(build):
    """The banner must be real nodes, which every builder can render.

    A raw HTML block is dropped by everything but the HTML builder, so the
    estimate would silently vanish from a ``text``, ``man`` or ``latex`` build.

    """
    assert published(build(PROSE, builder="text").rendered) == 4


def test_banner__classes(build):
    """The banner must carry the classes the stylesheet selects on.

    ``.reading-time`` alone is outranked by pydata-sphinx-theme's own
    ``.docutils.container`` rule, so the stylesheet repeats the horizontal
    padding on ``.reading-time.container``. That is only warranted while the
    banner really is a container.

    """
    classes = CLASSES.search(build(PROSE).rendered)

    assert classes is not None

    assert {"reading-time", "container"} <= set(classes.group(1).split())


def test_dependencies__noted(build):
    """The extension must rebuild the pages it estimates when it changes.

    Neither module is a document source that sphinx watches, so without this an
    incremental build serves a pickled doctree carrying the previous estimate.

    """
    app, _, _ = build(PROSE)
    noted = {
        Path(dependency).name
        for dependencies in app.env.dependencies.values()
        for dependency in dependencies
    }

    assert {"reading.py", "readingtime.py"} <= noted


def test_setup__declares_parallel_safety(registered):
    """The extension must declare itself safe for a parallel build.

    An extension that does not say warns twice and drops the build back to a
    serial read, which ``--fail-on-warning`` turns into a failure the moment
    the docs ``Makefile`` passes ``--jobs``.

    """
    _, metadata = registered

    assert metadata["parallel_read_safe"] is True
    assert metadata["parallel_write_safe"] is True


def test_setup__leaves_the_placeholder_unregistered(registered, readingtime):
    """The placeholder must fail the build rather than publish a blank.

    With no visitor registered for it, a page that reaches the writer with one
    still in it raises "unknown node type", which ``--fail-on-warning`` turns
    into a failure. Register the node and the same page publishes a blank space
    instead, saying nothing about the handler having stopped firing.

    """
    app, _ = registered

    app.add_directive.assert_called_once_with(
        "readingtime", readingtime.ReadingTimeDirective
    )
    app.connect.assert_called_once_with("doctree-read", readingtime.resolve)
    app.add_node.assert_not_called()


def test_stylesheet__properties_are_defined(html_root):
    """Every custom property the banner asks for must exist.

    A property that resolves to nothing is invalid at computed-value time, so
    the declaration falls back on the initial value of the property and nothing
    warns. The banner asked for ``--article-info-bg`` and ``--article-info-fg``,
    which no theme defines, and published a transparent box for it.

    """
    stylesheet = DOCS / "_static" / "readingtime.css"
    wanted = set(USED.findall(stylesheet.read_text(encoding="utf-8")))

    assert wanted, f"no custom properties found in {stylesheet.name}"

    defined: set[str] = set()

    for css in (html_root / "_static").rglob("*.css"):
        if css.name == stylesheet.name:
            continue

        defined |= set(
            DEFINED.findall(css.read_text(encoding="utf-8", errors="ignore"))
        )

    assert wanted <= defined, f"undefined custom properties: {sorted(wanted - defined)}"
