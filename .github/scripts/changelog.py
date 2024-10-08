# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Perform quality assurance of pull-request changelog.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import sys

import click
from towncrier._settings import ConfigError, load_config_from_options

EXT = "rst"
GITHUB_STEP_SUMMARY = os.getenv("GITHUB_STEP_SUMMARY")
PATTERN = re.compile(r"^\d+$")
PULL = "https://github.com/bjlittle/geovista/pull"
URL = "https://geovista.readthedocs.io/en/latest/developer/index.html#changelog"


@dataclass
class BadFragment:
    """Kinds of invalid towncrier news fragments."""

    ext: list[str] = field(default_factory=list)
    format: list[str] = field(default_factory=list)
    pr: list[str] = field(default_factory=list)
    type: list[str] = field(default_factory=list)


def debug(msg: str, verbose: bool | None = True) -> None:
    """Write markdown message with debug icon to GHA step summary stream.

    Parameters
    ----------
    msg : str
        The string message to be reported.
    verbose : bool, default=True
        Enable or disable output of message.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if verbose:
        summary(f"📢 {msg}")


def failure(msg: str | list[str], url: bool | None = True) -> None:
    """Write markdown message with failure icon to GHA step summary stream.

    Exits with a non-zero status.

    Parameters
    ----------
    msg : str or list of str
        The string message/s to be reported.
    url : bool, default=True
        Whether to report changelog documentation URL.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if isinstance(msg, str):
        msg = [msg]

    # report to the GHA runner console stdout
    output('💥 Also see "GHA Summary" for these changelog failure details.\n')

    for part in msg:
        summary(f"❌ {part}")

    if url:
        info = f"For further details see the [changelog]({URL}) documentation."
        summary(f"\nℹ️ {info}")

    sys.exit(1)


def output(msg: str, verbose: bool | None = True) -> None:
    """Write text message to stdout.

    Parameters
    ----------
    msg : str
        The string message to be reported.
    verbose : bool, default=True
        Enable or disable output of message.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if verbose:
        print(msg)


def report(pr: str, provided: bool, bad: BadFragment) -> None:
    """Generate a report of the changelog quality assurance.

    Parameters
    ----------
    pr : str
        The pull-request number.
    provided : bool
        Whether the pull-request has an associated changelog.
    bad : BadFragment
        Enumeration of invalid new fragments.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    emsgs = []

    def join(fragments: list[str]) -> str:
        return ", ".join([f"`{fragment}`" for fragment in fragments])

    if not provided:
        emsg = (
            "Please provide a **changelog news fragment file** for "
            f"**[PR#{pr}]({PULL}/{pr})**."
        )
        emsgs.append(emsg)

    if bad.format:
        emsg = (
            "Found invalid news fragment **format**, expected "
            f"`<PR>.<TYPE>.{EXT}`, got {join(bad.format)}."
        )
        emsgs.append(emsg)

    if bad.pr:
        emsg = f"Found invalid news fragment **PR number**, got {join(bad.pr)}."
        emsgs.append(emsg)

    if bad.type:
        emsg = f"Found invalid news fragment **type**, got {join(bad.type)}."
        emsgs.append(emsg)

    if bad.ext:
        emsg = (
            f"Found invalid news fragment **extension**, expected `.{EXT}`, "
            f"got {join(bad.ext)}."
        )
        emsgs.append(emsg)

    if emsgs:
        failure(emsgs)

    success("Your changelog contribution looks good to me. Awesome job!")


def success(msg: str) -> None:
    """Write markdown message with success icon to GHA step summary stream.

    Parameters
    ----------
    msg : str
        The string message to be reported.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    summary(f"🆗 {msg}")


def summary(msg: str) -> None:
    """Write markdown message to GHA step summary stream and stdout.

    Parameters
    ----------
    msg : str
        The string message to be reported.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if GITHUB_STEP_SUMMARY:
        with Path(GITHUB_STEP_SUMMARY).open("a") as gha:
            gha.write(f"{msg}\n")

    # report to the GHA runner console stdout
    output(msg)


@click.command()
@click.argument("pr", type=click.STRING)
@click.argument("changelog", type=click.STRING)
@click.option("-v", "--verbose", is_flag=True, help="Enable diagnostics.")
def main(pr: str, changelog: str, verbose: bool) -> None:
    """Perform quality assurance on pull-request changelog news fragment/s."""
    debug(f"argument: pr=<{pr}>", verbose=verbose)
    debug(f"argument: changes=<{changelog}>", verbose=verbose)

    if not len(pr):
        failure("Unable to collect PR number.")

    if not len(changelog):
        failure(
            "Please provide a **changelog news fragment file** for "
            f"**[PR#{pr}]({PULL}/{pr})**."
        )

    try:
        # locate and parse the towncrier configuration
        base_directory, config = load_config_from_options(
            directory=None, config_path=None
        )
        debug(f"{base_directory=}", verbose=verbose)
        debug(f"{config=}", verbose=verbose)
    except ConfigError as e:
        failure(f'**towncrier** exception:\n"{e.message}"', url=False)

    # enumerate the configured changelog types
    types = config.types.keys()
    debug(f"{types=}", verbose=verbose)

    if not types:
        failure("There are no configured **towncrier** types.")

    # get the configured base directory for the changelog new fragment files
    base = config.directory

    # sanitise the csv news fragment file names
    fragments = changelog.split(",")
    fragments = [
        str(Path(fragment.strip()).relative_to(base)) for fragment in fragments
    ]
    debug(f"{fragments=}", verbose=verbose)

    # bad news fragment buckets
    bad = BadFragment()

    # has the changelog from this pr been provided?
    provided = False

    # verify all the news fragments, rather than fail fast
    for fragment in fragments:
        fragment_parts = fragment.split(".")
        # expect exactly 3 parts i.e., <pr#>.<type>.<ext>
        if len(fragment_parts) != 3:
            bad.format.append(fragment)
            continue
        fragment_pr, fragment_type, fragment_ext = fragment_parts
        if fragment_pr == pr:
            provided = True
        if not bool(PATTERN.match(fragment_pr)):
            bad.pr.append(fragment)
        if fragment_type not in types:
            bad.type.append(fragment)
        if fragment_ext != EXT:
            bad.ext.append(fragment)

    debug(f"{provided=}", verbose=verbose)
    if bad.format:
        debug(f"{bad.format=}", verbose=verbose)
    if bad.pr:
        debug(f"{bad.pr=}", verbose=verbose)
    if bad.type:
        debug(f"{bad.type=}", verbose=verbose)
    if bad.ext:
        debug(f"{bad.ext=}", verbose=verbose)

    report(pr, provided, bad)


if __name__ == "__main__":
    main()
