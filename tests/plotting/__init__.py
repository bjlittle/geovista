# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests with plotting image comparison."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import threading

import pyvista as pv

from geovista.cache import CACHE
import geovista.config as gvc

BASE_DIR: Path = CACHE.abspath / "tests" / "unit"

# determine whether executing on a GHA runner
# https://docs.github.com/en/actions/learn-github-actions/variables#default-environment-variables
CI: bool = os.environ.get("CI", "false").lower() == "true"

# prepare geovista/pyvista for off-screen image testing
pv.global_theme.load_theme(pv.plotting.themes._TestingTheme())
pv.global_theme.background = "white"
pv.global_theme.cmap = "balance"
pv.global_theme.font.color = "black"
pv.global_theme.window_size = [450, 300]
pv.OFF_SCREEN = True
gvc.GEOVISTA_IMAGE_TESTING = True


def link_image_cache(link: Path, target: Path) -> None:
    """Link the image cache directory to the pooch cache of baseline images.

    Safe to call concurrently, as every pytest-xdist worker does on import.

    """
    if link.is_dir() and not link.is_symlink():
        # remove directory which may have been created by pytest-pyvista
        # when plugin is bootstrapped by pytest, tolerating a concurrent
        # worker that has already removed or replaced it
        shutil.rmtree(str(link), ignore_errors=True)

    if link.is_symlink() and link.exists() and link.readlink() == target:
        return

    target.mkdir(parents=True, exist_ok=True)
    # create the symbolic link under a name unique to this caller, then
    # rename it into place, which atomically replaces any broken or stale
    # link to another cache version, or one just made by a concurrent worker
    tmp = link.with_name(f".{link.name}.{os.getpid()}.{threading.get_ident()}")
    tmp.unlink(missing_ok=True)
    tmp.symlink_to(target)
    try:
        tmp.replace(link)
    finally:
        tmp.unlink(missing_ok=True)


# prepare to download image cache for each image test
# also see reference in pyproject.toml
link_image_cache(Path(__file__).resolve().parent / "unit_image_cache", BASE_DIR)
