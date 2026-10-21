# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.themes.ThemeMixin`."""

from __future__ import annotations

import pytest
from pyvista.plotting.themes import Theme

from geovista.themes import GeoVistaDocumentTheme, GeoVistaTheme, ThemeMixin


def test_runtime_base_is_object():
    """The theme base mypy sees never reaches runtime (typing spec §3.5)."""
    assert ThemeMixin.__bases__ == (object,)


@pytest.mark.parametrize("theme", [GeoVistaDocumentTheme, GeoVistaTheme])
def test_mro(theme):
    """Each theme finds the mixin before pyvista's theme."""
    mro = theme.__mro__
    assert mro.index(ThemeMixin) < mro.index(Theme)


@pytest.mark.parametrize("theme", [GeoVistaDocumentTheme, GeoVistaTheme])
def test_unknown_attribute_fail(theme):
    """Test a theme refuses an attribute it does not have, as pyvista's do."""
    with pytest.raises(AttributeError):
        theme().not_a_theme_property = "black"
