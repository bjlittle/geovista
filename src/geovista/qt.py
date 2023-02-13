"""
This module provides behaviour specialisation to support a QT geospatial aware
:class:`pyvistaqt.BackgroundPlotter` and :class:`pyvistaqt.MultiPlotter`.

Notes
-----
.. versionadded:: 0.1.3

"""
try:
    import pyvista as pvqt
except ImportError as e:
    emsg = 'please install the "pyvistaqt" and "pyqt" packages.'
    e.msg = f"{e.msg} - {emsg}"
    raise

from .geoplotter import GeoPlotterBase


class GeoBackgroundPlotter(GeoPlotterBase, pvqt.BackgroundPlotter):
    """
    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvistaqt.BackgroundPlotter`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """


class GeoMultiPlotter(GeoPlotterBase, pvqt.MultiPlotter):
    """
    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvistaqt.MultiPlotter`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
