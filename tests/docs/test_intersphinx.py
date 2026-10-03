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
from typing import TYPE_CHECKING, NamedTuple

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType
    from typing import NoReturn

try:
    from sphinx.application import Sphinx
    from sphinx.util.inventory import InventoryFile
except ImportError:
    Sphinx = None
    InventoryFile = None

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


class Build(NamedTuple):
    """A completed documentation build.

    Attributes
    ----------
    app : Sphinx
        The application that performed the build.
    status : str
        Everything the build reported to its status stream, which is where the
        extension reports a degraded build.

    """

    app: Sphinx
    status: str


@pytest.fixture(scope="session")
def inventories() -> ModuleType:
    """Load the refresher of the vendored inventories.

    It is loaded from its path rather than imported, as the workflow that runs
    it monthly has only the standard library available and so it is a
    standalone script rather than a module of the package.

    Returns
    -------
    ModuleType
        The loaded script.

    """
    spec = importlib.util.spec_from_file_location("inventories", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


@pytest.fixture
def build(require: Callable[[str], NoReturn], tmp_path: Path) -> Callable[..., Build]:
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
    ) -> Build:
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

        status = io.StringIO()
        app = Sphinx(
            srcdir=str(src),
            confdir=str(src),
            outdir=str(tmp_path / "html"),
            doctreedir=str(tmp_path / "doctrees"),
            buildername="html",
            status=status,
            warning=io.StringIO(),
            warningiserror=True,
            freshenv=True,
        )
        app.build()

        return Build(app, status.getvalue())

    return factory


def test_unreachable__degrades(build):
    """An unreachable inventory with no fallback must not fail the build."""
    app, status = build(MISSING, resilient=True, fallback=False)

    assert app.statuscode == 0
    assert app._warncount == 0
    # the cascade of nitpick misses is withdrawn along with the warning that
    # would otherwise be counted
    assert app.config.nitpicky is False
    # the guard is installed on every sphinx handler, each of which is offered
    # the same record, so a miscount here reports one outage several times over
    assert "1 intersphinx inventory is unreachable" in status


def test_unreachable__control(build):
    """Without the extension, the same build fails.

    Guards against sphinx changing in a way that leaves the degradation test
    passing for the wrong reason.

    """
    app, _ = build(MISSING, resilient=False, fallback=False)

    assert app.statuscode != 0
    assert app._warncount > 0


def test_vendored__complete(inventories):
    """Every documentation set cross-referenced must have a usable fallback.

    A mapping added without one is silent until the day that site is
    unreachable, which is exactly the day the fallback was wanted. Loading the
    refresher rather than re-reading the configuration also covers the parsing
    that the monthly "ci-inventories.yml" workflow depends on.

    """
    urls, directory = inventories.mapping(DOCS / "conf.py")

    assert urls, "no intersphinx mapping found"

    for name in urls:
        inventory = DOCS / directory / f"{name}.inv"

        assert inventory.is_file(), (
            f"no vendored inventory for {name!r}, refresh them with "
            f"'pixi run -e docs fetch-inventories'"
        )
        # a truncated, mis-versioned or wrongly compressed inventory raises here
        assert inventories.payload(inventory.read_bytes())


def test_vendored__loadable(require, inventories):
    """Every vendored inventory must be one that sphinx can actually load.

    The structural check of :func:`test_vendored__complete` is our own reading
    of the format, which the refresher has to make do with; this is sphinx's,
    and sphinx is what must read these files during an outage. A payload that
    decompresses is not thereby readable, and an inventory sphinx rejects is no
    fallback at all.

    """
    if InventoryFile is None:
        require("sphinx is not installed")

    urls, directory = inventories.mapping(DOCS / "conf.py")

    for name, url in urls.items():
        raw = (DOCS / directory / f"{name}.inv").read_bytes()
        inventory = InventoryFile.loads(raw, uri=url)

        assert inventory.data, f"the vendored inventory for {name!r} is empty"


@pytest.mark.parametrize(
    "corrupt",
    [
        b"# Sphinx inventory version 9",
        b"# Sphinx inventory version 1",
        b"not an inventory at all",
    ],
)
def test_refresh__repairs(inventories, tmp_path, monkeypatch, corrupt):
    """A vendored inventory sphinx cannot load must be replaced, not kept.

    Only the header of a corrupt inventory need differ for its payload to match
    the remote, so a refresher comparing payloads alone reports it unchanged -
    leaving a fallback that fails on the very day it is wanted.

    """
    valid = (DOCS / "_inventory" / FALLBACK).read_bytes()
    _, _, rest = valid.partition(b"\n")

    monkeypatch.setattr(inventories, "fetch", lambda _url: valid)

    inventory = tmp_path / FALLBACK
    inventory.write_bytes(corrupt + b"\n" + rest)

    assert inventories.refresh(UNREACHABLE, inventory).startswith("**updated**")
    assert inventory.read_bytes() == valid
    # and, now repaired, it is left alone rather than rewritten every month
    assert inventories.refresh(UNREACHABLE, inventory) == "unchanged"


def test_fallback__resolves(build):
    """A fallback consulted after an unreachable remote emits no warning.

    This is what keeps "--fail-on-warning" green through an upstream outage.
    The inventory did load, so nitpicky mode must be left alone, and the
    reference must resolve through it.

    """
    app, _ = build(PRESENT, resilient=True, fallback=True)

    assert app.statuscode == 0
    assert app._warncount == 0
    assert app.config.nitpicky is True

    html = (Path(app.outdir) / "index.html").read_text(encoding="utf-8")

    assert f"{UNREACHABLE}api_reference.html#{PRESENT}" in html
