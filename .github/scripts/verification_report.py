#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Report how each specification decision is verified, and where it is cited.

For every specification, or the one a prefix names, the report lists each
decision with its state, then every place in the repository that cites it,
grouped as source, tests, documentation, specifications and plans. It flags what
does not agree: a verified row whose test no longer cites its decision, and a
decision in force that nothing anywhere cites (ledger spec §3.8).

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
    from collections.abc import Mapping
    from types import ModuleType

#: The repository root.
REPO = Path(__file__).parents[2]

#: The specifications and the plans, relative to a repository root.
SPECS = Path("docs") / "src" / "developer" / "specs"
PLANS = Path("docs") / "src" / "developer" / "plans"

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


@dataclass(frozen=True)
class Cited:
    """A place a decision is cited."""

    path: Path
    line: int


def group(path: Path, root: Path) -> str:
    """Name the group a file's citations are listed under."""
    name = path.relative_to(root).as_posix()
    if name.startswith("tests/"):
        return "tests"
    if name.startswith(f"{SPECS.as_posix()}/"):
        return "specifications"
    if name.startswith(f"{PLANS.as_posix()}/"):
        return "plans"
    # code is source wherever it sits, the documentation's extensions included
    if name.startswith((".github/", "src/")) or path.suffix == ".py":
        return "source"
    return "documentation"


def _entries(text: str, slug: str) -> dict[int, str]:
    """Map each line of a decision's own entry to that decision's anchor."""
    lines = text.splitlines()
    found = grammar.decisions(text)
    owned: dict[int, str] = {}
    for index, decision in enumerate(found):
        last = found[index + 1].line - 1 if index + 1 < len(found) else len(lines)
        for number in range(decision.line, last + 1):
            if number > decision.line and not lines[number - 1].strip():
                break
            owned[number] = grammar.decision_anchor(slug, decision.number)
    return owned


def citations_of(texts: Mapping[Path, str], names: object) -> dict[str, list[Cited]]:
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
                found.setdefault(citation.slug, []).append(Cited(path, number))
    return found


def _title(text: str) -> str:
    """Read a specification's title, its first heading."""
    return next(
        (line[2:].strip() for line in text.splitlines() if line.startswith("# ")), ""
    )


def report(
    specs: list[Path], texts: Mapping[Path, str], names: object, root: Path
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
        out += [f"## {prefix}: {_title(text)}", ""]
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
            state = row.status if row else (decision.state or "no state")
            out += [f"### Decision {decision.number}: {decision.title}", "", state, ""]
            places = cited.get(anchor, [])
            for kind in GROUPS:
                listed = [
                    f"`{place.path.relative_to(root).as_posix()}:{place.line}`"
                    for place in places
                    if group(place.path, root) == kind
                ]
                if listed:
                    out.append(f"- **{kind}:** {', '.join(listed)}")
            if places:
                out.append("")
            if decision.state == grammar.AGREED and not places:
                findings.append(f"{name} is in force and cited nowhere.")
            if row and conventions.opened(row.status)[0] == grammar.VERIFIED:
                for file in re.findall(r"`([^`]+)`", row.evidence):
                    test = root / file
                    if test.is_file() and not conventions.cites(test, anchor, names):
                        findings.append(f"{name}: `{file}` no longer cites it.")
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
            if path.is_file():
                texts[path] = path.read_text(encoding="utf-8")
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
