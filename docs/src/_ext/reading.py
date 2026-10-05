# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""The reading-time model behind the ``readingtime`` directive.

One definition of what a word is, what the rate is, and how the directive's
argument is spelled, kept apart from the ``sphinx`` plumbing that renders it.

Nothing here imports anything outside the standard library, so the unit tests
covering it run in every environment rather than skipping wherever ``sphinx``
is absent.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re

__all__ = ["WPM", "Argument", "count_words", "estimate_minutes", "parse_argument"]

#: Words-per-minute reading rate for technical documentation. Brysbaert (2019),
#: a meta-analysis of 190 studies, puts most adults between 175 and 300 wpm on
#: English non-fiction, mean 238. These pages are set below that band because
#: they alternate prose with code and output a reader works through line by
#: line. Cited in "docs/src/developer/documentation.rst", so change the two
#: together.
WPM: int = 150

#: What counts as a word: a run of word characters. A dotted name therefore
#: counts as its parts, which is the behaviour inherited from the original
#: directive and kept rather than improved, so that no published estimate
#: changes for two reasons at once.
WORD: re.Pattern[str] = re.compile(r"\w+")

#: The two shapes the optional argument may take, anchored at both ends. A
#: leading zero or a minus sign is excluded by the digit pattern: a page that
#: reads in no minutes is not a duration, and a rate of zero would divide by it.
ARGUMENT: re.Pattern[str] = re.compile(
    r"\A(?:(?P<wpm>[1-9]\d*)wpm|(?P<minutes>[1-9]\d*))\Z", re.IGNORECASE
)


@dataclass(frozen=True)
class Argument:
    """A parsed ``readingtime`` argument.

    Attributes
    ----------
    minutes : int or None
        A literal duration to quote, or ``None`` to count the page.
    wpm : int
        The rate to count at.

    Notes
    -----
    .. versionadded:: 0.6.0

    """

    minutes: int | None
    wpm: int


def count_words(text: str) -> int:
    """Count the words in `text`.

    Parameters
    ----------
    text : str
        The text to count.

    Returns
    -------
    int
        The number of word-character runs.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    return len(WORD.findall(text))


def estimate_minutes(words: int, wpm: int = WPM) -> int:
    """Convert a word count to a reading time in minutes.

    Parameters
    ----------
    words : int
        The number of words on the page.
    wpm : int, optional
        The rate to count at. Defaults to :data:`WPM`.

    Returns
    -------
    int
        The estimate, rounded up, and never below one: a page a reader has
        opened costs them a minute even when it is a sentence long.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    return max(1, math.ceil(words / wpm))


def parse_argument(argument: str | None) -> Argument:
    """Read the optional argument of the directive.

    Parameters
    ----------
    argument : str or None
        ``None`` when the directive was given no argument, ``"30"`` for a
        literal duration in minutes, or ``"200wpm"`` for a rate override.

    Returns
    -------
    Argument
        The duration to quote, if any, and the rate to count at.

    Raises
    ------
    ValueError
        For any other argument. Falling back on an estimate here would publish
        a number the author did not ask for and never see a warning, so a
        misspelled argument is refused instead.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if argument is None:
        return Argument(minutes=None, wpm=WPM)

    match = ARGUMENT.match(argument.strip())

    if match is None:
        emsg = (
            f"readingtime: expected no argument, a duration in minutes such as "
            f"'30', or a rate such as '200wpm'; got {argument!r}"
        )
        raise ValueError(emsg)

    if match["wpm"] is not None:
        return Argument(minutes=None, wpm=int(match["wpm"]))

    return Argument(minutes=int(match["minutes"]), wpm=WPM)
