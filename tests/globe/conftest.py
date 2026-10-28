# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""pytest fixture infra-structure for :mod:`geovista.globe` unit-tests."""

from __future__ import annotations

import pytest

from geovista import common, globe


@pytest.fixture
def reordered_fields(monkeypatch):
    """Reverse the tuple of the four globe fields, wherever a module binds it.

    A globe that pairs its values with the field names by their place in the
    tuple then writes, or reads, each value in the wrong field.
    """
    fields = common._GV_GLOBE_FIELDS
    reordered = tuple(reversed(fields))
    for module in (common, globe):
        names = [name for name, value in vars(module).items() if value is fields]
        for name in names:
            monkeypatch.setattr(module, name, reordered)
