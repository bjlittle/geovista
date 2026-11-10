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
import os
from pathlib import Path
import shlex
import subprocess
import sys
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
    bench.makepyfile(test_bare=BARE, test_more=BARE)
    result = bench.runpytest_subprocess(*PLAIN, "--memray")
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    text = result.stderr.str()
    assert "bench spec §2 decision 5" in text
    for module in ("test_bare.py", "test_more.py"):
        for name in ("test_bare", "test_x[a]", "test_x[b]"):
            assert f"{module}::{name}" in text


def test_the_refusal_keeps_to_the_benchmarks(pytester):
    """Refuse no unit test run beside the benchmarks."""
    bench = pytester.mkdir("bench")
    (bench / "conftest.py").write_text(CONFTEST.read_text(encoding="utf-8"))
    (bench / "test_ceiled.py").write_text(CEILED)
    unit = pytester.mkdir("unit")
    (unit / "test_unit.py").write_text("def test_unit():\n    assert True\n")
    result = pytester.runpytest_subprocess(*PLAIN, "--memray", "bench", "unit")
    result.assert_outcomes(passed=2)


def test_openblas_is_warmed_before_any_benchmark(bench, monkeypatch):
    """Charge OpenBLAS's one-off buffers to no benchmark (bench spec §2 decision 5).

    The first matrix product in a process makes OpenBLAS set up its buffers,
    128 MiB of them under every kernel older than ``SkylakeX``, so whichever
    benchmark makes it would breach its ceiling on some runners. ``Prescott``,
    the oldest x86-64 kernel, is one of them, and runs on any x86-64 CPU.

    """
    monkeypatch.setenv("OPENBLAS_CORETYPE", "Prescott")
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    bench.makepyfile(
        test_first="""
import numpy as np
import pytest

@pytest.mark.limit_memory("8 MB")
def test_first(benchmark):
    benchmark(np.matmul, np.eye(3), np.eye(3))
"""
    )
    result = bench.runpytest_subprocess(*PLAIN, "--memray", "--trace-python-allocators")
    result.assert_outcomes(passed=1)


def test_grid_mesh_owns_its_data(bench):
    """Give each benchmark a mesh whose data it may change without harm."""
    bench.makepyfile(
        test_owns="""
import numpy as np

def test_owns(grid_mesh, grid_data):
    assert not np.shares_memory(grid_mesh.cell_data["data"], grid_data)
"""
    )
    result = bench.runpytest_subprocess(*PLAIN)
    result.assert_outcomes(passed=1)


def test_the_benchmarks_load_without_memray(bench, monkeypatch):
    """Load the conftest where pytest-memray is absent (bench spec §2 decision 6)."""
    absent = bench.mkdir("absent") / "pytest_memray"
    absent.mkdir()
    (absent / "__init__.py").write_text('raise ImportError("no pytest-memray")\n')
    monkeypatch.setenv("PYTHONPATH", str(absent.parent))
    bench.makepyfile(test_ceiled=CEILED)
    result = bench.runpytest_subprocess(*PLAIN, "-p", "no:memray", "--strict-markers")
    result.assert_outcomes(passed=1)


def test_vtk_runs_on_one_thread(bench, monkeypatch):
    """Run VTK on one thread, for a steady count (bench spec §2 decision 7).

    conda-forge's VTK defaults to its sequential backend, which runs on one
    thread whatever the conftest asks, so this test runs on the threaded backend
    that pip's VTK defaults to, where only the conftest keeps it to one. That
    backend caps its count at the CPU's, so on a single core this passes
    whatever the conftest does, and ``test_vtk_is_pinned_at_import`` reads the
    conftest instead.

    """
    monkeypatch.setenv("VTK_SMP_BACKEND_IN_USE", "STDThread")
    bench.makepyfile(
        test_threads="""
from vtkmodules.vtkCommonCore import vtkSMPTools

def test_threads():
    assert vtkSMPTools.GetBackend() == "STDThread"
    assert vtkSMPTools.GetEstimatedNumberOfThreads() == 1
"""
    )
    result = bench.runpytest_subprocess(*PLAIN)
    result.assert_outcomes(passed=1)


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


@pytest.mark.parametrize("name", [CODSPEED_TASK, MEMORY_TASK])
def test_no_task_forces_an_openblas_kernel(name):
    """Leave OpenBLAS to choose its kernel for the CPU it runs on.

    A forced kernel can use instructions an older CPU lacks, and crash there
    (#2935). The warm-up of the conftest makes a benchmark's peak the same
    under every kernel, so none needs forcing.

    """
    assert "OPENBLAS_CORETYPE" not in _task(name).get("env", {})


def test_the_codspeed_task_runs_without_memray():
    """Run CodSpeed with memray disabled, and memray without CodSpeed's measuring."""
    assert _task(CODSPEED_TASK)["cmd"] == "pytest benchmarks --codspeed -p no:memray"
    expected = (
        "pytest benchmarks --memray --trace-python-allocators --most-allocations=0"
    )
    assert _task(MEMORY_TASK)["cmd"] == expected


def test_a_benchmark_alone_keeps_within_its_ceiling():
    """Hold a benchmark run alone to the ceiling it keeps in the full run.

    Without Python's allocators traced, memray sees whole pymalloc arenas, so a
    benchmark's peak depends on the arenas the benchmarks before it left free,
    and ``test_npoints`` alone breaches a ceiling it keeps in the full run.

    """
    command = shlex.split(_task(MEMORY_TASK)["cmd"])
    assert command[:2] == ["pytest", "benchmarks"]
    node = "benchmarks/test_geodesic.py::test_npoints"
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", node, *command[2:], *PLAIN],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout[-2000:]


def benchmark_functions(root: Path) -> list[tuple[str, bool]]:
    """Return each test function under ``root``, with whether it takes the fixture.

    Every module named ``test_*.py`` at any depth is read, and every function
    named ``test_*`` in it, a method of a ``Test`` class and an ``async def``
    included. Each is named as pytest names it, by its module's path and its
    classes, and the fixture counts whether passed by position or by keyword.

    """

    def visit(nodes: list[ast.stmt], where: str, found: list[tuple[str, bool]]) -> None:
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                visit(node.body, f"{where}::{node.name}", found)
            elif isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and node.name.startswith("test_"):
                params = [arg.arg for arg in node.args.args + node.args.kwonlyargs]
                found.append((f"{where}::{node.name}", "benchmark" in params))

    functions: list[tuple[str, bool]] = []
    for path in root.rglob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        visit(tree.body, path.relative_to(root).as_posix(), functions)
    return sorted(functions)


def test_every_benchmark_uses_the_fixture():
    """Write every benchmark with the fixture (bench spec §2 decision 6)."""
    functions = benchmark_functions(BENCHMARKS)
    assert functions
    assert [name for name, uses in functions if not uses] == []


def test_a_benchmark_in_a_class_is_read(tmp_path):
    """Read a benchmark as pytest collects it, wherever and however written."""
    (tmp_path / "test_mod.py").write_text(
        "class TestX:\n    def test_y(self):\n        pass\n\n"
        "async def test_z():\n    pass\n"
    )
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "test_sub.py").write_text(
        "def test_k(*, benchmark):\n    pass\n"
    )
    assert benchmark_functions(tmp_path) == [
        ("sub/test_sub.py::test_k", True),
        ("test_mod.py::TestX::test_y", False),
        ("test_mod.py::test_z", False),
    ]


def test_pull_requests_are_measured_of_every_type():
    """Measure a pull request whatever its activity (bench spec §2 decision 2)."""
    assert "types" not in (_workflow()[True]["pull_request"] or {})


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
    # a pending run is cancelled by a newer one in its group whatever
    # "cancel-in-progress" says, so each commit of main has a group of its own
    group = (
        "${{ github.workflow }}-${{ github.event_name == 'pull_request' "
        "&& github.ref || github.sha }}"
    )
    assert concurrency["group"] == group
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


#: The names a benchmark would use to draw, which none may (bench spec §2 decision 7).
RENDERING = frozenset(
    {
        "BackgroundPlotter",
        "GeoBackgroundPlotter",
        "GeoPlotter",
        "Plotter",
        "Renderer",
        "add_mesh",
        "plot",
        "render",
        "screenshot",
        "show",
    }
)

#: The modules whose random state is global, and so never seeded by a benchmark.
GLOBAL_RANDOM = frozenset({"random"})


def _uses_benchmark(node: ast.AST) -> bool:
    """Tell whether ``node`` is the ``benchmark`` fixture, or an attribute of it."""
    if isinstance(node, ast.Attribute):
        return _uses_benchmark(node.value)
    return isinstance(node, ast.Name) and node.id == "benchmark"


def _imports(tree: ast.Module) -> dict[str, str]:
    """Map each name a module binds by import to the dotted name it stands for.

    ``import numpy as np`` binds ``np`` to ``numpy``, ``import numpy.random``
    binds ``numpy``, and ``from numpy.random import default_rng as make`` binds
    ``make`` to ``numpy.random.default_rng``.

    """
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    imported[alias.asname] = alias.name
                else:
                    root = alias.name.split(".")[0]
                    imported[root] = root
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imported[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return imported


def _origin(node: ast.AST, imported: dict[str, str]) -> str | None:
    """Return the dotted name ``node`` stands for, if it is reached by an import."""
    if isinstance(node, ast.Name):
        return imported.get(node.id)
    if isinstance(node, ast.Attribute):
        owner = _origin(node.value, imported)
        return f"{owner}.{node.attr}" if owner else None
    return None


def _root(node: ast.AST) -> str | None:
    """Return the name an attribute chain starts from, as ``bbox`` of ``bbox.a``."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def measured_elsewhere(root: Path) -> list[str]:
    """Return where a benchmark measures code of its own, not the library's.

    A benchmark hands ``benchmark`` a function it imported, or a method of an
    imported name or of a fixture, and its inputs, which Python makes before the
    call is measured. Anything else, a lambda, a ``functools.partial``, a
    function defined in the benchmarks at any level, the decorator form or
    ``benchmark.pedantic``, measures code of the benchmark's own, which may
    build its inputs while it is timed.

    """
    found = []
    for path in sorted(root.rglob("test_*.py")):
        where = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = _imports(tree)
        for test in ast.walk(tree):
            if not isinstance(test, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            params = {arg.arg for arg in test.args.args + test.args.kwonlyargs}
            found.extend(
                f"{where}:{decorator.lineno}"
                for decorator in test.decorator_list
                if _uses_benchmark(decorator)
            )
            for node in ast.walk(test):
                if isinstance(node, ast.Attribute) and _uses_benchmark(node):
                    found.append(f"{where}:{node.lineno}")
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "benchmark"
                ):
                    continue
                target = node.args[0] if node.args else None
                if isinstance(target, ast.Name):
                    named = target.id in imported
                elif isinstance(target, ast.Attribute):
                    named = _root(target) in imported.keys() | params
                else:
                    named = False
                if not named:
                    found.append(f"{where}:{node.lineno}")
    return sorted(set(found), key=lambda item: int(item.rsplit(":", 1)[1]))


def unseeded(root: Path) -> list[str]:
    """Return where a module under ``root`` draws from an unseeded generator.

    That is a ``numpy.random.default_rng`` given no seed or ``None``, any other
    function of ``numpy.random``, whose state is global, or the standard
    library's ``random``, however each was imported.

    """
    found = []
    for path in sorted(root.rglob("*.py")):
        where = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = _imports(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name.split(".")[0] in GLOBAL_RANDOM for alias in node.names
            ):
                found.append(f"{where}:{node.lineno}")
                continue
            if isinstance(node, ast.ImportFrom) and node.module in GLOBAL_RANDOM:
                found.append(f"{where}:{node.lineno}")
                continue
            if not isinstance(node, ast.Call):
                continue
            origin = _origin(node.func, imported) or ""
            if not origin.startswith("numpy.random."):
                continue
            if origin != "numpy.random.default_rng":
                found.append(f"{where}:{node.lineno}")
                continue
            seeds = [*node.args, *(keyword.value for keyword in node.keywords)]
            if not seeds or any(
                isinstance(seed, ast.Constant) and seed.value is None for seed in seeds
            ):
                found.append(f"{where}:{node.lineno}")
    return found


def rendering(root: Path) -> list[str]:
    """Return where a module under ``root`` names a way to draw."""
    found = []
    for path in sorted(root.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            name = node.attr if isinstance(node, ast.Attribute) else None
            name = node.id if isinstance(node, ast.Name) else name
            name = node.name if isinstance(node, ast.alias) else name
            if name in RENDERING:
                found.append(f"{path.relative_to(root).as_posix()}:{node.lineno}")
    return found


def test_every_input_is_built_outside_the_measured_call(tmp_path):
    """Measure one named call, its inputs made before (bench spec §2 decision 7)."""
    assert measured_elsewhere(BENCHMARKS) == []
    (tmp_path / "test_x.py").write_text(
        "import functools\nimport numpy as np\n\n"
        "def test_lambda(benchmark):\n"
        "    benchmark(lambda: len(np.arange(10)))\n\n"
        "def test_local(benchmark):\n"
        "    def run():\n        return len(np.arange(10))\n"
        "    benchmark(run)\n\n"
        "def test_partial(benchmark):\n"
        "    benchmark(functools.partial(len, [1]))\n\n"
        "def test_pedantic(benchmark):\n"
        "    benchmark.pedantic(len, args=([1],))\n\n"
        "def test_named(benchmark, grid):\n"
        "    benchmark(np.sum, grid)\n"
    )
    assert measured_elsewhere(tmp_path) == [
        "test_x.py:5",
        "test_x.py:10",
        "test_x.py:13",
        "test_x.py:16",
    ]
    (tmp_path / "test_x.py").write_text(
        "import numpy as np\n\ndef test_decorated(benchmark):\n"
        "    @benchmark\n    def run():\n        return len(np.arange(10))\n"
    )
    assert measured_elsewhere(tmp_path) == ["test_x.py:4"]
    (tmp_path / "test_x.py").write_text(
        "import numpy as np\nfrom geovista.core import combine\n\n"
        "def run():\n    return len(np.arange(10))\n\n"
        "RUN = lambda: len(np.arange(10))\n\n"
        "def test_module(benchmark):\n    benchmark(run)\n\n"
        "def test_assigned(benchmark):\n    benchmark(RUN)\n\n"
        "def test_imported(benchmark, meshes):\n    benchmark(combine, *meshes)\n"
    )
    assert measured_elsewhere(tmp_path) == ["test_x.py:10", "test_x.py:13"]


def test_every_generator_is_seeded(tmp_path):
    """Draw every random input from a seeded generator (bench spec §2 decision 7)."""
    assert unseeded(BENCHMARKS) == []
    (tmp_path / "conftest.py").write_text(
        "import random\nimport numpy as np\n\n"
        "A = np.random.default_rng()\n"
        "B = np.random.default_rng(None)\n"
        "C = np.random.default_rng(seed=None)\n"
        "D = np.random.uniform(0, 1, 5)\n"
        "E = np.random.default_rng(0)\n"
    )
    assert unseeded(tmp_path) == [
        "conftest.py:1",
        "conftest.py:4",
        "conftest.py:5",
        "conftest.py:6",
        "conftest.py:7",
    ]
    (tmp_path / "conftest.py").write_text(
        "import numpy.random as rnd\n"
        "from numpy import random as nr\n"
        "from numpy.random import default_rng\n"
        "from numpy.random import default_rng as make\n"
        "from numpy.random import uniform\n\n"
        "A = default_rng()\n"
        "B = make(None)\n"
        "C = rnd.default_rng()\n"
        "D = nr.normal(0, 1, 5)\n"
        "E = uniform(0, 1, 5)\n"
        "F = default_rng(0)\n"
        "G = rnd.default_rng(seed=1)\n"
    )
    assert unseeded(tmp_path) == [
        "conftest.py:7",
        "conftest.py:8",
        "conftest.py:9",
        "conftest.py:10",
        "conftest.py:11",
    ]


def test_nothing_is_downloaded(tmp_path):
    """Run the benchmarks offline, from an empty cache (bench spec §2 decision 7).

    geovista fetches into ``GEOVISTA_CACHEDIR``, PROJ is kept off the network,
    and every other HTTP fetch is sent to a proxy that cannot be reached, so a
    download of any kind fails the run or leaves the cache behind.

    """
    cache = tmp_path / "cache"
    cache.mkdir()
    unreachable = "http://127.0.0.1:9"
    env = {
        **os.environ,
        "GEOVISTA_CACHEDIR": str(cache),
        "PROJ_NETWORK": "OFF",
        "HTTP_PROXY": unreachable,
        "HTTPS_PROXY": unreachable,
        "http_proxy": unreachable,
        "https_proxy": unreachable,
    }
    env.pop("NO_PROXY", None)
    env.pop("no_proxy", None)
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", "benchmarks", "-p", "no:memray", *PLAIN],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout[-2000:]
    assert [path.name for path in cache.rglob("*")] == []


def test_no_benchmark_renders(tmp_path):
    """Draw nothing, as a scene measures VTK (bench spec §2 decision 7)."""
    assert rendering(BENCHMARKS) == []
    (tmp_path / "test_x.py").write_text(
        "import pyvista as pv\nfrom geovista import GeoPlotter\n\n"
        "def test_x(benchmark, mesh):\n"
        "    renderer = pv.Renderer()\n"
        "    benchmark(renderer.add_mesh, mesh)\n"
    )
    assert rendering(tmp_path) == ["test_x.py:2", "test_x.py:5", "test_x.py:6"]


def test_vtk_is_pinned_at_import():
    """Pin VTK to one thread as the conftest loads (bench spec §2 decision 7).

    VTK's threaded backend caps its thread count at the CPU's, so on a single
    core ``test_vtk_runs_on_one_thread`` passes whatever the conftest does. This
    reads the conftest instead, which holds on any host.

    """
    tree = ast.parse(CONFTEST.read_text(encoding="utf-8"))
    pinned = [
        node
        for node in tree.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "Initialize"
        and getattr(node.value.func.value, "id", None) == "vtkSMPTools"
        and [getattr(arg, "value", None) for arg in node.value.args] == [1]
    ]
    assert pinned
