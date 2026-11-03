# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that every pixi task has a row in the task tables of the developer pages.

The tasks are declared in "pyproject.toml", and documented by hand in a "Pixi
Tasks" table on the packaging page, which lists them all, and on the page for the
workflow each serves, the testing page or the documentation page. Nothing ties
the tables to the manifest, so a task can be added without a row, as
``check-spec-renumbering`` was, or renamed and leave a row behind.

These tests read both as text, and hold every task to a row on the packaging page
and on the page its feature maps to. A task's name is local to its feature, so
two features may each declare a task of the same name, and the packaging page
gives each a row under its own feature. A page may list a task of another feature
too, as the testing page lists the browser tests of the documentation.

"""

from __future__ import annotations

from functools import cache
from itertools import pairwise
from pathlib import Path
import re
import tomllib
from typing import Any

import pytest

#: The section of the repository checks page that documents this check.
CHECK = "pixi-task-tables"

#: The repository root, holding the manifest.
ROOT = Path(__file__).parents[1]
#: The manifest declaring the tasks.
PYPROJECT = ROOT / "pyproject.toml"
#: The developer pages with a "Pixi Tasks" table.
PAGES = ROOT / "docs" / "src" / "developer"

#: The page listing every task, with the feature of each.
PACKAGING = "packaging"
#: The page that documents the tasks of each feature, besides the packaging page.
#: A feature with tasks must have one, so that a new feature is given a page.
FEATURE_PAGES = {
    "default": "testing",
    "docs": "documentation",
    "geovista": "documentation",
    "test": "testing",
}
#: The name of the tasks of the manifest's own "[tool.pixi.tasks]" table, as the
#: packaging page names it, "{default}".
DEFAULT = "default"

#: The title of the table of tasks on each page.
TITLE = re.compile(r"^\s*\.\. table:: Pixi Tasks\s*$")
#: The line under a grid table's header, whose "+" marks the column boundaries.
HEADER = re.compile(r"^\s*\+(?:=+\+)+\s*$")
#: A cell naming a task, as ``name`` or :guilabel:`name`.
TASK = re.compile(r"^(?:``(?P<literal>[\w-]+)``|:guilabel:`(?P<label>[\w-]+)`)$")
#: A cell naming a feature, as ``{name}``.
FEATURE = re.compile(r"^``\{(?P<name>[\w-]+)\}``$")


@cache
def _manifest() -> dict[str, Any]:
    """Return the parsed manifest, read once for the whole module."""
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def _tasks(manifest: dict[str, Any]) -> set[tuple[str, str]]:
    """Return each pixi task of a manifest, with the feature that declares it.

    A task's name is local to its feature, so a name two features declare is two
    tasks.

    Parameters
    ----------
    manifest : dict
        The parsed "pyproject.toml".

    Returns
    -------
    set of tuple
        The name and feature of each task, :data:`DEFAULT` for the feature of one
        of "[tool.pixi.tasks]".

    """
    pixi = manifest["tool"]["pixi"]
    tasks = {(name, DEFAULT) for name in pixi.get("tasks", {})}
    for feature, table in pixi.get("feature", {}).items():
        tasks |= {(name, feature) for name in table.get("tasks", {})}
    return tasks


def _table(text: str) -> list[tuple[str, str | None]]:
    """Read the rows of the "Pixi Tasks" table of a page.

    The table is a grid table with a column whose header names a task, and
    perhaps a "Feature" column, whose cell spans the rows of its tasks. A rule
    across that column closes the cell, so a row under a cell naming no feature
    has none, rather than the feature of the cell above.

    Parameters
    ----------
    text : str
        The page.

    Returns
    -------
    list of tuple
        The task each row names, and the feature its "Feature" column names, or
        ``None`` where the column names none or the table has no such column, in
        the order written.

    """
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if TITLE.match(line)), None)
    if start is None:
        return []

    index = next(i for i in range(start, len(lines)) if HEADER.match(lines[i]))
    bounds = [i for i, char in enumerate(lines[index]) if char == "+"]
    columns = list(pairwise(bounds))

    def cells(line: str) -> list[str]:
        return [line[left + 1 : right].strip() for left, right in columns]

    header = cells(lines[index - 1])
    task = next(i for i, name in enumerate(header) if "Task" in name)
    feature = header.index("Feature") if "Feature" in header else None

    rows: list[tuple[str, str | None]] = []
    current = None
    for line in lines[index + 1 :]:
        if not line.strip().startswith(("|", "+")):
            break
        values = cells(line)
        if not line.strip().startswith("|"):
            if feature is not None and set(values[feature]) == {"-"}:
                current = None
            continue
        if feature is not None and (match := FEATURE.match(values[feature])):
            current = match["name"]
        if match := TASK.match(values[task]):
            rows.append((match["literal"] or match["label"], current))
    return rows


def _unlisted(
    tasks: set[tuple[str, str]], rows: list[tuple[str, str | None]]
) -> list[str]:
    """Return the tasks with no row, as ``name {feature}``, in order.

    A row naming a feature lists the task of that feature, and a row naming none
    lists the task of its name in any feature, so :func:`_misfiled` reports a
    row of the packaging page that names none.
    """
    listed = set(rows)
    return sorted(
        f"{name} {{{feature}}}"
        for name, feature in tasks
        if (name, feature) not in listed and (name, None) not in listed
    )


def _unknown(
    tasks: set[tuple[str, str]], rows: list[tuple[str, str | None]]
) -> list[str]:
    """Return the rows naming a task the manifest does not declare, in order."""
    return sorted({name for name, _ in rows} - {name for name, _ in tasks})


def _misfiled(
    tasks: set[tuple[str, str]], rows: list[tuple[str, str | None]]
) -> list[str]:
    """Return the rows naming no feature, or one that does not declare the task.

    For a table with a "Feature" column, where every row must name a feature.
    """
    declared: dict[str, list[str]] = {}
    for name, feature in sorted(tasks):
        declared.setdefault(name, []).append(feature)
    return [
        f"{name} (row {feature!r}, manifest {declared[name]!r})"
        for name, feature in rows
        if name in declared and feature not in declared[name]
    ]


def _unmapped(tasks: set[tuple[str, str]]) -> list[str]:
    """Return the features with tasks but no page in :data:`FEATURE_PAGES`."""
    return sorted({feature for _, feature in tasks} - set(FEATURE_PAGES))


@cache
def _page(name: str) -> list[tuple[str, str | None]]:
    """Return the rows of the "Pixi Tasks" table of a developer page."""
    return _table((PAGES / f"{name}.rst").read_text(encoding="utf-8"))


#: A packaging table, with a feature spanning two tasks, and one of another feature.
PACKAGING_TABLE = """
The tasks:

.. table:: Pixi Tasks
   :widths: 1 1 6

   +-------------+-------------+---------------------+
   | Feature     | Task        | Description         |
   +=============+=============+=====================+
   | ``{docs}``  | ``make``    | Build the docs e.g.,|
   |             |             |                     |
   |             |             | ``pixi run make``   |
   |             +-------------+---------------------+
   |             | ``clean``   | Purge the build.    |
   +-------------+-------------+---------------------+
   | ``{test}``  | ``unit``    | Run the unit tests. |
   +-------------+-------------+---------------------+

After the table.
"""

#: A page's table, with no "Feature" column.
PAGE_TABLE = """
.. table:: Pixi Tasks
   :align: center

   +----------------------+-------------------+
   | Pixi Task            | Description       |
   +======================+===================+
   | :guilabel:`unit`     | Run the tests.    |
   +----------------------+-------------------+
"""


def test_a_table_reads_a_feature_spanning_its_tasks():
    """Each task takes the feature of the cell its row lies under."""
    expected = [("make", "docs"), ("clean", "docs"), ("unit", "test")]
    assert _table(PACKAGING_TABLE) == expected


def test_a_table_reads_a_blank_feature_as_none():
    """A row under a "Feature" cell naming no feature has none."""
    blank = PACKAGING_TABLE.replace("| ``{docs}``  |", "|             |")
    expected = [("make", None), ("clean", None), ("unit", "test")]
    assert _table(blank) == expected


def test_a_blank_feature_takes_none_from_the_cell_above():
    """A rule across the "Feature" column closes the cell above."""
    blank = PACKAGING_TABLE.replace("| ``{test}``  |", "|             |")
    expected = [("make", "docs"), ("clean", "docs"), ("unit", None)]
    assert _table(blank) == expected


def test_a_table_reads_a_task_as_a_label():
    """A task written as a GUI label is read, with no feature."""
    assert _table(PAGE_TABLE) == [("unit", None)]


def test_a_page_with_no_table_has_no_rows():
    """A page without a "Pixi Tasks" table has no rows."""
    assert _table(".. table:: Make Tasks\n") == []


def test_tasks_take_the_feature_declaring_them():
    """A task of "[tool.pixi.tasks]" is the default feature's."""
    manifest = {
        "tool": {
            "pixi": {
                "tasks": {"download": "cmd"},
                "feature": {"docs": {"tasks": {"make": {"cmd": "make"}}}, "py": {}},
            }
        }
    }
    assert _tasks(manifest) == {("download", DEFAULT), ("make", "docs")}


def test_a_name_two_features_declare_is_two_tasks():
    """A task's name is local to its feature, so neither declaration is lost."""
    manifest = {
        "tool": {
            "pixi": {
                "feature": {
                    "hidden": {"tasks": {"make": "echo hidden"}},
                    "docs": {"tasks": {"make": "make"}},
                }
            }
        }
    }
    tasks = _tasks(manifest)
    assert tasks == {("make", "hidden"), ("make", "docs")}
    assert _unmapped(tasks) == ["hidden"]


def test_a_task_with_no_row_is_unlisted():
    """A task no row names is reported."""
    tasks = {("make", "docs"), ("clean", "docs"), ("serve", "docs")}
    rows = [("make", "docs"), ("clean", "docs")]
    assert _unlisted(tasks, rows) == ["serve {docs}"]


def test_a_row_lists_the_task_of_its_feature_alone():
    """A row under one feature leaves the task of that name in another unlisted."""
    tasks = {("make", "docs"), ("make", "hidden")}
    assert _unlisted(tasks, [("make", "docs")]) == ["make {hidden}"]


def test_a_row_naming_no_feature_lists_the_task_in_any():
    """A row of a table with no "Feature" column lists the task by name."""
    tasks = {("make", "docs"), ("make", "hidden")}
    assert _unlisted(tasks, [("make", None)]) == []


def test_a_row_naming_no_task_is_unknown():
    """A row naming a task the manifest lacks is reported."""
    tasks = {("make", "docs")}
    assert _unknown(tasks, [("make", None), ("gone", None)]) == ["gone"]


def test_a_row_naming_another_feature_is_misfiled():
    """A row whose feature is not the task's is reported."""
    misfiled = _misfiled({("make", "docs")}, [("make", "test")])
    assert misfiled == ["make (row 'test', manifest ['docs'])"]


def test_a_row_naming_any_feature_of_the_task_is_filed():
    """A row under any feature declaring a task of its name is filed rightly."""
    tasks = {("make", "docs"), ("make", "hidden")}
    assert _misfiled(tasks, [("make", "hidden"), ("make", "docs")]) == []


def test_a_row_naming_no_feature_is_misfiled():
    """A row under a "Feature" cell naming no feature is reported."""
    blank = PACKAGING_TABLE.replace("| ``{docs}``  |", "|             |")
    tasks = {("make", "docs"), ("clean", "docs"), ("unit", "test")}
    assert _misfiled(tasks, _table(blank)) == [
        "make (row None, manifest ['docs'])",
        "clean (row None, manifest ['docs'])",
    ]


def test_a_feature_with_no_page_is_unmapped():
    """A feature that is not in the map is reported."""
    assert _unmapped({("make", "docs"), ("view", "qt")}) == ["qt"]


@pytest.mark.parametrize("page", sorted({PACKAGING, *FEATURE_PAGES.values()}))
def test_every_page_has_a_task_table(page):
    """Each page has a "Pixi Tasks" table to read, so no check passes on nothing."""
    assert _page(page), f"no 'Pixi Tasks' table read from {page}.rst"


def test_every_feature_has_a_page():
    """Every feature declaring a task maps to the page documenting it."""
    unmapped = _unmapped(_tasks(_manifest()))
    assert not unmapped, f"features with tasks but no page in FEATURE_PAGES: {unmapped}"


def test_every_task_has_a_packaging_row():
    """The packaging page lists every task."""
    unlisted = _unlisted(_tasks(_manifest()), _page(PACKAGING))
    assert not unlisted, f"tasks with no row on {PACKAGING}.rst: {unlisted}"


@pytest.mark.parametrize("page", sorted(set(FEATURE_PAGES.values())))
def test_every_task_has_a_row_on_its_features_page(page):
    """The page of each feature lists the tasks of that feature."""
    tasks = {
        (name, feature)
        for name, feature in _tasks(_manifest())
        if FEATURE_PAGES.get(feature) == page
    }
    unlisted = _unlisted(tasks, _page(page))
    assert not unlisted, f"tasks with no row on {page}.rst: {unlisted}"


@pytest.mark.parametrize("page", sorted({PACKAGING, *FEATURE_PAGES.values()}))
def test_every_row_names_a_task(page):
    """No row names a task the manifest no longer declares."""
    unknown = _unknown(_tasks(_manifest()), _page(page))
    assert not unknown, f"rows on {page}.rst naming no pixi task: {unknown}"


def test_the_packaging_rows_name_each_tasks_feature():
    """Every row of the packaging page names a feature that declares its task."""
    misfiled = _misfiled(_tasks(_manifest()), _page(PACKAGING))
    message = f"rows on {PACKAGING}.rst naming no feature, or another: {misfiled}"
    assert not misfiled, message
