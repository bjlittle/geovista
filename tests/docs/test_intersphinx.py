# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the resilience of the documentation to an intersphinx outage.

An unreachable inventory is simulated with a refused connection, so these
tests require no network of their own.

"""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import shutil
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import NoReturn

try:
    from sphinx.application import Sphinx
except ImportError:
    Sphinx = None

#: The documentation source, carrying the extension and the vendored
#: inventories under test.
DOCS = Path(__file__).parents[2] / "docs" / "src"

#: The refresher of the vendored inventories, which also parses the sphinx
#: configuration that declares them.
SCRIPT = Path(__file__).parents[2] / ".github" / "scripts" / "inventories.py"

#: A vendored inventory, small enough to copy about, standing in for whichever
#: one a build cannot reach.
FALLBACK = "pyvistaqt.inv"

#: A location nothing can be served from, which refuses a connection rather
#: than waiting on a timeout.
UNREACHABLE = "http://127.0.0.1:1/"

#: A minimal sphinx configuration cross-referencing an unreachable inventory.
#:
#: Every application after the first in a process re-registers the docutils
#: nodes, directives and roles of each extension, and sphinx warns once per
#: registration - which would fail these builds for reasons of the harness.
#: Those warnings are typed, unlike the inventory failure, and so can simply
#: be named here.
CONF = """
import sys

sys.path.append({ext!r})

extensions = {extensions!r}
nitpicky = True
intersphinx_timeout = 5
intersphinx_mapping = {{"python": ({url!r}, {locations!r})}}
exclude_patterns = ["_build"]
suppress_warnings = ["app"]
"""

#: A document carrying a cross-reference that only an inventory can resolve.
INDEX = """
Title
=====

:class:`{target}`
"""

#: A target carried by no inventory at all, and so always a nitpick miss.
MISSING = "collections.abc.Sequence"

#: A target carried by the fallback inventory, and so resolvable only through
#: it while the remote is unreachable.
PRESENT = "pyvistaqt.BackgroundPlotter"


@pytest.fixture
def build(require: Callable[[str], NoReturn], tmp_path: Path) -> Callable[..., Sphinx]:
    """Provide a factory building a minimal documentation set.

    Parameters
    ----------
    require : Callable
        The guard for an unavailable prerequisite.
    tmp_path : Path
        The temporary directory of the build.

    Returns
    -------
    Callable
        A factory taking the cross-reference target, whether the extension is
        enabled, and whether a fallback inventory is available.

    """
    if Sphinx is None:
        require("sphinx is not installed")

    def factory(
        target: str, *, resilient: bool = True, fallback: bool = False
    ) -> Sphinx:
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)

        extensions = ["sphinx.ext.intersphinx"]

        if resilient:
            extensions.insert(0, "intersphinx_resilience")

        locations = None

        if fallback:
            shutil.copyfile(DOCS / "_inventory" / FALLBACK, src / FALLBACK)
            locations = (None, FALLBACK)

        conf = CONF.format(
            ext=str(DOCS / "_ext"),
            extensions=extensions,
            url=UNREACHABLE,
            locations=locations,
        )
        (src / "conf.py").write_text(conf, encoding="utf-8")
        (src / "index.rst").write_text(INDEX.format(target=target), encoding="utf-8")

        app = Sphinx(
            srcdir=str(src),
            confdir=str(src),
            outdir=str(tmp_path / "html"),
            doctreedir=str(tmp_path / "doctrees"),
            buildername="html",
            status=None,
            warning=io.StringIO(),
            warningiserror=True,
            freshenv=True,
        )
        app.build()

        return app

    return factory


def test_unreachable__degrades(build):
    """An unreachable inventory with no fallback must not fail the build."""
    app = build(MISSING, resilient=True, fallback=False)

    assert app.statuscode == 0
    assert app._warncount == 0
    # the cascade of nitpick misses is withdrawn along with the warning that
    # would otherwise be counted
    assert app.config.nitpicky is False


def test_unreachable__control(build):
    """Without the extension, the same build fails.

    Guards against sphinx changing in a way that leaves the degradation test
    passing for the wrong reason.

    """
    app = build(MISSING, resilient=False, fallback=False)

    assert app.statuscode != 0
    assert app._warncount > 0


def test_vendored__complete():
    """Every documentation set cross-referenced must have a usable fallback.

    A mapping added without one is silent until the day that site is
    unreachable, which is exactly the day the fallback was wanted. Loading the
    refresher rather than re-reading the configuration also covers the parsing
    that the monthly "ci-inventories.yml" workflow depends on.

    """
    spec = importlib.util.spec_from_file_location("inventories", SCRIPT)
    inventories = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inventories)

    urls, directory = inventories.mapping(DOCS / "conf.py")

    assert urls, "no intersphinx mapping found"

    for name in urls:
        inventory = DOCS / directory / f"{name}.inv"

        assert inventory.is_file(), (
            f"no vendored inventory for {name!r}, refresh them with "
            f"'pixi run -e docs fetch-inventories'"
        )
        # a truncated or wrongly formatted inventory raises here
        assert inventories.payload(inventory.read_bytes())


def test_fallback__resolves(build):
    """A fallback consulted after an unreachable remote emits no warning.

    This is what keeps "--fail-on-warning" green through an upstream outage.
    The inventory did load, so nitpicky mode must be left alone, and the
    reference must resolve through it.

    """
    app = build(PRESENT, resilient=True, fallback=True)

    assert app.statuscode == 0
    assert app._warncount == 0
    assert app.config.nitpicky is True

    html = (Path(app.outdir) / "index.html").read_text(encoding="utf-8")

    assert f"{UNREACHABLE}api_reference.html#{PRESENT}" in html
