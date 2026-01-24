#!/usr/bin/env python3
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Perform quality assurance of pull-request changelog news fragments.

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
PATTERN_AUTHOR = re.compile(r":user:`[^`]+`", flags=re.MULTILINE)
PATTERN_PR = re.compile(r"^\d+$")
PULL = "https://github.com/bjlittle/geovista/pull"
URL = "https://geovista.readthedocs.io/en/latest/developer/towncrier.html#changelog"


@dataclass
class BadFragment:
    """Kinds of invalid towncrier news fragments."""

    author: list[str] = field(default_factory=list)
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


def missing_author(base: Path, fragment: str, verbose: bool | None = True) -> bool:
    """Detect missing author :user: directive within news fragment.

    Parameters
    ----------
    base : Path
        The absolute path to the changelog directory containing the
        news fragments.
    fragment : str
        The name of the news fragment file i.e., "<PR>.<TYPE>.<EXT>".
    verbose : bool, default=True
        Enable or disable output of message.

    Returns
    -------
    bool

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    fname = base / fragment
    debug(f"{fname=}", verbose=verbose)

    with fname.open() as fi:
        contents = fi.read()

    debug(f"{contents=}", verbose=verbose)
    match = PATTERN_AUTHOR.search(contents)
    debug(f"{match=}", verbose=verbose)

    return not bool(match)


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

    def combine(fragments: list[str]) -> str:
        return ", ".join([f"`{fragment}`" for fragment in fragments])

    if not provided:
        emsg = (
            "Please provide a **changelog news fragment file** for "
            f"**[PR#{pr}]({PULL}/{pr})**."
        )
        emsgs.append(emsg)

    if bad.author:
        plural = "s" if len(bad.author) > 1 else ""
        emsg = (
            f'Detected missing author ":user:" directive in news fragment{plural} '
            f"{combine(bad.author)}."
        )
        emsgs.append(emsg)

    if bad.format:
        emsg = (
            "Found invalid news fragment **format**, expected "
            f"`<PR>.<TYPE>.{EXT}`, got {combine(bad.format)}."
        )
        emsgs.append(emsg)

    if bad.pr:
        emsg = f"Found invalid news fragment **PR number**, got {combine(bad.pr)}."
        emsgs.append(emsg)

    if bad.type:
        emsg = f"Found invalid news fragment **type**, got {combine(bad.type)}."
        emsgs.append(emsg)

    if bad.ext:
        emsg = (
            f"Found invalid news fragment **extension**, expected `.{EXT}`, "
            f"got {combine(bad.ext)}."
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
    debug(f"argument: changelog=<{changelog}>", verbose=verbose)

    if not len(pr):
        failure("Unable to collect PR number.")

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

    # the directory containing the changelog new fragment files
    base_directory = Path(base_directory)
    changelog_base = base_directory / config.directory

    # sanitise the csv news fragment file names
    fragments = [
        str(
            (base_directory / fragment.strip())
            .resolve(strict=True)
            .relative_to(changelog_base)
        )
        for fragment in changelog.split(",")
        if fragment
    ]
    debug(f"{fragments=}", verbose=verbose)

    # detect and discard towncrier template from the candidate news fragments
    template = Path(config.template).name
    fragments = [fragment for fragment in fragments if fragment != template]
    debug(f"{fragments=}", verbose=verbose)

    if not fragments:
        failure(
            "Please provide a **changelog news fragment file** for "
            f"**[PR#{pr}]({PULL}/{pr})**."
        )

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

        if not bool(PATTERN_PR.match(fragment_pr)):
            bad.pr.append(fragment)

        if fragment_type not in types:
            bad.type.append(fragment)

        if fragment_ext != EXT:
            bad.ext.append(fragment)

        if missing_author(changelog_base, fragment, verbose=verbose):
            bad.author.append(fragment)

    debug(f"{provided=}", verbose=verbose)

    if bad.author:
        debug(f"{bad.author=}", verbose=verbose)
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
