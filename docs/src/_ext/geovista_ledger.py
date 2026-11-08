# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Write the summary line under each Verification table, and link its evidence.

The table carries one row per decision (ledger spec §3.4), and the line under it
counts each state, so a reader sees how much of a specification is verified
without counting. The build writes the line from the table, so nobody keeps it
up to date by hand.

Each test file a row names as evidence links to the first line in it that cites
the row's decision, at the commit or tag the documentation was built from
(ledger spec §2 decision 18). ``conf.py`` names where the links point with
:func:`source`, and a build that names nothing links nothing.

What the states are, and how one is read, is the grammar of
``geovista_citations``. The transform reads the doctree, not the source, so it
sees the table as MyST rendered it.

"""

from __future__ import annotations

from pathlib import Path
import re
from typing import TYPE_CHECKING

from docutils import nodes
import geovista_citations
from sphinx.transforms import SphinxTransform

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sphinx.application import Sphinx

#: Where the repository's files are browsed on GitHub, by commit or tag.
BLOB = "https://github.com/bjlittle/geovista/blob"

#: The directory of the specifications, relative to the documentation's source.
SPECS = Path("developer") / "specs"

#: The grammar of the specifications, read once a build starts.
NAMES: geovista_citations.Namespace | None = None
#: The prefix of each specification, keyed by its docname.
OWNERS: dict[str, str] = {}

#: The title of the section holding the ledger, as MyST renders it, numbered.
TITLE = re.compile(rf"^(?:\d+(?:\.\d+)*\.?\s+)?{geovista_citations.VERIFICATION}$")

#: The summary line, which the citation grammar writes for every reader of a ledger.
summary = geovista_citations.summary


def _cells(row: nodes.row) -> list[str]:
    """Read the text of each entry of a table row."""
    return [entry.astext().strip() for entry in row.findall(nodes.entry)]


def source(environ: Mapping[str, str], commit: str) -> str:
    """Return where evidence links point: the tag of a release, or else its commit.

    A release is browsed by its tag, which a reader recognises, and every other
    build by its commit, which keeps pointing at the test as it stood when the
    documentation was built (ledger spec §2 decision 18).

    Parameters
    ----------
    environ : mapping
        The environment, read for Read the Docs's version type and identifier.
    commit : str
        The full hash of the commit the documentation is built from.

    Returns
    -------
    str
        The base of each link, ending in a slash.

    """
    tag = environ.get("READTHEDOCS_GIT_IDENTIFIER")
    if environ.get("READTHEDOCS_VERSION_TYPE") == "tag" and tag:
        return f"{BLOB}/{tag}/"
    return f"{BLOB}/{commit}/"


def citing_line(path: Path, anchor: str) -> int | None:
    """Return the first line of a file that cites an anchor, or ``None``.

    The file is read as the conventions test reads it, in its prose and its
    comments, so the line is the one that makes the file evidence.

    Parameters
    ----------
    path : Path
        The file.
    anchor : str
        The anchor of the decision, e.g. ``ledger-spec-2-decision-18``.

    Returns
    -------
    int or None
        The line, counted from 1.

    """
    if NAMES is None:
        return None
    text = path.read_text(encoding="utf-8")
    for number, line in geovista_citations.source_lines(path, text):
        prose = geovista_citations.prose(line)[0]
        if any(
            c.slug == anchor for c in geovista_citations.scan(prose, NAMES.signed, None)
        ):
            return number
    return None


def _link_evidence(row: nodes.row, owner: str, root: Path, base: str) -> list[Path]:
    """Link each file the row's Evidence names, returning the files read."""
    entries = list(row.findall(nodes.entry))
    if len(entries) < len(geovista_citations.LEDGER_HEADER):
        return []
    cell = geovista_citations.LEDGER_CELL.fullmatch(entries[0].astext().strip())
    anchor = (
        None
        if cell is None
        else geovista_citations.decision_anchor(owner, int(cell["decision"]))
    )
    read = []
    for literal in list(entries[2].findall(nodes.literal)):
        name = literal.astext()
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            continue
        read.append(path)
        line = None if anchor is None else citing_line(path, anchor)
        url = f"{base}{Path(name).as_posix()}" + ("" if line is None else f"#L{line}")
        reference = nodes.reference("", "", internal=False, refuri=url)
        literal.parent.replace(literal, reference)
        reference += literal
    return read


class LedgerSummary(SphinxTransform):
    """Append the summary line after each Verification table (ledger spec §3.4)."""

    default_priority = 410

    def apply(self, **kwargs: object) -> None:  # noqa: ARG002
        """Write the line under the first ledger table of each Verification."""
        self.env.note_dependency(__file__)
        self.env.note_dependency(geovista_citations.__file__)
        for section in list(self.document.findall(nodes.section)):
            title = next(iter(section.findall(nodes.title)), None)
            if title is None or not TITLE.match(title.astext().strip()):
                continue
            for table in section.findall(nodes.table):
                head = next(iter(table.findall(nodes.thead)), None)
                rows = list(head.findall(nodes.row)) if head is not None else []
                if (
                    not rows
                    or tuple(_cells(rows[0])) != geovista_citations.LEDGER_HEADER
                ):
                    continue
                body = next(iter(table.findall(nodes.tbody)), None)
                self._link(body)
                statuses = [
                    cells[1]
                    for row in (body.findall(nodes.row) if body is not None else [])
                    if len(cells := _cells(row)) > 1
                ]
                line = summary(statuses)
                paragraph = nodes.paragraph(line, line, classes=["ledger-summary"])
                table.parent.insert(table.parent.index(table) + 1, paragraph)
                break

    def _link(self, body: nodes.tbody | None) -> None:
        """Link the evidence of each row, if the build names where links point."""
        base = self.config.geovista_ledger_source
        owner = OWNERS.get(self.env.docname)
        if body is None or not base or owner is None:
            return
        root = Path(
            self.config.geovista_ledger_root or Path(self.env.srcdir).parents[1]
        )
        for row in body.findall(nodes.row):
            # a test edited moves the line its link names, so re-read the page then
            for path in _link_evidence(row, owner, root.resolve(), base):
                self.env.note_dependency(str(path))


def _build_registry(app: Sphinx) -> None:
    """Read the specifications' grammar and owners, once a build starts."""
    global NAMES  # noqa: PLW0603
    srcdir = Path(app.srcdir)
    NAMES = geovista_citations.namespace(
        geovista_citations.specifications(srcdir / SPECS)
    )
    OWNERS.clear()
    OWNERS.update(
        {
            path.relative_to(srcdir).with_suffix("").as_posix(): prefix
            for path, prefix in NAMES.owners.items()
        }
    )


def setup(app: Sphinx) -> dict[str, object]:
    """Register the transform.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The application.

    Returns
    -------
    dict
        The extension metadata.

    """
    # where evidence links point, and the root their paths are read from; a
    # change to either rewrites no page that was read before it
    app.add_config_value("geovista_ledger_source", None, "", types=frozenset({str}))
    app.add_config_value("geovista_ledger_root", None, "", types=frozenset({str}))
    app.connect("builder-inited", _build_registry)
    app.add_transform(LedgerSummary)
    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
