# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that the benchmarks are configured and run as bench spec §2 decides.

The benchmarks live in "benchmarks/", outside the unit suite, and are run by two
pixi tasks: one under CodSpeed, without memray, and one under memray, without
CodSpeed. These tests hold the conftest, the tasks and the manifest to the
decisions of the benchmarks specification. The conftest is exercised in a
subprocess with "pytester", against a copy of itself, so that memray and the
benchmarks' own settings never leak into this suite.

"""

from __future__ import annotations

import ast
from functools import cache
from pathlib import Path
import tomllib
from typing import Any

import pytest
import yaml

#: The repository root, holding the manifest.
ROOT = Path(__file__).parents[1]
#: The manifest declaring the tasks and the pytest configuration.
PYPROJECT = ROOT / "pyproject.toml"
#: The directory of the benchmarks.
BENCHMARKS = ROOT / "benchmarks"
#: The conftest of the benchmarks.
CONFTEST = BENCHMARKS / "conftest.py"
#: The workflow that runs the benchmarks.
WORKFLOW = ROOT / ".github" / "workflows" / "ci-benchmarks.yml"

#: The task that runs the benchmarks under CodSpeed.
CODSPEED_TASK = "benchmarks"
#: The task that runs the benchmarks under memray.
MEMORY_TASK = "benchmarks-memory"

#: The options of every run, without "pytest-pretty", whose summary line
#: "pytester" cannot read.
PLAIN = ("-p", "no:pretty")

#: A benchmark with no memory ceiling.
BARE = """
import pytest

def test_bare(benchmark):
    benchmark(len, "geovista")

@pytest.mark.parametrize("value", ["a", "b"])
def test_x(benchmark, value):
    benchmark(len, value)
"""

#: A benchmark carrying its memory ceiling.
CEILED = """
import pytest

@pytest.mark.limit_memory("64 MB")
def test_ceiled(benchmark):
    benchmark(len, "geovista")
"""

#: A module whose memory ceiling every benchmark in it carries.
MODULE_CEILED = """
import pytest

pytestmark = pytest.mark.limit_memory("64 MB")

def test_ceiled(benchmark):
    benchmark(len, "geovista")
"""

#: A benchmark that records each call of its target.
COUNTED = """
CALLS = []

def test_counted(benchmark):
    benchmark(CALLS.append, 1)
    assert CALLS == [1]
"""


@cache
def _manifest() -> dict[str, Any]:
    """Read the manifest."""
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


@cache
def _workflow() -> dict[Any, Any]:
    """Read the workflow, whose "on" key PyYAML reads as ``True``."""
    workflow: dict[Any, Any] = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return workflow


def _steps(uses: str) -> list[dict[str, Any]]:
    """Return every step of the workflow that uses the action named."""
    return [
        step
        for job in _workflow()["jobs"].values()
        for step in job["steps"]
        if step.get("uses", "").startswith(f"{uses}@")
    ]


def _task(name: str) -> dict[str, Any]:
    """Return a task of the "test" feature."""
    task: dict[str, Any] = _manifest()["tool"]["pixi"]["feature"]["test"]["tasks"][name]
    return task


@pytest.fixture
def bench(pytester: pytest.Pytester) -> pytest.Pytester:
    """Provide a pytester directory holding a copy of the benchmarks conftest."""
    pytester.makeconftest(CONFTEST.read_text(encoding="utf-8"))
    return pytester


def test_memray_refuses_a_benchmark_without_a_ceiling(bench):
    """Refuse, naming each, a benchmark with no ceiling (bench spec §2 decision 5)."""
    bench.makepyfile(test_bare=BARE)
    result = bench.runpytest_subprocess(*PLAIN, "--memray")
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    text = result.stderr.str()
    assert "bench spec §2 decision 5" in text
    for name in ("test_bare", "test_x[a]", "test_x[b]"):
        assert name in text


def test_memray_accepts_a_benchmark_with_a_ceiling(bench):
    """Accept a benchmark carrying its ceiling under memray."""
    bench.makepyfile(test_ceiled=CEILED)
    result = bench.runpytest_subprocess(*PLAIN, "--memray")
    result.assert_outcomes(passed=1)


def test_a_ceiling_on_the_module_is_carried(bench):
    """Accept a ceiling set for every benchmark of a module."""
    bench.makepyfile(test_module=MODULE_CEILED)
    result = bench.runpytest_subprocess(*PLAIN, "--memray")
    result.assert_outcomes(passed=1)


def test_a_ceiling_is_accepted_without_memray(bench):
    """Accept the ceiling's marker with memray disabled, as the CodSpeed run has it."""
    bench.makepyfile(test_ceiled=CEILED)
    result = bench.runpytest_subprocess(*PLAIN, "-p", "no:memray", "--strict-markers")
    result.assert_outcomes(passed=1)


def test_the_benchmarks_render_off_screen(bench):
    """Render nothing to a window, as the benchmarks of pyvista do."""
    bench.makepyfile(
        test_screen="""
import pyvista as pv

def test_screen():
    assert pv.OFF_SCREEN
"""
    )
    result = bench.runpytest_subprocess(*PLAIN)
    result.assert_outcomes(passed=1)


def test_a_plain_run_refuses_nothing(bench):
    """Run each benchmark once, refusing nothing, with neither option given."""
    bench.makepyfile(test_bare=BARE, test_counted=COUNTED)
    result = bench.runpytest_subprocess(*PLAIN)
    result.assert_outcomes(passed=4)


def test_the_unit_suite_never_collects_the_benchmarks():
    """Collect the unit suite from "tests" alone (bench spec §2 decision 6)."""
    assert _manifest()["tool"]["pytest"]["ini_options"]["testpaths"] == "tests"


@pytest.mark.parametrize("name", [CODSPEED_TASK, MEMORY_TASK])
def test_the_tasks_run_openmp_on_one_thread(name):
    """Run OpenMP on one thread for a steady count (bench spec §2 decision 7)."""
    assert _task(name)["env"]["OMP_NUM_THREADS"] == "1"


def test_the_codspeed_task_runs_without_memray():
    """Run CodSpeed with memray disabled, and memray without CodSpeed's measuring."""
    assert _task(CODSPEED_TASK)["cmd"] == "pytest benchmarks --codspeed -p no:memray"
    assert _task(MEMORY_TASK)["cmd"] == "pytest benchmarks --memray"


def test_every_benchmark_uses_the_fixture():
    """Write every benchmark with the fixture (bench spec §2 decision 6)."""
    names = []
    for path in sorted(BENCHMARKS.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                params = [arg.arg for arg in node.args.args]
                assert "benchmark" in params, f"{path.name}::{node.name}"
                names.append(node.name)
    assert names


def test_codspeed_runs_in_simulation():
    """Count instructions with CodSpeed's simulation (bench spec §2 decision 1)."""
    (step,) = _steps("CodSpeedHQ/action")
    assert step["with"]["mode"] == "simulation"


def test_every_pull_request_and_push_to_main_is_measured():
    """Measure every pull request and push to main (bench spec §2 decision 2)."""
    triggers = _workflow()[True]
    assert set(triggers) == {"pull_request", "push", "workflow_dispatch"}
    filters = {"branches", "branches-ignore", "paths", "paths-ignore"}
    assert not (triggers["pull_request"] or {}).keys() & filters
    assert "main" in triggers["push"]["branches"]


def test_a_run_of_main_is_never_cancelled():
    """Cancel a run of a pull request alone (bench spec §4.4)."""
    concurrency = _workflow()["concurrency"]
    expected = "${{ github.event_name == 'pull_request' }}"
    assert concurrency["cancel-in-progress"] == expected


def test_both_jobs_run_the_test_environment():
    """Run in the unsuffixed test environment (bench spec §2 decision 3)."""
    steps = _steps("prefix-dev/setup-pixi")
    assert len(steps) == len(_workflow()["jobs"]) == 2
    assert all(step["with"]["environments"] == "test" for step in steps)
    dependencies = _manifest()["tool"]["pixi"]["feature"]["test"]["dependencies"]
    assert {"pytest-codspeed", "pytest-memray"} <= dependencies.keys()


def test_every_install_is_frozen():
    """Install every environment from the lock (bench spec §2 decision 8)."""
    steps = _steps("prefix-dev/setup-pixi")
    assert all(step["with"]["frozen"] is True for step in steps)
    lines = [
        line
        for job in _workflow()["jobs"].values()
        for step in job["steps"]
        for command in (step.get("run"), step.get("with", {}).get("run"))
        if command
        for line in command.splitlines()
        if "pixi run" in line
    ]
    assert len(lines) == 2
    assert all("pixi run --frozen -e test " in line for line in lines)


def test_the_jobs_ask_only_what_they_need():
    """Grant each job only its own permissions (bench spec §4.4)."""
    workflow = _workflow()
    assert workflow["permissions"] == {}
    jobs = workflow["jobs"]
    assert jobs["codspeed"]["permissions"] == {
        "contents": "read",
        "id-token": "write",
    }
    assert jobs["memory"]["permissions"] == {"contents": "read"}
