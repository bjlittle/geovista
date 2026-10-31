#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Check the work each specification status cites against GitHub.

A status names the work that put it there, as in "✅ landed (2026-10-06,
{pull}`2565`)". "tests/test_spec_conventions.py" checks that a terminal status
carries a date and a reference, but not that the reference is real, since
reaching GitHub from the unit suite would fail it on a network outage. This
script asks GitHub instead, following the vocabulary of docs spec §3.6:

- A "✅ landed" row cites only pull requests, every one merged, and its date
  is within a day of the last of them to merge.
- A "Resolved" item cites work that exists, and any pull request it cites has
  merged. An issue may still be open, since raising one can be what settled it,
  and the date may come before the merge, being when the decision was taken.
- An "Abandoned" item cites work that exists.

A role must also name the kind of work it says: "{pull}" a pull request and
"{issue}" an issue.

With "--drift" it also reports a non-terminal status whose work has moved on
without it: an "in progress" row whose pull request has merged or closed, and a
"not started" row, or an "Open" or "Deferred" item, whose issue has closed.
Drift appears when other work lands, so it is checked on a schedule rather than
by the pull request that wrote the status.

With "--pull" a status may cite that pull request while it is still open, as a
pull request can record what it resolves, and the date of a "✅ landed" row
citing it is not checked.

It asks GitHub about each ledger too (ledger spec §3.7):

- Every pull request a decision cites has merged, or is the one being checked.
- A verified or retired row is dated within a day of its pull request's merge.
- A signed-off row holds when the reviewer it names added the "signed-off"
  label to the pull request it cites, and the label is on it still, read from
  that pull request's events. Its date is within a day of the label's.

The statuses are read with the parser of "tests/test_spec_conventions.py",
which reads specifications with the citation grammar of
"docs/src/_ext/geovista_citations.py", so that a status has one definition
rather than two that disagree. A token in
the "GITHUB_TOKEN" or "GH_TOKEN" environment variable is used when set.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import traceback
from typing import TYPE_CHECKING
import urllib.error
import urllib.request

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from types import ModuleType

#: The section of the repository checks page that documents this check.
CHECK = "spec-statuses"

#: The repository root.
ROOT = Path(__file__).parents[2]

#: The tests holding the grammar of a specification status.
CONVENTIONS = ROOT / "tests" / "test_spec_conventions.py"

#: The repository that an "{issue}" or "{pull}" role names.
REPOSITORY = "bjlittle/geovista"

#: The GitHub REST API.
API = "https://api.github.com"

#: An "{issue}" or "{pull}" role.
ROLE = re.compile(r"\{(?P<role>issue|pull)\}`(?P<number>\d+)`")

#: A link to an issue or pull request, in this repository or another.
LINK = re.compile(
    r"\]\(https://github\.com/(?P<repository>[\w.-]+/[\w.-]+)/"
    r"(?P<role>issues|pull)/(?P<number>\d+)\)"
)


def _load(
    path: Path, name: str = "spec_conventions", *, register: bool = True
) -> ModuleType:
    """Load the module at `path`, registered, if asked, so its dataclasses resolve."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if register:
        sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


conventions = _load(CONVENTIONS)

#: The link a finding ends with, to this check's section (checks spec §3.3).
breadcrumb = _load(
    Path(__file__).parent / "breadcrumb.py", "breadcrumb", register=False
)


@dataclass(frozen=True)
class Reference:
    """A reference to an issue or pull request, as a status writes it."""

    repository: str
    number: int
    role: str
    text: str


@dataclass(frozen=True)
class Work:
    """An issue or pull request, as GitHub reports it."""

    kind: str
    state: str
    when: date | None


#: Look up the work at a repository and number, or None when there is none.
type Resolver = Callable[[str, int], Work | None]

#: The label a reviewer adds to sign off the decisions a pull request records.
SIGN_OFF = "signed-off"

#: A reviewer, as a sign-off names them.
REVIEWER = re.compile(r"\{user\}`(?P<login>[^`]+)`")

#: The next page of a paginated answer, from its Link header.
NEXT = re.compile(r'<(?P<url>[^>]+)>;\s*rel="next"')


@dataclass(frozen=True)
class Labelling:
    """A label added to or removed from a pull request, as GitHub reports it."""

    action: str
    label: str
    login: str | None
    when: date


#: Read the label events of the pull request at a repository and number.
type Labeller = Callable[[str, int], list[Labelling]]


def references(evidence: str) -> list[Reference]:
    """Return the references in the text a status carries, in written order."""
    found = [
        (
            match.start(),
            Reference(REPOSITORY, int(match["number"]), match["role"], match[0]),
        )
        for match in ROLE.finditer(evidence)
    ]
    found += [
        (
            match.start(),
            Reference(
                match["repository"],
                int(match["number"]),
                "pull" if match["role"] == "pull" else "issue",
                match[0].removeprefix("](").removesuffix(")"),
            ),
        )
        for match in LINK.finditer(evidence)
    ]
    return [reference for _, reference in sorted(found, key=lambda item: item[0])]


def _parse(kind: str, written: str) -> tuple[str, str] | None:
    """Split a status into its state and the rest, or None if it has none."""
    if kind == "row":
        state = next((s for s in conventions.ROW_STATES if written.startswith(s)), None)
        return None if state is None else (state, written[len(state) :])
    bold = conventions.STATE.match(written)
    return None if bold is None else (bold["state"].strip(), bold["rest"])


def cited(text: str) -> list[Reference]:
    """Return every reference that a status of the specification carries."""
    found = []
    for _, kind, written in conventions.statuses(text):
        if (parsed := _parse(kind, written)) is not None:
            found += references(conventions.carried(parsed[1]))
    return found


def ledger_cited(text: str) -> list[Reference]:
    """Return every reference a ledger carries, its decisions' and its rows'."""
    found = []
    for decision in conventions.decisions(text):
        found += references(decision.carried)
    for row in conventions.ledger(text) or []:
        found += references(conventions.carried(conventions.opened(row.status)[1]))
    return found


def _terminal(
    state: str,
    evidence: str,
    works: list[tuple[Reference, Work]],
    pull: int | None,
) -> list[str]:
    """Check what a terminal status cites."""
    problems = []

    def current(reference: Reference) -> bool:
        return reference.repository == REPOSITORY and reference.number == pull

    written = conventions.DATE.search(evidence)
    landed = None if written is None else conventions.dated(written[0])
    if written is not None and landed is None:
        problems.append(f"{written[0]} is not a date")

    if state == conventions.LANDED:
        merged = []
        pending = False
        for reference, work in works:
            if work.kind != "pull":
                problems.append(f"{reference.text} is not a pull request")
            elif current(reference):
                # it lands when it merges, so there is no date to hold it to yet
                pending = True
            elif work.state != "merged":
                problems.append(f"{reference.text} has not merged")
            elif work.when is not None:
                merged.append(work.when)
        if merged and landed is not None and not pending:
            last = max(merged)
            if abs((landed - last).days) > 1:
                problems.append(
                    f"landed on {landed}, but its last pull request merged on {last}"
                )
    elif state == "Resolved":
        for reference, work in works:
            if work.kind != "pull" or current(reference):
                continue
            if work.state == "open":
                problems.append(f"{reference.text} is still open")
            elif work.state == "closed":
                problems.append(f"{reference.text} closed without merging")
    return problems


def _drift(state: str, works: list[tuple[Reference, Work]]) -> list[str]:
    """Report a non-terminal status whose work has moved on without it."""
    problems = []
    for reference, work in works:
        if state == "in progress" and work.kind == "pull":
            if work.state != "open":
                moved = "merged" if work.state == "merged" else "closed"
                problems.append(f"{state}, but {reference.text} has {moved}")
        elif (
            state in ("not started", "Open", "Deferred")
            # these are held by an issue, and a pull request beside it is context
            and work.kind == "issue"
            and work.state != "open"
        ):
            problems.append(f"{state}, but {reference.text} has closed")
    return problems


def check(
    path: Path,
    text: str,
    resolve: Resolver,
    *,
    pull: int | None = None,
    drift: bool = False,
) -> list[str]:
    """Check the work cited by each status of a specification.

    Parameters
    ----------
    path : Path
        The specification, to locate each fault.
    text : str
        The specification.
    resolve : Resolver
        Look up the work at a repository and number.
    pull : int, optional
        The number of the pull request being checked, which a status may cite
        while it is still open.
    drift : bool, default=False
        Whether to also report a non-terminal status whose work has moved on.

    Returns
    -------
    list of str
        One message per fault, as ``path:line: message``.

    """
    problems = []
    for number, kind, written in conventions.statuses(text):
        if (parsed := _parse(kind, written)) is None:
            # a malformed status is the unit test's to report
            continue
        state, rest = parsed
        evidence = conventions.carried(rest)
        found = []
        faults = []
        for reference in references(evidence):
            work = resolve(reference.repository, reference.number)
            if work is None:
                faults.append(f"{reference.text} does not exist")
            elif reference.role == "pull" and work.kind == "issue":
                faults.append(f"{reference.text} is an issue")
            elif reference.role == "issue" and work.kind == "pull":
                faults.append(f"{reference.text} is a pull request")
            else:
                found.append((reference, work))
        if state in conventions.TERMINAL:
            faults += _terminal(state, evidence, found, pull)
        elif drift:
            faults += _drift(state, found)
        problems += [f"{conventions.where(path, number)}: {fault}" for fault in faults]
    return problems


def check_ledger(
    path: Path,
    text: str,
    resolve: Resolver,
    labelled: Labeller,
    *,
    pull: int | None = None,
) -> list[str]:
    """Check the work each decision and each Verification row of a ledger cites.

    Parameters
    ----------
    path : Path
        The specification, to locate each fault.
    text : str
        The specification.
    resolve : Resolver
        Look up the work at a repository and number.
    labelled : Labeller
        Read the label events of a pull request.
    pull : int, optional
        The number of the pull request being checked, which may not have merged.

    Returns
    -------
    list of str
        One message per fault, as ``path:line: message``.

    """
    problems = []

    def current(reference: Reference) -> bool:
        return reference.repository == REPOSITORY and reference.number == pull

    def pulled(evidence: str) -> Iterator[tuple[Reference, Work | None]]:
        for reference in references(evidence):
            yield reference, resolve(reference.repository, reference.number)

    def found(reference: Reference, work: Work | None) -> str | None:
        if work is None:
            return f"{reference.text} does not exist"
        if work.kind != "pull":
            return f"{reference.text} is an issue"
        return None

    for decision in conventions.decisions(text):
        faults = []
        for reference, work in pulled(decision.carried):
            if (fault := found(reference, work)) is not None:
                faults.append(fault)
            elif work.state != "merged" and not current(reference):
                faults.append(f"{reference.text} has not merged")
        at = conventions.where(path, decision.line)
        problems += [f"{at}: {fault}" for fault in faults]

    for row in conventions.ledger(text) or []:
        state, rest = conventions.opened(row.status)
        evidence = conventions.carried(rest)
        written = conventions.DATE.search(evidence)
        when = None if written is None else conventions.dated(written[0])
        faults = []
        for reference, work in pulled(evidence):
            if (fault := found(reference, work)) is not None:
                faults.append(fault)
            elif state == conventions.SIGNED_OFF:
                faults += _signed(
                    evidence, reference, labelled, when, current(reference)
                )
            elif state in (conventions.VERIFIED, conventions.LEDGER_RETIRED):
                if current(reference):
                    continue
                said = "verified" if state == conventions.VERIFIED else "retired"
                if work.state != "merged":
                    faults.append(f"{reference.text} has not merged")
                elif when and work.when and abs((when - work.when).days) > 1:
                    faults.append(
                        f"{said} on {when}, but {reference.text} merged on {work.when}"
                    )
        at = conventions.where(path, row.line)
        problems += [f"{at}: {fault}" for fault in faults]
    return problems


def _signed(
    evidence: str,
    reference: Reference,
    labelled: Labeller,
    when: date | None,
    pending: bool,
) -> list[str]:
    """Check that the reviewer a sign-off names put the label on its pull request."""
    named = REVIEWER.search(evidence)
    reviewer = named["login"] if named else "no reviewer"
    events = [
        event
        for event in labelled(reference.repository, reference.number)
        if event.label == SIGN_OFF
    ]
    if not events or events[-1].action != "labeled":
        return [f"{reference.text} carries no {SIGN_OFF} label"]
    last = events[-1]
    if last.login != reviewer:
        added = last.login or "no one"
        said = f"the {SIGN_OFF} label on {reference.text} was added by {added}"
        return [f"{said}, not {reviewer}"]
    if when is not None and not pending and abs((when - last.when).days) > 1:
        return [f"signed off on {when}, but the label was added on {last.when}"]
    return []


def _headers(token: str | None) -> dict[str, str]:
    """Return the headers of a GitHub REST API request."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "geovista-check-status-references",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def labeller(token: str | None = None) -> Labeller:
    """Return a labeller that reads a pull request's events, every page, cached.

    Parameters
    ----------
    token : str, optional
        A GitHub token, which raises the rate limit.

    Returns
    -------
    Labeller
        The labeller.

    """
    headers = _headers(token)
    cache: dict[tuple[str, int], list[Labelling]] = {}

    def labelled(repository: str, number: int) -> list[Labelling]:
        key = (repository, number)
        if key not in cache:
            events: list[Labelling] = []
            url: str | None = (
                f"{API}/repos/{repository}/issues/{number}/events?per_page=100"
            )
            while url:
                request = urllib.request.Request(url, headers=headers)  # noqa: S310
                with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                    page = json.load(response)
                    following = NEXT.search(response.headers.get("Link") or "")
                for event in page:
                    if event.get("event") not in ("labeled", "unlabeled"):
                        continue
                    # a deleted account leaves its events behind, with no actor
                    actor = event.get("actor") or {}
                    events.append(
                        Labelling(
                            event["event"],
                            event["label"]["name"],
                            actor.get("login"),
                            datetime.fromisoformat(event["created_at"]).date(),
                        )
                    )
                url = following["url"] if following else None
            cache[key] = events
        return cache[key]

    return labelled


def github(token: str | None = None) -> Resolver:
    """Return a resolver that asks the GitHub REST API, caching each answer.

    Parameters
    ----------
    token : str, optional
        A GitHub token, which raises the rate limit.

    Returns
    -------
    Resolver
        The resolver.

    """
    headers = _headers(token)
    cache: dict[tuple[str, int], Work | None] = {}

    def when(stamp: str | None) -> date | None:
        return None if stamp is None else datetime.fromisoformat(stamp).date()

    def resolve(repository: str, number: int) -> Work | None:
        key = (repository, number)
        if key not in cache:
            url = f"{API}/repos/{repository}/issues/{number}"
            request = urllib.request.Request(url, headers=headers)  # noqa: S310
            try:
                with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                    found = json.load(response)
            except urllib.error.HTTPError as error:
                if error.code not in (404, 410):
                    raise
                cache[key] = None
            else:
                # the issues endpoint serves pull requests too, with their merge
                if (pull := found.get("pull_request")) is not None:
                    merged = pull.get("merged_at")
                    state = "merged" if merged else found["state"]
                    cache[key] = Work("pull", state, when(merged or found["closed_at"]))
                else:
                    cache[key] = Work("issue", found["state"], when(found["closed_at"]))
        return cache[key]

    return resolve


def main(
    argv: list[str] | None = None,
    resolve: Resolver | None = None,
    labelled: Labeller | None = None,
) -> int:
    """Check every specification, printing each fault.

    Parameters
    ----------
    argv : list of str, optional
        The command line arguments. Defaults to those of the process.
    resolve : Resolver, optional
        Look up the work at a repository and number. Defaults to asking GitHub.
    labelled : Labeller, optional
        Read the label events of a pull request. Defaults to asking GitHub.

    Returns
    -------
    int
        Zero when every status holds, and one when any does not. Two when the
        checking could not be finished, as when GitHub is unreachable or rate
        limited, so that a failure of the check is never taken for a finding.

    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--pull",
        type=int,
        help="the pull request being checked, which a status may cite while open",
    )
    parser.add_argument(
        "--drift",
        action="store_true",
        help="also report a non-terminal status whose work has moved on",
    )
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if resolve is None:
        resolve = github(token)
    if labelled is None:
        labelled = labeller(token)
    specifications = conventions.specifications()

    try:
        problems = []
        for path in specifications:
            text = path.read_text(encoding="utf-8")
            problems += check(path, text, resolve, pull=args.pull, drift=args.drift)
            problems += check_ledger(path, text, resolve, labelled, pull=args.pull)
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"could not ask GitHub: {error}", file=sys.stderr)
        if isinstance(error, urllib.error.HTTPError) and error.code in (403, 429):
            print(
                "set GITHUB_TOKEN or GH_TOKEN to raise the rate limit, e.g. "
                'GH_TOKEN="$(gh auth token)"',
                file=sys.stderr,
            )
        return 2
    except Exception:  # noqa: BLE001
        # the nightly workflow opens an issue on one, so anything unexpected
        # must leave by another door
        traceback.print_exc()
        print("could not finish checking", file=sys.stderr)
        return 2

    for problem in problems:
        print(problem)

    if problems:
        print(breadcrumb.breadcrumb(CHECK))

    texts = [path.read_text(encoding="utf-8") for path in specifications]
    count = sum(len(cited(text)) + len(ledger_cited(text)) for text in texts)
    verdict = f"{len(problems)} fault(s)" if problems else "all hold"
    print(
        f"checked {count} reference(s) across {len(specifications)} "
        f"specification(s): {verdict}",
        file=sys.stderr,
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
