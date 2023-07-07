"""pytest fixture infra-structure for :mod:`geovista.gridlines` unit-tests."""
from __future__ import annotations


def deindex(keys: list[str, ...] | str) -> list[str, ...] | str:
    """Remove the index from the GraticuleGrid.blocks.keys()."""
    if isinstance(keys, str):
        result = keys.split(",")[1]
    else:
        result = [key.split(",")[1] for key in keys]
    return result
