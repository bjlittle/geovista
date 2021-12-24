from typing import Any, Optional

import pyvista as pv
from pyvista.utilities import abstract_class
import pyvistaqt as pvqt
import vtk

from .geometry import COASTLINE_RESOLUTION, get_coastlines
from .log import get_logger

__all__ = ["GeoBackgroundPlotter", "GeoMultiPlotter", "GeoPlotter"]

# configure the logger
logger = get_logger(__name__)


@abstract_class
class GeoBasePlotter:
    def add_base_layer(self, **kwargs: Optional[Any]) -> vtk.vtkActor:
        """
        TBD

        Parameters
        ----------
        kwargs : Any, optional


        Returns
        -------
        vtkActor


        Notes
        -----
        .. versionadded:: 0.1.0

        """
        # TODO: provide robust zorder support
        mesh = pv.Sphere(radius=1 - (1e-2), theta_resolution=360, phi_resolution=180)
        return self.add_mesh(mesh, **kwargs)

    def add_coastlines(
        self, resolution: Optional[str] = COASTLINE_RESOLUTION, **kwargs: Optional[Any]
    ) -> vtk.vtkActor:
        """
        TBD

        Parameters
        ----------
        resolution : str, default=COASTLINE_RESOLUTION

        kwargs : Any, optional


        Returns
        -------
        vtkActor


        Notes
        -----
        .. versionadded:: 0.1.0

        """
        mesh = get_coastlines(resolution=resolution)
        return self.add_mesh(mesh, **kwargs)


class GeoBackgroundPlotter(pvqt.BackgroundPlotter, GeoBasePlotter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GeoMultiPlotter(pvqt.MultiPlotter, GeoBasePlotter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GeoPlotter(pv.Plotter, GeoBasePlotter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
