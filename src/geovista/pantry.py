"""
This module contains convenience functions to download, cache and load
geovista sample data, which can then be used by the :mod:`geovista.bridge`
to generate a mesh.

Notes
-----
.. versionadded:: 0.1.0

"""
from dataclasses import dataclass, field
from typing import Optional

import netCDF4 as nc
import numpy as np
from numpy import ma
import numpy.typing as npt
import pooch

from .cache import CACHE

__all__ = [
    "fesom",
    "fvcom_tamar",
    "hexahedron",
    "icon_soil",
    "lam_equator",
    "lam_falklands",
    "lam_london",
    "lam_new_zealand",
    "lam_pacific",
    "lam_polar",
    "lam_uk",
    "lfric_orog",
    "lfric_sst",
    "oisst_avhrr_sst",
    "um_orca2",
    "ww3_global_smc",
    "ww3_global_tri",
]


@dataclass(frozen=True)
class SampleStructuredXY:
    lons: npt.ArrayLike
    lats: npt.ArrayLike
    data: npt.ArrayLike = field(default=None)
    name: str = field(default=None)
    units: str = field(default=None)
    steps: int = field(default=None)
    ndim: int = 2


@dataclass(frozen=True)
class SampleUnstructuredXY:
    lons: npt.ArrayLike
    lats: npt.ArrayLike
    connectivity: npt.ArrayLike
    data: npt.ArrayLike = field(default=None)
    face: npt.ArrayLike = field(default=None)
    node: npt.ArrayLike = field(default=None)
    start_index: int = field(default=None)
    name: str = field(default=None)
    units: str = field(default=None)
    steps: int = field(default=None)
    ndim: int = 2


def capitalise(title: str) -> str:
    """
    Format the title by capitalising each word and replacing
    inappropriate characters.

    Parameters
    ----------
    title : str
        The string title to be reformatted.

    Returns
    -------
    str

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    title = title.replace("_", " ")
    title = title.split(" ")
    title = " ".join([word.capitalize() for word in title])

    return title


def fesom(step: Optional[int] = None) -> SampleUnstructuredXY:
    """
    Load AWI-CM FESOM 1.4 unstructured mesh.

    Parameters
    ----------
    step : int, default=0
        The time-series offset.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "tos_Omon_AWI-ESM-1-1-LR_historical_r1i1p1f1_gn_185001-185012.nc"
    resource = CACHE.fetch(f"{fname}")
    dataset = nc.Dataset(resource)

    # load the lon/lat cell grid
    lons = dataset.variables["lon_bnds"][:]
    lats = dataset.variables["lat_bnds"][:]
    shape = lons.shape
    n_cells = shape[0]

    emsg = (
        "Unable to create FESOM pantry sample, as spatial points have "
        f"different shapes. Got '{lons.shape=}' and '{lats.shape=}'."
    )
    assert shape == lats.shape, emsg

    # load the mesh payload
    data = dataset.variables["tos"]
    name = capitalise(data.standard_name)
    units = data.units

    # deal with the time-series step
    steps = dataset.dimensions["time"].size
    idx = 0 if step is None else (step % steps)

    # construct the masked connectivity based on protocol of
    # repeated identical trailing spatial values being used
    # to identify padding to fill the fixed number of points
    # for all cells
    lons_mask = ~np.array(np.diff(lons), dtype=bool)
    lats_mask = ~np.array(np.diff(lats), dtype=bool)

    emsg = "Unable to create FESOM pantry sample, as cell point masks are not equal."
    assert np.array_equal(lons_mask, lats_mask), emsg

    mask = np.hstack([np.zeros(n_cells, dtype=bool).reshape(-1, 1), lons_mask])
    connectivity = ma.arange(np.prod(shape), dtype=np.uint32).reshape(shape)
    connectivity.mask = mask

    sample = SampleUnstructuredXY(
        lons, lats, connectivity, data=data[idx], name=name, units=units, steps=steps
    )

    return sample


def fvcom_tamar() -> SampleUnstructuredXY:
    """
    Load PML FVCOM unstructured mesh.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "fvcom_tamar.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"pantry/{fname}.bz2", processor=processor)
    dataset = nc.Dataset(resource)

    # load the lon/lat cell grid
    lons = dataset.variables["lon"][:]
    lats = dataset.variables["lat"][:]

    # load the face/node connectivity
    offset = 1  # minimum connectivity index offset
    connectivity = dataset.variables["nv"][:]

    # load the mesh payload
    face = dataset.variables["h_center"]
    name = capitalise(face.standard_name)
    units = face.units
    node = dataset.variables["h"][:]

    sample = SampleUnstructuredXY(
        lons,
        lats,
        connectivity.T,
        face=face[:],
        node=node,
        start_index=offset,
        name=name,
        units=units,
    )

    return sample


def hexahedron() -> SampleUnstructuredXY:
    """
    Load DYNAMICO hexahedron unstructured mesh.

    Returns
    -------
    SampleUnstructuredXY
        The hexagonal unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "hexahedron.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"pantry/{fname}.bz2", processor=processor)
    dataset = nc.Dataset(resource)

    # load the lon/lat hex cell grid
    lons = dataset.variables["bounds_lon_i"][:]
    lats = dataset.variables["bounds_lat_i"][:]

    # load the mesh payload
    data = dataset.variables["phis"][:]
    name = capitalise("synthetic")
    units = "1"

    sample = SampleUnstructuredXY(
        lons, lats, lons.shape, data=data, name=name, units=units
    )

    return sample


def icon_soil() -> SampleUnstructuredXY:
    """
    Load Icosahedral Nonhydrostatic Weather and Climate Model (ICON)
    global 160km resolution (R02B04 grid) triangular mesh.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and data payload.

    Sourced from http://icon-downloads.mpimet.mpg.de/dwd_grids.xml

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "icon_extpar_0010_R02B04_G.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"pantry/{fname}.bz2", processor=processor)
    dataset = nc.Dataset(resource)

    # load the lon/lat triangular cell grid (radians)
    rlons = dataset.variables["clon_vertices"][:]
    rlats = dataset.variables["clat_vertices"][:]

    # convert from radians to degrees
    lons = np.rad2deg(rlons)
    lats = np.rad2deg(rlats)

    # load the mesh payload
    data = dataset.variables["SOILTYP"][:]
    name = capitalise("soil type")
    units = "1"

    sample = SampleUnstructuredXY(
        lons, lats, lons.shape, data=data, name=name, units=units
    )

    return sample


def _gungho_lam(fname: str) -> SampleUnstructuredXY:
    """
    Load the GungHo C4 cubed-sphere LAM unstructured mesh.

    Parameters
    ----------
    fname : str
        The file name of the resource to load.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and connectivity.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"pantry/lams/{fname}.bz2", processor=processor)
    dataset = nc.Dataset(resource)

    # load the lon/lat cell grid
    lons = dataset.variables["gungho_node_x"]
    lats = dataset.variables["gungho_node_y"]

    # load the face/node connectivity
    connectivity = dataset.variables["gungho_face_nodes"]
    start_index = connectivity.start_index

    sample = SampleUnstructuredXY(lons, lats, connectivity[:], start_index=start_index)

    return sample


def lam_equator() -> SampleUnstructuredXY:
    """
    Load the GungHo C4 cubed-sphere LAM unstructured mesh located over
    the equator.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and connectivity.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _gungho_lam("equator.nc")


def lam_falklands() -> SampleUnstructuredXY:
    """
    Load the GungHo C4 cubed-sphere LAM unstructured mesh located over
    the Falkland Islands.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and connectivity.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _gungho_lam("falklands.nc")


def lam_london() -> SampleUnstructuredXY:
    """
    Load the GungHo C4 cubed-sphere LAM unstructured mesh located over
    London, UK.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and connectivity.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _gungho_lam("london.nc")


def lam_new_zealand() -> SampleUnstructuredXY:
    """
    Load the GungHo C4 cubed-sphere LAM unstructured mesh located over
    New Zealand.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and connectivity.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _gungho_lam("new_zealand.nc")


def lam_pacific() -> SampleUnstructuredXY:
    """
    Load a high-resolution LAM unstructured mesh located over the Pacific Ocean.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "lam.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"pantry/{fname}.bz2", processor=processor)
    dataset = nc.Dataset(resource)

    # load the lon/lat cell grid
    lons = dataset.variables["Mesh2d_face_node_x"][:]
    lats = dataset.variables["Mesh2d_face_node_y"][:]

    # load the face/node connectivity
    connectivity = dataset.variables["Mesh2d_face_face_nodes"]
    start_index = connectivity.start_index

    # load the mesh payload
    data = dataset.variables["theta"]
    name = capitalise(data.standard_name)
    units = data.units

    sample = SampleUnstructuredXY(
        lons,
        lats,
        connectivity[:],
        data=data[:],
        start_index=start_index,
        name=name,
        units=units,
    )

    return sample


def lam_polar() -> SampleUnstructuredXY:
    """
    Load the GungHo C4 cubed-sphere LAM unstructured mesh located over the
    Polar cap.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and connectivity.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _gungho_lam("polar.nc")


def lam_uk() -> SampleUnstructuredXY:
    """
    Load the GungHo C4 cubed-sphere LAM unstructured mesh located over the UK.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and connectivity.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _gungho_lam("uk.nc")


def lfric_orog() -> SampleUnstructuredXY:
    """
    Load CF UGRID global nodal orography unstructured mesh.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "qrparam_shared.orog.ugrid.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"pantry/{fname}.bz2", processor=processor)
    dataset = nc.Dataset(resource)

    # load the lon/lat cell grid
    lons = dataset.variables["dynamics_node_x"][:]
    lats = dataset.variables["dynamics_node_y"][:]

    # load the face/node connectivity
    connectivity = dataset.variables["dynamics_face_nodes"]
    start_index = connectivity.start_index

    # load the mesh payload
    data = dataset.variables["nodal_surface_altitude"]
    name = capitalise(data.standard_name)
    units = data.units

    sample = SampleUnstructuredXY(
        lons,
        lats,
        connectivity[:],
        data=data[:],
        start_index=start_index,
        name=name,
        units=units,
    )

    return sample


def lfric_sst() -> SampleUnstructuredXY:
    """
    Load CF UGRID global unstructured mesh.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "qrclim.sst.ugrid.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"pantry/{fname}.bz2", processor=processor)
    dataset = nc.Dataset(resource)

    # load the lon/lat cell grid
    lons = dataset.variables["dynamics_node_x"][:]
    lats = dataset.variables["dynamics_node_y"][:]

    # load the face/node connectivity
    connectivity = dataset.variables["dynamics_face_nodes"]
    start_index = connectivity.start_index

    # load the mesh payload
    data = dataset.variables["surface_temperature"]
    name = capitalise(data.standard_name)
    units = data.units

    sample = SampleUnstructuredXY(
        lons,
        lats,
        connectivity[:],
        data=data[:],
        start_index=start_index,
        name=name,
        units=units,
    )

    return sample


def oisst_avhrr_sst() -> SampleStructuredXY:
    """
    Load NOAA/NCEI OISST AVHRR rectilinear mesh.

    Returns
    -------
    SampleStructuredXY
        The curvilinear spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "oisst-avhrr.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"pantry/{fname}.bz2", processor=processor)
    dataset = nc.Dataset(resource)

    # load the lon/lat grid
    lons = dataset.variables["lon_bnds"][:]
    lats = dataset.variables["lat_bnds"][:]

    # load the mesh payload
    data = dataset.variables["sst"]
    name = capitalise(data.long_name)
    units = data.units

    sample = SampleStructuredXY(lons, lats, data=data[0, 0], name=name, units=units)

    return sample


def um_orca2() -> SampleStructuredXY:
    """
    Load Met Office Unified Model (UM) ORCA2 curvilinear mesh.

    Returns
    -------
    SampleStructuredXY
        The curvilinear spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "votemper.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"pantry/{fname}.bz2", processor=processor)
    dataset = nc.Dataset(resource)

    # load the lon/lat grid
    lons = dataset.variables["lont_bounds"][:]
    lats = dataset.variables["latt_bounds"][:]

    # load the mesh payload
    data = dataset.variables["votemper"]
    name = capitalise(data.standard_name)
    units = data.units

    sample = SampleStructuredXY(lons, lats, data=data[0, 0], name=name, units=units)

    return sample


def ww3_global_smc(step: Optional[int] = None) -> SampleUnstructuredXY:
    """
    Load the WAVEWATCH III (WW3) unstructured Spherical Multi-Cell (SMC) mesh.

    Parameters
    ----------
    step : int, default=0
        The time-series offset.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "ww3_gbl_smc_hs.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"pantry/ww3/{fname}.bz2", processor=processor)
    dataset = nc.Dataset(resource)

    # load the lon/lat grid cell centres
    cc_lons = dataset.variables["longitude"][:]
    cc_lats = dataset.variables["latitude"][:]

    # load integer scaling factor for the grid cells
    cx_coord = dataset.variables["cx"][:]
    cy_coord = dataset.variables["cy"][:]
    base_lon_size = dataset.getncattr("base_lon_size")
    base_lat_size = dataset.getncattr("base_lat_size")

    # construct the grid cells
    dlon = cx_coord * base_lon_size
    dlat = cy_coord * base_lat_size
    fac = 0.5
    x1_coord = (cc_lons - fac * dlon).reshape(-1, 1)
    x2_coord = (cc_lons + fac * dlon).reshape(-1, 1)
    y1_coord = (cc_lats - fac * dlat).reshape(-1, 1)
    y2_coord = (cc_lats + fac * dlat).reshape(-1, 1)

    lons = np.hstack([x1_coord, x2_coord, x2_coord, x1_coord])
    lats = np.hstack([y1_coord, y1_coord, y2_coord, y2_coord])

    # deal with the time-series step
    steps = dataset.dimensions["time"].size
    idx = 0 if step is None else (step % steps)

    # load mesh payload
    data = dataset.variables["hs"]
    name = capitalise(data.standard_name)
    units = data.units

    sample = SampleUnstructuredXY(
        lons, lats, lons.shape, data=data[idx], name=name, units=units, steps=steps
    )

    return sample


def ww3_global_tri() -> SampleUnstructuredXY:
    """
    Load the WAVEWATCH III (WW3) unstructured triangular mesh.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "ww3_gbl_tri_hs.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"pantry/ww3/{fname}.bz2", processor=processor)
    dataset = nc.Dataset(resource)

    # load the lon/lat points
    lons = dataset.variables["longitude"][:]
    lats = dataset.variables["latitude"][:]

    # load the face/node connectivity
    offset = 1  # minimum connectivity index offset
    connectivity = dataset.variables["tri"][:]

    # we know this is a single step timeseries, a priori
    idx = 0

    # load mesh payload
    data = dataset.variables["hs"]
    name = capitalise(data.standard_name)
    units = data.units

    sample = SampleUnstructuredXY(
        lons,
        lats,
        connectivity,
        data=data[idx],
        start_index=offset,
        name=name,
        units=units,
    )

    return sample
