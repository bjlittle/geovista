# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.active_kernel`."""
from __future__ import annotations

import pytest

from geovista.common import active_kernel


def test_kernel_none():
    """Test with no ipython kernel."""
    assert not active_kernel()


@pytest.mark.parametrize("exception", [AttributeError, ModuleNotFoundError])
def test_kernel__exception(mocker, exception):
    """Test with a mock ipython kernel raising exceptions."""
    module = mocker.MagicMock(get_ipython=mocker.MagicMock(side_effect=exception))
    mocker.patch.dict("sys.modules", IPython=module)
    assert not active_kernel()


def test_kernel_active(mocker):
    """Test with a mock active ipython kernel."""
    kernel = mocker.sentinel.kernel
    module = mocker.MagicMock(get_ipython=mocker.MagicMock(kernel=kernel))
    mocker.patch.dict("sys.modules", IPython=module)
    assert active_kernel()
