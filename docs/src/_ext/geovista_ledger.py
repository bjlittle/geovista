# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Write the summary line under each specification's Verification table.

The table carries one row per decision (ledger spec §3.4), and the line under it
counts each state, so a reader sees how much of a specification is verified
without counting. The build writes the line from the table, so nobody keeps it
up to date by hand.

What the states are, and how one is read, is the grammar of
``geovista_citations``. The transform reads the doctree, not the source, so it
sees the table as MyST rendered it.

"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from docutils import nodes
import geovista_citations
from sphinx.transforms import SphinxTransform

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sphinx.application import Sphinx

#: The title of the section holding the ledger, as MyST renders it, numbered.
TITLE = re.compile(rf"^(?:\d+(?:\.\d+)*\.?\s+)?{geovista_citations.VERIFICATION}$")

#: The states in the order the summary counts them.
STATES = (
    geovista_citations.VERIFIED,
    geovista_citations.SIGNED_OFF,
    geovista_citations.PENDING,
    geovista_citations.LEDGER_RETIRED,
)


def summary(statuses: Iterable[str]) -> str:
    """Count each state of a ledger, as the line under its table reads.

    Parameters
    ----------
    statuses : iterable of str
        The Status cells, each opening with its state.

    Returns
    -------
    str
        Each state's emoji and count, then how many decisions in force are
        verified, as ledger spec §3.4 spells it.

    """
    counts = dict.fromkeys(STATES, 0)
    total = 0
    for status in statuses:
        total += 1
        state = geovista_citations.state_of(status.strip(), STATES)
        if state is not None:
            counts[state] += 1
    verified, signed, _, retired = counts.values()
    tally = " · ".join(f"{state.split()[0]} {count}" for state, count in counts.items())
    return (
        f"{tally}: {verified + signed} of {total - retired} decisions in force verified"
    )


def _cells(row: nodes.row) -> list[str]:
    """Read the text of each entry of a table row."""
    return [entry.astext().strip() for entry in row.findall(nodes.entry)]


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
                statuses = [
                    cells[1]
                    for row in (body.findall(nodes.row) if body is not None else [])
                    if len(cells := _cells(row)) > 1
                ]
                line = summary(statuses)
                paragraph = nodes.paragraph(line, line, classes=["ledger-summary"])
                table.parent.insert(table.parent.index(table) + 1, paragraph)
                break


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
    app.add_transform(LedgerSummary)
    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
