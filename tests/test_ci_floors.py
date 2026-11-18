# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that hold the jobs at the pip floors to floors spec §4.3.

The ``pypi`` job of ``ci-floors.yml`` installs geovista with its ``test`` and
``exam`` extras at their lowest from PyPI, with ``uv``, on the oldest supported
Python, and runs the suite without the image tests. The ``floors-pypi`` composite
action does the work, so that ``ci-wheels.yml`` can run it against a built wheel
(row 4 of floors spec §9). The action restores the data through the two cache
actions, which run their commands from its environment rather than through
``pixi``.

The tests run the steps' own shell, with stand-ins for ``uv``, ``pixi`` and the
other commands on the ``PATH``, so they check what the steps do rather than how
they read.

"""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

import pytest
import yaml

#: The repository root, holding the workflows.
ROOT = Path(__file__).parents[1]
#: The directory of the composite actions.
COMPOSITE = ROOT / ".github" / "workflows" / "composite"
#: The composite actions restoring the data, which take the ``pixi`` input.
CACHES = ("cartopy-cache", "geovista-cache")

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None, reason="the actions' steps run under bash"
)


def _action(name: str) -> dict[str, Any]:
    """Return the parsed composite action of the given name."""
    path = COMPOSITE / name / "action.yml"
    assert path.is_file(), f"no composite action {name!r}"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _step(steps: list[dict[str, Any]], name: str) -> dict[str, Any]:
    """Return the one step of the given name."""
    found = [step for step in steps if step.get("name") == name]
    assert len(found) == 1, f"{len(found)} steps named {name!r}"
    return found[0]


@pytest.mark.parametrize("name", CACHES)
def test_the_cache_actions_run_through_pixi_by_default(name):
    """A caller that passes nothing runs the cache action as before."""
    pixi = _action(name).get("inputs", {}).get("pixi")

    assert pixi is not None, f"{name!r} takes no 'pixi' input"
    assert pixi.get("required") is False
    assert pixi.get("default") == "true"


@pytest.mark.parametrize(
    ("name", "step", "command"),
    [
        ("cartopy-cache", "refresh cartopy cache", "cartopy_feature_download"),
        ("geovista-cache", "get geovista-data version", "geovista"),
        ("geovista-cache", "refresh geovista cache", "geovista"),
    ],
)
@pytest.mark.parametrize("pixi", ["true", "false"])
def test_a_cache_action_runs_its_command_through_pixi_unless_told_not_to(
    tmp_path, stub, run_step, name, step, command, pixi
):
    """The floors job has no pixi, and runs the command from its environment."""
    body = _step(_action(name)["runs"]["steps"], step)
    log = tmp_path / "calls.log"
    for word in ("pixi", command):
        stub(word, f'printf "%s\\n" "{word} $*" >> "{log}"')
    env = {"INPUTS_PIXI": pixi, "GITHUB_OUTPUT": str(tmp_path / "output")}

    result = run_step(body, env)

    assert result.returncode == 0, result.stderr
    assert (body.get("env") or {}).get("INPUTS_PIXI") == "${{ inputs.pixi }}"
    calls = log.read_text(encoding="utf-8").splitlines()
    assert calls, f"{step!r} ran nothing"
    first = {call.split()[0] for call in calls}
    if pixi == "true":
        assert first == {"pixi"}, calls
    else:
        assert first == {command}, calls
