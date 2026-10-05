# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests for the documentation tooltips.

``sphinx-tippy`` is configured in two halves that fail in different ways, and
neither announces itself. ``tippy_skip_urls`` is applied when the tips are
collected, so whatever it fails to exclude is visible in the per-page payload
the extension writes under ``_static/tippy/``. ``tippy_skip_anchor_classes``,
by contrast, is applied at *runtime* by the emitted javascript, so a skipped
anchor still has a tip generated for it in that payload and merely never has
one attached - which only a browser can tell you.

Both halves are covered here. The payloads are read directly, and the two
behaviours a reader alone encounters are hovered.

A missing tooltip is not a broken page, so none of this fails a build. That is
exactly why it is worth asserting: the extension is dormant upstream, the
runtime is vendored rather than fetched, and every guard below was at some
point written in good faith and quietly matched nothing.

"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import TYPE_CHECKING, NamedTuple

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import NoReturn

#: The directory of the per-page javascript the extension writes, named in the
#: "src" of a script on every page it has tipped.
PAYLOAD = "_static/tippy/"

#: The pages sphinx builds without a source document behind them, which the
#: extension never sees and so can never tip: the general and module indices,
#: the search page, the "viewcode" sources, and the macro fragments of the
#: theme. Named rather than discovered, so that a page losing its tooltips
#: fails the checks below instead of dropping out of them.
UNTIPPABLE = re.compile(
    r"^(?:_modules|_static)/|^(?:genindex|py-modindex|search)\.html$"
)

#: The "src" of a script on a page.
SCRIPT = re.compile(r'<script\b[^>]*\bsrc="([^"]*)"')

#: A "src" naming a host rather than a path within the build.
ABSOLUTE = re.compile(r"^[a-z][a-z0-9+.-]*:|^//", re.IGNORECASE)

#: The sphinx cache-busting query, which is not part of the path it follows.
QUERY = re.compile(r"\?.*$")

#: The vendored tooltip runtime, which the extension would otherwise fetch from
#: a content delivery network on behalf of every reader of every page.
RUNTIME = re.compile(r"\b(popper|tippy-bundle)\b", re.IGNORECASE)

#: The bundles the runtime is split across, the positioning engine and tippy.
BUNDLES = 2

#: The suffix of the file carrying the upstream notice of a vendored bundle,
#: the convention "pydata-sphinx-theme" ships for the bundles it vendors.
NOTICE_SUFFIX = ".LICENSE.txt"

#: The notice an "MIT" licence requires to travel with every copy, which the
#: bare "MIT License" banner of a minified bundle does not satisfy.
NOTICE = re.compile(
    r"Copyright \(c\).*?above copyright notice and this permission notice",
    re.DOTALL,
)

#: The body of a page, which is "tippy_anchor_parent_selector" and so the only
#: part of one the extension attaches a tip within.
ARTICLE = re.compile(r'<article class="bd-article">(.*?)</article>', re.DOTALL)

#: The "href" of an anchor.
ANCHOR = re.compile(r'<a\b[^>]*\bhref="([^"]*)"')

#: The assignment of the tip map, which the extension writes on a line of its
#: own as JSON.
ASSIGNED = re.compile(r"^\s*selector_to_html\s*=\s*", re.MULTILINE)

#: The "href" a tip is keyed on. The remainder of the map is the wikipedia and
#: doi selectors, which this build has turned off.
SELECTOR = re.compile(r'a\[href="(.*)"\]$')

#: The assignment of the classes the emitted javascript refuses to attach a tip
#: to. Read from its own line rather than from the whole payload, as a copied
#: tip body can carry any of them in its markup.
SKIP_CLASSES = re.compile(r"^\s*skip_classes\s*=\s*(.*)$", re.MULTILINE)

#: A sphinx-gallery thumbnail, which carries a hover panel of its own in the
#: "tooltip" attribute of its container.
THUMBNAIL = re.compile(
    r'<div class="sphx-glr-thumbcontainer"\s+tooltip="[^"]*".*?'
    r'<div class="sphx-glr-thumbnail-title">.*?</div>',
    re.DOTALL,
)

#: The glossary, whose definitions are the tooltips most worth having.
GLOSSARY = "reference/glossary.html"

#: The directory of the sphinx-tags pages, each headed by the very badge that
#: links to it.
TAGS = "tags"

#: A page carrying enough glossary terms to hover one.
TERMS_PAGE = "quick_start.html"

#: A page carrying a sphinx-design card, whose body is covered by a stretched
#: anchor and so would raise the card's own tooltip from edge to edge.
CARD_PAGE = "tutorials/index.html"

#: The class sphinx-design stretches over a card body.
STRETCHED = "sd-stretched-link"

#: Every class the emitted javascript must refuse, the first and last of which
#: are the extension's own defaults and are dropped by naming any others.
GUARDS = ("headerlink", "sd-sphinx-override", STRETCHED)

#: The tooltip property that keeps a tip from being clicked into. The tips
#: carry bare fragment links copied from their source page, which resolve
#: against whichever page is showing the tip and so mostly lead nowhere.
INERT = "interactive: false"

#: The element tippy renders a tip into.
BOX = ".tippy-box"

#: The viewport of the browser tests, wide enough to lay the cards out in a row.
VIEWPORT = 1400

#: Milliseconds to wait for a tip to be raised, or to be sure none is coming.
PATIENCE = 2000

#: Measure the card a stretched anchor covers, and confirm the anchor is what
#: the pointer lands on at its centre. The anchor is zero-size and reaches the
#: card through an "::after" rule, so its own bounding rect says nothing at all
#: about what a reader is hovering.
PROBE = """(selector) => {
    const link = document.querySelector(selector);
    const href = link.getAttribute("href");
    const card = link.closest(".sd-card");
    card.scrollIntoView({block: "center"});
    const rect = card.getBoundingClientRect();
    const x = rect.x + rect.width / 2;
    const y = rect.y + rect.height / 2;
    return {
        x: x,
        y: y,
        href: href,
        attached: link._tippy !== undefined,
        covered: document.elementFromPoint(x, y) === link,
        generated: Object.hasOwn(selector_to_html, `a[href="${href}"]`),
    };
}"""


class Tips(NamedTuple):
    """The tooltips of a single built page.

    Attributes
    ----------
    page : str
        The path of the page, relative to the build root.
    file : Path
        The page itself.
    html : str
        The whole of the page.
    article : str
        The body of the page, within which tips are attached.
    payload : Path or None
        The javascript the extension wrote for the page, or ``None`` when it
        tipped nothing on it.
    tips : dict of str
        The tip markup of the page, keyed on the "href" that raises it, and
        empty for an untipped page.
    trailer : str
        The payload below the tip map, carrying the runtime guards.
    scripts : list of str
        The "src" of every script on the page, in document order.

    """

    page: str
    file: Path
    html: str
    article: str
    payload: Path | None
    tips: dict[str, str]
    trailer: str
    scripts: list[str]


def _resolve(root: Path, page: Path, href: str) -> Path | None:
    """Locate the file an ``href`` points at.

    Parameters
    ----------
    root : Path
        The root directory of the build.
    page : Path
        The page carrying the ``href``.
    href : str
        The reference, as it appears in the page.

    Returns
    -------
    Path or None
        The file referenced, or ``None`` when the reference names a host
        rather than a path within the build.

    """
    if ABSOLUTE.match(href):
        return None

    path = QUERY.sub("", href).split("#")[0]

    if not path:
        return page

    # a leading "/" would otherwise discard the page it is relative to
    base = root if path.startswith("/") else page.parent

    return Path(base, path.lstrip("/")).resolve()


def _read(root: Path, file: Path) -> Tips:
    """Collect the tooltips of a built page.

    A page the extension tipped nothing on is read all the same, with an
    empty tip map, so that a regression stripping the tooltips off a page
    cannot also drop that page out of the coverage meant to catch it.

    Parameters
    ----------
    root : Path
        The root directory of the build.
    file : Path
        The page to collect from.

    Returns
    -------
    Tips
        The tooltips of the page.

    """
    html = file.read_text(encoding="utf-8", errors="replace")
    scripts = SCRIPT.findall(html)
    payloads = [src for src in scripts if PAYLOAD in src]
    payload = _resolve(root, file, payloads[0]) if payloads else None
    # a page the extension found nothing on carries an empty payload file, and
    # one it never reached carries no payload script at all
    javascript = "" if payload is None else payload.read_text(encoding="utf-8")
    assigned = ASSIGNED.search(javascript)
    tips, trailer = {}, ""

    if assigned is not None:
        end = javascript.index("\n", assigned.end())
        trailer = javascript[end:]

        for selector, markup in json.loads(javascript[assigned.end() : end]).items():
            keyed = SELECTOR.match(selector)

            if keyed is not None:
                tips[keyed.group(1)] = markup

    article = ARTICLE.search(html)

    return Tips(
        page=file.relative_to(root).as_posix(),
        file=file,
        html=html,
        article="" if article is None else article.group(1),
        payload=payload,
        tips=tips,
        trailer=trailer,
        scripts=scripts,
    )


@pytest.fixture(scope="session")
def pages(html_root: Path) -> list[Tips]:
    """Collect the tooltips of every page the extension can reach.

    Everything bar the handful of ``UNTIPPABLE`` pages is collected, tipped or
    not, so that a page is only ever left out of a check by name.

    Parameters
    ----------
    html_root : Path
        The root directory of the build.

    Returns
    -------
    list of Tips
        The tooltips of the build, one entry per page.

    """
    return [
        _read(html_root, file)
        for file in sorted(html_root.rglob("*.html"))
        if not UNTIPPABLE.match(file.relative_to(html_root).as_posix())
    ]


@pytest.fixture(scope="session")
def tipped(require: Callable[[str], NoReturn], pages: list[Tips]) -> list[Tips]:
    """Collect the tooltips of every page the extension tipped.

    Parameters
    ----------
    require : Callable
        The guard for an unavailable prerequisite.
    pages : list of Tips
        The tooltips of every page of the build.

    Returns
    -------
    list of Tips
        The tooltips of the build, one entry per tipped page.

    """
    found = [page for page in pages if page.tips]

    if not found:
        require("no tooltips found in the build")

    return found


def test_glossary_terms_are_tipped(pages, html_root):
    """Tip every glossary term with its definition.

    The glossary is the whole reason for the extension: a term in the prose
    defines itself on hover, rather than sending the reader to another page
    and back. Every page is checked, tipped or not, so that a regression
    stripping the tooltips off one of them is a failure rather than a page
    quietly dropping out of the search.

    """
    glossary = (html_root / GLOSSARY).resolve()
    seen, missing, undefined = 0, [], []

    for page in pages:
        for href in ANCHOR.findall(page.article):
            if "#term-" not in href or _resolve(html_root, page.file, href) != glossary:
                continue

            seen += 1

            if href not in page.tips:
                missing.append(f"{page.page} -> {href}")
            elif "<dd>" not in page.tips[href]:
                undefined.append(f"{page.page} -> {href}")

    assert seen, "no glossary terms are referenced anywhere in the build"
    assert not missing, f"glossary terms left untipped: {missing}"
    assert not undefined, f"glossary tips carrying no definition: {undefined}"


def test_gallery_thumbnails_are_not_tipped(pages):
    """Leave the sphinx-gallery thumbnails to sphinx-gallery.

    Every thumbnail carries a ``tooltip`` attribute that sphinx-gallery styles
    into a panel replacing the image in place. A tip over the same link raises
    a second, larger panel saying much the same thing over the neighbouring
    thumbnails.

    """
    seen, tipped_thumbnails = 0, []

    for page in pages:
        for thumbnail in THUMBNAIL.findall(page.html):
            for href in ANCHOR.findall(thumbnail):
                seen += 1

                if href in page.tips:
                    tipped_thumbnails.append(f"{page.page} -> {href}")

    assert seen, "no gallery thumbnails in the build to be tipped"
    assert not tipped_thumbnails, f"gallery thumbnails tipped: {tipped_thumbnails}"


def test_tag_badges_are_not_tipped(pages, html_root):
    """Leave the sphinx-tags badges untipped.

    A tag page is headed by the tag itself, so its tip repeats the badge that
    raised it word for word.

    """
    tags = (html_root / TAGS).resolve()
    seen, tipped_badges = 0, []

    for page in pages:
        for href in ANCHOR.findall(page.article):
            target = _resolve(html_root, page.file, href)

            if target is None or target.parent != tags or "#" in href:
                continue

            seen += 1

            if href in page.tips:
                tipped_badges.append(f"{page.page} -> {href}")

    assert seen, "no tag badges in the build to be tipped"
    assert not tipped_badges, f"tag badges tipped: {tipped_badges}"


def test_runtime_is_vendored(tipped, html_root):
    """Serve the tooltip runtime from the build rather than a third party.

    The extension defaults ``tippy_js`` to two floating-major ``unpkg`` URLs,
    fetched by every reader of every tipped page. Nothing in a build log says
    so, and an unreachable host takes the tooltips away entirely.

    Vendoring a bundle is also distributing it, and both are ``MIT`` licensed,
    so the upstream notice must travel alongside. A minified bundle carries at
    most a one-line banner naming the licence, which is not that notice.

    """
    for page in tipped:
        runtime = [src for src in page.scripts if RUNTIME.search(src)]

        assert len(runtime) == BUNDLES, (
            f"{page.page} loads {len(runtime)} tooltip runtime scripts: {runtime}"
        )

        for src in runtime:
            assert not ABSOLUTE.match(src), f"{page.page} loads {src} off-site"

            resolved = _resolve(html_root, page.file, src)

            assert resolved.is_file(), f"{page.page} loads a missing {src}"
            assert html_root.resolve() in resolved.parents, (
                f"{page.page} loads {src} from outside the build"
            )

            notice = resolved.with_name(f"{resolved.name}{NOTICE_SUFFIX}")

            assert notice.is_file(), (
                f"{page.page} loads {src} with no published {notice.name}"
            )
            assert NOTICE.search(notice.read_text(encoding="utf-8")), (
                f"{notice.name} carries no copyright and permission notice"
            )


def test_runtime_guards_are_emitted(tipped):
    """Assert the guards the emitted javascript applies at runtime.

    Neither can be read off the configuration, because ``sphinx-tippy``
    *replaces* the anchor classes it is given rather than extending its own
    defaults, and fills in the tooltip properties it is not given.

    """
    for page in tipped:
        skipped = SKIP_CLASSES.search(page.trailer)

        assert skipped is not None, f"{page.page} emits no skip classes at all"

        classes = json.loads(skipped.group(1).rstrip().rstrip(";"))

        for guard in GUARDS:
            assert guard in classes, f"{page.page} does not skip {guard}: {classes}"

        assert INERT in page.trailer, (
            f"{page.page} raises tips that can be clicked into"
        )


def test_label_convention_opts_tips_in(tipped):
    """Honour the ``tippy-gv-`` and ``gv-`` labelling convention.

    A cross-reference target labelled ``tippy-gv-`` is tipped and one labelled
    ``gv-`` is not, which is how a page decides for itself. The two differ by a
    prefix alone, so a ``tippy_skip_urls`` pattern loose enough to catch the
    second would silently take the first with it.

    """
    opted_in, opted_out = 0, []

    for page in tipped:
        for href in page.tips:
            if "#tippy-gv-" in href:
                opted_in += 1
            elif "#gv-" in href:
                opted_out.append(f"{page.page} -> {href}")

    assert opted_in, "no tippy-gv- labelled target is tipped anywhere in the build"
    assert not opted_out, f"gv- labelled targets tipped: {opted_out}"


@pytest.mark.browser
def test_glossary_term_raises_a_tip(require, goto, html_root):
    """Raise a glossary definition by hovering a term."""
    if not (html_root / TERMS_PAGE).is_file():
        require(f"no {TERMS_PAGE} in the build")

    page = goto(VIEWPORT, TERMS_PAGE)
    term = page.locator(f'article.bd-article a[href*="{GLOSSARY}#term-"]').first

    assert term.count(), f"no glossary term referenced on {TERMS_PAGE}"

    term.scroll_into_view_if_needed()
    term.hover()
    page.wait_for_selector(BOX, timeout=PATIENCE)

    assert page.locator(BOX).first.inner_text().strip(), "the tip raised is empty"


@pytest.mark.browser
def test_stretched_card_raises_no_tip(require, goto, html_root):
    """Keep a sphinx-design card from raising the tip of the page it links to.

    The anchor is zero-size and stretched over the whole card body by an
    ``::after`` rule, so hovering anywhere on the card hovers it. The card here
    is labelled ``tippy-gv-``, so its tip is generated and sits in the payload;
    only the runtime skip class keeps it off the card. That makes this the one
    guard no amount of reading the build can confirm.

    """
    if not (html_root / CARD_PAGE).is_file():
        require(f"no {CARD_PAGE} in the build")

    page = goto(VIEWPORT, CARD_PAGE)
    selector = f"article.bd-article a.{STRETCHED}"

    assert page.locator(selector).count(), f"no stretched card on {CARD_PAGE}"

    probe = page.evaluate(PROBE, selector)

    assert probe["generated"], f"no tip was generated for {probe['href']} to be skipped"
    assert probe["covered"], (
        "the stretched anchor does not cover the centre of its card"
    )
    assert not probe["attached"], "a tip is attached to the stretched card anchor"

    page.mouse.move(probe["x"], probe["y"])
    page.wait_for_timeout(PATIENCE)

    assert not page.locator(BOX).count(), "hovering the card raised a tip"
