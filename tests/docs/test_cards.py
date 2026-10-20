# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Browser tests of the ``sphinx-design`` cards in the documentation.

The cards of the landing page, and of several section indices, carry an icon
beside their body. ``sphinx-design`` leaves a card transparent, and
``pydata-sphinx-theme`` paints only the body of one, so the icon sits on
whatever lies behind the card. Before 0.20 the theme asked for a colour it never
defined, which left the body transparent too and hid the difference; from then
the icon sat on the page in dark mode, on a strip of a different colour to the
card it belongs to.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from playwright.sync_api import Page

pytestmark = pytest.mark.browser

#: A viewport wide enough to lay the landing page cards out side by side.
WIDTH = 1280

#: A card carrying an image of its own.
PICTURED = ".sd-card:has(> img.sd-card-img-top)"

#: The colour a reader sees behind an element: its own background, or that of
#: the nearest ancestor painting one.
BEHIND = """(element) => {
    for (; element; element = element.parentElement) {
        const colour = getComputedStyle(element).backgroundColor;
        if (colour !== "rgba(0, 0, 0, 0)" && colour !== "transparent") {
            return colour;
        }
    }
    return null;
}"""


#: The class the built HTML gives the image of a card.
IMAGE = "sd-card-img-top"


def pictured(html_root: Path) -> list[str]:
    """Find every built page carrying a card with an image.

    Derived from the build rather than listed, so that a page gaining such a
    card is covered the day it does.

    Parameters
    ----------
    html_root : Path
        The root directory of the build.

    Returns
    -------
    list of str
        The path of each page, relative to the build root.

    """
    return sorted(
        path.relative_to(html_root).as_posix()
        for path in html_root.rglob("*.html")
        if IMAGE in path.read_text(encoding="utf-8", errors="ignore")
    )


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_card_image__sits_on_the_card_colour(
    goto: Callable[..., Page], html_root: Path, scheme: str
) -> None:
    """An icon must sit on the colour of its own card, in either mode.

    The theme is left in its default "auto" mode and the browser asked for the
    colour scheme, so it is the theme's own switch that is exercised.

    """
    pages = pictured(html_root)

    assert "index.html" in pages, "the landing page carries no card with an image"

    problems = []

    for path in pages:
        page = goto(WIDTH, path)
        page.emulate_media(color_scheme=scheme)
        page.wait_for_function(
            "scheme => document.documentElement.dataset.theme === scheme",
            arg=scheme,
        )
        cards = page.locator(PICTURED)

        if not cards.count():
            problems.append(f"{path}: no card with an image was rendered")

        for index in range(cards.count()):
            card = cards.nth(index)
            title = card.locator(".sd-card-title").inner_text().strip()
            image = card.locator(f":scope > img.{IMAGE}").evaluate(BEHIND)
            body = card.locator(":scope > .sd-card-body").evaluate(BEHIND)

            if image != body:
                problems.append(f"{path}: {title!r} icon on {image}, body on {body}")

    assert not problems, f"in {scheme} mode:\n" + "\n".join(problems)
