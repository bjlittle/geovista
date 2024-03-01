# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""pytest fixture infra-structure for :mod:`geovista.gridlines` unit-tests."""

from __future__ import annotations


def deindex(keys: list[str, ...] | str) -> list[str, ...] | str:
    """Remove the index from the GraticuleGrid.blocks.keys()."""
    if isinstance(keys, str):
        result = keys.split(",")[1]
    else:
        result = [key.split(",")[1] for key in keys]
    return result
