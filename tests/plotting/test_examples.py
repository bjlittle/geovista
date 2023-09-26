"""Unit-test for :mod:`geovista.examples`."""

from geovista.examples import earthquakes


def test_earthquakes(verify_image_cache):
    """Image test of earthquakes examples."""
    earthquakes.main(off_screen=True)
