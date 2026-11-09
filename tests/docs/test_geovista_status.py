# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the Status column of the specifications index (docs spec §3.8).

The extension is ``docs/src/_ext/geovista_status.py``. It sits in the corpus the
grammar governs, so these fixtures build each state's emoji by name, as the
extension does.

"""

from __future__ import annotations

from html.parser import HTMLParser
import importlib.util
import io
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType
    from typing import NoReturn

#: The extensions, which import one another by bare name, as a build does.
EXT = Path(__file__).parents[2] / "docs" / "src" / "_ext"

#: The states of a roadmap row (docs spec §3.6), built by name.
LANDED = "\N{WHITE HEAVY CHECK MARK} landed (2026-11-09, 1)"
NOT_STARTED = "\N{CLIPBOARD} not started"
CANDIDATE = "\N{ELECTRIC LIGHT BULB} candidate"

#: The cells the build writes for the specifications below.
ONE_CELL = (
    "\N{WHITE HEAVY CHECK MARK} complete \N{MIDDLE DOT} \N{ELECTRIC LIGHT BULB} 1"
)
TWO_CELL = "\N{CONSTRUCTION SIGN} 1 of 2 rows"
NO_CELL = "\N{EM DASH}"

#: The configuration of the end-to-end build.
CONF = """
extensions = ["geovista_status", "myst_parser"]
suppress_warnings = ["app"]
geovista_status_index = "index"
"""

#: The index, whose table links two specifications and one row of plain text.
INDEX = """Index
=====

.. toctree::

   one
   two

.. list-table::
    :header-rows: 1
    :widths: 35 65

    * - {first}
      - Document
    * - ``one spec``
      - :doc:`one`
    * - ``two spec``
      - :doc:`two`
    * - ``no spec``
      - plain text
"""


def spec(*statuses: str) -> str:
    """Return a specification whose roadmap has a row of each status."""
    rows = "\n".join(f"| {n} | Scope {n} | {s} |" for n, s in enumerate(statuses, 1))
    return f"# Demo\n\n## 1. Roadmap\n\n| # | Scope | Status |\n|---|---|---|\n{rows}\n"


@pytest.fixture(scope="module")
def status(require: Callable[[str], NoReturn]) -> ModuleType:
    """Load the extension by path, or skip without sphinx."""
    try:
        import sphinx  # noqa: F401, PLC0415
    except ImportError:
        require("sphinx is not installed")
    sys.path.insert(0, str(EXT))
    try:
        found = importlib.util.spec_from_file_location(
            "geovista_status", EXT / "geovista_status.py"
        )
        module = importlib.util.module_from_spec(found)
        sys.modules[found.name] = module
        found.loader.exec_module(module)
    finally:
        sys.path.remove(str(EXT))
    return module


def project(src: Path, first: str = "Citation") -> None:
    """Write the project: its configuration, its index and two specifications."""
    src.mkdir(exist_ok=True)
    (src / "conf.py").write_text(CONF, encoding="utf-8")
    (src / "index.rst").write_text(INDEX.format(first=first), encoding="utf-8")
    (src / "one.md").write_text(spec(LANDED, CANDIDATE), encoding="utf-8")
    (src / "two.md").write_text(spec(LANDED, NOT_STARTED), encoding="utf-8")


def build(src: Path, out: Path) -> tuple[Path, str]:
    """Build ``src``, returning its HTML and its warnings."""
    from sphinx.application import Sphinx  # noqa: PLC0415
    from sphinx.util.docutils import docutils_namespace  # noqa: PLC0415

    warning = io.StringIO()
    with pytest.MonkeyPatch.context() as patch, docutils_namespace():
        patch.syspath_prepend(str(EXT))
        app = Sphinx(
            str(src),
            str(src),
            str(out / "html"),
            str(out / "doctrees"),
            "html",
            status=None,
            warning=warning,
        )
        app.build()
    return out / "html", warning.getvalue()


class _Tables(HTMLParser):
    """Collect the text of every cell of every table, row by row."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: ARG002
        if tag == "table":
            self.tables.append([])
        elif tag == "tr" and self.tables:
            self.tables[-1].append([])
        elif tag in ("td", "th") and self.tables:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._cell is not None:
            self.tables[-1][-1].append(" ".join("".join(self._cell).split()))
            self._cell = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


def tables(page: Path) -> list[list[list[str]]]:
    """Read every table of a built page, as rows of cell texts."""
    parser = _Tables()
    parser.feed(page.read_text(encoding="utf-8"))
    return parser.tables


@pytest.mark.usefixtures("status")
def test_a_build_writes_each_status_into_the_index(tmp_path):
    """The build adds a Status column, summing the roadmap each row links.

    Holds docs spec §2 decision 8.
    """
    project(tmp_path / "src")

    html, warning = build(tmp_path / "src", tmp_path)
    (table,) = tables(html / "index.html")

    assert warning == ""
    assert table[0] == ["Citation", "Document", "Status"]
    assert [row[2] for row in table[1:]] == [ONE_CELL, TWO_CELL, NO_CELL]


@pytest.mark.usefixtures("status")
def test_a_row_linking_no_document_reads_a_dash(tmp_path):
    """A row whose Document cell links no document has no roadmap to sum."""
    project(tmp_path / "src")

    html, _ = build(tmp_path / "src", tmp_path)
    (table,) = tables(html / "index.html")

    assert table[3] == ["no spec", "plain text", NO_CELL]


@pytest.mark.usefixtures("status")
def test_an_incremental_build_reads_a_changed_roadmap(tmp_path):
    """A roadmap changed after a build moves the index on the next build."""
    src = tmp_path / "src"
    project(src)
    build(src, tmp_path)
    (src / "two.md").write_text(spec(LANDED, LANDED), encoding="utf-8")

    html, _ = build(src, tmp_path)
    (table,) = tables(html / "index.html")

    assert table[2][2] == "\N{WHITE HEAVY CHECK MARK} complete"


@pytest.mark.usefixtures("status")
def test_a_table_of_another_header_is_left_alone(tmp_path):
    """Only the index's table, headed Citation and Document, gains the column."""
    project(tmp_path / "src", first="Name")

    html, _ = build(tmp_path / "src", tmp_path)
    (table,) = tables(html / "index.html")

    assert table[0] == ["Name", "Document"]


@pytest.mark.usefixtures("status")
def test_a_table_on_another_page_is_left_alone(tmp_path):
    """Only the index's own table gains the column, not one of its header elsewhere."""
    src = tmp_path / "src"
    project(src)
    other = "Other\n=====\n\n.. list-table::\n    :header-rows: 1\n\n"
    other += "    * - Citation\n      - Document\n    * - a\n      - b\n"
    (src / "other.rst").write_text(other, encoding="utf-8")
    index = (src / "index.rst").read_text(encoding="utf-8")
    (src / "index.rst").write_text(index.replace("   two\n", "   two\n   other\n"))

    html, _ = build(src, tmp_path)
    (table,) = tables(html / "other.html")

    assert table[0] == ["Citation", "Document"]


def test_the_extension_builds_its_emoji_by_name():
    """The module sits in the corpus it serves, so writes no emoji literally (#2787)."""
    source = (EXT / "geovista_status.py").read_text(encoding="utf-8")

    assert not [char for char in source if ord(char) > 0x2000 and char != "·"]


#: The specifications, whose roadmaps the index's column sums.
SPECS = Path(__file__).parents[2] / "docs" / "src" / "developer" / "specs"


def test_the_index_shows_each_specification_status(html_root, status):
    """On the real build, the index shows every specification's status.

    Each row's cell is the sum of the roadmap its row links, in the order the
    index lists them. Holds docs spec §2 decision 8.
    """
    citations = status.geovista_citations
    index = (SPECS / "index.rst").read_text(encoding="utf-8")
    linked = [line.split("`")[1] for line in index.splitlines() if ":doc:`" in line]
    expected = [
        citations.roadmap_status(
            row.status
            for row in citations.rows(
                (SPECS / f"{name}.md").read_text(encoding="utf-8")
            )
        )
        for name in linked
    ]

    found = [
        table
        for table in tables(html_root / "developer" / "specs" / "index.html")
        if table and table[0][:2] == ["Citation", "Document"]
    ]

    assert len(found) == 1
    (table,) = found
    assert table[0] == ["Citation", "Document", "Status"]
    assert [row[2] for row in table[1:]] == expected
    assert NO_CELL not in expected
