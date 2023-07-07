"""Provide specialisation to support a QT geospatial aware plotter.

See :class:`pyvistaqt.BackgroundPlotter` and :class:`pyvistaqt.MultiPlotter`.

Notes
-----
.. versionadded:: 0.1.3

"""
from __future__ import annotations

try:
    import pyvistaqt as pvqt
except ImportError as e:
    e.msg = f'{e.msg} - please install the "pyvistaqt" and "pyqt" packages.'
    raise

from .geoplotter import GeoPlotterBase


class GeoBackgroundPlotter(GeoPlotterBase, pvqt.BackgroundPlotter):
    """A QT aware background plotter.

    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvistaqt.BackgroundPlotter`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """


class GeoMultiPlotter(GeoPlotterBase, pvqt.MultiPlotter):
    """A QT aware multi-plotter.

    See :class:`geovista.geoplotter.GeoPlotterBase` and
    :class:`pyvistaqt.MultiPlotter`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
