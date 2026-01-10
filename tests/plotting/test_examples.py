# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :mod:`geovista.examples`."""

from __future__ import annotations

import importlib

import pytest

from geovista.common import get_modules

from . import CI

# construct list of example module names relative to "geovista.examples"
EXAMPLES = get_modules("geovista.examples")

# individual GHA CI example test case exceptions to the default image tolerances
thresholds = {
    "point_cloud.from_points__orca_cloud": {"warning_value": 202.0},
    "point_cloud.from_points__orca_cloud_eqc": {"warning_value": 250.0},
    "spatial_index.uber_h3": {"warning_value": 450.0},
}


@pytest.mark.example
@pytest.mark.image
@pytest.mark.parametrize("example", EXAMPLES)
def test(plot_nodeid, example, verify_image_cache):
    """Image test the example scripts."""
    verify_image_cache.test_name = plot_nodeid

    # apply individual test case image tolerance exceptions only when
    # executing within a remote GHA runner environment
    if CI and example in thresholds:
        for attr, value in thresholds[example].items():
            setattr(verify_image_cache, attr, value)

    try:
        # import the example module
        module = importlib.import_module(f"geovista.examples.{example}")
        # execute the example module for image testing
        module.main()
    except ImportError:
        pytest.skip("optional dependency missing")
