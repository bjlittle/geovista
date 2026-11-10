# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Benchmarks of :mod:`geovista.gridlines`."""

from __future__ import annotations

import pytest

from geovista.gridlines import create_meridians, create_parallels


@pytest.mark.limit_memory("1 MB")
def test_create_meridians(benchmark):
    """Create the graticule's meridians (bench spec §2 decision 7)."""
    result = benchmark(create_meridians)
    assert result.blocks


@pytest.mark.limit_memory("1 MB")
def test_create_parallels(benchmark):
    """Create the graticule's parallels (bench spec §2 decision 7)."""
    result = benchmark(create_parallels)
    assert result.blocks
