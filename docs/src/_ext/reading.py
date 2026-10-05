# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""The reading-time model behind the ``readingtime`` directive.

One definition of what a word is, what the rate is, how the directive's
argument is spelled and where on a page it belongs, kept apart from the
``sphinx`` plumbing that renders it.

Nothing here imports anything outside the standard library, so the unit tests
covering it run in every environment rather than skipping wherever ``sphinx``
is absent. That matters most for the scanner at the foot of this module, which
polices the documentation sources rather than a build of them: it reads a page
as text, and so must stay runnable in the bare test environment.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = [
    "WPM",
    "Argument",
    "carries_reading_time",
    "count_words",
    "directive_lines",
    "estimate_minutes",
    "first_section_line",
    "lead_directive_lines",
    "myst_scan",
    "notebook_markdown",
    "parse_argument",
    "title_line",
]

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


#: A fenced block opening at column 0. An indented fence is content within
#: something else, not page structure.
FENCE: re.Pattern[str] = re.compile(r"\A(?P<rail>`{3,}|~{3,})(?P<info>.*)\Z")

#: A reStructuredText section underline at column 0, three characters or more.
UNDERLINE: re.Pattern[str] = re.compile(
    r"""\A(?P<char>[=\-~^"'`#*+:.])(?P=char){2,}[ \t]*\Z"""
)

#: The directive at column 0. Indented, it is a demonstration rather than a
#: banner, which is what lets "developer/documentation.rst" show the directive
#: and carry a live one. The lookahead requires the name to end at whitespace
#: or line end, so "readingtime::junk" does not match - docutils parses that as
#: a comment, and a prefix match would credit a page with a banner that never
#: renders.
RST_DIRECTIVE: re.Pattern[str] = re.compile(r"\A\.\. readingtime::(?=\s|\Z)")

#: The info string of the fence that opens the directive natively in MyST.
MYST_DIRECTIVE: str = "{readingtime}"

#: The info string of a fence whose body is evaluated as reStructuredText. Both
#: MyST pages here reach the directive through one, so its body is page content
#: and is scanned rather than skipped.
RST_WINDOW: str = "{eval-rst}"

#: The first section heading of a MyST page, whose title is a single "#".
MYST_HEADING: str = "## "

#: The suffixes read as MyST. A notebook is a JSON wrapper around markdown
#: cells, so it is scanned as MyST once those have been lifted out of it.
MYST_SUFFIXES: tuple[str, ...] = (".ipynb", ".md")


def notebook_markdown(text: str) -> str:
    """Lift the MyST source out of a Jupyter notebook.

    Only the markdown cells carry page structure. A code cell is skipped, so
    neither a comment that looks like a heading nor a string that looks like a
    directive can be mistaken for one.

    Parameters
    ----------
    text : str
        The ``.ipynb`` JSON.

    Returns
    -------
    str
        The markdown cell sources, in document order, newline separated.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    notebook = json.loads(text)

    return "\n".join(
        "".join(cell.get("source", ()))
        for cell in notebook.get("cells", ())
        if cell.get("cell_type") == "markdown"
    )


def myst_scan(text: str) -> Iterator[tuple[int, str, str | None]]:
    """Yield the column-0 lines of ``text`` that carry page structure.

    A MyST directive *is* a fence, and its opening rail carries the info string
    naming it, so a reader that skipped each fence whole could not see the
    thing being looked for. The rail is therefore yielded with its info string,
    and the body of a :data:`RST_WINDOW` fence is yielded too.

    A fence closes only on a rail of the same character, at least as long, and
    carrying no info string - so a block opened with four backticks may quote a
    three-backtick block without being closed by it.

    Parameters
    ----------
    text : str
        The page source.

    Yields
    ------
    tuple of (int, str, str or None)
        The 1-indexed line number, the line, and - when the line opens a fence
        - its stripped info string.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    rail: str | None = None
    window = False

    for number, line in enumerate(text.splitlines(), start=1):
        fence = FENCE.match(line)

        if fence is not None:
            found, info = fence["rail"], fence["info"].strip()

            if rail is None:
                rail = found
                window = info == RST_WINDOW
                yield number, line, info
                continue

            if found[0] == rail[0] and len(found) >= len(rail) and not info:
                rail, window = None, False
                continue

        if rail is None or window:
            yield number, line, None


def _underlines(text: str) -> list[int]:
    """Return the 1-indexed lines that underline a title or section heading."""
    lines = text.splitlines()
    found: list[int] = []

    for number, line in enumerate(lines, start=1):
        if UNDERLINE.match(line) is None:
            continue

        # a transition - a rule on its own between paragraphs - underlines
        # nothing, whereas a real underline sits beneath text and is at least
        # as long as it
        above = lines[number - 2].rstrip() if number >= 2 else ""

        if above and len(line.rstrip()) >= len(above):
            found.append(number)

    return found


def title_line(text: str, suffix: str) -> int | None:
    """Locate the title of a page.

    Parameters
    ----------
    text : str
        The page source.
    suffix : str
        The file extension, which decides how the page is read. One of
        :data:`MYST_SUFFIXES`, or anything else for reStructuredText.

    Returns
    -------
    int or None
        The 1-indexed line of the title underline for reStructuredText, of the
        ``"# "`` heading for MyST, or ``None`` for a page with no title.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if suffix in MYST_SUFFIXES:
        source = notebook_markdown(text) if suffix == ".ipynb" else text

        for number, line, _ in myst_scan(source):
            if line.startswith("# "):
                return number

        return None

    underlines = _underlines(text)

    return underlines[0] if underlines else None


def first_section_line(text: str, suffix: str) -> int | None:
    """Locate the first section heading below the title of a page.

    Parameters
    ----------
    text : str
        The page source.
    suffix : str
        The file extension, as for :func:`title_line`.

    Returns
    -------
    int or None
        The 1-indexed line of the heading, or ``None`` when the page has no
        sections, in which case the whole of it is its lead.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if suffix in MYST_SUFFIXES:
        source = notebook_markdown(text) if suffix == ".ipynb" else text

        for number, line, _ in myst_scan(source):
            if line.startswith(MYST_HEADING):
                return number

        return None

    underlines = _underlines(text)

    return underlines[1] if len(underlines) > 1 else None


def directive_lines(text: str, suffix: str) -> list[int]:
    """Find every occurrence of the directive at column 0.

    Parameters
    ----------
    text : str
        The page source.
    suffix : str
        The file extension, as for :func:`title_line`.

    Returns
    -------
    list of int
        The 1-indexed lines, in document order.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    if suffix in MYST_SUFFIXES:
        source = notebook_markdown(text) if suffix == ".ipynb" else text

        # a directive taking an argument spells it on the info string, as
        # "{readingtime} 30" or "{readingtime} 200wpm", so the name is the
        # first token of that string rather than the whole of it
        return [
            number
            for number, line, info in myst_scan(source)
            if (info is not None and info.split()[:1] == [MYST_DIRECTIVE])
            or RST_DIRECTIVE.match(line) is not None
        ]

    return [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if RST_DIRECTIVE.match(line) is not None
    ]


def lead_directive_lines(text: str, suffix: str) -> list[int]:
    """Find the occurrences of the directive in the lead of a page.

    The lead is what sits after the title and before the first section
    heading, which is the only place a banner is of any use: lower down it
    quotes a reader time they have already spent. A directive below the lead
    is a demonstration, as in the ``readingtime`` section of
    ``developer/documentation.rst``, and is not a banner.

    Parameters
    ----------
    text : str
        The page source.
    suffix : str
        The file extension, as for :func:`title_line`.

    Returns
    -------
    list of int
        The 1-indexed lines, in document order. Empty for a page with no
        title, which has no lead to put a banner in.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    title = title_line(text, suffix)

    if title is None:
        return []

    section = first_section_line(text, suffix)

    return [
        number
        for number in directive_lines(text, suffix)
        if number > title and (section is None or number < section)
    ]


def carries_reading_time(text: str, suffix: str) -> bool:
    """Report whether a page opens with a reading-time banner.

    Parameters
    ----------
    text : str
        The page source.
    suffix : str
        The file extension, as for :func:`title_line`.

    Returns
    -------
    bool
        Whether the lead of the page carries the directive.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    return bool(lead_directive_lines(text, suffix))
