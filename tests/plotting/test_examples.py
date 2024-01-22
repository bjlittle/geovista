# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :mod:`geovista.examples`."""
from __future__ import annotations

import importlib
import os
from pathlib import Path
import shutil

import pytest
import pyvista as pv

import geovista as gv
from geovista.cache import CACHE
from geovista.common import get_modules

BASE_DIR: Path = CACHE.abspath / "tests" / "images"

# determine whether executing on a GHA runner
# https://docs.github.com/en/actions/learn-github-actions/variables#default-environment-variables
CI: bool = os.environ.get("CI", "false").lower() == "true"

# construct list of example module names relative to "geovista.examples"
EXAMPLES = get_modules("geovista.examples")

# prepare geovista/pyvista for off-screen image testing
pv.global_theme.load_theme(pv.plotting.themes._TestingTheme())
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

# individual GHA CI example test case exceptions to the default image tolerances
thresholds = {
    "point_cloud.from_points__orca_cloud": {"warning_value": 202.0},
    "point_cloud.from_points__orca_cloud_eqc": {"warning_value": 250.0},
    "spatial_index.uber_h3": {"warning_value": 446.0},
}


@pytest.mark.example()
@pytest.mark.image()
@pytest.mark.parametrize("example", EXAMPLES)
def test(example, verify_image_cache):
    """Image test the example scripts."""
    # apply individual test case image tolerance exceptions only when
    # executing within a remote GHA runner environment
    if CI and example in thresholds:
        for attr, value in thresholds[example].items():
            setattr(verify_image_cache, attr, value)

    # replace dot notation with double underscores
    safe = example.replace(".", "__")
    verify_image_cache.test_name = f"test_{safe}"
    # import the example module
    module = importlib.import_module(f"geovista.examples.{example}")
    # if necessary, download and cache missing example base image (expected) to
    # compare with the actual test image generated via pytest-pyvista plugin
    if verify_image_cache.add_missing_images is False:
        _ = CACHE.fetch(f"tests/images/{safe}.png")
    # execute the example module for image testing
    module.main()
