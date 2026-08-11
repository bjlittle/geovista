# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""pytest fixture infra-structure for image comparison unit-tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def verify_image_cache(verify_image_cache, plot_nodeid):
    """Fixture overriding the ``pytest-pyvista`` image cache verifier.

    A test may have a *directory* of baseline image variants in the cache,
    rather than a single baseline image, where each variant is an equally valid
    render for a specific dependency stack e.g., ``+proj=eqc`` renders differ
    between ``PROJ <9.8`` and ``PROJ >=9.8``.

    However, ``pytest-pyvista`` only compares a render against the remaining
    variants when the *error* threshold is exceeded. A render which merely
    exceeds the *warning* threshold is never adjudicated against the other
    variants, and the resultant warning is promoted to a test failure by the
    ``filterwarnings`` configuration.

    Therefore, collapse the error threshold onto the warning threshold for such
    tests, so that any render which is not a close match to the first variant is
    compared against all the other variants before failing.

    """
    # pytest-pyvista removes the "test_" prefix from the baseline image, and
    # uses the resultant stem as the name of the image variants directory
    stem = plot_nodeid.removeprefix("test_")

    if (Path(verify_image_cache.cache_dir) / stem).is_dir():
        verify_image_cache.error_value = verify_image_cache.warning_value

    return verify_image_cache
