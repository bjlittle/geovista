"""Unit-tests for :mod:`geovista.examples`."""

from geovista.examples import earthquakes


def test_earthquakes(verify_image_cache):
    """Test earthquakes example."""
    earthquakes.main(off_screen=True, verify_image_cache=verify_image_cache)
