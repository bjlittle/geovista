# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests of the summary line the build writes under each Verification table.

The extension is ``docs/src/_ext/geovista_ledger.py``, loaded here by path as the
citation transform's tests load theirs. This module sits inside the corpus the
citation grammar governs, so it builds its emojis rather than write them.

"""

from __future__ import annotations

from html.parser import HTMLParser
import importlib.util
import io
from pathlib import Path
import re
import sys
import textwrap
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType
    from typing import NoReturn

#: The extensions, which import one another by bare name, as a build does.
EXT = Path(__file__).parents[2] / "docs" / "src" / "_ext"

#: The states of ledger spec §3.4, built by name: see the module docstring.
PENDING = "\N{HOURGLASS WITH FLOWING SAND} pending"
VERIFIED = "\N{WHITE HEAVY CHECK MARK} verified"
SIGNED_OFF = "\N{WRITING HAND}\N{VARIATION SELECTOR-16} signed off"
RETIRED = "\N{FILE CABINET}\N{VARIATION SELECTOR-16} retired"
SECTION = "\N{SECTION SIGN}"


@pytest.fixture(scope="module")
def ledger(require: Callable[[str], NoReturn]) -> ModuleType:
    """Load the extension by path, or skip without sphinx."""
    try:
        import sphinx  # noqa: F401, PLC0415
    except ImportError:
        require("sphinx is not installed")
    sys.path.insert(0, str(EXT))
    try:
        spec = importlib.util.spec_from_file_location(
            "geovista_ledger", EXT / "geovista_ledger.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(EXT))
    return module


def test_summary_counts_each_state(ledger):
    """The line the build writes for ledger spec §2 decision 5 counts every state."""
    statuses = [VERIFIED, VERIFIED, VERIFIED, PENDING, RETIRED, SIGNED_OFF]

    assert ledger.summary(statuses) == (
        f"{VERIFIED[0]} 3 · {SIGNED_OFF[:2]} 1 · {PENDING[0]} 1 · {RETIRED[:2]} 1: "
        "4 of 5 decisions in force verified"
    )


def test_summary_reads_a_status_with_its_parenthetical(ledger):
    """A status carries its date and pull request, which the count reads past."""
    assert ledger.summary([f"{VERIFIED} (2026-10-30, {{pull}}`1`)"]).endswith(
        "1 of 1 decisions in force verified"
    )


def test_summary_reads_a_state_without_its_variation_selector(ledger):
    """A retirement typed without U+FE0F still counts as one."""
    summary = ledger.summary(["\N{FILE CABINET} retired", PENDING])

    assert summary.endswith("0 of 1 decisions in force verified")


#: The configuration of the end-to-end build.
CONF = """
extensions = ["geovista_ledger", "myst_parser"]
suppress_warnings = ["app"]
"""

#: A specification with a ledger of two decisions, one verified.
SPEC = f"""# Demo

(demo-spec-1)=
## 1. Verification

| Decision | Row | Status | Evidence |
|---|---|---|---|
| {SECTION}2 decision 1 | row 1 of {SECTION}9 | {VERIFIED} (2026-10-30, 1) | `x.py` |
| {SECTION}2 decision 2 | row 2 of {SECTION}9 | {PENDING} | |

After the table.
"""


def build(src: Path, out: Path, status: io.StringIO | None = None) -> tuple[Path, str]:
    """Build ``src``, returning its HTML and its warnings, and writing its status."""
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
            status=status,
            warning=warning,
        )
        app.build()
    return out / "html", warning.getvalue()


@pytest.mark.usefixtures("ledger")
def test_a_build_writes_the_summary_under_the_table(tmp_path):
    """The summary follows the table, so nobody keeps it up to date by hand."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "conf.py").write_text(CONF, encoding="utf-8")
    (src / "spec.md").write_text(SPEC, encoding="utf-8")
    toctree = textwrap.indent("spec", " " * 3)
    (src / "index.rst").write_text(f"Index\n=====\n\n.. toctree::\n\n{toctree}\n")

    html, warning = build(src, tmp_path)
    page = (html / "spec.html").read_text(encoding="utf-8")

    assert warning == ""
    table_end = page.index("</table>")
    summary = page.index("1 of 2 decisions in force verified")
    assert table_end < summary < page.index("After the table.")
    assert 'class="ledger-summary"' in page


def test_the_extension_builds_its_emoji_by_name():
    """The module sits in the corpus it serves, so writes no emoji literally (#2787)."""
    source = (EXT / "geovista_ledger.py").read_text(encoding="utf-8")

    assert not [char for char in source if ord(char) > 0x2000 and char != "·"]


#: The base the end-to-end build links evidence into.
BASE = "https://example.org/blob/abc/"

#: A specification whose ledger names evidence of every kind: a test citing its
#: decision, a test citing none, a path to no file, and a word.
EVIDENCED = f"""# Demo

- **Citation prefix:** `demo spec {SECTION}\N{HORIZONTAL ELLIPSIS}`

(demo-spec-1)=
## 1. Purpose

A demo.

(demo-spec-2)=
## 2. Decisions

1. **Agreed** - **One.** The first.
2. **Agreed** - **Two.** The second.
3. **Agreed** - **Three.** The third.
4. **Agreed** - **Four.** The fourth.

(demo-spec-3)=
## 3. Verification

| Decision | Row | Status | Evidence |
|---|---|---|---|
| {SECTION}2 decision 1 | `row 1` | {VERIFIED} (2026-11-08, 1) | `tests/test_demo.py` |
| {SECTION}2 decision 2 | `row 1` | {VERIFIED} (2026-11-08, 1) | `tests/test_silent.py`|
| {SECTION}2 decision 3 | `row 2` | {PENDING} | `tests/test_gone.py` |
| {SECTION}2 decision 4 | `row 2` | {PENDING} | `candidate` |
"""

#: A test file whose fifth line cites decision 1 of the demo specification.
CITING = f'''"""A demo test."""


def test_one():
    """Holds demo spec {SECTION}2 decision 1."""
'''


def evidenced(tmp_path: Path, source: str | None = BASE) -> str:
    """Build a repository's documentation, returning the specification's page."""
    repo = tmp_path / "repo"
    src = repo / "docs" / "src"
    specs = src / "developer" / "specs"
    specs.mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "tests" / "test_demo.py").write_text(CITING, encoding="utf-8")
    (repo / "tests" / "test_silent.py").write_text('"""Cites nothing."""\n')
    conf = CONF + f"geovista_ledger_root = {str(repo)!r}\n"
    if source is not None:
        conf += f"geovista_ledger_source = {source!r}\n"
    (src / "conf.py").write_text(conf, encoding="utf-8")
    (specs / "2026-01-01-demo-design.md").write_text(EVIDENCED, encoding="utf-8")
    toctree = textwrap.indent("developer/specs/2026-01-01-demo-design", " " * 3)
    (src / "index.rst").write_text(f"Index\n=====\n\n.. toctree::\n\n{toctree}\n")

    html, warning = build(src, tmp_path / "out")
    assert warning == ""
    return (html / "developer" / "specs" / "2026-01-01-demo-design.html").read_text(
        encoding="utf-8"
    )


#: A specification with a decision in each state the line under it reads, and a
#: sixth decision with no Verification row.
OWNED = f"""# Demo

- **Citation prefix:** `demo spec {SECTION}\N{HORIZONTAL ELLIPSIS}`

(demo-spec-1)=
## 1. Purpose

A demo.

(demo-spec-2)=
## 2. Decisions

1. **Agreed** - **One.** The first.
2. **Agreed** - **Two.** The second.
3. **Agreed** - **Three.** The third.
4. **Retired** - **Four.** The fourth.
5. **Retired** - **Five.** The fifth.
6. **Agreed** - **Six.** The sixth.

(demo-spec-3)=
## 3. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | The first | \N{WHITE HEAVY CHECK MARK} landed (2026-11-08, 1) |
| 2 | The second | \N{CLIPBOARD} not started |

(demo-spec-4)=
## 4. Verification

| Decision | Row | Status | Evidence |
|---|---|---|---|
| {SECTION}2 decision 1 | row 1 of {SECTION}3 | {VERIFIED} (2026-11-08, 1) | `x.py` |
| {SECTION}2 decision 2 | row 1 of {SECTION}3 | {SIGNED_OFF} (2026-11-08, a, 1) | Seen.|
| {SECTION}2 decision 3 | row 2 of {SECTION}3 | {PENDING} | |
| {SECTION}2 decision 4 | row 1 of {SECTION}3 | {RETIRED} (2026-11-09, 2) | |
| {SECTION}2 decision 5 | | {RETIRED} (2026-11-09, 2) | |
"""


def owned_page(tmp_path: Path) -> str:
    """Build the owned specification with the citations linked, returning its page."""
    src = tmp_path / "src"
    specs = src / "developer" / "specs"
    specs.mkdir(parents=True)
    (src / "conf.py").write_text(
        'extensions = ["geovista_citation_xrefs", "geovista_ledger", "myst_parser"]\n'
        'suppress_warnings = ["app"]\n',
        encoding="utf-8",
    )
    (specs / "2026-01-01-demo-design.md").write_text(OWNED, encoding="utf-8")
    toctree = textwrap.indent("developer/specs/2026-01-01-demo-design", " " * 3)
    (src / "index.rst").write_text(f"Index\n=====\n\n.. toctree::\n\n{toctree}\n")

    html, warning = build(src, tmp_path / "out")
    assert warning == ""
    return (html / "developer" / "specs" / "2026-01-01-demo-design.html").read_text(
        encoding="utf-8"
    )


def owner_lines(page: str) -> list[tuple[str, list[str]]]:
    """Read each line naming a decision's owner: its text, and where it links."""
    found = []
    for line in re.findall(r'<p class="decision-owner">(.*?)</p>', page, re.DOTALL):
        text = " ".join(re.sub(r"<[^>]+>", "", line).split())
        found.append((text, re.findall(r'href="([^"]+)"', line)))
    return found


@pytest.mark.usefixtures("ledger")
def test_the_line_under_a_decision_names_its_owner(tmp_path):
    """Owner spec §2 decision 9: each decision's owner, named and linked under it.

    Delivered by, once verified or signed off, or retired with an owner; owned
    by, while pending (owner spec §4.5).
    """
    lines = owner_lines(owned_page(tmp_path))

    assert lines == [
        (f"Delivered by row 1 of {SECTION}3", ["#demo-spec-3-row-1"]),
        (f"Delivered by row 1 of {SECTION}3", ["#demo-spec-3-row-1"]),
        (f"Owned by row 2 of {SECTION}3", ["#demo-spec-3-row-2"]),
        (f"Delivered by row 1 of {SECTION}3", ["#demo-spec-3-row-1"]),
    ]


@pytest.mark.usefixtures("ledger")
def test_no_line_under_a_retired_decision_with_no_owner(tmp_path):
    """A decision retired undelivered names no owner: owner spec §2 decision 10."""
    page = owned_page(tmp_path)
    fifth = page[page.index("The fifth") : page.index("The sixth")]

    assert "decision-owner" not in fifth


@pytest.mark.usefixtures("ledger")
def test_no_line_under_a_decision_with_no_row(tmp_path):
    """A decision the Verification table does not yet name gets no line."""
    page = owned_page(tmp_path)
    sixth = page[page.index("The sixth") : page.index("3. Roadmap")]

    assert "decision-owner" not in sixth


def test_the_line_is_written_by_the_build_alone():
    """Nothing is written in a specification for the line (owner spec §4.5).

    The build reads it from the Row column, so a specification writing it by
    hand would show it twice, and could disagree with its table.
    """
    specs = sorted((EXT.parent / "developer" / "specs").glob("*-design.md"))
    # a line naming a row, as the build writes it; owner spec §4.5 describes the
    # line with "row N", which names none
    line = re.compile(r"\*\*(?:Delivered|Owned) by\*\* row [0-9]")
    written = [spec.name for spec in specs if line.search(spec.read_text("utf-8"))]

    assert specs
    assert not written


@pytest.mark.usefixtures("ledger")
def test_evidence_links_to_the_line_citing_its_decision(tmp_path):
    """A test named as evidence links to its citing line: ledger spec §2 decision 18."""
    page = evidenced(tmp_path)

    assert f'href="{BASE}tests/test_demo.py#L5"' in page


@pytest.mark.usefixtures("ledger")
def test_evidence_citing_no_decision_links_to_its_top(tmp_path):
    """A file that cites no decision still links, to its first line."""
    page = evidenced(tmp_path)

    assert f'href="{BASE}tests/test_silent.py"' in page


@pytest.mark.usefixtures("ledger")
def test_evidence_naming_no_file_is_left_as_written(tmp_path):
    """A path to no file, and a word, are not links."""
    page = evidenced(tmp_path)

    assert "test_gone.py" in page
    assert "candidate" in page
    assert "tests/test_gone.py#" not in page
    assert f'href="{BASE}candidate' not in page
    assert page.count(f'href="{BASE}') == 2


@pytest.mark.usefixtures("ledger")
def test_a_build_naming_no_source_links_no_evidence(tmp_path):
    """Without a source, the evidence is left as text."""
    page = evidenced(tmp_path, source=None)

    assert "tests/test_demo.py" in page
    assert BASE not in page


def rebuild(tmp_path: Path, old: str, new: str) -> tuple[str, str]:
    """Edit the configuration and build again into the same output.

    Returns the specification's page and the status of the second build, which
    names each document it read.
    """
    conf = tmp_path / "repo" / "docs" / "src" / "conf.py"
    conf.write_text(conf.read_text(encoding="utf-8").replace(old, new))
    status = io.StringIO()
    html, warning = build(conf.parent, tmp_path / "out", status)
    assert warning == ""
    page = html / "developer" / "specs" / "2026-01-01-demo-design.html"
    return page.read_text(encoding="utf-8"), status.getvalue()


@pytest.mark.usefixtures("ledger")
def test_a_new_source_relinks_the_specifications_alone(tmp_path):
    """A commit since the last build re-reads each specification, and no more.

    Links baked into an unchanged page would otherwise point at the commit an
    earlier build read, against ledger spec §2 decision 18 (Codex, #2902).
    """
    evidenced(tmp_path, source="https://example.org/blob/commit-a/")

    page, status = rebuild(tmp_path, "commit-a", "commit-b")

    assert "https://example.org/blob/commit-b/tests/test_demo.py#L5" in page
    assert "commit-a" not in page
    assert "0 added, 1 changed, 0 removed" in status


@pytest.mark.usefixtures("ledger")
def test_an_unchanged_source_reads_nothing_again(tmp_path):
    """A build where nothing changed re-reads no specification."""
    evidenced(tmp_path)

    page, status = rebuild(tmp_path, "", "")

    assert f"{BASE}tests/test_demo.py#L5" in page
    assert "0 added, 0 changed, 0 removed" in status


@pytest.mark.usefixtures("ledger")
def test_a_new_root_relinks_the_specifications(tmp_path):
    """Evidence read from another root takes that root's citing line."""
    evidenced(tmp_path)
    other = tmp_path / "other"
    (other / "tests").mkdir(parents=True)
    (other / "tests" / "test_demo.py").write_text("\n" + CITING, encoding="utf-8")
    (other / "tests" / "test_silent.py").write_text('"""Cites nothing."""\n')

    page, _ = rebuild(tmp_path, str(tmp_path / "repo"), str(other))

    assert f"{BASE}tests/test_demo.py#L6" in page


@pytest.mark.parametrize(
    ("environ", "expected"),
    [
        pytest.param(
            {"READTHEDOCS_VERSION_TYPE": "tag", "READTHEDOCS_GIT_IDENTIFIER": "v0.6.0"},
            "v0.6.0",
            id="release",
        ),
        pytest.param(
            {
                "READTHEDOCS_VERSION_TYPE": "branch",
                "READTHEDOCS_GIT_IDENTIFIER": "main",
            },
            "0123abc",
            id="latest",
        ),
        pytest.param(
            {
                "READTHEDOCS_VERSION_TYPE": "external",
                "READTHEDOCS_GIT_IDENTIFIER": "2902",
            },
            "0123abc",
            id="pull-request",
        ),
        pytest.param({}, "0123abc", id="local"),
    ],
)
def test_source_names_a_release_by_its_tag_and_else_its_commit(
    ledger, environ, expected
):
    """A release links into its tag, and every other build into its commit."""
    assert ledger.source(environ, "0123abc") == f"{ledger.BLOB}/{expected}/"


#: The header of a ledger's table, as the built page renders it, with its Row
#: column (owner spec §4.1), which owner spec §2 decision 2 adds.
LEDGER_HEADER = ["Decision", "Row", "Status", "Evidence"]


class Evidence(HTMLParser):
    """Read each piece of code in a ledger's Evidence column, with its link.

    Attributes
    ----------
    found : list of tuple
        Each code's text, and the destination of the link around it, if any.

    """

    def __init__(self) -> None:
        super().__init__()
        self.found: list[tuple[str, str | None]] = []
        self._header: list[str] = []
        self._column = -1
        self._ledger = False
        self._evidence = -1
        self._cell: str | None = None
        self._href: list[str | None] = []
        self._code: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track the table, its cells and the links and code inside them."""
        if tag == "table":
            self._header, self._ledger = [], False
        elif tag == "tr":
            self._column = -1
        elif tag in ("th", "td"):
            self._column += 1
            self._cell = ""
        elif tag == "a":
            self._href.append(dict(attrs).get("href"))
        elif tag == "code" and self._ledger and self._column == self._evidence:
            self._code = []

    def handle_endtag(self, tag: str) -> None:
        """Close what each end tag closes."""
        if tag == "th" and self._cell is not None:
            self._header.append(self._cell.strip())
            self._ledger = self._header == LEDGER_HEADER
            if self._ledger:
                self._evidence = self._header.index("Evidence")
            self._cell = None
        elif tag == "td":
            self._cell = None
        elif tag == "a" and self._href:
            self._href.pop()
        elif tag == "code" and self._code is not None:
            link = next((h for h in reversed(self._href) if h), None)
            self.found.append(("".join(self._code).strip(), link))
            self._code = None

    def handle_data(self, data: str) -> None:
        """Gather the text of a header cell or a piece of code."""
        if self._cell is not None:
            self._cell += data
        if self._code is not None:
            self._code.append(data)


def evidence(html: str) -> list[tuple[str, str | None]]:
    """Read each piece of code in a page's ledger Evidence, with its link."""
    parser = Evidence()
    parser.feed(html)
    parser.close()
    return parser.found


def test_evidence_is_read_from_the_ledger_alone():
    """Code in another table, or in another column, is not read as evidence."""
    html = (
        "<table><thead><tr><th>A</th><th>B</th><th>C</th></tr></thead><tbody>"
        "<tr><td>x</td><td>y</td><td><code>tests/test_a.py</code></td></tr>"
        "</tbody></table><table><thead><tr><th>Decision</th><th>Row</th>"
        "<th>Status</th><th>Evidence</th></tr></thead><tbody><tr><td>"
        "<code>tests/test_b.py</code></td><td><code>row 1</code></td><td>y</td>"
        '<td><a href="u#L3"><code><span>tests/test_c.py</span>'
        "</code></a> and <code>tests/test_d.py</code></td></tr></tbody></table>"
    )
    assert evidence(html) == [("tests/test_c.py", "u#L3"), ("tests/test_d.py", None)]


def test_every_test_named_as_evidence_links_to_its_citing_line(html_root):
    """On the real build, ledger spec §2 decision 18 links every verified test."""
    specs = sorted((html_root / "developer" / "specs").glob("*.html"))
    found = [
        (page.name, name, link)
        for page in specs
        for name, link in evidence(page.read_text(encoding="utf-8"))
        if name.startswith("tests/") and name.endswith(".py")
    ]
    unlinked = [
        f"{page}: {name}"
        for page, name, link in found
        if link is None
        or not link.startswith("https://github.com/bjlittle/geovista/blob/")
        or "#L" not in link
    ]

    assert found, "the build names no test as evidence"
    assert not unlinked, "evidence not linked to its citing line:\n" + "\n".join(
        unlinked
    )
