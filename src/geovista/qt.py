import pyvista as pvqt

from .geoplotter import GeoPlotterBase


class GeoBackgroundPlotter(GeoPlotterBase, pvqt.BackgroundPlotter):
    """
    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvistaqt.BackgroundPlotter`.

    """


class GeoMultiPlotter(GeoPlotterBase, pvqt.MultiPlotter):
    """
    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvistaqt.MultiPlotter`.

    """
