# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :class:`geovista.report.Report`."""

from __future__ import annotations

import pytest
import scooby

from geovista.report import Report


@pytest.mark.parametrize(
    "additional",
    ["scooby", scooby, ["scooby"], [scooby]],
    ids=["name", "module", "names", "modules"],
)
def test_additional(additional):
    """Test a single package or a list of them is reported."""
    report = Report(additional=additional, gpu=False)
    assert "scooby" in report.packages


def test_gpu(mocker):
    """Test the GPU details are reported."""
    gpu_info = mocker.patch("pyvista.GPUInfo")
    gpu_info.return_value.get_info.return_value = [("GPU Vendor", "geovista")]
    report = Report()
    assert "GPU Vendor" in str(report)
    assert "geovista" in str(report)


def test_gpu_fail(mocker):
    """Test a GPU fault is reported, not raised."""
    mocker.patch("pyvista.GPUInfo", side_effect=RuntimeError)
    report = Report()
    assert "GPU Details : Error" in " ".join(str(report).split())


def test_no_gpu():
    """Test the GPU details are skipped when not wanted."""
    report = Report(gpu=False)
    assert "GPU Details : None" in " ".join(str(report).split())
