"""
Provides geovista resource configuration.

"""
from os import environ
from pathlib import Path

from appdirs import user_cache_dir

from .log import get_logger

__all__ = ["logger", "resources"]

# Configure the top-level logger.
logger = get_logger(__name__)

# see https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

#: GeoVista resources configuration dictionary.
resources = dict(
    cache_dir=Path(environ.get("XDG_CACHE_HOME", user_cache_dir())) / __package__
)
logger.debug(f"default: {resources=}")

try:
    from .siteconfig import update_config

    update_config(resources)
    logger.debug(f"siteconfig: {resources=}")
except ImportError:
    pass

try:
    from geovistaconfig import update_config

    update_config(resources)
    logger.debug(f"geovista: {resources=}")
except ImportError:
    pass
