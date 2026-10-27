# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Guard the citations of a specification section against its renumbering.

A specification may insert a section where it belongs, and every section after
it takes a new number. A citation written against the old number still resolves,
to whatever the number names now, and nothing else notices. So, on a pull request,
this compares each specification it changes with the one on its base branch,
pairs every section with its counterpart, and fails on any line the pull request
did not touch that still cites a section which moved or went. With "--fix" it
rewrites the citations of the moved ones. With "--audit" it compares every
citation in the repository with the specification as it stood when the citing
line was written, which finds one that arrived by a branch older than the
renumber. The design is the citation links design, citation spec §4.5.

Numbered items and roadmap rows are cited by number too, in forms no grammar
reads, so they are held to being appended: one that moves or goes fails.

The citations are read with the grammar of "docs/src/_ext/geovista_citations.py",
which the conventions test and the documentation build share.

"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import difflib
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import traceback
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from types import ModuleType

#: The section of the repository checks page that documents this check.
CHECK = "spec-renumbering"

#: The repository root.
ROOT = Path(__file__).parents[2]

#: How alike the text of two sections must be to pair them, once their titles
#: have failed to: enough that a renamed section finds itself, and two that merely
#: share a subject do not.
LIKENESS = 0.6


def _load(path: Path, name: str) -> ModuleType:
    """Load a module by path, reusing a copy already registered from it."""
    registered = sys.modules.get(name)
    if registered is not None and Path(registered.__file__).resolve() == path.resolve():
        return registered
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


#: The citation grammar, shared with the conventions test and the build.
grammar = _load(
    ROOT / "docs" / "src" / "_ext" / "geovista_citations.py", "geovista_citations"
)

#: The link a finding ends with, to this check's section.
breadcrumb = _load(Path(__file__).parent / "breadcrumb.py", "breadcrumb")


@dataclass(frozen=True)
class Section:
    """One numbered section of a specification.

    Attributes
    ----------
    anchor : str
        Its anchor, e.g. ``typing-spec-3-2``.
    title : str
        Its heading, less the number.
    body : str
        The text beneath the heading, up to the next anchor, less any code.

    """

    anchor: str
    title: str
    body: str


@dataclass(frozen=True)
class Fate:
    """What became of a section on the base branch.

    Attributes
    ----------
    kind : {"kept", "moved", "removed"}
        Kept under its own anchor, moved to another, or gone.
    anchor : str or None
        The anchor it is under now, or ``None`` when it was removed.
    title : str
        Its title on the base branch, which a finding names it by.

    """

    kind: Literal["kept", "moved", "removed"]
    anchor: str | None
    title: str


def sections(text: str) -> dict[str, Section]:
    """Read a specification's sections, keyed by anchor, in the order written."""
    found: dict[str, Section] = {}
    lines = [line for _, line in grammar.read_lines(text)]
    current: tuple[str, str] | None = None
    body: list[str] = []
    for index, line in enumerate(lines):
        anchor = grammar.ANCHOR.match(line)
        heading = (
            grammar.HEADING.match(lines[index + 1]) if index + 1 < len(lines) else None
        )
        if anchor is not None and heading is not None:
            if current is not None:
                found[current[0]] = Section(*current, "\n".join(body).strip())
            current, body = (f"{anchor['slug']}-{anchor['num']}", heading["title"]), []
            continue
        if current is not None and not grammar.HEADING.match(line):
            body.append(line)
    if current is not None:
        found[current[0]] = Section(*current, "\n".join(body).strip())
    return found


def _plain(title: str) -> str:
    """Spell a title without case or punctuation, as a title style sweep leaves it."""
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def _likeness(old: str, new: str) -> float:
    """Rate how alike two texts are, from 0 to 1."""
    return difflib.SequenceMatcher(None, old, new).ratio()


def pair(
    base: dict[str, Section], head: dict[str, Section], *, in_place: bool = False
) -> dict[str, Fate]:
    """Pair each section on the base branch with its counterpart, if it has one.

    Sections pair by title first, those sharing a title with the counterpart whose
    text is likest, then those left over by the likeness of their text, best pair
    first, which is what finds a section renamed as it moved. With ``in_place``, a
    section still unpaired whose number is free in ``head`` was edited in place,
    as an item is when it is resolved and reworded.

    Parameters
    ----------
    base, head : dict
        The sections of the specification on the base branch and now.
    in_place : bool, optional
        Pair what is left over by number, as items and rows are.

    Returns
    -------
    dict
        The fate of each section on the base branch, keyed by its anchor there.

    """
    paired: dict[str, str] = {}
    free = list(head)
    titled = sorted(
        (
            (_likeness(section.body, head[other].body), anchor == other, anchor, other)
            for anchor, section in base.items()
            for other in head
            if _plain(head[other].title) == _plain(section.title)
        ),
        reverse=True,
    )
    for _, _, old, new in titled:
        if old not in paired and new in free:
            paired[old] = new
            free.remove(new)
    likely = sorted(
        (
            (_likeness(base[old].body, head[new].body), old, new)
            for old in base
            if old not in paired and base[old].body
            for new in free
            if head[new].body
        ),
        reverse=True,
    )
    for likeness, old, new in likely:
        if likeness < LIKENESS:
            break
        if old not in paired and new in free:
            paired[old] = new
            free.remove(new)
    if in_place:
        for old in base:
            if old not in paired and old in free:
                paired[old] = old
                free.remove(old)
    fates: dict[str, Fate] = {}
    for anchor, section in base.items():
        new = paired.get(anchor)
        if new is None:
            fates[anchor] = Fate("removed", None, section.title)
        else:
            fates[anchor] = Fate(
                "kept" if new == anchor else "moved", new, section.title
            )
    return fates


#: An item of a numbered list, opening at the left margin.
ITEM = re.compile(r"^(?P<number>\d+)\.\s+(?P<rest>\S.*)$")

#: A run of bold text, which may wrap.
BOLD = re.compile(r"\*\*(?P<text>.+?)\*\*", flags=re.DOTALL)

#: The statuses an open item opens with, before its title.
STATES = frozenset({"Open", "Resolved", "Deferred", "Abandoned"})

#: The header of a roadmap table: its number, its scope, and somewhere a status.
ROADMAP = re.compile(r"^\|\s*#\s*\|\s*Scope\s*\|.*\bStatus\s*\|")


def numbered_items(text: str) -> dict[str, dict[str, Section]]:
    """Read every numbered item opening with a bold title, by section and number.

    Each is read as a :class:`Section` keyed by its number, titled by its bold
    title, the one after its status if it opens with one, with its text as the
    body, so that items pair as sections do.
    """
    found: dict[str, dict[str, Section]] = {}
    lines = [line for _, line in grammar.read_lines(text)]
    current = None
    for index, line in enumerate(lines):
        anchor = grammar.ANCHOR.match(line)
        if anchor is not None:
            current = f"{anchor['slug']}-{anchor['num']}"
            continue
        item = ITEM.match(line)
        if current is None or item is None or not item["rest"].startswith("**"):
            continue
        body = [item["rest"]]
        for following in lines[index + 1 :]:
            if not following[:1].isspace() or not following.strip():
                break
            body.append(following.strip())
        joined = " ".join(body)
        bolds = [match["text"].replace("\n", " ") for match in BOLD.finditer(joined)]
        title = bolds[1] if bolds[0] in STATES and len(bolds) > 1 else bolds[0]
        number = item["number"]
        found.setdefault(current, {})[number] = Section(number, title, joined)
    return found


def roadmap_rows(text: str) -> dict[str, Section]:
    """Read every row of a roadmap table, keyed by its number and titled by scope."""
    found: dict[str, Section] = {}
    inside = False
    for _, line in grammar.read_lines(text):
        if ROADMAP.match(line):
            inside = True
            continue
        if not line.startswith("|"):
            inside = False
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if inside and cells and not set(cells[0]) <= set("-: "):
            found[cells[0]] = Section(cells[0], cells[1], cells[1])
    return found


def _split(old: str, new: str | None) -> bool:
    """Say whether row ``old`` became ``new`` by splitting, as 6 into 6a."""
    return new is not None and re.fullmatch(rf"{re.escape(old)}[a-z]", new) is not None


def frozen(base_text: str, head_text: str) -> list[str]:
    """Report each numbered item and roadmap row that moved or went.

    Parameters
    ----------
    base_text, head_text : str
        The specification on the base branch and now.

    Returns
    -------
    list of str
        One message per item or row whose number now names another, or nothing.

    """
    problems: list[str] = []
    fates = pair(sections(base_text), sections(head_text))
    base_items, head_items = numbered_items(base_text), numbered_items(head_text)
    for anchor, listed in base_items.items():
        fate = fates.get(anchor)
        if fate is None or fate.anchor is None:
            continue
        paired = pair(listed, head_items.get(fate.anchor, {}), in_place=True)
        for number, item in paired.items():
            if item.kind == "moved":
                problems.append(
                    f'{fate.title}, item {number} "{listed[number].title}" is now '
                    f"item {item.anchor}: append an item rather than insert it"
                )
            elif item.kind == "removed":
                problems.append(
                    f'{fate.title}, item {number} "{listed[number].title}" was '
                    "removed: mark it as no longer applying, in place"
                )
    base_rows, head_rows = roadmap_rows(base_text), roadmap_rows(head_text)
    for number, row in pair(base_rows, head_rows, in_place=True).items():
        split = any(_split(number, other) for other in head_rows)
        if row.kind == "moved" and not _split(number, row.anchor):
            problems.append(
                f'roadmap row {number} "{base_rows[number].title}" is now row '
                f"{row.anchor}: append a row rather than insert it"
            )
        elif row.kind == "removed" and not split:
            problems.append(
                f'roadmap row {number} "{base_rows[number].title}" was removed'
            )
    return problems


@dataclass(frozen=True)
class Finding:
    """A citation, on a line the pull request did not touch, of a section that left.

    Attributes
    ----------
    path : Path
        The citing file.
    line : int
        The citing line, 1-indexed.
    cited : str
        The citation as written.
    fate : Fate
        What became of the section it was written against.
    old : str
        The anchor it names, which no longer holds that section.

    """

    path: Path
    line: int
    cited: str
    fate: Fate
    old: str


def _number(anchor: str) -> str:
    """Spell an anchor's section number, as ``typing-spec-3-2`` is ``3.2``."""
    return grammar.LABEL.match(anchor)["num"].replace("-", ".")


def _citations(
    path: Path, line: str, names: object
) -> list[tuple[int, int, str, str, str]]:
    """Find a line's citations, as their span, text, anchor and kind of writing.

    A plain citation spans its text; a role spans its body, between the
    backticks, so that a rewrite can turn its display and its target together.
    """
    found: list[tuple[int, int, str, str, str]] = []
    plain, _ = grammar.prose(line)
    owner = names.owners.get(path)
    found.extend(
        (citation.start, citation.end, citation.text, citation.slug, "plain")
        for citation in grammar.scan(plain, names.signed, owner)
        if citation.slug is not None
    )
    for match in grammar.SPAN.finditer(line):
        if match["role"] is None or len(match["ticks"]) != 1:
            continue
        role = grammar.section_role(match["role"].strip("{}:"), match["body"], names)
        if role is not None:
            shown, target = role
            found.append(
                (
                    match.start("body"),
                    match.end("body"),
                    shown or target,
                    target,
                    "role",
                )
            )
    return found


def stale(
    texts: dict[Path, str],
    fates: dict[str, Fate],
    names: object,
    changed: dict[Path, set[int]],
) -> list[Finding]:
    """Find each untouched citation of a section that moved or went.

    Parameters
    ----------
    texts : dict
        The corpus, each file's text keyed by its path.
    fates : dict
        What became of each section of the specifications that changed.
    names : Namespace
        The citation grammar of the specifications as they are now.
    changed : dict
        The lines the pull request changed, keyed by path.

    Returns
    -------
    list of Finding
        In the order of the corpus and of each file's lines.

    """
    findings: list[Finding] = []
    for path, text in texts.items():
        touched = changed.get(path, set())
        for number, line in grammar.source_lines(path, text):
            if number in touched:
                continue
            for _, _, cited, anchor, _ in _citations(path, line, names):
                fate = fates.get(anchor)
                if fate is not None and fate.kind != "kept":
                    findings.append(Finding(path, number, cited, fate, anchor))
    return findings


def describe(finding: Finding, root: Path, now: dict[str, Section]) -> str:
    """Say what a stale citation was written against, and what became of it."""
    where = (
        finding.path.relative_to(root)
        if finding.path.is_relative_to(root)
        else (finding.path)
    )
    head = (
        f'{where.as_posix()}:{finding.line}: {finding.cited} was "{finding.fate.title}"'
    )
    if finding.fate.kind == "moved":
        return f"{head}, which is now {grammar.SECTION}{_number(finding.fate.anchor)}"
    sign = f"{grammar.SECTION}{_number(finding.old)}"
    later = now.get(finding.old)
    return f"{head}, which was removed; {sign} is " + (
        f'now "{later.title}"' if later is not None else "no longer a section"
    )


def rewrite(
    text: str, path: Path, fates: dict[str, Fate], names: object, lines: set[int]
) -> str:
    """Move each citation of a moved section, on the lines given, to its new number.

    A citation of a removed section has no new number, and is left as written.
    """
    out = text.splitlines(keepends=True)
    for number, line in grammar.source_lines(path, text):
        if number not in lines:
            continue
        edits = []
        for start, end, _, anchor, kind in _citations(path, line, names):
            fate = fates.get(anchor)
            if fate is None or fate.kind != "moved":
                continue
            new = _number(fate.anchor)
            if kind == "plain":
                replaced = re.sub(r"\d+(?:\.\d+)*$", new, line[start:end])
            else:
                targeted = grammar.TARGETED.match(line[start:end])
                shown = re.sub(r"\d+(?:\.\d+)*$", new, targeted["text"])
                replaced = f"{shown} <{fate.anchor}>"
            edits.append((start, end, replaced))
        edited = line
        for start, end, replaced in sorted(edits, reverse=True):
            edited = edited[:start] + replaced + edited[end:]
        ending = out[number - 1][len(out[number - 1].rstrip("\r\n")) :]
        out[number - 1] = edited + ending
    return "".join(out)


#: Where a repository keeps its specifications.
SPECS = Path("docs") / "src" / "developer" / "specs"

#: The commit blame gives a line not yet committed.
UNCOMMITTED = "0" * 40

#: The commit at which every citation in the repository was audited by hand,
#: against its specification, when this check was written. The nightly audit
#: judges a line older than it from here, so that it only ever judges history the
#: check was there to see. One citation was flagged that day: the typing spec's own
#: section 3.4, renamed and nearly tripled in a single change, which is the same
#: section, and which a renumber guard would have asked to have checked by hand.
AUDITED: str | None = "a9e25a86f4aba8863128120db0a87410d91f99b3"


class GitError(RuntimeError):
    """Git could not answer, which is never a finding."""


def git(root: Path, *args: str) -> str:
    """Run git in ``root``, returning its output."""
    try:
        # git by name, with arguments this script builds, never a shell
        done = subprocess.run(  # noqa: S603
            ["git", "--no-pager", *args],  # noqa: S607
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        emsg = f"git {' '.join(args)}: {error.stderr.strip()}"
        raise GitError(emsg) from error
    return done.stdout


def at(root: Path, ref: str, path: Path) -> str | None:
    """Return a file's text at ``ref``, or ``None`` if it did not exist there."""
    relative = path.relative_to(root).as_posix() if path.is_absolute() else path
    try:
        return git(root, "show", f"{ref}:{relative}")
    except GitError:
        return None


#: A file a unified diff names, as changed.
DIFFED = re.compile(r"^\+\+\+ b/(?P<path>.+)$")

#: The lines of a hunk, as they are now.
HUNK = re.compile(r"^@@ -\S+ \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")


def changed_lines(root: Path, base: str) -> dict[Path, set[int]]:
    """Read the lines changed since ``base`` branched, as they are numbered now."""
    changed: dict[Path, set[int]] = {}
    current: Path | None = None
    for line in git(root, "diff", "--unified=0", "--no-color", base, "--").splitlines():
        if diffed := DIFFED.match(line):
            current = root / diffed["path"]
            continue
        if (hunk := HUNK.match(line)) and current is not None:
            start, count = int(hunk["start"]), int(hunk["count"] or 1)
            changed.setdefault(current, set()).update(range(start, start + count))
    return changed


def _fates(root: Path, ref: str, specs: list[Path]) -> dict[str, Fate]:
    """Pair the sections of each specification at ``ref`` with those now."""
    fates: dict[str, Fate] = {}
    for spec in specs:
        before = at(root, ref, spec)
        if before is not None and spec.is_file():
            now = spec.read_text(encoding="utf-8")
            if before != now:
                fates.update(pair(sections(before), sections(now)))
        elif before is not None:
            fates.update(pair(sections(before), {}))
    return fates


def _ancestor(root: Path, older: str, newer: str) -> bool:
    """Say whether ``older`` is an ancestor of ``newer``."""
    try:
        git(root, "merge-base", "--is-ancestor", older, newer)
    except GitError:
        return False
    return True


def _chain(root: Path, spec: Path, start: str) -> dict[str, Fate]:
    """Follow each section of a specification from ``start`` to now, change by change.

    Pairing the two ends alone loses a section renamed in one change and grown in
    others, which is how a living section changes. Each change is one a pull
    request made, which is what the pairing reads well, so the fates are
    composed step by step.
    """
    first = at(root, start, spec)
    if first is None:
        return {}
    relative = spec.relative_to(root).as_posix()
    listed = git(
        root, "rev-list", "--reverse", "--topo-order", f"{start}..HEAD", "--", relative
    )
    texts = [at(root, revision, spec) for revision in listed.split()]
    texts.append(spec.read_text(encoding="utf-8"))
    origin = sections(first)
    where = {anchor: anchor for anchor in origin}
    gone: set[str] = set()
    previous = origin
    for text in texts:
        if text is None:
            continue
        current = sections(text)
        step = pair(previous, current)
        for anchor in origin:
            if anchor in gone:
                continue
            fate = step.get(where[anchor])
            if fate is None or fate.anchor is None:
                gone.add(anchor)
            else:
                where[anchor] = fate.anchor
        previous = current
    return {
        anchor: Fate(
            "removed"
            if anchor in gone
            else ("kept" if where[anchor] == anchor else "moved"),
            None if anchor in gone else where[anchor],
            section.title,
        )
        for anchor, section in origin.items()
    }


def audit(root: Path, texts: dict[Path, str], names: object) -> list[Finding]:
    """Follow every citation's section from when the citing line was written.

    Each specification is followed change by change from the commit that last
    wrote the line, or from :data:`AUDITED` when the line is older than that, so a
    citation that arrived on a branch older than a renumber is found whatever
    route it came by.
    """
    owners = {prefix: spec for spec, prefix in names.owners.items()}
    baseline = AUDITED
    if baseline is not None:
        try:
            git(root, "cat-file", "-e", f"{baseline}^{{commit}}")
        except GitError:
            # another repository, as a test's, which never saw the hand audit
            baseline = None
    chained: dict[tuple[str, Path], dict[str, Fate]] = {}
    findings: list[Finding] = []
    for path, text in texts.items():
        cited = [
            (number, found)
            for number, line in grammar.source_lines(path, text)
            if (found := _citations(path, line, names))
        ]
        if not cited:
            continue
        blamed = _blame(root, path)
        for number, found in cited:
            commit = blamed.get(number)
            if commit is None or commit == UNCOMMITTED:
                continue
            if baseline is not None and _ancestor(root, commit, baseline):
                commit = baseline
            for _, _, citation, anchor, _ in found:
                spec = owners.get(grammar.LABEL.match(anchor)["prefix"])
                if spec is None:
                    continue
                if (commit, spec) not in chained:
                    chained[commit, spec] = _chain(root, spec, commit)
                fate = chained[commit, spec].get(anchor)
                if fate is not None and fate.kind != "kept":
                    findings.append(Finding(path, number, citation, fate, anchor))
    return findings


def _blame(root: Path, path: Path) -> dict[int, str]:
    """Map each line of a file to the commit that last wrote it."""
    blamed: dict[int, str] = {}
    relative = path.relative_to(root).as_posix()
    for line in git(root, "blame", "--porcelain", "--", relative).splitlines():
        fields = line.split()
        if len(fields) >= 3 and re.fullmatch(r"[0-9a-f]{40}", fields[0]):
            blamed[int(fields[2])] = fields[0]
    return blamed


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    """Check the specifications changed since a base, or audit every citation.

    Parameters
    ----------
    argv : list of str, optional
        The command line arguments. Defaults to those of the process.
    root : Path, optional
        The repository. Defaults to this one; a test passes one of its own.

    Returns
    -------
    int
        Zero when no citation went stale, one when any did, and two when the
        check could not be finished, as when git cannot find the base.

    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--base", default="origin/main", help="the branch a pull request targets"
    )
    parser.add_argument(
        "--fix", action="store_true", help="rewrite the citations of moved sections"
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="compare every citation with its specification when it was written",
    )
    args = parser.parse_args(argv)

    try:
        texts = grammar.corpus(root)
        specs = grammar.specifications(root / SPECS)
        names = grammar.namespace(specs)
        now = {
            anchor: section
            for spec in specs
            for anchor, section in sections(spec.read_text(encoding="utf-8")).items()
        }
        problems: list[str] = []
        if args.audit:
            findings = audit(root, texts, names)
            scope = "every citation in the repository"
        else:
            branched = git(root, "merge-base", args.base, "HEAD").strip()
            listed = git(root, "ls-tree", "--name-only", branched, f"{SPECS}/")
            specs_then = {
                root / name for name in listed.split() if name.endswith(".md")
            }
            fates = _fates(root, branched, sorted(specs_then | set(specs)))
            changed = changed_lines(root, branched)
            findings = stale(texts, fates, names, changed)
            for spec in specs:
                before = at(root, branched, spec)
                if before is not None:
                    problems += [
                        f"{spec.relative_to(root).as_posix()}: {problem}"
                        for problem in frozen(before, spec.read_text(encoding="utf-8"))
                    ]
            scope = f"the specifications changed since {args.base}"
            if args.fix:
                findings = _fix(texts, fates, names, findings)
    except GitError as error:
        print(f"could not compare with git: {error}", file=sys.stderr)
        return 2
    except Exception:  # noqa: BLE001
        # the nightly workflow opens an issue on one, so anything unexpected must
        # leave by another door
        traceback.print_exc()
        print("could not finish checking", file=sys.stderr)
        return 2

    for finding in findings:
        print(describe(finding, root, now))
    for problem in problems:
        print(problem)
    if findings or problems:
        print(breadcrumb.breadcrumb(CHECK))
        return 1
    print(f"checked {scope}: no citation went stale")
    return 0


def _fix(
    texts: dict[Path, str],
    fates: dict[str, Fate],
    names: object,
    findings: list[Finding],
) -> list[Finding]:
    """Rewrite the citations of moved sections, and return what is left."""
    lines: dict[Path, set[int]] = {}
    for finding in findings:
        if finding.fate.kind == "moved":
            lines.setdefault(finding.path, set()).add(finding.line)
    for path, numbers in lines.items():
        path.write_text(
            rewrite(texts[path], path, fates, names, numbers), encoding="utf-8"
        )
        print(f"fixed {path.name}, lines {', '.join(map(str, sorted(numbers)))}")
    return [finding for finding in findings if finding.fate.kind != "moved"]


if __name__ == "__main__":
    sys.exit(main())
