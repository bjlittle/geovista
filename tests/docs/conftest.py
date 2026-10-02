# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Fixtures for the documentation theme chrome browser tests.

Every fixture here skips rather than fails when its prerequisite is missing, so
that a plain ``pytest`` run is unaffected for contributors who have neither
``playwright`` nor a documentation build.

"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from playwright.sync_api import Browser, Page

#: The root of the built documentation, relative to this file.
HTML_ROOT = Path(__file__).parents[2] / "docs" / "_build" / "html"

#: A page carrying a secondary "On this page" sidebar with enough entries to
#: be worth revealing.
API_PAGE = "reference/generated/api/geovista/bridge/index.html"

#: The viewport height used throughout, tall enough to render the chrome
#: without the page itself scrolling.
HEIGHT = 900

#: An element the themes inject on every page, used to detect settled chrome.
SENTINEL = ".primary-toggle"

#: Milliseconds between settle polls.
POLL = 100

#: Consecutive unchanged polls required before the chrome is settled.
QUIET = 6

#: Milliseconds to wait for the chrome to settle before giving up.
PATIENCE = 30000

#: Poll until the theme chrome stops changing.
#:
#: Both themes inject their toggles from JavaScript after load, so the chrome
#: is not final the moment the page is ready. Waiting for it to stop changing
#: is reliable where a fixed delay is only a guess, and a guess tuned on a
#: developer machine is apt to be too short on a loaded CI runner.
SETTLED = """([selector, quiet]) => {
    const found = document.querySelectorAll(selector).length;
    const state = window.__geovista_settle ?? { seen: -1, stable: 0 };
    state.stable = found > 0 && found === state.seen ? state.stable + 1 : 0;
    state.seen = found;
    window.__geovista_settle = state;
    return state.stable >= quiet;
}"""


@pytest.fixture(scope="session")
def html_root() -> Path:
    """Locate the built documentation.

    Returns
    -------
    Path
        The root directory of the build.

    """
    if not (HTML_ROOT / "index.html").is_file():
        pytest.skip(f"no documentation build found at {HTML_ROOT}")

    return HTML_ROOT


@pytest.fixture(scope="session")
def api_page(html_root: Path) -> str:
    """Locate a built page carrying a secondary sidebar.

    Parameters
    ----------
    html_root : Path
        The root directory of the build.

    Returns
    -------
    str
        The path of the page, relative to the build root.

    """
    if not (html_root / API_PAGE).is_file():
        pytest.skip(f"no api reference page built at {API_PAGE}")

    return API_PAGE


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """Provide a headless chromium browser.

    Yields
    ------
    Browser
        A launched browser, closed on teardown.

    """
    sync_api = pytest.importorskip(
        "playwright.sync_api", reason="playwright is not installed"
    )

    with sync_api.sync_playwright() as driver:
        try:
            instance = driver.chromium.launch()
        except sync_api.Error as err:
            # the python package is installed but "playwright install chromium"
            # has not been run, or the host is missing the shared libraries it
            # needs - neither is a failure of the documentation
            pytest.skip(f"unable to launch chromium: {err}")

        yield instance

        instance.close()


@pytest.fixture
def goto(browser: Browser, html_root: Path) -> Iterator[Callable[..., Page]]:
    """Provide a factory opening a built page at a given viewport width.

    Pages are served over ``file://``; the theme chrome needs no web server.

    Parameters
    ----------
    browser : Browser
        The browser to open pages in.
    html_root : Path
        The root directory of the build.

    Yields
    ------
    Callable
        A factory taking a viewport width and an optional page path.

    """
    pages: list[Page] = []

    def factory(width: int, page: str = "index.html") -> Page:
        instance = browser.new_page(viewport={"width": width, "height": HEIGHT})
        # "load" waits for the gallery thumbnails the carousel asserts on
        instance.goto((html_root / page).as_uri(), wait_until="load")
        instance.wait_for_function(
            SETTLED, arg=[SENTINEL, QUIET], polling=POLL, timeout=PATIENCE
        )
        pages.append(instance)
        return instance

    yield factory

    for instance in pages:
        instance.close()
