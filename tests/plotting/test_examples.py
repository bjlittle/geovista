"""Unit-tests for :mod:`geovista.examples`."""
from __future__ import annotations

import importlib
import pkgutil

import pytest

from geovista.cache import CACHE
import geovista.examples

# construct list of example script names
SCRIPTS = sorted(
    [submodule.name for submodule in pkgutil.iter_modules(geovista.examples.__path__)]
)


@pytest.mark.image
@pytest.mark.mpl_image_compare
@pytest.mark.parametrize("script", SCRIPTS)
def test(script, screenshot):
    """Perform an image test of each example script."""
    # import the example script
    module = importlib.import_module(f"geovista.examples.{script}")

    # if necessary, download and cache missing script base image (expected) to
    # compare with the actual test image generated via pytest-mpl plugin
    _ = CACHE.fetch(f"tests/images/{script}.png")

    # execute the example script for image testing
    module.main()

    return screenshot.figure
