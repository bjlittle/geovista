# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that ``conf.py`` sets the notebook execution mode before Sphinx compares it.

Sphinx compares the configuration with the one stored by the last build before the
``builder-inited`` event, and re-reads every document when a value that affects
reading differs. ``nb_execution_mode`` is one, and ``conf.py`` turns it off when the
tutorials are not built. Turned off in ``builder-inited``, the value was stored as
``"off"`` and read as ``"cache"`` on the next run, so no build was ever incremental
(#2904). It is now turned off in ``config-inited``, before the comparison.

``conf.py`` is executed in a subprocess, from a clean environment, as
``test_conf_gallery.py`` does, since importing it configures ``pyvista``.

"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import NoReturn

DOCS = Path(__file__).parents[2] / "docs" / "src"

PROBE = """
import json, runpy, sys
sys.path.insert(0, sys.argv[1])
namespace = runpy.run_path(sys.argv[2])


class Config(dict):
    __getattr__ = dict.__getitem__


class App:
    def __init__(self, config):
        self.config = config
        self.builder = type("Builder", (), {"config": config})()
        self.connected = []

    def connect(self, event, handler, priority=500):
        self.connected.append([event, handler.__name__])

    def add_config_value(self, *args, **kwargs):
        pass

    def setup_extension(self, name):
        pass


def configured(tutorial):
    config = Config(
        plot_docstring="False",
        plot_gallery="False",
        plot_inline="False",
        plot_tutorial=tutorial,
        nb_execution_mode="cache",
    )
    app = App(config)
    namespace["geovista_execution_mode"](app, config)
    after_config = config["nb_execution_mode"]
    config["nb_execution_mode"] = "cache"
    namespace["geovista_builder_inited"](app)
    return after_config, config["nb_execution_mode"]


app = App(Config())
namespace["setup"](app)
print(json.dumps({
    "off": configured("False"),
    "on": configured("True"),
    "connected": app.connected,
}))
"""
"""Execute ``conf.py``, run its handlers on a stand-in, and report what they set."""


@pytest.fixture(scope="module")
def probed(require: Callable[[str], NoReturn]) -> dict[str, object]:
    """Execute ``conf.py`` in a clean subprocess, and report its handlers' work."""
    try:
        import sphinx_gallery  # noqa: F401, PLC0415
    except ImportError:
        require("sphinx-gallery is not installed")
    # conf.py derives the version from the git repository
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", PROBE, str(DOCS / "_ext"), str(DOCS / "conf.py")],
        capture_output=True,
        text=True,
        check=False,
        cwd=DOCS.parents[1],
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_execution_is_off_without_the_tutorials(probed):
    """Without the tutorials, the configuration turns notebook execution off."""
    assert probed["off"][0] == "off"


def test_execution_is_left_as_configured_with_the_tutorials(probed):
    """With the tutorials, the configured mode stands."""
    assert probed["on"][0] == "cache"


def test_the_mode_is_set_as_the_configuration_is_read(probed):
    """The handler runs on ``config-inited``, before Sphinx compares the config."""
    assert ["config-inited", "geovista_execution_mode"] in probed["connected"]


def test_builder_inited_leaves_the_mode_alone(probed):
    """A change in ``builder-inited`` comes too late, and re-reads every page."""
    assert probed["off"][1] == "cache"
    assert probed["on"][1] == "cache"
