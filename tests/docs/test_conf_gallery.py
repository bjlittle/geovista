# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the parallel ``sphinx-gallery`` configuration in ``conf.py``.

``conf.py`` is executed in a subprocess, from a clean environment, so that what
it configures is observed exactly as a documentation build sees it.

"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import NoReturn

try:
    import sphinx_gallery
except ImportError:
    sphinx_gallery = None

DOCS = Path(__file__).parents[2] / "docs" / "src"

PROBE = """
import json, os, runpy, subprocess, sys
sys.path.insert(0, sys.argv[1])
namespace = runpy.run_path(sys.argv[2])
# a gallery worker is a fresh process, which sees only the environment
child = subprocess.run(
    [sys.executable, "-c", "import pyvista; print(pyvista.OFF_SCREEN)"],
    capture_output=True, text=True, check=True,
)
print(json.dumps({
    "parallel": namespace["sphinx_gallery_conf"].get("parallel", False),
    "cpus": os.process_cpu_count(),
    "child_off_screen": child.stdout.strip(),
}))
"""
"""Execute ``conf.py`` and report what a documentation build would see."""


@pytest.fixture
def probe(require: Callable[[str], NoReturn]) -> Callable[..., dict[str, object]]:
    """Provide a factory that executes ``conf.py`` in a clean subprocess."""
    if sphinx_gallery is None:
        require("sphinx-gallery is not installed")

    def run(**environ: str) -> dict[str, object]:
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"PYVISTA_OFF_SCREEN", "GEOVISTA_SPHX_GLR_SERIAL"}
        }
        env.update(environ)
        # conf.py derives the version from the git repository
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-c", PROBE, str(DOCS / "_ext"), str(DOCS / "conf.py")],
            capture_output=True,
            text=True,
            check=False,
            cwd=DOCS.parents[1],
            env=env,
        )
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout.strip().splitlines()[-1])

    return run


def test_parallel(probe):
    """Test the gallery is built with up to four workers by default."""
    result = probe()
    workers = min(4, result["cpus"])
    assert result["parallel"] == (workers if workers > 1 else False)


def test_serial(probe):
    """Test the gallery is built serially on request."""
    assert probe(GEOVISTA_SPHX_GLR_SERIAL="1")["parallel"] is False


def test_worker_off_screen(probe):
    """Test a fresh gallery worker process renders off-screen.

    A worker that does not opens an on-screen window under ``xvfb-run`` and
    waits on it forever, which is how a parallel Read the Docs build hung.

    """
    assert probe()["child_off_screen"] == "True"
