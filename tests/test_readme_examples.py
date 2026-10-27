# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Policy gate that every Python example in the README runs.

The README is the project's front page on GitHub and its long description on
PyPI, so its examples are the first ``geovista`` code most users copy, and
nothing else runs them. One imported a sample that did not exist until #782
reported it.

Every fenced ``python`` or ``py`` block of ``README.md`` is an example. Each runs
as a script of its own, in a fresh namespace, off screen, with the pantry's data
from the cache, and fails its test if it raises or warns. A test's id is the
example's number and the heading above it, and a traceback names the line of
``README.md`` that raised. Each renders, so each is marked ``image``.

"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import textwrap

import pytest
import pyvista as pv

#: The section of the repository checks page that documents this check.
CHECK = "readme-examples"

README = Path(__file__).parents[1] / "README.md"
"""The README whose examples are run."""

LANGUAGES: frozenset[str] = frozenset({"py", "python"})
"""The info strings of a fenced block that make it an example."""

FENCE = re.compile(r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})\s*(?P<info>\S*)")
"""The opening of a fenced block, as CommonMark has it."""

HEADING = re.compile(r"^ {0,3}#{1,6}\s+(?P<text>.+?)(?:\s+#+)?\s*$")
"""An ATX heading, outside a fenced block."""


@dataclass(frozen=True)
class Example:
    """A fenced Python block of the README."""

    number: int
    """The block's position among the examples, from 1."""

    line: int
    """The line of the README holding the block's first line of code."""

    heading: str
    """The heading above the block."""

    source: str
    """The block's code."""

    @property
    def id(self) -> str:
        """The test id: the number, then the heading as a slug."""
        slug = re.sub(r"[^a-z0-9]+", "-", self.heading.lower()).strip("-")
        return f"{self.number}-{slug}" if slug else str(self.number)


def examples(text: str) -> list[Example]:
    """Find the Python examples in a README.

    Parameters
    ----------
    text : str
        The README, as Markdown.

    Returns
    -------
    list of Example
        Each fenced ``python`` or ``py`` block, in order. A heading is read only
        outside a fenced block, so a comment in code is never taken for one, and
        a block never closed runs to the end of the README, as CommonMark has it.

    """
    # each block as its info string, first line of code, heading and lines.
    blocks: list[tuple[str, int, str, list[str]]] = []
    heading = fence = ""
    for number, line in enumerate(text.splitlines(), start=1):
        if not fence:
            if match := FENCE.match(line):
                fence = match["fence"]
                blocks.append((match["info"].lower(), number + 1, heading, []))
            elif match := HEADING.match(line):
                heading = match["text"]
            continue
        closing = line.strip()
        if closing.startswith(fence) and set(closing) == {fence[0]}:
            fence = ""
        else:
            blocks[-1][3].append(line)
    python = [block for block in blocks if block[0] in LANGUAGES]
    return [
        Example(number, start, above, textwrap.dedent("\n".join(lines)))
        for number, (_, start, above, lines) in enumerate(python, start=1)
    ]


def run(example: Example, path: Path = README) -> None:
    """Run an example as a script of its own.

    The code is compiled as the lines of `path` it was read from, so a traceback
    names the line of the README that raised.

    Parameters
    ----------
    example : Example
        The example to run.
    path : Path, default=README
        The file the example was read from.

    """
    code = compile("\n" * (example.line - 1) + example.source, str(path), "exec")
    # running the README's own code is the point of the check.
    exec(code, {"__name__": "__main__"})  # noqa: S102


EXAMPLES = examples(README.read_text(encoding="utf-8"))
"""The examples of the README."""


def test_the_readme_has_examples():
    """The README has examples, so the check never passes by finding none."""
    assert EXAMPLES


@pytest.mark.image
@pytest.mark.parametrize("example", EXAMPLES, ids=[e.id for e in EXAMPLES])
def test_the_example_runs(example, monkeypatch):
    """Every example of the README runs, off screen, without raising or warning."""
    monkeypatch.setattr(pv, "OFF_SCREEN", True)
    try:
        run(example)
    finally:
        pv.close_all()


def test_a_comment_in_code_is_no_heading():
    """A comment in a block leaves the heading above it in place."""
    text = "## Title\n\n```python\n# a comment\nx = 1\n```\n\n```python\ny = 2\n```\n"
    assert [e.heading for e in examples(text)] == ["Title", "Title"]


def test_only_python_blocks_are_examples():
    """A ``shell`` block is no example, while a ``py`` block is one."""
    text = "```shell\nls\n```\n\n```py\nx = 1\n```\n\n~~~python\ny = 2\n~~~\n"
    assert [e.source for e in examples(text)] == ["x = 1", "y = 2"]


def test_a_longer_fence_holds_a_shorter_one():
    """A block opened by four backticks runs on past a line of three."""
    text = "````python\nx = '''\n```\n'''\n````\n"
    assert [e.source for e in examples(text)] == ["x = '''\n```\n'''"]


def test_an_unclosed_block_runs_to_the_end():
    """A block never closed is an example to the end, as CommonMark has it."""
    text = "```python\nx = 1\n```\n\n```python\ny = 2\n"
    assert [e.source for e in examples(text)] == ["x = 1", "y = 2"]


def test_an_example_records_its_line_and_id():
    """An example knows the README line of its first line of code, and its id."""
    text = "# Top\n\n#### LFRic Cube-Sphere\n\n```python\nx = 1\n```\n"
    (example,) = examples(text)
    assert example.line == 6
    assert example.id == "1-lfric-cube-sphere"


def test_a_traceback_names_the_readme_line(tmp_path):
    """An example that raises is reported at the line of the README it is on."""
    readme = tmp_path / "README.md"
    readme.write_text("# Top\n\n```python\nx = 1\nraise ValueError(x)\n```\n")
    (example,) = examples(readme.read_text())
    with pytest.raises(ValueError, match="1") as info:
        run(example, readme)
    frame = info.traceback[-1]
    assert Path(frame.path) == readme
    assert frame.lineno + 1 == 5
