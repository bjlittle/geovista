# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests with plotting image comparison."""

from __future__ import annotations

import os
from pathlib import Path
import shutil

import pyvista as pv

import geovista as gv
from geovista.cache import CACHE

BASE_DIR: Path = CACHE.abspath / "tests" / "unit"

# determine whether executing on a GHA runner
# https://docs.github.com/en/actions/learn-github-actions/variables#default-environment-variables
CI: bool = os.environ.get("CI", "false").lower() == "true"

# prepare geovista/pyvista for off-screen image testing
pv.global_theme.load_theme(pv.plotting.themes._TestingTheme())  # noqa: SLF001
pv.global_theme.background = "white"
pv.global_theme.cmap = "balance"
pv.global_theme.font.color = "black"
pv.global_theme.window_size = [450, 300]
pv.OFF_SCREEN = True
gv.GEOVISTA_IMAGE_TESTING = True

# prepare to download image cache for each image test
# also see reference in pyproject.toml
cache_dir = Path(__file__).parent.resolve() / "image_cache"
if cache_dir.is_dir() and not cache_dir.is_symlink():
    # remove directory which may have been created by pytest-pyvista
    # when plugin is bootstrapped by pytest
    shutil.rmtree(str(cache_dir))

if cache_dir.is_symlink() and (
    not cache_dir.exists() or cache_dir.readlink() != BASE_DIR
):
    # detected a broken symlink or non-latest version of cache
    cache_dir.unlink()

if not cache_dir.exists():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    # create the symbolic link to the pooch cache
    cache_dir.symlink_to(BASE_DIR)
