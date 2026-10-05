# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests for the assets a built page loads.

An extension that defaults its asset URLs to a content delivery network makes
every reader of every page fetch them, and announces it nowhere. The URL is
written into the page as it is read, so no build log carries it and no build
fails when the host is unreachable - the page simply arrives without whatever
the asset was doing. Three such dependencies have been closed one at a time,
each found by hand and after the fact: the intersphinx inventories gained
vendored fallbacks in #2538, ``sphinx-tippy`` had its runtime vendored in
#2549, and ``sphinx-iconify`` was dropped for committed SVGs in #2559.

This is the standing check that a fourth cannot arrive unremarked. It covers
scripts and stylesheets, the assets a browser executes or blocks rendering on.
Content images are deliberately out of scope: the project badges and the
contributor avatars are remote by intent, and an image that fails to load costs
its alternative text rather than the page.

The companion check is of the source tree, because vendoring an asset is also
distributing it. It needs no build and so never skips.

"""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urlsplit

import pytest

#: The documentation source, carrying the vendored assets.
DOCS = Path(__file__).parents[2] / "docs" / "src"

#: The tree holding the inline icons, each beside its upstream notice.
ICONS = DOCS / "_static" / "icons"

#: The suffix of the file carrying the upstream notice of a vendored asset,
#: the convention "pydata-sphinx-theme" ships for the bundles it vendors.
NOTICE_SUFFIX = ".LICENSE.txt"

#: The line of a notice naming who is to be credited. A minified bundle carries
#: at most a one-line banner naming the licence, which is not that notice.
COPYRIGHT = re.compile(r"copyright\b", re.IGNORECASE)

#: The tags that fetch an asset, and the attribute naming it in each.
SOURCE = {"link": "href", "script": "src"}

#: The "<link>" relationships that fetch an asset for the page itself. Named as
#: an allowlist rather than an exclusion, so that "canonical" - which sphinx
#: emits as an absolute URL from "html_baseurl", and must - is out of scope by
#: construction along with any relationship a future theme invents. "rel" holds
#: a whitespace-separated token list, so one token matching is a match.
RENDERING = frozenset({"modulepreload", "preload", "prefetch", "stylesheet"})


class _Assets(HTMLParser):
    """Collect the off-site scripts and stylesheets of the markup fed to it.

    Reading the tags with the standard-library parser rather than a pattern is
    what makes the audit indifferent to how sphinx, the theme or an extension
    happened to write them. Single-quoted, unquoted and self-closing shapes are
    all one thing to it, as is the order the attributes come in, and it honours
    the CDATA rule for "<script>" content - where a pattern matches a tag named
    inside a string literal. Every one of those is a way for an off-site asset
    to enter the build unseen by a gate that exists to see it.

    Attributes
    ----------
    found : list of str
        The URL of each off-site asset, in the order the markup loads them.

    """

    def __init__(self) -> None:
        super().__init__()
        self.found: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record the tag if it fetches an asset from another host.

        Parameters
        ----------
        tag : str
            The name of the tag, lowercased by the parser.
        attrs : list of tuple
            The attributes of the tag, each name lowercased by the parser and
            each value unquoted and unescaped by it. A value is ``None`` for an
            attribute given without one.

        Notes
        -----
        A self-closing tag arrives here too, the inherited
        ``handle_startendtag`` delegating to this method.

        """
        if (attribute := SOURCE.get(tag)) is None:
            return

        values = {name: value or "" for name, value in attrs}

        if tag == "link" and not RENDERING & set(values.get("rel", "").lower().split()):
            return

        url = values.get(attribute, "")
        parts = urlsplit(url)

        if parts.scheme or parts.netloc:
            self.found.append(url)


def _remote(page: Path) -> list[str]:
    """Collect the off-site scripts and stylesheets a page loads.

    Parameters
    ----------
    page : Path
        The built page to read.

    Returns
    -------
    list of str
        The URL of each off-site asset, in the order the page loads them.

    """
    parser = _Assets()
    parser.feed(page.read_text(encoding="utf-8", errors="replace"))
    parser.close()

    return parser.found


#: The shapes an off-site asset can arrive in, each with what the audit must
#: make of it. How an attribute is quoted, how many tokens its "rel" carries
#: and what order the attributes come in are all the author's choice, of no
#: consequence to a browser and invisible in the rendered page - so an audit
#: that reads one shape of each is one an extension walks past without anybody
#: having written anything wrong.
SHAPES = {
    "script": ('<script src="https://x.example/run.js"></script>', 1),
    "script-single-quoted": ("<script src='https://x.example/run.js'></script>", 1),
    "script-unquoted": ("<script src=https://x.example/run.js></script>", 1),
    "script-protocol-relative": ('<script src="//x.example/run.js"></script>', 1),
    "script-vendored": ('<script src="_static/js/run.js"></script>', 0),
    "script-inline": (
        """<script>var t = '<link rel="stylesheet" href="https://x.example">';</script>""",
        0,
    ),
    "stylesheet": ('<link rel="stylesheet" href="https://x.example/t.css">', 1),
    "stylesheet-many-tokens": (
        '<link rel="alternate stylesheet" href="https://x.example/t.css" title="Alt">',
        1,
    ),
    "stylesheet-self-closing": (
        '<link rel="stylesheet" href="https://x.example/t.css" />',
        1,
    ),
    "stylesheet-reordered": (
        '<link href="https://x.example/t.css" rel="stylesheet">',
        1,
    ),
    "stylesheet-vendored": ('<link rel="stylesheet" href="_static/styles/t.css">', 0),
    "canonical": (
        '<link rel="canonical" href="https://geovista.readthedocs.io/en/latest/">',
        0,
    ),
}


@pytest.mark.parametrize(("markup", "expected"), SHAPES.values(), ids=list(SHAPES))
def test_remote_reads_every_shape(tmp_path, markup, expected):
    """Find an off-site asset however the page happens to spell it.

    The audit is only as good as the markup it can read, and an asset missed
    for the quoting of its attribute is missed as thoroughly as one nobody
    looked for. The negative cases matter equally: an audit that cried off at
    a vendored path, a canonical link or a tag named inside an inline script
    would be turned off long before it ever caught anything.

    """
    page = tmp_path / "page.html"
    page.write_text(markup, encoding="utf-8")

    assert len(_remote(page)) == expected


def test_pages_load_no_off_site_assets(html_root):
    """Serve every script and stylesheet from the build rather than a third party.

    A reader of these pages should need this site and nothing else. An asset
    fetched from elsewhere is a host that can be slow, blocked, or simply gone,
    taking with it whatever the page relied on it for - and a build that cannot
    tell, having never fetched it.

    """
    pages = sorted(html_root.rglob("*.html"))

    assert pages, f"no built pages under {html_root}"

    offenders = {
        str(page.relative_to(html_root)): remote
        for page in pages
        if (remote := _remote(page))
    }

    assert not offenders, (
        f"{len(offenders)} of {len(pages)} pages load off-site assets: {offenders}"
    )


def test_vendored_icons_carry_a_notice():
    """Publish the upstream notice of every vendored icon alongside it.

    Vendoring an icon is also distributing it, so its licence travels with it.
    Three of the four are ``MIT`` and the fourth is ``CC BY 4.0``, and all four
    require the credit be given, which an SVG has nowhere to carry itself.

    Holding the icons under "_static" rather than beside the page is what
    publishes these notices: sphinx copies that tree wholesale, where the copy
    ``docutils`` makes under "_images" for the page to reference would leave
    them behind.

    """
    icons = sorted(ICONS.glob("*.svg"))

    assert icons, f"no vendored icons under {ICONS}"

    for icon in icons:
        notice = icon.with_name(f"{icon.name}{NOTICE_SUFFIX}")

        assert notice.is_file(), f"{icon.name} has no published {notice.name}"
        assert COPYRIGHT.search(notice.read_text(encoding="utf-8")), (
            f"{notice.name} carries no copyright line"
        )
