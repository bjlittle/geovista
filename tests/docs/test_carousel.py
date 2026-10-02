# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Browser tests for the gallery carousel.

The carousel is built from rendered gallery thumbnails, so it only exists in a
build made with ``plot_gallery`` enabled. These tests skip on a no-plot build
rather than silently passing over an empty page.

"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.browser

#: The container holding the gallery carousel cards.
CAROUSEL = ".sd-cards-carousel"

#: Collect the state of every carousel card, and of the clipping rect that
#: decides which of them can meaningfully be hit-tested.
PROBE = """() => {
    const wrapper = document.querySelector(".sd-cards-carousel");
    if (!wrapper) { return null; }
    const bounds = wrapper.getBoundingClientRect();
    return [...wrapper.querySelectorAll(".sd-card")].map((card) => {
        const image = card.querySelector("img.sd-card-img");
        const body = card.querySelector(".sd-card-body");
        const link = card.querySelector("a.sd-stretched-link");
        const rect = card.getBoundingClientRect();
        const x = rect.x + rect.width / 2;
        const y = rect.y + rect.height / 2;
        // a carousel deliberately hangs cards past its own edge, so only a
        // card lying wholly inside the clipping rect can be hit-tested
        const testable = rect.x >= bounds.x - 1 && rect.right <= bounds.right + 1
                         && y >= 0 && y <= window.innerHeight && rect.width > 0;
        const found = testable ? document.elementFromPoint(x, y) : null;
        return {
            loaded: !!image && image.complete && image.naturalWidth > 0,
            shown: !!image && getComputedStyle(image).display !== "none",
            body: body ? getComputedStyle(body).display : "absent",
            empty: body ? body.textContent.trim() === "" : null,
            height: Math.round(rect.height),
            href: link ? link.getAttribute("href") : null,
            testable: testable,
            hit: found ? (found.closest("a") === link) : null,
        };
    });
}"""


@pytest.fixture
def cards(goto):
    """Collect the carousel cards from the landing page.

    Parameters
    ----------
    goto : Callable
        The page factory.

    Returns
    -------
    list of dict
        The state of each carousel card.

    """
    page = goto(1400)

    if page.locator(CAROUSEL).count() == 0:
        pytest.skip("no gallery carousel in this build, see plot_gallery")

    # the carousel sits below the fold, and a hit-test off-screen is vacuous
    page.evaluate(
        """() => document.querySelector(".sd-cards-carousel")
            .scrollIntoView({ block: "center", behavior: "instant" })"""
    )
    page.wait_for_timeout(1500)

    found = page.evaluate(PROBE)
    assert found, "gallery carousel contains no cards"

    return found


def test_carousel_cards_show_their_thumbnail(cards):
    """Paint a gallery thumbnail on every carousel card.

    A card body is rendered even when empty, and will paint over the thumbnail
    behind it unless suppressed.

    """
    for index, card in enumerate(cards):
        assert card["loaded"], f"card {index} thumbnail failed to load"
        assert card["shown"], f"card {index} thumbnail is not displayed"
        assert card["height"] > 0, f"card {index} has collapsed"

        if card["empty"]:
            assert card["body"] == "none", (
                f"card {index} paints an empty body over its thumbnail"
            )


def test_carousel_cards_link_to_the_gallery(cards):
    """Give every carousel card a destination."""
    for index, card in enumerate(cards):
        assert card["href"], f"card {index} has no stretched link"


def test_carousel_cards_are_clickable(cards):
    """Land a click anywhere on a card on that card's link."""
    testable = [(index, card) for index, card in enumerate(cards) if card["testable"]]

    assert testable, "no unclipped card to hit-test, the assertion would be vacuous"

    for index, card in testable:
        assert card["hit"], f"a click on card {index} does not reach its link"
