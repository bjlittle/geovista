# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Minimal geolocated raster utility support.

Notes
-----
.. versionadded:: 0.1.0

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import lazy_loader as lazy

from .common import wrap

if TYPE_CHECKING:
    import pyvista as pv

# lazy import third-party dependencies
np = lazy.load("numpy")
pv = lazy.load("pyvista")

__all__ = ["wrap_texture"]


def wrap_texture(
    texture: pv.Texture, central_meridian: float | None = None
) -> pv.Texture:
    """Re-center and wrap texture about the specified central meridian.

    Assumes that the source of the texture has global coverage, is on the Geographic
    projection and uses the WGS84 datum, with square pixels and no rotation.

    Parameters
    ----------
    texture : Texture
        The global texture to be re-centered.
    central_meridian : float, default=0.0
        The meridian (degrees) that specifies the new center of the texture image.

    Returns
    -------
    Texture
        The re-centered PyVista texture.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if central_meridian is None:
        central_meridian = 0.0

    meridian = wrap(central_meridian)[0]

    if not np.isclose(meridian, 0):
        # get the texture as a pyvista.ImageData
        grid = texture.to_image()
        shape = (grid.dimensions[1], grid.dimensions[0], texture.n_components)
        # convert grid to an rgb image (un-do pyvista.Texture._from_array mangling)
        image = np.flip(grid.active_scalars.reshape(shape), axis=0)
        width = image.shape[1]
        # calculate the rendering window over the tiled image centered around
        # the meridian
        offset = int(np.round(((meridian + 180) / 360) * width, decimals=0)) + width
        start = offset - (width // 2)
        end = start + width
        # horizontally tile the image (along the x-axis)
        tiled = np.concatenate([image, image, image], axis=1)
        # now extract the image based on the central meridian
        image = tiled[:, start:end]
        texture = pv.Texture(image)

    return texture
