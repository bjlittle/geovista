# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.pantry.meshes`."""

from __future__ import annotations

import pytest

from geovista.pantry import meshes


@pytest.mark.parametrize("preference", ["low", "medium", "high", "very_high", "mesh"])
def test_cloud_amount(preference):
    """Test generation of cloud amount meshes."""
    mesh = meshes.cloud_amount(preference=preference)
    assert mesh.n_points == 3538946
    assert mesh.n_cells == 3538944


def test_cloud_amount__preference_bad():
    """Test bad preference for cloud amount mesh."""
    emsg = (
        "Expected a preference of 'low' or 'medium' or 'high' or 'very_high' or 'mesh'."
    )
    with pytest.raises(ValueError, match=emsg):
        _ = meshes.cloud_amount(preference="bad")


def test_dynamico():
    """Test generation of dynamico mesh."""
    mesh = meshes.dynamico()
    assert mesh.n_points == 96012
    assert mesh.n_cells == 16002


def test_fesom():
    """Test generation of fesom mesh."""
    mesh = meshes.fesom()
    assert mesh.n_points == 2283462
    assert mesh.n_cells == 126859


@pytest.mark.parametrize("preference", ["cell", "point"])
def test_fvcom_tamar(preference):
    """Test generation of tamar mesh."""
    mesh = meshes.fvcom_tamar(preference=preference)
    assert mesh.n_points == 39910
    assert mesh.n_cells == 75400


def test_fvcom_tamar__preference_bad():
    """Test bad preference for fvcom tamar mesh."""
    emsg = "Expected a preference of 'cell' or 'point'"
    with pytest.raises(ValueError, match=emsg):
        _ = meshes.fvcom_tamar(preference="bad")


def test_icon_soil():
    """Test generation of icon soil mesh."""
    mesh = meshes.icon_soil()
    assert mesh.n_points == 61440
    assert mesh.n_cells == 20480


def test_lam_equator():
    """Test generation of lam equator mesh."""
    mesh = meshes.lam_equator()
    assert mesh.n_points == 25
    assert mesh.n_cells == 16


def test_lam_falklands():
    """Test generation of lam falklands mesh."""
    mesh = meshes.lam_falklands()
    assert mesh.n_points == 25
    assert mesh.n_cells == 16


def test_lam_london():
    """Test generation of lam london mesh."""
    mesh = meshes.lam_london()
    assert mesh.n_points == 25
    assert mesh.n_cells == 16


def test_lam_new_zealand():
    """Test generation of lam new zealand mesh."""
    mesh = meshes.lam_new_zealand()
    assert mesh.n_points == 25
    assert mesh.n_cells == 16


def test_lam_pacific():
    """Test generation of lam pacific mesh."""
    mesh = meshes.lam_pacific()
    assert mesh.n_points == 153549
    assert mesh.n_cells == 152764


def test_lam_polar():
    """Test generation of lam polar mesh."""
    mesh = meshes.lam_polar()
    assert mesh.n_points == 25
    assert mesh.n_cells == 16


def test_lam_uk():
    """Test generation of lam uk mesh."""
    mesh = meshes.lam_uk()
    assert mesh.n_points == 25
    assert mesh.n_cells == 16


@pytest.mark.parametrize(
    ("resolution", "n_points", "n_cells"),
    [("c48", 13826, 13824), ("c96", 55298, 55296), ("c192", 221186, 221184)],
)
def test_lfric(resolution, n_points, n_cells):
    """Test generation of lfric mesh."""
    mesh = meshes.lfric(resolution=resolution)
    assert mesh.n_points == n_points
    assert mesh.n_cells == n_cells


def test_lfric__resolution_bad():
    """Test bad resolution for lfric mesh."""
    wmsg = "unknown LFRic cubed-sphere resolution"
    with pytest.warns(UserWarning, match=wmsg):
        mesh = meshes.lfric(resolution="bad")
    assert mesh.n_points == 55298
    assert mesh.n_cells == 55296


def test_lfric_orog():
    """Test generation of lfric orog mesh."""
    mesh = meshes.lfric_orog()
    assert mesh.n_points == 13826
    assert mesh.n_cells == 13824


def test_lfric_sst():
    """Test generation of lfric sst mesh."""
    mesh = meshes.lfric_sst()
    assert mesh.n_points == 13826
    assert mesh.n_cells == 13824


def test_regular_grid():
    """Test generation of regular grid mesh."""
    mesh = meshes.regular_grid(resolution="r10")
    assert mesh.n_points == 176
    assert mesh.n_cells == 150


def test_regular_grid__resolution_bad():
    """Test bad resolution of regular grid mesh."""
    wmsg = "Unknown regular grid resolution"
    with pytest.warns(UserWarning, match=wmsg):
        mesh = meshes.regular_grid(resolution="x100")
    assert mesh.n_points == 5551
    assert mesh.n_cells == 5400


def test_oisst_avhrr_sst():
    """Test generation of oisst avhrr sst mesh."""
    mesh = meshes.oisst_avhrr_sst()
    assert mesh.n_points == 1038961
    assert mesh.n_cells == 1036800


def test_nemo_orca2():
    """Test generation of nemo orca2 mesh."""
    mesh = meshes.nemo_orca2()
    assert mesh.n_points == 106560
    assert mesh.n_cells == 26640


def test_nemo_orca2_cloud():
    """Test generation of nemo orca2 cloud mesh."""
    mesh = meshes.nemo_orca2_cloud()
    assert mesh.n_points == 265791
    assert mesh.n_cells == 265791


def test_ww3_global_smc():
    """Test generation of ww3 global smc mesh."""
    mesh = meshes.ww3_global_smc()
    assert mesh.n_points == 2665312
    assert mesh.n_cells == 666328


def test_ww3_global_tri():
    """Test generation of ww3 global tri mesh."""
    mesh = meshes.ww3_global_tri()
    assert mesh.n_points == 16160
    assert mesh.n_cells == 30559
