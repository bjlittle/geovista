"""Provide geovista resource configuration.

Notes
-----
.. versionadded:: 0.1.0

"""
from __future__ import annotations

from os import environ
from pathlib import Path

from platformdirs import user_cache_dir

__all__ = ["resources"]

# see https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

#: geovista resources configuration dictionary.
resources = {
    "cache_dir": Path(environ.get("XDG_CACHE_HOME", user_cache_dir())) / __package__
}

try:
    # system level override of resources dictionary
    from .siteconfig import update_config

    update_config(resources)
except ImportError:
    pass

try:
    # user level override of resources dictionary
    from geovistaconfig import update_config

    update_config(resources)
except ImportError:
    pass
