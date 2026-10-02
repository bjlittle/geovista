# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Browser tests for the documentation sidebars.

These assert that a reader can reach the navigation, which is a property of the
rendered documentation rather than of any particular theme release. They are
therefore expected to outlive ``docs/src/_static/sidebar_toggle.js``, and are
the signal for when that workaround can be dropped.

"""

from __future__ import annotations

import pytest

from ._theme import (
    PRIMARY_MODAL,
    SECONDARY_MODAL,
    WIDE,
    centre_tag,
    click_visible,
    dialog,
    press_visible,
    sidebar_offset,
)

pytestmark = pytest.mark.browser

#: Viewports narrow enough that the primary sidebar is presented as a dialog.
NARROW_WIDTHS = [390, 600, 800, 900]

#: Viewports wide enough that the primary sidebar collapses in place.
WIDE_WIDTHS = [1000, 1200, 1600]


@pytest.mark.parametrize("width", NARROW_WIDTHS)
def test_primary_toggle_reveals_navigation(goto, width):
    """Reveal the primary sidebar on a viewport where it is off-canvas."""
    page = goto(width)

    assert click_visible(page, ".primary-toggle"), "no visible primary toggle"

    state = dialog(page, PRIMARY_MODAL)
    assert state is not None, "primary sidebar dialog is absent"
    assert state["open"], "primary toggle did not open the sidebar"
    assert state["visibility"] == "visible", "primary sidebar opened but is invisible"
    assert state["links"] > 0, "primary sidebar opened but contains no links"


@pytest.mark.parametrize("width", WIDE_WIDTHS)
def test_primary_toggle_collapses_navigation(goto, width):
    """Collapse the primary sidebar in place on a wide viewport."""
    page = goto(width)

    assert sidebar_offset(page) >= 0, "primary sidebar is not on-canvas to begin with"
    assert click_visible(page, ".primary-toggle"), "no visible primary toggle"

    assert sidebar_offset(page) < 0, "primary toggle did not collapse the sidebar"
    assert not dialog(page, PRIMARY_MODAL)["open"], "wide viewport opened a dialog"


@pytest.mark.parametrize("width", [390, 900, 1100])
def test_secondary_toggle_reveals_contents(goto, api_page, width):
    """Reveal the secondary sidebar table of contents."""
    page = goto(width, api_page)

    assert click_visible(page, ".secondary-toggle"), "no visible secondary toggle"

    state = dialog(page, SECONDARY_MODAL)
    assert state is not None, "secondary sidebar dialog is absent"
    assert state["open"], "secondary toggle did not open the contents"
    assert state["visibility"] == "visible", (
        "secondary contents opened but is invisible"
    )
    assert state["links"] > 0, "secondary contents opened but contains no links"


def test_secondary_dialog_dismissed_by_escape(goto, api_page):
    """Dismiss the secondary sidebar with the keyboard and restore the contents."""
    page = goto(390, api_page)

    assert click_visible(page, ".secondary-toggle"), "no visible secondary toggle"
    assert dialog(page, SECONDARY_MODAL)["open"], "secondary toggle did not open"

    page.keyboard.press("Escape")
    page.wait_for_timeout(600)

    assert not dialog(page, SECONDARY_MODAL)["open"], "escape did not dismiss"
    # the contents must go back to the sidebar, not be left in the closed dialog
    assert dialog(page, SECONDARY_MODAL)["links"] == 0, "contents stranded in dialog"


def test_widening_does_not_strand_primary_dialog(goto):
    """Release the page when a viewport is widened with the sidebar open.

    An open dialog holds the top layer. Should it survive into a viewport whose
    styling hides it, the whole page is blocked by something a reader can
    neither see nor dismiss.

    """
    page = goto(390)

    assert click_visible(page, ".primary-toggle"), "no visible primary toggle"
    assert dialog(page, PRIMARY_MODAL)["open"], "primary toggle did not open"

    page.set_viewport_size({"width": 1400, "height": 900})
    page.wait_for_timeout(800)

    assert not dialog(page, PRIMARY_MODAL)["open"], "dialog survived the widening"
    assert centre_tag(page) != "HTML", "page is blocked by an invisible dialog"


def test_primary_toggle_live_after_widening(goto):
    """Keep the primary toggle working across a viewport transition."""
    page = goto(390)

    assert click_visible(page, ".primary-toggle"), "no visible primary toggle"
    page.set_viewport_size({"width": 1400, "height": 900})
    page.wait_for_timeout(800)

    assert sidebar_offset(page) >= 0, "sidebar did not return on widening"
    assert click_visible(page, ".primary-toggle"), "no visible primary toggle"
    assert sidebar_offset(page) < 0, "primary toggle is inert after the transition"


@pytest.mark.parametrize("toggle", [".primary-toggle", ".secondary-toggle"])
def test_toggle_keyboard_activation(goto, api_page, toggle):
    """Activate each sidebar toggle from the keyboard."""
    page = goto(390, api_page)
    modal = PRIMARY_MODAL if toggle == ".primary-toggle" else SECONDARY_MODAL

    assert press_visible(page, toggle), f"no visible {toggle}"
    assert dialog(page, modal)["open"], f"{toggle} is not keyboard operable"


def test_wide_breakpoint_is_the_theme_breakpoint(goto):
    """Confirm the sidebar switches presentation either side of the breakpoint.

    The two themes do not share a breakpoint scale, so this pins the behaviour
    to the viewport that governs it rather than to a value that merely happens
    to work.

    """
    narrow = goto(WIDE - 1)
    assert click_visible(narrow, ".primary-toggle"), "no visible primary toggle"
    assert dialog(narrow, PRIMARY_MODAL)["open"], "below the breakpoint is not a dialog"

    wide = goto(WIDE + 1)
    assert click_visible(wide, ".primary-toggle"), "no visible primary toggle"
    assert not dialog(wide, PRIMARY_MODAL)["open"], "above the breakpoint is a dialog"
