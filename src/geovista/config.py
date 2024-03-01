# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Provide :mod:`geovista` resource configuration.

The :data:`resources` dictionary defines the options used to configure the
location of various :mod:`geovista` resources.

The following :data:`resources` dictionary keys are defined:

* ``cache_dir`` - The directory used to store :mod:`geovista.cache` assets.  The default
  configuration is based on the
  `XDG Base Directory Specification <https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_
  i.e., ``${XDG_CACHE_HOME}/geovista``.  Otherwise, the default is the ``geovista``
  directory under :func:`platformdirs.user_cache_dir`.

The :data:`resources` dictionary ``cache_dir`` may be overridden at a package
**system** or **environment** level by creating a ``siteconfig.py`` file in the
:mod:`geovista` package installation root directory and defining an ``update_config``
function that updates the ``resources`` dictionary.  For example:

.. code-block:: python

        def update_config(resources: dict[str, str]) -> None:
            resources["cache_dir"] = "/var/cache/geovista"

The user may override both the default and package level configuration by defining an
``update_config`` function within a ``geovistaconfig``
`user site-packages <https://docs.python.org/3/library/site.html#site.USER_SITE>`_
module.

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

resources: dict = {
    "cache_dir": Path(environ.get("XDG_CACHE_HOME", user_cache_dir())) / __package__
}
"""Resources configuration dictionary."""


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
