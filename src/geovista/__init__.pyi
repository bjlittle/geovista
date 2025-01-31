# see https://scientific-python.org/specs/spec-0001/#type-checkers
from .bridge import Transform
from .geoplotter import GeoPlotter
from .pantry.textures import (
    black_marble,
    blue_marble,
    checkerboard,
    natural_earth_1,
    natural_earth_hypsometric,
)
from .report import Report


__version__: str
GEOVISTA_IMAGE_TESTING: bool


__all__ = [
    "__version__",
    "GeoPlotter",
    "GEOVISTA_IMAGE_TESTING",
    "Report",
    "Transform",
    "black_marble",
    "blue_marble",
    "checkerboard",
    "natural_earth_1",
    "natural_earth_hypsometric",
]
