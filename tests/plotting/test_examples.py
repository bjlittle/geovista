"""Unit-tests for :mod:`geovista.examples`."""

import pyvista as pv

from geovista.examples import earthquakes

pv.OFF_SCREEN = True


def test_earthquakes(verify_image_cache):
    """Image test of earthquakes example."""
    verify_image_cache.high_variance_test = True
    verify_image_cache.var_error_value = (value := 4470)
    verify_image_cache.var_warning_value = value
    earthquakes.main()
