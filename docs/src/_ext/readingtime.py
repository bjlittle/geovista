# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Sphinx extension to estimate reading time for documentation pages.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

import math
from pathlib import Path
import re
from typing import TYPE_CHECKING

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

if TYPE_CHECKING:
    from sphinx.application import Sphinx

WPM: int = 120
"""Words per minute reading speed baseline for technical documentation"""


def count_words(text: str) -> int:
    """Count the number of words in a given text.

    Parameters
    ----------
    text : str
        The text to count words in.

    Returns
    -------
    int
        The number of words in the text.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    words = re.findall(r"\w+", text)
    return len(words)


class ReadingTimeDirective(SphinxDirective):
    """Directive to estimate reading time for a documentation page."""

    has_content = False
    optional_arguments = 1
    final_argument_whitespace = False

    def run(self) -> list[nodes.Node]:
        """Estimate the reading time for a documentation page.

        Returns
        -------
        list[nodes.Node]
            A list containing a single raw HTML node with the estimated reading time.

        Notes
        -----
        .. versionadded:: 0.6.0

        """
        env = self.env
        docname = env.docname
        source_path = env.doc2path(docname)

        if self.arguments:
            try:
                minutes = int(self.arguments[0])
            except ValueError:
                minutes = None
        else:
            minutes = None

        if minutes is None:
            with Path(source_path).open("r", encoding="utf-8") as fi:
                text = fi.read()

            # common reading speed baselines for technical docs is 100-150 wpm
            # let's roll with the lower end to be conservative and account for
            # code snippets, figures, etc.
            words = count_words(text)
            minutes = max(1, math.ceil(words / WPM))

        html = (
            f'<div class="reading-time">'
            f'<i class="fa-solid fa-clock"></i> '
            f"Estimated reading time: {minutes} minute{'s' if minutes != 1 else ''}"
            f"</div>"
        )

        return [nodes.raw("", html, format="html")]


def setup(app: Sphinx) -> None:
    """Set up the reading time Sphinx extension.

    Parameters
    ----------
    app : Sphinx
        The Sphinx application object.

    Returns
    -------
    dict
        A dictionary containing the extension version.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    app.add_directive("readingtime", ReadingTimeDirective)
    return {"version": "1.0"}
