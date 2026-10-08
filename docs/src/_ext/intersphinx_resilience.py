# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Stop an unreachable intersphinx inventory from failing the build.

``nitpicky`` mode and ``--fail-on-warning`` together make every remote
inventory a hard build dependency. One unreachable inventory emits a warning
of its own and then hundreds more, as each cross-reference it would have
resolved becomes a nitpick miss - so an outage anywhere upstream turns the
documentation jobs red for reasons that have nothing to do with the change
under test.

The fallback inventories vendored under ``_inventory`` cover the common case,
leaving this extension to cover the remainder: a mapping added without a
fallback, or a fallback that is itself unreadable. It demotes the inventory
failure and disables ``nitpicky`` for the rest of the build, so that an
upstream outage degrades the build rather than failing it.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

import logging
import os
import threading
from typing import TYPE_CHECKING

from sphinx.util import logging as sphinx_logging

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

__all__ = ["setup"]

#: The logging namespace that sphinx attaches its handlers to.
NAMESPACE = "sphinx"

#: Identifies the intersphinx loggers among the records those handlers see.
ORIGIN = "ext.intersphinx"

#: The sphinx message reporting that every location for an inventory failed.
#: It carries no warning type, and so cannot be named in "suppress_warnings".
UNREACHABLE = "failed to reach any of the inventories"

#: The advice accompanying a degraded build.
ADVICE = (
    "nitpicky mode is disabled for the remainder of this build, so broken "
    "cross-references will not be reported. refresh the vendored fallback "
    "inventories with 'pixi run -e docs fetch-inventories'"
)

#: Renders a degraded build as an annotation on the GitHub Actions job, which
#: a passing job would otherwise give no hint of.
ANNOTATION = "::warning title=intersphinx::{message}"

LOGGER = sphinx_logging.getLogger(__name__)


class InventoryFailure(logging.Filter):
    """Withhold the intersphinx inventory failure from the warning count.

    Sphinx counts a warning in the first filter on its warning handler, so
    this one is inserted ahead of that rather than appended, and drops the
    record entirely. The failure is reported by :func:`degrade` instead.

    Notes
    -----
    .. versionadded:: 0.6.0

    """

    def __init__(self) -> None:
        """Record no failures yet.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        super().__init__()
        self.failures: list[str] = []
        self._lock = threading.Lock()
        self._seen: list[logging.LogRecord] = []

    def filter(self, record: logging.LogRecord) -> bool:
        """Determine whether the record should be handled.

        Parameters
        ----------
        record : logging.LogRecord
            The record offered to the handler.

        Returns
        -------
        bool
            Whether the record is anything other than an inventory failure.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        if (
            record.levelno < logging.WARNING
            or ORIGIN not in record.name
            or UNREACHABLE not in str(record.msg)
        ):
            return True

        # the guard is installed on every sphinx handler, so that the record is
        # suppressed whichever of them would emit it, and logging offers each
        # handler the same record in turn - so count it only the first time it
        # is seen, or one unreachable inventory is reported as three.
        #
        # sphinx fetches the inventories on a thread pool, and "Handler.handle"
        # filters outside its lock, so the records of two failures can
        # interleave across the handlers. Remembering only the last record seen
        # would then count the first of them twice, and the check and its
        # record must be a single atomic step. The records held are one per
        # mapping, and holding them is what makes the identity test sound.
        with self._lock:
            if all(record is not seen for seen in self._seen):
                self._seen.append(record)
                self.failures.append(record.getMessage())

        return False


def guard() -> InventoryFailure | None:
    """Find the guard installed on the sphinx logging handlers.

    Returns
    -------
    InventoryFailure or None
        The guard, or ``None`` when it is not installed.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    for handler in logging.getLogger(NAMESPACE).handlers:
        for instance in handler.filters:
            if isinstance(instance, InventoryFailure):
                return instance

    return None


def install(app: Sphinx, config: Config) -> None:  # noqa: ARG001
    """Install the guard ahead of the sphinx warning filters.

    Sphinx replaces its handlers for each application it creates, so this
    install is always a fresh one.

    Parameters
    ----------
    app : Sphinx
        The sphinx application.
    config : Config
        The sphinx configuration, which is unused.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    instance = InventoryFailure()

    for handler in logging.getLogger(NAMESPACE).handlers:
        handler.filters.insert(0, instance)


def degrade(app: Sphinx) -> None:
    """Disable nitpicky mode when an inventory could not be reached.

    Runs after the intersphinx inventories have been loaded, and before any
    cross-reference is resolved.

    Parameters
    ----------
    app : Sphinx
        The sphinx application.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    instance = guard()

    if instance is None or not instance.failures or not app.config.nitpicky:
        return

    app.config.nitpicky = False

    summary = f"{len(instance.failures)} intersphinx inventory is unreachable"

    if len(instance.failures) > 1:
        summary = f"{len(instance.failures)} intersphinx inventories are unreachable"

    LOGGER.info("")

    for failure in instance.failures:
        LOGGER.info(failure, color="darkred")

    LOGGER.info(f"{summary}, {ADVICE}", color="darkred")  # noqa: G004
    LOGGER.info("")

    if os.environ.get("GITHUB_ACTIONS"):
        print(ANNOTATION.format(message=f"{summary}, {ADVICE}"))  # noqa: T201


def setup(app: Sphinx) -> dict[str, bool]:
    """Configure the sphinx application.

    Parameters
    ----------
    app : Sphinx
        The sphinx application.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    # install before the inventories are fetched at "builder-inited"
    app.connect("config-inited", install)
    # "sphinx.ext.intersphinx" loads the inventories at the default priority
    app.connect("builder-inited", degrade, priority=800)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
