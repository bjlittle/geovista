# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.cache.pooch_mute`."""

from __future__ import annotations

from pooch import get_logger

from geovista.cache import pooch_mute


def test():
    """Test all behaviours as one atomic test."""
    logger = get_logger()

    # default silent kwarg
    previous = pooch_mute()
    assert logger.getEffectiveLevel() == 30
    from geovista.cache import GEOVISTA_POOCH_MUTE

    assert GEOVISTA_POOCH_MUTE is True
    assert previous is False

    # explicit verbose
    previous = pooch_mute(silent=False)
    assert logger.getEffectiveLevel() == 0
    from geovista.cache import GEOVISTA_POOCH_MUTE

    assert GEOVISTA_POOCH_MUTE is False
    assert previous is True

    # explicit silence
    previous = pooch_mute(silent=True)
    assert logger.getEffectiveLevel() == 30
    from geovista.cache import GEOVISTA_POOCH_MUTE

    assert GEOVISTA_POOCH_MUTE is True
    assert previous is False
