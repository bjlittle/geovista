"""
This module provides behaviour specialisation to support a QT geospatial aware
:class:`pyvistaqt.BackgroundPlotter` and :class:`pyvistaqt.MultiPlotter`.

Notes
-----
.. versionadded:: 0.1.3

"""
try:
    # pylint: disable-next=import-outside-toplevel
    import pyvistaqt as pvqt
except ImportError as e:
    e.msg = f'{e.msg} - please install the "pyvistaqt" and "pyqt" packages.'
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
