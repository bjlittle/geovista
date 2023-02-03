"""
This module provides geovista resource configuration.

Notes
-----
.. versionadded:: 0.1.0

"""
from os import environ
from pathlib import Path

from appdirs import user_cache_dir

__all__ = ["resources"]

# see https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

#: geovista resources configuration dictionary.
resources = dict(
    cache_dir=Path(environ.get("XDG_CACHE_HOME", user_cache_dir())) / __package__
)

try:
    from .siteconfig import update_config

    update_config(resources)
except ImportError:
    pass

try:
    from geovistaconfig import update_config

    update_config(resources)
except ImportError:
    pass
