from os import environ
from pathlib import Path

from appdirs import user_cache_dir

from ._version import version as __version__  # noqa: F401
from .logger import get_logger

# Configure the logger as the root logger.
logger = get_logger(__name__, root=True)

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
