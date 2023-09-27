"""Unit-test for :mod:`geovista.examples`."""

from geovista.examples import earthquakes


def test_earthquakes(verify_image_cache):
    """Image test of earthquakes examples."""
    verify_image_cache.high_variance_test = True
    verify_image_cache.var_error_value = 4470
    earthquakes.main(off_screen=True)
