# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Fixtures for the documentation tests.

Most are for the theme chrome browser tests, and every one of those skips
rather than fails when its prerequisite is missing, so that a plain ``pytest``
run is unaffected for contributors who have neither ``playwright`` nor a
documentation build.

That is the wrong default for CI, which installs every prerequisite and builds
the gallery deliberately, and so would report success having silently stopped
covering anything. Pass ``--browser-strict`` to require them instead.

The exception is :func:`reading`, which needs neither a browser nor a build and
so never skips.

"""

from __future__ import annotations

from functools import partial
import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from types import ModuleType
    from typing import NoReturn

    from playwright.sync_api import Browser, Page

#: The option requiring, rather than skipping, each prerequisite, registered
#: in the test root "conftest.py" as pytest honours "pytest_addoption" only
#: there.
STRICT = "--browser-strict"

#: The root of the built documentation, relative to this file.
HTML_ROOT = Path(__file__).parents[2] / "docs" / "_build" / "html"

#: The documentation source, carrying the extensions under test.
DOCS = Path(__file__).parents[2] / "docs" / "src"

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


def _require(config: pytest.Config, reason: str) -> NoReturn:
    """Skip an unmet prerequisite, or fail it under ``--browser-strict``.

    Parameters
    ----------
    config : pytest.Config
        The pytest configuration, carrying the command line options.
    reason : str
        The prerequisite that is unavailable.

    Raises
    ------
    Failed
        When the prerequisite is required.
    Skipped
        Otherwise.

    """
    if config.getoption(STRICT):
        pytest.fail(f"{reason} ({STRICT})")

    pytest.skip(reason)


@pytest.fixture(scope="session")
def require(pytestconfig: pytest.Config) -> Callable[[str], NoReturn]:
    """Provide the guard for a prerequisite that only a test can detect.

    Parameters
    ----------
    pytestconfig : pytest.Config
        The pytest configuration, carrying the command line options.

    Returns
    -------
    Callable
        A callable taking the prerequisite that is unavailable, which skips, or
        fails under ``--browser-strict``.

    """
    return partial(_require, pytestconfig)


@pytest.fixture(scope="session")
def reading() -> ModuleType:
    """Load the reading-time model.

    It is loaded from its path rather than imported, as ``docs/src/_ext`` is on
    the path of a documentation build and of nothing else. It imports nothing
    beyond the standard library, so unlike the browser fixtures here this one
    has no prerequisite to skip on.

    Returns
    -------
    ModuleType
        The loaded module.

    """
    path = DOCS / "_ext" / "reading.py"
    spec = importlib.util.spec_from_file_location("reading", path)
    module = importlib.util.module_from_spec(spec)
    # registered before it is executed, as "dataclass" resolves the annotations
    # of a module compiled with "from __future__ import annotations" by looking
    # the module up by name
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


@pytest.fixture(scope="session")
def html_root(pytestconfig: pytest.Config) -> Path:
    """Locate the built documentation.

    Parameters
    ----------
    pytestconfig : pytest.Config
        The pytest configuration, carrying the command line options.

    Returns
    -------
    Path
        The root directory of the build.

    """
    if not (HTML_ROOT / "index.html").is_file():
        _require(pytestconfig, f"no documentation build found at {HTML_ROOT}")

    return HTML_ROOT


@pytest.fixture(scope="session")
def api_page(pytestconfig: pytest.Config, html_root: Path) -> str:
    """Locate a built page carrying a secondary sidebar.

    Parameters
    ----------
    pytestconfig : pytest.Config
        The pytest configuration, carrying the command line options.
    html_root : Path
        The root directory of the build.

    Returns
    -------
    str
        The path of the page, relative to the build root.

    """
    if not (html_root / API_PAGE).is_file():
        _require(pytestconfig, f"no api reference page built at {API_PAGE}")

    return API_PAGE


@pytest.fixture(scope="session")
def browser(pytestconfig: pytest.Config) -> Iterator[Browser]:
    """Provide a headless chromium browser.

    Parameters
    ----------
    pytestconfig : pytest.Config
        The pytest configuration, carrying the command line options.

    Yields
    ------
    Browser
        A launched browser, closed on teardown.

    """
    try:
        sync_api = importlib.import_module("playwright.sync_api")
    except ImportError:
        _require(pytestconfig, "playwright is not installed")

    with sync_api.sync_playwright() as driver:
        try:
            instance = driver.chromium.launch()
        except sync_api.Error as err:
            # the python package is installed but "playwright install chromium"
            # has not been run, or the host is missing the shared libraries it
            # needs - neither is a failure of the documentation
            _require(pytestconfig, f"unable to launch chromium: {err}")

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
