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

from pathlib import Path
import re

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

#: A "<script>" or "<link>" opening tag, in whichever attribute order sphinx,
#: the theme or an extension happened to write it.
TAG = re.compile(r"<(script|link)\b([^>]*)>", re.IGNORECASE)

#: A double-quoted attribute within such a tag.
ATTR = re.compile(r'\b([a-z-]+)\s*=\s*"([^"]*)"', re.IGNORECASE)

#: The "<link>" relationships that fetch an asset for the page itself. Named as
#: an allowlist rather than an exclusion, so that "canonical" - which sphinx
#: emits as an absolute URL from "html_baseurl", and must - is out of scope by
#: construction along with any relationship a future theme invents.
RENDERING = frozenset({"modulepreload", "preload", "prefetch", "stylesheet"})

#: A URL naming a host rather than a path within the build.
ABSOLUTE = re.compile(r"^[a-z][a-z0-9+.-]*:|^//", re.IGNORECASE)


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
    html = page.read_text(encoding="utf-8", errors="replace")
    found = []

    for tag, body in TAG.findall(html):
        attrs = {key.lower(): value for key, value in ATTR.findall(body)}

        if tag.lower() == "script":
            url = attrs.get("src", "")
        elif attrs.get("rel", "").lower() in RENDERING:
            url = attrs.get("href", "")
        else:
            continue

        if url and ABSOLUTE.match(url):
            found.append(url)

    return found


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
