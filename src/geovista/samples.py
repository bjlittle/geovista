"""Download, cache, load and transform geovista sample data into a pyvista mesh.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

from warnings import warn

import numpy as np
import pooch
import pyvista as pv

from geovista import pantry

from .bridge import Transform
from .cache import CACHE
from .common import Preference

__all__ = [
    "LFRIC_RESOLUTION",
    "LFRIC_RESOLUTIONS",
    "PREFERENCE",
    "REGULAR_RESOLUTION",
    "WARP_FACTOR",
    "ZLEVEL_SCALE_CLOUD",
    "cloud_amount",
    "fesom",
    "fvcom_tamar",
    "icon_soil",
    "icosahedral",
    "lam_equator",
    "lam_falklands",
    "lam_london",
    "lam_new_zealand",
    "lam_pacific",
    "lam_polar",
    "lam_uk",
    "lfric",
    "lfric_orog",
    "lfric_sst",
    "oisst_avhrr_sst",
    "regular_grid",
    "um_orca2",
    "um_orca2_cloud",
    "ww3_global_smc",
    "ww3_global_tri",
]

#: The default LFRic model unstructured cubed-sphere resolution.
LFRIC_RESOLUTION: str = "c96"

#: The available Met Office cubed-sphere assets.
LFRIC_RESOLUTIONS: list[str] = ["c48", "c96", "c192"]

#: The default mesh preference.
PREFERENCE: Preference = Preference.CELL

#: Default regular grid resolution.
REGULAR_RESOLUTION: str = "r60"

#: The default warp factor for mesh points.
WARP_FACTOR: float = 2e-5

#: Proportional multiplier for point-cloud levels/offsets.
ZLEVEL_SCALE_CLOUD: float = 1e-5


def _lfric_sample_to_mesh(sample: pantry.SampleUnstructuredXY) -> pv.PolyData:
    """Transform the provided pantry `sample` into a mesh.

    Parameters
    ----------
    sample : SampleUnstructuredXY
        The unstructured spatial coordinates and connectivity.

    Returns
    -------
    PolyData
        The unstructured cubed-sphere mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    mesh = Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        start_index=sample.start_index,
    )

    return mesh


def cloud_amount(preference: str | pantry.CloudPreference | None = None) -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a Met Office c768 unstructured cubed-sphere with
    optional cloud amount data.

    Parameters
    ----------
    preference : str or CloudPreference, optional
        The cloud type, which may be ``low``, ``medium``, ``high``,
        ``very_high`` or ``mesh``. Defaults to ``mesh``, the
        c768 mesh with no data payload attached.

    Returns
    -------
    pv.PolyData
        The unstructured cubed-sphere mesh.

    Notes
    -----
    .. versionadded:: 0.4.0

    """
    if preference is None:
        preference = pantry.CLOUD_AMOUNT_PREFERENCE

    if not pantry.CloudPreference.valid(preference):
        options = " or ".join(f"{item!r}" for item in pantry.CloudPreference.values())
        emsg = f"Expected a preference of {options}, got '{preference}'."
        raise ValueError(emsg)

    preference = pantry.CloudPreference(preference)

    sample = pantry.cloud_amount(preference)
    mesh = _lfric_sample_to_mesh(sample)

    if preference != pantry.CloudPreference.MESH:
        mesh[sample.name] = sample.data

    return mesh


def fesom() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a AWI-CM FESOM 1.4 mesh with Sea Surface Temperature data.

    Returns
    -------
    PolyData
        The FESOM mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    sample = pantry.fesom()

    mesh = Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
        name=sample.name,
    )

    return mesh


def fvcom_tamar(
    preference: str | Preference | None = None,
    warp: bool | None = False,
    factor: float | None = None,
) -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a Plymouth Marine Laboratory (PML) Finite Volume Community Ocean
    Model (FVCOM) mesh of the Tamar Estuaries and Plymouth Sound.

    Parameters
    ----------
    preference : str or Preference, optional
        Render the mesh using ``cell`` or ``point`` data. Defaults to
        :data:`PREFERENCE`.
    warp : boolean, default=False
        Warp the mesh nodes by the ``point`` data.
    factor : float, optional
        The scale factor used to warp the mesh. Defaults to
        :data:`WARP_FACTOR`.

    Returns
    -------
    PolyData
        The FVCOM mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if preference is None:
        preference = PREFERENCE

    if not Preference.valid(preference):
        options = " or ".join(f"{item!r}" for item in Preference.values())
        emsg = f"Expected a preference of {options}, got '{preference}'."
        raise ValueError(emsg)

    preference = Preference(preference)

    if factor is None:
        factor = WARP_FACTOR

    sample = pantry.fvcom_tamar()
    data = sample.face if preference == Preference.CELL else sample.node
    name = sample.name

    mesh = Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=data,
        name=name,
    )

    if warp:
        if preference == Preference.CELL:
            mesh.point_data[name] = sample.node

        mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
        mesh.warp_by_scalar(scalars=name, inplace=True, factor=factor)

    mesh.set_active_scalars(name, preference.value)

    return mesh


def icon_soil() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate an Icosahedral Nonhydrostatic Weather and Climate Model (ICON)
    global 160km resolution (R02B04 grid) triangular mesh with soil type data.

    Returns
    -------
    PolyData
        The ICON mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    sample = pantry.icon_soil()

    mesh = Transform.from_unstructured(
        sample.lons,
        sample.lats,
        data=sample.data,
        name=sample.name,
    )

    return mesh


def icosahedral() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a DYNAMICO icosahedral mesh.

    Returns
    -------
    PolyData
        The DYNAMICO mesh.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    sample = pantry.icosahedral()

    mesh = Transform.from_unstructured(
        sample.lons,
        sample.lats,
        data=sample.data,
        name=sample.name,
    )

    return mesh


def lam_equator() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a C4 cubed-sphere Local Area Model (LAM) mesh located at the equator.

    Returns
    -------
    PolyData
        The LAM mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _lfric_sample_to_mesh(pantry.lam_equator())


def lam_falklands() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a C4 cubed-sphere Local Area Model (LAM) mesh located over
    the Falkland Islands.

    Returns
    -------
    PolyData
        The LAM mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _lfric_sample_to_mesh(pantry.lam_falklands())


def lam_london() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a C4 cubed-sphere Local Area Model (LAM) mesh located over
    London, United Kingdom.

    Returns
    -------
    PolyData
        The LAM mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _lfric_sample_to_mesh(pantry.lam_london())


def lam_new_zealand() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a C4 cubed-sphere Local Area Model (LAM) mesh located over
    New Zealand.

    Returns
    -------
    PolyData
        The LAM mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _lfric_sample_to_mesh(pantry.lam_new_zealand())


def lam_pacific() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a high-resolution Local Area Model (LAM) mesh located over the
    Pacific Ocean.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    sample = pantry.lam_pacific()

    mesh = Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
        name=sample.name,
        start_index=sample.start_index,
    )

    return mesh


def lam_polar() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a C4 cubed-sphere Local Area Model (LAM) mesh located over
    the Polar cap.

    Returns
    -------
    PolyData
        The LAM mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _lfric_sample_to_mesh(pantry.lam_polar())


def lam_uk() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a C4 cubed-sphere Local Area Model (LAM) mesh located over
    the United Kingdom.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    return _lfric_sample_to_mesh(pantry.lam_uk())


def lfric(resolution: str | None = None) -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Get the LFRic model unstructured cubed-sphere at the specified `resolution`.

    Parameters
    ----------
    resolution : str, optional
        The resolution of the LFRic model mesh, which may be either
        ``c48``, ``c96`` or ``c192``. Defaults to :data:`LFRIC_RESOLUTION`.
        Also see :data:`LFRIC_RESOLUTIONS`.

    Returns
    -------
    PolyData
        The LFRic cubed-sphere mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if resolution is None:
        resolution = LFRIC_RESOLUTION

    original = str(resolution)
    resolution = original.lower()

    if resolution not in LFRIC_RESOLUTIONS:
        wmsg = (
            f"Unknown LFRic cubed-sphere resolution {original!r}, "
            f"using {LFRIC_RESOLUTION!r} instead."
        )
        warn(wmsg, stacklevel=2)
        resolution = LFRIC_RESOLUTION

    fname = f"lfric_{resolution}.vtk"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"mesh/{fname}.bz2", processor=processor)
    mesh = pv.read(resource)

    return mesh


def lfric_orog(warp: bool | None = False, factor: float | None = None) -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a global surface altitude mesh.

    Parameters
    ----------
    warp : boolean, default=False
        Warp the mesh nodes by the orography ``point`` data.
    factor : float, optional
        The scale factor used to warp the mesh. Defaults to
        :data:`WARP_FACTOR`.

    Returns
    -------
    PolyData
        The orography mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if factor is None:
        factor = WARP_FACTOR

    sample = pantry.lfric_orog()
    name = sample.name

    mesh = Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
        name=name,
        start_index=sample.start_index,
    )

    if warp:
        mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True)
        mesh.warp_by_scalar(scalars=name, inplace=True, factor=factor)

    return mesh


def lfric_sst() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a global Sea Surface Temperature (SST) mesh.

    Returns
    -------
    PolyData
        The SST mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    sample = pantry.lfric_sst()

    mesh = Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
        name=sample.name,
        start_index=sample.start_index,
    )

    return mesh


def regular_grid(
    resolution: str | None = None,
    radius: float | None = None,
) -> pv.PolyData:
    """Generate a regular grid given the `resolution`.

    Parameters
    ----------
    resolution : str, optional
        In the format of ``rN``, where ``N`` is the number of cells in latitude,
        and ``N * 1.5`` cells in longitude. Defaults to :data:`REGULAR_RESOLUTION`.
    radius: float, optional
        The radius of the sphere. Defaults to :data:`geovista.common.RADIUS`.

    Returns
    -------
    PolyData
        The regular longitude/latitude grid mesh.

    Notes
    -----
    .. versionadded:: 0.3.0

    """
    if resolution is None:
        resolution = REGULAR_RESOLUTION

    original = str(resolution)
    resolution = original.lower()

    def warn_unknown() -> None:
        """Generate warning message for invalid resolution."""
        wmsg = (
            f"Unknown regular grid resolution {original!r}, using "
            f"{REGULAR_RESOLUTION!r} instead."
        )
        warn(wmsg, stacklevel=2)

    if resolution.startswith("r"):
        try:
            n_cells = int(resolution.split("r")[1])
        except ValueError:
            warn_unknown()
            n_cells = int(REGULAR_RESOLUTION.split("r")[1])
    else:
        warn_unknown()
        n_cells = int(REGULAR_RESOLUTION.split("r")[1])

    lats = np.linspace(-90.0, 90.0, n_cells + 1)
    lons = np.linspace(-180.0, 180.0, int(n_cells * 1.5) + 1)
    mesh = Transform.from_1d(lons, lats, radius=radius)
    return mesh


def oisst_avhrr_sst() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a global Sea Surface Temperature (SST) NOAA/NCEI OISST AVHRR mesh.

    Returns
    -------
    PolyData
        The SST mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    sample = pantry.oisst_avhrr_sst()

    mesh = Transform.from_1d(
        sample.lons,
        sample.lats,
        data=sample.data,
        name=sample.name,
    )

    return mesh


def um_orca2() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a global Sea Water Potential Temperature ORCA2 mesh.

    Returns
    -------
    PolyData
        The ORCA2 mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    sample = pantry.um_orca2()

    mesh = Transform.from_2d(
        sample.lons, sample.lats, data=sample.data, name=sample.name
    )

    return mesh


def um_orca2_cloud(zscale: float | None = None) -> pv.PolyData:
    """Create a point-cloud mesh from :mod:`geovista.pantry` sample data.

    Generate an ORCA2 point-cloud of Sea Water Potential Temperature gradients.

    Parameters
    ----------
    zscale : float, optional
        The proportional multiplier for z-axis ``zlevel``. Defaults to
        :data:`ZLEVEL_SCALE_CLOUD`.

    Returns
    -------
    PolyData
        The ORCA2 point-cloud.

    Notes
    -----
    .. versionadded:: 0.2.0

    """
    sample = pantry.um_orca2_gradient()

    zscale = ZLEVEL_SCALE_CLOUD if zscale is None else float(zscale)

    cloud = Transform.from_points(
        sample.lons,
        sample.lats,
        data=sample.zlevel,
        name=sample.name,
        zlevel=-sample.zlevel,
        zscale=zscale,
    )

    return cloud


def ww3_global_smc(step: int | None = None) -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a global Sea Surface Wave Significant Height WAVEWATCH III (WW3)
    Spherical Multi-Cell (SMC) mesh.

    Parameters
    ----------
    step : int, default=0
        The time-series offset.

    Returns
    -------
    PolyData
        The WW3 SMC mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    sample = pantry.ww3_global_smc(step=step)

    mesh = Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
        name=sample.name,
    )

    return mesh


def ww3_global_tri() -> pv.PolyData:
    """Create a mesh from :mod:`geovista.pantry` sample data.

    Generate a global Sea Surface Wave Significant Height WAVEWATCH III (WW3)
    triangular mesh.

    Returns
    -------
    PolyData
        The WW3 mesh.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    sample = pantry.ww3_global_tri()

    mesh = Transform.from_unstructured(
        sample.lons,
        sample.lats,
        connectivity=sample.connectivity,
        data=sample.data,
        name=sample.name,
    )

    return mesh
