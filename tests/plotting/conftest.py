"""pytest fixture infra-structure for plotting image tests."""
from __future__ import annotations

from pathlib import Path
import shutil

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import pytest
import pyvista as pv

import geovista as gv
from geovista.cache import CACHE

# matplotlib figure dots-per-inch of the plotter screenshot
SCREENSHOT_DPI = 100


# prepare geovista/pyvista for off-screen image testing
pv.global_theme.load_theme(pv.plotting.themes._TestingTheme())
pv.OFF_SCREEN = True
gv.GEOVISTA_IMAGE_TESTING = True

# prepare to download image cache for each image test
# also see reference in pyproject.toml
cache_dir = Path(__file__).parent.resolve() / "image_cache"

if cache_dir.is_dir() and not cache_dir.is_symlink():
    # remove directory which may have been created by pytest-pyvista
    # when plugin is bootstrapped by pytest
    shutil.rmtree(str(cache_dir))

if not cache_dir.exists():
    base_dir = CACHE.abspath / "tests" / "images"
    base_dir.mkdir(parents=True, exist_ok=True)
    # create the symbolic link to the pooch cache
    cache_dir.symlink_to(base_dir)


class Screenshot:
    """Generate a mpl screenshot of pyvista plotter image."""

    def __init__(self):
        self._image = None
        self.dpi = None
        self.figsize = None

    def __call__(self, plotter) -> None:
        """Snap the rendered plotter image."""
        # invoked by the plotter via the "before_close_callback" hook
        self._image = np.asarray(plotter.image)

    def to_inches(self, pixels: int) -> int:
        """Convert pixel length to whole inches, given the dots-per-inch."""
        if self.dpi is None:
            emsg = (
                "Require to set the dots-per-inch (dpi) before converting "
                "pixels to whole inches."
            )
            raise ValueError(emsg)

        result = (pixels + self.dpi - 1) // self.dpi

        return result

    @property
    def figure(self) -> Figure:
        """Render plotter image within mpl figure."""
        if self.dpi is None:
            self.dpi = SCREENSHOT_DPI

        if self.figsize is None:
            pixel_width, pixel_height = pv.global_theme.window_size
            width = self.to_inches(pixel_width)
            height = self.to_inches(pixel_height)
            self.figsize = (width, height)

        # create the mpl figure and axes
        figure, axes = plt.subplots(frameon=False, figsize=self.figsize, dpi=self.dpi)
        # render the captured plotter image
        axes.imshow(self._image)
        # disable mpl rendering axes, ticks and labels
        axes.set_axis_off()
        # ensure image fills the figure with no padding
        figure.tight_layout(pad=0)

        return figure


@pytest.fixture
def screenshot() -> Screenshot:
    """Fixture to capture mpl screenshot of pyvista plotter image."""
    # create the screenshot that will snap the rendered plotter image
    snap = Screenshot()

    # register with plotter hook
    pv.global_theme.before_close_callback = snap

    yield snap

    # fixture finalization - unregister the plotter hook
    pv.global_theme.before_close_callback = None
