# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Write each specification's status into the specifications index.

The namespace table of the index names each specification by its citation and
links its document. The build adds a third column, Status, which sums the roadmap
of the document each row links (docs spec §3.8), so nobody keeps it up to date by
hand and a new specification makes no edit for it.

The transform finds the table by its header, ``Citation`` and ``Document``, and
records each specification it reads as a dependency of the page, so that an
incremental build re-reads the index when a roadmap changes. What a status is, and
how a roadmap is read, is the grammar of ``geovista_citations``, which spells each
state's emoji by name, as this module does, since both sit in the corpus they
serve.

"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from docutils import nodes
import geovista_citations
from sphinx import addnodes
from sphinx.transforms import SphinxTransform
from sphinx.util import docname_join

if TYPE_CHECKING:
    from sphinx.application import Sphinx

#: The header of the index's table, which the transform adds the column to.
HEADER = ("Citation", "Document")

#: The header of the column it adds.
STATUS = "Status"

#: The relative width of the column, beside those the table gives its others.
WIDTH = 30

#: The cell of a row whose Document cell links no document.
NONE = "\N{EM DASH}"


def _cells(row: nodes.row) -> list[str]:
    """Read the text of each cell of a table row."""
    return [entry.astext().strip() for entry in row.findall(nodes.entry)]


def _entry(text: str) -> nodes.entry:
    """Build a table cell holding a paragraph of text."""
    entry = nodes.entry()
    entry += nodes.paragraph(text, text)
    return entry


class SpecStatus(SphinxTransform):
    """Add each specification's status to the index's table (docs spec §3.8)."""

    default_priority = 410

    def apply(self, **kwargs: object) -> None:  # noqa: ARG002
        """Append a Status column to each table headed ``Citation``, ``Document``."""
        for table in list(self.document.findall(nodes.table)):
            group = next(iter(table.findall(nodes.tgroup)), None)
            head = next(iter(table.findall(nodes.thead)), None)
            body = next(iter(table.findall(nodes.tbody)), None)
            if group is None or head is None or body is None:
                continue
            header = next(iter(head.findall(nodes.row)), None)
            if header is None or tuple(_cells(header)) != HEADER:
                continue
            self.env.note_dependency(__file__)
            self.env.note_dependency(geovista_citations.__file__)
            colspecs = [child for child in group if isinstance(child, nodes.colspec)]
            group.insert(group.index(colspecs[-1]) + 1, nodes.colspec(colwidth=WIDTH))
            group["cols"] = len(colspecs) + 1
            header += _entry(STATUS)
            for row in body.findall(nodes.row):
                row.append(_entry(self._status(row)))

    def _status(self, row: nodes.row) -> str:
        """Sum the roadmap of the document a row's Document cell links."""
        entries = [child for child in row if isinstance(child, nodes.entry)]
        link = None
        if len(entries) > 1:
            link = next(iter(entries[1].findall(addnodes.pending_xref)), None)
        if link is None or link.get("reftype") != "doc":
            return NONE
        docname = docname_join(link.get("refdoc", self.env.docname), link["reftarget"])
        path = Path(self.env.doc2path(docname))
        if not path.is_file():
            return NONE
        # a roadmap edited later re-reads the index, so its cell moves with it
        self.env.note_dependency(str(path))
        text = path.read_text(encoding="utf-8")
        return geovista_citations.roadmap_status(
            roadmap_row.status for roadmap_row in geovista_citations.rows(text)
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
    app.add_transform(SpecStatus)
    return {
        "version": "0.1.0",
        "env_version": 1,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
