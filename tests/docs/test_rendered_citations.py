# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that every citation the documentation renders became a working link.

The transform of ``docs/src/_ext/geovista_citation_xrefs.py`` links citations as
the build reads them, and the conventions test checks the source. Neither can see
the other's failure: the source check cannot tell whether the transform ran, and
the transform cannot tell a page it never saw. So the built HTML is read too. This
is a port of ``tephpy``'s rendered-citation gate.

It finds citations with a pattern looser than the grammar, a section sign and a
number, and shares no code with it. A check that asked the grammar what to look
for would go blind in the same moment the grammar did. It also resolves each
link, so a citation that links to an anchor no page holds fails here.

The checks of a tree run on small pages written here, and on the real build
through ``html_root``, which skips without one, and fails under
``--browser-strict``. This module sits inside the corpus the citation grammar
governs, so it builds the section sign rather than write it.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache
from html.parser import HTMLParser
import re
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlsplit

if TYPE_CHECKING:
    from pathlib import Path

#: The section sign, built rather than written: see the module docstring.
SECTION = "\N{SECTION SIGN}"

#: A section sign and a number, looser than a citation on purpose.
CITATION = re.compile(rf"{SECTION}\s*\d+(?:\.\d+)*")

#: Text inside these is never linked, by design.
EXEMPT = frozenset({"code", "pre", "script", "style"})

#: ``viewcode`` renders verbatim source, whose section signs are Python, not prose.
SKIP_PAGES = ("_modules/",)

#: Elements that never close, so are never pushed onto the stack.
VOID = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta"}
    | {"source", "track", "wbr"}
)

#: Ancestors that say where an unlinked citation sat, outermost first. They decide
#: what a failure says, never whether it fails.
PLACEMENT = ("title", "nav", "dt")

#: How each placement is named, and what to do about it.
ADVICE = {
    "title": "a page title, which the browser tab copies without its link: "
    "cite the section in the prose under the heading instead",
    "nav": "navigation, which repeats a heading or a toctree caption without its "
    "markup: cite the section in the prose of the page that owns it",
    "dt": "an API signature, which the transform never rewrites: cite the section "
    "in the docstring's prose instead",
    "": "body text, where a citation the transform did not link comes out: check "
    "that 'geovista_citation_xrefs' is in conf.py's extensions, that the grammar "
    "reads the citation, and that it is not in a raw block or a toctree caption",
}

#: How many citations of one placement on one page to name before counting them.
SHOWN = 4


class Scan(HTMLParser):
    """Collect every citation in one page, by where it sits, and every ``id``."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, str | None]] = []
        self.linked: list[tuple[str, str]] = []
        self.bare: list[tuple[str, str]] = []
        self.nested: list[str] = []
        self.exempt = 0
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Push ``tag``, with its ``href`` if it is a link, unless it is void."""
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        if tag not in VOID:
            self.stack.append((tag, values.get("href") if tag == "a" else None))

    def handle_startendtag(
        self, _tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        """Record a self-closing tag's ``id``; it encloses nothing."""
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])

    def handle_endtag(self, tag: str) -> None:
        """Pop back to ``tag``, tolerating elements left unclosed."""
        if any(name == tag for name, _ in self.stack):
            while self.stack and self.stack.pop()[0] != tag:
                pass

    def handle_data(self, data: str) -> None:
        """Classify each citation in a run of text."""
        hits = CITATION.findall(data)
        if not hits:
            return
        tags = [name for name, _ in self.stack]
        links = [href for name, href in self.stack if name == "a"]
        if any(name in EXEMPT for name in tags):
            self.exempt += len(hits)
        elif len(links) > 1:
            self.nested.extend(hits)
        elif links:
            self.linked.extend((hit, links[0] or "") for hit in hits)
        else:
            where = next((name for name in PLACEMENT if name in tags), "")
            self.bare.extend((hit, where) for hit in hits)


@cache
def scanned(page: Path) -> Scan:
    """Scan a page once, however many links land on it."""
    scan = Scan()
    scan.feed(page.read_text(encoding="utf-8"))
    return scan


@dataclass
class Report:
    """What a tree of pages holds, by kind of citation."""

    pages: int = 0
    linked: int = 0
    exempt: int = 0
    bare: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    nested: dict[str, list[str]] = field(default_factory=dict)
    broken: dict[str, list[str]] = field(default_factory=dict)


def landing(root: Path, page: Path, href: str) -> str | None:
    """Say why a local link from ``page`` lands nowhere, or ``None`` if it lands."""
    parts = urlsplit(href)
    if parts.scheme or parts.netloc:
        return None
    target = (page.parent / unquote(parts.path)).resolve() if parts.path else page
    if not target.is_file():
        return f"{href} names no page"
    if parts.fragment and unquote(parts.fragment) not in scanned(target).ids:
        return f"{href} names no anchor on {target.relative_to(root).as_posix()}"
    return None


def check(root: Path) -> Report:
    """Read every page under ``root``, less the ``viewcode`` listings."""
    report = Report()
    for page in sorted(root.rglob("*.html")):
        relative = page.relative_to(root).as_posix()
        if relative.startswith(SKIP_PAGES):
            continue
        report.pages += 1
        scan = scanned(page)
        report.linked += len(scan.linked)
        report.exempt += scan.exempt
        if scan.bare:
            report.bare[relative] = scan.bare
        if scan.nested:
            report.nested[relative] = scan.nested
        broken = [
            f"{hit} -> {why}"
            for hit, href in scan.linked
            if (why := landing(root, page, href)) is not None
        ]
        if broken:
            report.broken[relative] = broken
    return report


def listed(hits: list[str]) -> str:
    """Name the first few citations, and say how many are not named."""
    rest = len(hits) - SHOWN
    listing = ", ".join(hits[:SHOWN])
    return f"{listing} and {rest} more" if rest > 0 else listing


def unlinked(report: Report) -> str:
    """Describe each page's bare citations by placement, with what to do."""
    lines, seen = [], []
    for relative, hits in sorted(report.bare.items()):
        grouped: dict[str, list[str]] = {}
        for hit, where in hits:
            grouped.setdefault(where, []).append(hit)
        for where, found in grouped.items():
            lines.append(f"  {relative}: {listed(found)}")
            seen.append(where)
    advice = [f"In {ADVICE[where]}." for where in dict.fromkeys(seen)]
    return "\n".join(["Unlinked citations:", *lines, *advice])


def page(tmp_path: Path, name: str, body: str) -> Path:
    """Write a page of ``body`` under ``tmp_path``."""
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"<html><body>{body}</body></html>", encoding="utf-8")
    return path


def scan(html: str) -> Scan:
    """Scan one string of HTML."""
    found = Scan()
    found.feed(html)
    return found


CITED = f"typing spec {SECTION}3.2"


def test_a_citation_inside_a_link_is_linked():
    """The transform's output, and the case every other test departs from."""
    found = scan(f'<p><a href="x.html#typing-spec-3-2">{CITED}</a></p>')

    assert found.linked == [(f"{SECTION}3.2", "x.html#typing-spec-3-2")]
    assert found.bare == []


def test_every_citation_in_one_run_of_text_is_counted():
    """A run of two is two citations, linked or not."""
    found = scan(f"<p>{CITED}, {SECTION}4</p>")

    assert [hit for hit, _ in found.bare] == [f"{SECTION}3.2", f"{SECTION}4"]


def test_a_citation_inside_a_literal_is_exempt_at_any_depth():
    """An example quoted as code stays an example."""
    found = scan(f"<pre><span><em>{CITED}</em></span></pre><code>{CITED}</code>")

    assert found.exempt == 2
    assert found.bare == []


def test_a_section_sign_without_a_number_is_no_citation():
    """The pattern is loose, but not so loose as a bare sign."""
    assert scan(f"<p>{SECTION} and {SECTION}x</p>").bare == []


def test_a_bare_citation_is_placed_by_its_outermost_ancestor():
    """The placement decides the advice, never whether it fails."""
    found = scan(
        f"<title>{CITED}</title><nav><dt>{CITED}</dt></nav><dl><dt>{CITED}</dt></dl>"
        f"<p>{CITED}</p>"
    )

    assert [where for _, where in found.bare] == ["title", "nav", "dt", ""]


def test_a_citation_nested_in_two_links_is_reported():
    """Two anchors around one citation is invalid HTML a browser restructures."""
    found = scan(f'<a href="#a"><a href="#b">{CITED}</a></a>')

    assert found.nested == [f"{SECTION}3.2"]
    assert found.linked == []


def test_an_unclosed_element_and_a_stray_end_tag_do_not_corrupt_the_stack():
    """An end tag pops back past anything left open; one never opened is ignored."""
    found = scan(f"<div><p><span>x</div></i><p>{CITED}</p>")

    assert [where for _, where in found.bare] == [""]
    assert found.stack == []


def test_a_void_element_is_never_pushed_and_its_id_is_kept():
    """A void element encloses nothing, but can still be a link's landing."""
    found = scan(f'<br id="here"><img src="x.png"/><p>{CITED}</p>')

    assert "here" in found.ids
    assert [where for _, where in found.bare] == [""]


def test_a_tree_whose_citations_link_and_land_passes(tmp_path):
    """The whole check, on a tree it should pass."""
    page(tmp_path, "specs/typing.html", '<h2 id="typing-spec-3-2">3.2</h2>')
    page(
        tmp_path,
        "guide.html",
        f'<a href="specs/typing.html#typing-spec-3-2">{CITED}</a>',
    )

    report = check(tmp_path)

    assert (report.pages, report.linked) == (2, 1)
    assert report.bare == report.nested == report.broken == {}


def test_a_link_to_an_anchor_no_page_holds_is_broken(tmp_path):
    """A citation that links somewhere that is not there is no better than plain."""
    page(tmp_path, "specs/typing.html", '<h2 id="typing-spec-3-1">3.1</h2>')
    page(
        tmp_path,
        "guide.html",
        f'<a href="specs/typing.html#typing-spec-3-2">{CITED}</a>',
    )
    page(
        tmp_path, "other.html", f'<a href="specs/gone.html#typing-spec-3-2">{CITED}</a>'
    )

    report = check(tmp_path)

    assert list(report.broken) == ["guide.html", "other.html"]
    assert "no anchor" in report.broken["guide.html"][0]
    assert "no page" in report.broken["other.html"][0]


def test_an_external_link_is_not_followed(tmp_path):
    """An author's own link to another site is theirs to keep working."""
    page(tmp_path, "guide.html", f'<a href="https://example.com/#x">{CITED}</a>')

    assert check(tmp_path).broken == {}


def test_viewcode_listings_are_not_read(tmp_path):
    """Their section signs are Python source, quoted verbatim."""
    page(tmp_path, "_modules/geovista/crs.html", f"<p>{CITED}</p>")

    report = check(tmp_path)

    assert (report.pages, report.bare) == (0, {})


def test_the_report_names_each_page_and_advises_once_per_placement(tmp_path):
    """A failure says where each citation sat and what to do there."""
    page(tmp_path, "a.html", f"<p>{CITED}</p>" * 6)
    page(tmp_path, "b.html", f"<p>{CITED}</p><title>{CITED}</title>")

    text = unlinked(check(tmp_path))

    assert f"a.html: {', '.join([f'{SECTION}3.2'] * 4)} and 2 more" in text
    assert text.count("In body text") == 1
    assert text.count("In a page title") == 1


def test_every_rendered_citation_is_a_link(html_root):
    """No citation reaches a reader of the built documentation as plain text."""
    report = check(html_root)

    assert not report.bare, unlinked(report)
    assert not report.nested, f"Citations nested in two links: {report.nested}"


def test_every_citation_link_lands_on_an_anchor_that_exists(html_root):
    """A link to a section that is not there misleads more than plain text."""
    assert not check(html_root).broken


def test_the_build_links_some_citation(html_root):
    """A transform that stopped running would leave the checks above nothing."""
    report = check(html_root)

    assert report.pages, f"no pages under {html_root}"
    assert report.linked, (
        f"no citation became a link across {report.pages} pages: is "
        "'geovista_citation_xrefs' in conf.py's extensions?"
    )
