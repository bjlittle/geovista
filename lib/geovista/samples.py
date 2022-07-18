"""
This module contains convenience functions to download, cache and load
geovista sample data.

"""

from dataclasses import dataclass, field

import netCDF4 as nc
import numpy.typing as npt
import pooch

from .cache import CACHE

__all__ = ["ww3_gbl_tri_hs"]


@dataclass(frozen=True)
class SampleDataXY:
    lons: npt.ArrayLike
    lats: npt.ArrayLike
    connectivity: npt.ArrayLike
    data: npt.ArrayLike
    name: str = field(default=None)
    units: str = field(default=None)
    ndim: int = 2


def ww3_gbl_tri_hs() -> SampleDataXY:
    """
    Load the WAVEWATCH III (WW3) unstructured triangular mesh.

    Returns
    -------
    SampleDataXY

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "ww3_gbl_tri_hs.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"samples/{fname}.bz2", processor=processor)
    ds = nc.Dataset(resource)

    # load the lon/lat points
    lons = ds.variables["longitude"][:]
    lats = ds.variables["latitude"][:]

    # load the connectivity
    offset = 1  # minimum connectivity index offset
    connectivity = ds.variables["tri"][:] - offset

    # we know this is a timeseries, a priori
    idx = 0

    # load mesh payload
    data = ds.variables["hs"]
    name = data.standard_name
    units = data.units

    sample = SampleDataXY(lons, lats, connectivity, data[idx], name, units)

    return sample
