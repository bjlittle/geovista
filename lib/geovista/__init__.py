from os import environ
from pathlib import Path

from appdirs import user_cache_dir

from ._version import version as __version__  # noqa: F401
from .bridge import Transform  # noqa: F401
from .geodesic import BBox, line, panel, wedge  # noqa: F401
from .geometry import get_coastlines  # noqa: F401
from .log import get_logger

# Configure the top-level logger.
logger = get_logger(__name__)

# https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
_cache_dir = Path(environ.get("XDG_CACHE_HOME", user_cache_dir())) / __package__

#: GeoVista configuration dictionary.
config = dict(cache_dir=_cache_dir)

try:
    from .siteconfig import update_config as _update_config

    _update_config(config)
    del _update_config
except ImportError:
    pass

try:
    from geovista_config import update_config as _update_config

    _update_config(config)
    del _update_config
except ImportError:
    pass

del _cache_dir
