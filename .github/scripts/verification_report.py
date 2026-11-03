#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Report each specification's decisions, roadmap and open items.

For every specification, or the one a prefix names, the report shows its
roadmap, each row with its status, then each decision with its state and every
place in the repository that cites it, grouped as source, tests, documentation,
specifications and plans, and last its open items, each with its state, the row
that owes it and how often it has moved (items spec §3.9). It flags what does
not agree: a verified row whose test no longer cites its decision, and a
decision in force that nothing anywhere cites (ledger spec §3.8). It also flags
an item on its last move, which must settle or graduate when its row lands, and
an item owed by a row in progress, which that row's pull request must answer.

It is a view of the ledger on demand, never a gate: it exits 0 whatever it finds,
and 2 only when it cannot read a specification, or a prefix names none. The
ledger in each specification is the record, and the conventions test is what
holds it. The specifications are read with the parsers of
"tests/test_spec_conventions.py", and citations with the grammar of
"docs/src/_ext/geovista_citations.py", so the report reads the ledger as the
checks do. It writes Markdown, and appends it to the job summary in CI.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import re
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from types import ModuleType

#: The repository root.
REPO = Path(__file__).parents[2]

#: The specifications and the plans, relative to a repository root.
SPECS = Path("docs") / "src" / "developer" / "specs"
PLANS = Path("docs") / "src" / "developer" / "plans"

#: What a table cell holds when it has nothing to say.
EM_DASH = "\N{EM DASH}"

#: The title of an item in the grammar of docs spec \N{SECTION SIGN}3.6, after its
#: status, any parenthesis and a dash.
OLD_TITLE = re.compile(
    r"(?:\(.*?\)\s*)?[\N{EM DASH}\N{EN DASH}-]\s*\*\*(?P<title>.+?)\*\*"
)

#: The groups citations are listed under, in the order they are listed.
GROUPS = ("source", "tests", "documentation", "specifications", "plans")


def _load(path: Path, name: str) -> ModuleType:
    """Load the module at `path`, registered so its dataclasses resolve."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


#: The conventions test, whose parsers read the ledger, and its citation grammar.
conventions = _load(REPO / "tests" / "test_spec_conventions.py", "spec_conventions")
grammar = conventions.citations

#: The grammar's types, which the annotations below name.
Namespace = grammar.Namespace
LedgerRow = grammar.LedgerRow
Item = grammar.Item

#: The MyST roles a status carries, and the GitHub Markdown each reads as.
ROLES = (
    (re.compile(r"\{pull\}`(?P<number>\d+)`"), r"#\g<number>"),
    (re.compile(r"\{issue\}`(?P<number>\d+)`"), r"#\g<number>"),
    (re.compile(r"\{user\}`(?P<login>[^`]+)`"), r"@\g<login>"),
)


def markdown(status: str) -> str:
    """Spell a status's roles as GitHub Markdown, as a job summary renders no MyST."""
    for role, written in ROLES:
        status = role.sub(written, status)
    return status


def _cell(text: str) -> str:
    """Write a table cell as GitHub Markdown, escaping a pipe that would end it."""
    return markdown(grammar.PIPE.sub(r"\\|", text))


def _section(text: str, title: str) -> str | None:
    """Find the number of the section a specification titles so, whatever its case."""
    return next(
        (
            heading["num"]
            for heading, _ in grammar.headed(text)
            if heading["title"].casefold() == title.casefold()
        ),
        None,
    )


def _items_section(text: str) -> str | None:
    """Find the number of a specification's Open Items section, which names an item."""
    return _section(text, grammar.OPEN_ITEMS)


def _roadmap(text: str) -> list[str]:
    """Write a specification's roadmap, each row with its scope and status.

    Only the rows of its own Roadmap section are shown (items spec \N{SECTION SIGN}3.9).
    """
    section = _section(text, "Roadmap")
    rows = [row for row in grammar.rows(text) if row.section == section]
    if not rows:
        return ["No roadmap.", ""]
    return [
        "| # | Scope | Status |",
        "|---|---|---|",
        *(f"| {row.row} | {_cell(row.scope)} | {_cell(row.status)} |" for row in rows),
        "",
    ]


def _stated(item: Item) -> tuple[str, str]:
    """Read an item's state and title, as the table shows them.

    An item still in the grammar of docs spec \N{SECTION SIGN}3.6 leads with its
    status in bold, which the grammar reads as its title, and its title follows a
    dash, so the status is shown as its state.
    """
    if item.state is not None:
        return item.state, item.title
    old = OLD_TITLE.match(item.body)
    if old is None:
        return "no state", item.title
    return item.title, old["title"]


def _open_items(text: str) -> list[str]:
    """Write a specification's open items, each with its state, owing row and moves."""
    found = grammar.items(text)
    if not found:
        return ["No open items.", ""]
    lines = ["| Item | State | Owed by | Moves |", "|---|---|---|---|"]
    for item in found:
        state, title = _stated(item)
        owed = _cell(item.owed) if item.owed else EM_DASH
        lines.append(
            f"| {item.number}: {_cell(title)} | {_cell(state)} | {owed} | "
            f"{len(item.moves)} |"
        )
    return [*lines, ""]


def _item_findings(path: Path, text: str, prefix: str, names: Namespace) -> list[str]:
    """Find an item on its last move, and one owed by a row in progress.

    The row an item names is read as the conventions test reads it, and an item
    owed by no row of its own roadmap, by a landed row, or moved three times, is
    left to the suite, which refuses each (items spec \N{SECTION SIGN}3.9).
    """
    section = _items_section(text)
    found = []
    for item in grammar.items(text):
        if item.state not in (grammar.OPEN, grammar.DEFERRED) or item.owed is None:
            continue
        row = conventions.own_row(path, text, item.owed, names)
        if isinstance(row, str) or row.status.startswith(conventions.LANDED):
            continue
        name = f"{prefix} {grammar.SECTION}{section} item {item.number}"
        if len(item.moves) == 2:
            found.append(
                f"{name} is on its last move: when {item.owed} lands, it must "
                "settle or graduate."
            )
        if row.status.startswith("in progress"):
            found.append(
                f"{name} is owed by {item.owed}, which is in progress: its pull "
                "request must answer it."
            )
    return found


@dataclass(frozen=True)
class Cited:
    """A place a decision is cited."""

    path: Path
    line: int


def group(path: Path, root: Path, specs: Collection[Path] = ()) -> str:
    """Name the group a file's citations are listed under.

    Only a specification is grouped as one: the index beside them is a page.
    """
    name = path.relative_to(root).as_posix()
    if name.startswith("tests/"):
        return "tests"
    if path in specs:
        return "specifications"
    if name.startswith(f"{PLANS.as_posix()}/"):
        return "plans"
    # code is source wherever it sits, the documentation's extensions included
    if name.startswith((".github/", "src/")) or path.suffix == ".py":
        return "source"
    return "documentation"


def _entries(text: str, slug: str) -> dict[int, str]:
    """Map each line of a decision's own entry to that decision's anchor.

    An entry runs as the grammar reads it (:func:`grammar.decision_entries`): the
    lines of its item in the Decisions' list, as markdown reads them.
    """
    return {
        number: grammar.decision_anchor(slug, entry.written)
        for entry in grammar.decision_entries(text)
        for number in range(entry.line, entry.end + 1)
    }


def citations_of(texts: Mapping[Path, str], names: Namespace) -> dict[str, list[Cited]]:
    """Find every citation of a decision, a decision's own entry aside.

    Parameters
    ----------
    texts : mapping of Path to str
        The files to read, each with its text.
    names : Namespace
        The namespace of the specifications.

    Returns
    -------
    dict
        Each decision anchor cited, mapped to where it is cited, in file order.

    """
    found: dict[str, list[Cited]] = {}
    for path, text in texts.items():
        owner = names.owners.get(path)
        own = _entries(text, owner) if owner is not None else {}
        for number, line in grammar.source_lines(path, text):
            plain = grammar.prose(line)[0]
            for citation in grammar.scan(plain, names.signed, owner):
                label = grammar.LABEL.match(citation.slug or "")
                if label is None or label["decision"] is None:
                    continue
                if own.get(number) == citation.slug:
                    continue
                places = found.setdefault(citation.slug, [])
                # one line is one place, however often it names the decision
                if Cited(path, number) not in places:
                    places.append(Cited(path, number))
    return found


def _title(text: str) -> str:
    """Read a specification's title, its first heading."""
    return next(
        (line[2:].strip() for line in text.splitlines() if line.startswith("# ")), ""
    )


def _evidence(
    name: str, anchor: str, row: LedgerRow, names: Namespace, root: Path
) -> list[str]:
    """Find what does not hold in the evidence of a verified or signed-off row.

    A test that cannot be read is a finding, never an abort, so the report still
    prints whatever else it finds.
    """
    state = conventions.opened(row.status)[0]
    if state == grammar.SIGNED_OFF and not row.evidence.strip():
        return [f"{name} is signed off with nothing said of what was checked."]
    if state != grammar.VERIFIED:
        return []
    files = re.findall(r"`([^`]+)`", row.evidence)
    if not files:
        return [f"{name} is verified by nothing."]
    found = []
    for file in files:
        test = root / file
        if not test.is_file():
            found.append(f"{name}: `{file}` is missing.")
            continue
        try:
            silent = not conventions.cites(test, anchor, names)
        except (OSError, UnicodeDecodeError):
            found.append(f"{name}: `{file}` cannot be read.")
            continue
        if silent:
            found.append(f"{name}: `{file}` no longer cites it.")
    return found


def report(
    specs: list[Path], texts: Mapping[Path, str], names: Namespace, root: Path
) -> str:
    """Write the report of the specifications given, in Markdown.

    Parameters
    ----------
    specs : list of Path
        The specifications to report.
    texts : mapping of Path to str
        Every file to look for citations in.
    names : Namespace
        The namespace of the whole collection.
    root : Path
        The repository root, which every path is shown relative to.

    Returns
    -------
    str
        The report.

    """
    cited = citations_of(texts, names)
    out = ["# Verification Report", ""]
    findings: list[str] = []
    for spec in specs:
        text = spec.read_text(encoding="utf-8")
        slug = names.owners[spec]
        prefix = slug.replace("-", " ")
        out += [f"## {prefix}: {_title(text)}", "", "### Roadmap", ""]
        out += _roadmap(text)
        rows = {row.decision: row for row in grammar.ledger(text) or []}
        if rows:
            out += [grammar.summary(row.status for row in rows.values()), ""]
        decisions = grammar.decisions(text)
        if not decisions:
            out += ["No numbered decisions.", ""]
        for decision in decisions:
            anchor = grammar.decision_anchor(slug, decision.number)
            name = f"{prefix} {grammar.SECTION}2 decision {decision.number}"
            row = rows.get(decision.number)
            state = markdown(row.status) if row else (decision.state or "no state")
            out += [f"### Decision {decision.number}: {decision.title}", "", state, ""]
            places = cited.get(anchor, [])
            for kind in GROUPS:
                listed = [
                    f"`{place.path.relative_to(root).as_posix()}:{place.line}`"
                    for place in places
                    if group(place.path, root, names.owners) == kind
                ]
                if listed:
                    out.append(f"- **{kind}:** {', '.join(listed)}")
            if places:
                out.append("")
            if decision.state == grammar.AGREED and not places:
                findings.append(f"{name} is in force and cited nowhere.")
            if row is not None:
                findings += _evidence(name, anchor, row, names, root)
        out += ["### Open Items", ""]
        out += _open_items(text)
        findings += _item_findings(spec, text, prefix, names)
    out += ["## Findings", ""]
    out += [f"- {finding}" for finding in findings] or ["No findings."]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None, root: Path = REPO) -> int:
    """Print the report of every specification, or of the one a prefix names.

    Parameters
    ----------
    argv : list of str, optional
        The command line: an optional prefix, such as ``heights``.
    root : Path, optional
        The repository root. A test passes a repository of its own.

    Returns
    -------
    int
        Zero, whatever the report finds; two when it cannot read a specification,
        or the prefix names none.

    """
    args = sys.argv[1:] if argv is None else argv
    try:
        specs = grammar.specifications(root / SPECS)
        names = grammar.namespace(specs)
        texts = dict(grammar.corpus(root))
        for path in sorted((root / PLANS).rglob("*")):
            if not path.is_file():
                continue
            try:
                texts[path] = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # a file that is not UTF-8 is not text, as the corpus has it
                continue
    except (OSError, UnicodeDecodeError) as error:
        print(f"could not read the specifications: {error}", file=sys.stderr)
        return 2
    owned = [spec for spec in specs if spec in names.owners]
    if args:
        wanted = f"{args[0]}-spec"
        owned = [spec for spec in owned if names.owners[spec] == wanted]
        if not owned:
            known = sorted(p.removesuffix("-spec") for p in names.owners.values())
            print(
                f"{args[0]!r} names no specification; known: {', '.join(known)}",
                file=sys.stderr,
            )
            return 2
    written = report(owned, texts, names, root)
    print(written, end="")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write(written)
    return 0


if __name__ == "__main__":
    sys.exit(main())
