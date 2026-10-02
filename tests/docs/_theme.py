# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Helpers for driving the documentation theme chrome in a browser.

These deliberately assert on what a reader can see and do, rather than on the
markup of any particular theme release, so that they survive a theme bump and
report what actually broke.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.sync_api import Page

#: The identifier of the dialog opened for the primary sidebar.
PRIMARY_MODAL = "pst-primary-sidebar-modal"

#: The identifier of the dialog opened for the secondary sidebar.
SECONDARY_MODAL = "pst-secondary-sidebar-modal"

#: The identifier of the primary sidebar itself.
PRIMARY_SIDEBAR = "pst-primary-sidebar"

#: The viewport width at which the primary sidebar stops being a dialog and
#: starts collapsing in place, as per ``sphinx-book-theme``.
WIDE = 992

#: Milliseconds allowed for a dialog transition or a media query to settle.
SETTLE = 600


def visible_index(page: Page, selector: str) -> int:
    """Find the first rendered element matching ``selector``.

    Both themes render a duplicate of each toggle and hide one of them, so
    "the button" is ambiguous - this picks the one a reader can actually see.

    Parameters
    ----------
    page : Page
        The browser page to query.
    selector : str
        The CSS selector to match.

    Returns
    -------
    int
        The index of the first visible match, or ``-1`` if none is visible.

    """
    return page.evaluate(
        """(selector) => [...document.querySelectorAll(selector)].findIndex(
            (element) => !!(element.offsetWidth || element.offsetHeight
                            || element.getClientRects().length),
        )""",
        selector,
    )


def click_visible(page: Page, selector: str) -> bool:
    """Click the first rendered element matching ``selector``.

    Parameters
    ----------
    page : Page
        The browser page to act on.
    selector : str
        The CSS selector to match.

    Returns
    -------
    bool
        Whether a visible element was found and clicked.

    """
    index = visible_index(page, selector)

    if index < 0:
        return False

    page.locator(selector).nth(index).click()
    page.wait_for_timeout(SETTLE)

    return True


def press_visible(page: Page, selector: str, key: str = "Enter") -> bool:
    """Activate the first rendered element matching ``selector`` from the keyboard.

    Parameters
    ----------
    page : Page
        The browser page to act on.
    selector : str
        The CSS selector to match.
    key : str, optional
        The key to press once the element holds focus.

    Returns
    -------
    bool
        Whether a visible element was found and activated.

    """
    index = visible_index(page, selector)

    if index < 0:
        return False

    page.locator(selector).nth(index).focus()
    page.keyboard.press(key)
    page.wait_for_timeout(SETTLE)

    return True


def dialog(page: Page, modal: str) -> dict[str, Any] | None:
    """Report the state of a sidebar dialog.

    Parameters
    ----------
    page : Page
        The browser page to query.
    modal : str
        The identifier of the dialog element.

    Returns
    -------
    dict or None
        Whether the dialog is open, its computed visibility and how many links
        it contains, or ``None`` if the dialog is absent.

    """
    return page.evaluate(
        """(modal) => {
            const element = document.getElementById(modal);
            if (!element) { return null; }
            return {
                open: element.hasAttribute("open"),
                visibility: getComputedStyle(element).visibility,
                links: element.querySelectorAll("a").length,
            };
        }""",
        modal,
    )


def centre_tag(page: Page) -> str | None:
    """Identify the element occupying the centre of the viewport.

    An open dialog holds the top layer, so when one is stranded this reports
    the dialog - or ``HTML`` where the dialog is invisible - instead of the
    page content a reader is trying to reach.

    Parameters
    ----------
    page : Page
        The browser page to query.

    Returns
    -------
    str or None
        The tag name of the element at the viewport centre.

    """
    return page.evaluate(
        """() => {
            const element = document.elementFromPoint(
                window.innerWidth / 2, window.innerHeight / 2,
            );
            return element ? element.tagName : null;
        }"""
    )


def sidebar_offset(page: Page, sidebar: str = PRIMARY_SIDEBAR) -> int | None:
    """Measure the horizontal offset of a sidebar.

    A collapsed sidebar is pushed off-canvas, so a negative offset is how
    collapse-in-place is distinguished from a dialog.

    Parameters
    ----------
    page : Page
        The browser page to query.
    sidebar : str, optional
        The identifier of the sidebar element.

    Returns
    -------
    int or None
        The rounded x offset, or ``None`` if the sidebar is absent.

    """
    return page.evaluate(
        """(sidebar) => {
            const element = document.getElementById(sidebar);
            return element ? Math.round(element.getBoundingClientRect().x) : null;
        }""",
        sidebar,
    )
