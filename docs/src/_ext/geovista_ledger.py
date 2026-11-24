# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Write the lines a specification's ledger shows: its summary, owners and links.

The table carries one row per decision (ledger spec §3.4), and the line under it
counts each state, so a reader sees how much of a specification is verified
without counting. The build writes the line from the table, so nobody keeps it
up to date by hand.

Each test file a row names as evidence links to the first line in it that cites
the row's decision, at the commit or tag the documentation was built from
(ledger spec §2 decision 18). ``conf.py`` names where the links point with
:func:`source`, and a build that names nothing links nothing.

Under each decision's entry, a line names the roadmap row that owns it, read
from the table's Row column: Delivered by, once the decision is verified, signed
off or retired, and Owned by while it is pending (owner spec §4.5). The line's
citation is plain text, which the citation extension links.

What the states are, and how one is read, is the grammar of
``geovista_citations``. The summary and the evidence links read the doctree, so
they see the table as MyST rendered it; the line under each decision reads the
page's source, through the grammar, as the conventions test reads its ledger.

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
    from sphinx.environment import BuildEnvironment

#: Where the repository's files are browsed on GitHub, by commit or tag.
BLOB = "https://github.com/bjlittle/geovista/blob"

#: The directory of the specifications, relative to the documentation's source.
SPECS = Path("developer") / "specs"

#: The grammar of the specifications, read once a build starts.
NAMES: geovista_citations.Namespace | None = None
#: The prefix of each specification, keyed by its docname.
OWNERS: dict[str, str] = {}

#: The attribute of the environment recording where the last build's evidence
#: links pointed, and the root their paths were read from.
ENV_SOURCE = "geovista_ledger_source"

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


def _link_evidence(
    row: nodes.row, owner: str, root: Path, base: str, column: int
) -> list[Path]:
    """Link each file the row's Evidence, its cell at ``column``, names.

    Returns the files read.
    """
    entries = list(row.findall(nodes.entry))
    if len(entries) <= column:
        return []
    cell = geovista_citations.LEDGER_CELL.fullmatch(entries[0].astext().strip())
    anchor = (
        None
        if cell is None
        else geovista_citations.decision_anchor(owner, int(cell["decision"]))
    )
    read = []
    for literal in list(entries[column].findall(nodes.literal)):
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


#: The words the line under a decision opens with, by the state of its row
#: (owner spec §4.5): delivered once verified, signed off or retired, owned while
#: pending.
OWNER_WORDS = {
    geovista_citations.VERIFIED: "Delivered by",
    geovista_citations.SIGNED_OFF: "Delivered by",
    geovista_citations.LEDGER_RETIRED: "Delivered by",
    geovista_citations.PENDING: "Owned by",
}


class DecisionOwners(SphinxTransform):
    """Name each decision's owner in a line under its entry (owner spec §4.5).

    The line is read from the Row column of the page's Verification table, so
    nothing is written in the specification for it. Its citation is plain text,
    which :class:`geovista_citation_xrefs.CitationTransform`, at priority 400,
    links as it links any citation; this runs before it, and after docutils moves
    the ``(...-2)=`` target onto the Decisions section, at priority 260.
    """

    default_priority = 350

    def apply(self, **kwargs: object) -> None:  # noqa: ARG002
        """Append the line to each decision of a specification that names an owner."""
        self.env.note_dependency(__file__)
        self.env.note_dependency(geovista_citations.__file__)
        owner = OWNERS.get(self.env.docname)
        if owner is None:
            return
        text = Path(self.env.doc2path(self.env.docname)).read_text(encoding="utf-8")
        owners = {
            row.decision: (row.owned, words)
            for row in geovista_citations.ledger(text) or []
            if row.decision is not None
            and row.owned
            and (state := geovista_citations.state_of(row.status, OWNER_WORDS))
            and (words := OWNER_WORDS.get(state))
        }
        if not owners:
            return
        for section in self.document.findall(nodes.section):
            if f"{owner}-2" not in section["ids"]:
                continue
            listing = next(
                (c for c in section.children if isinstance(c, nodes.enumerated_list)),
                None,
            )
            if listing is None:
                return
            start = listing.get("start", 1)
            for offset, item in enumerate(listing.children):
                if (found := owners.get(start + offset)) is None:
                    continue
                cited, words = found
                line = nodes.paragraph(classes=["decision-owner"])
                line += nodes.strong(words, words)
                line += nodes.Text(f" {cited}")
                item.append(line)
            return


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
                header = tuple(_cells(rows[0])) if rows else ()
                if header != geovista_citations.LEDGER_HEADER:
                    continue
                # each cell is read by its header, as the grammar reads the source
                status, evidence = header.index("Status"), header.index("Evidence")
                body = next(iter(table.findall(nodes.tbody)), None)
                self._link(body, evidence)
                statuses = [
                    cells[status]
                    for row in (body.findall(nodes.row) if body is not None else [])
                    if len(cells := _cells(row)) > status
                ]
                line = summary(statuses)
                paragraph = nodes.paragraph(line, line, classes=["ledger-summary"])
                table.parent.insert(table.parent.index(table) + 1, paragraph)
                break

    def _link(self, body: nodes.tbody | None, column: int) -> None:
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
            for path in _link_evidence(row, owner, root.resolve(), base, column):
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


def _outdated(
    app: Sphinx,
    env: BuildEnvironment,
    added: set[str],
    changed: set[str],
    _removed: set[str],
) -> set[str]:
    """Re-read every specification when its evidence links would point elsewhere.

    The links are baked into each pickled doctree, and the source changes with
    every commit, so a page an incremental build did not otherwise re-read would
    go on linking into an earlier commit (ledger spec §2 decision 18). Only the
    specifications carry a ledger, so only they are re-read, where an ``"env"``
    rebuild of the setting would re-read every page after every commit.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The application, read for where links point and the root of their paths.
    env : sphinx.environment.BuildEnvironment
        The environment, which records where the last build's links pointed.
    added : set of str
        Documents new since the last build.
    changed : set of str
        Documents Sphinx has already found out of date.
    _removed : set of str
        Documents gone since the last build. Unread.

    Returns
    -------
    set of str
        The specifications to re-read on top of those Sphinx found itself.

    """
    current = (app.config.geovista_ledger_source, app.config.geovista_ledger_root)
    if getattr(env, ENV_SOURCE, None) == current:
        return set()
    setattr(env, ENV_SOURCE, current)
    # on a first build every specification is already added, so this is empty
    return (set(OWNERS) & set(env.found_docs)) - added - changed


def setup(app: Sphinx) -> dict[str, object]:
    """Register the transforms, the line under each decision and the summary.

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
    # change to either re-reads the specifications alone, through _outdated
    app.add_config_value("geovista_ledger_source", None, "", types=frozenset({str}))
    app.add_config_value("geovista_ledger_root", None, "", types=frozenset({str}))
    app.connect("builder-inited", _build_registry)
    app.connect("env-get-outdated", _outdated)
    app.add_transform(DecisionOwners)
    app.add_transform(LedgerSummary)
    return {
        "version": "0.1.0",
        "env_version": 1,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
