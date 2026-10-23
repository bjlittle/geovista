# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the output of ``.github/scripts/changelog.py``.

The script imports ``towncrier``, which only the ``docs`` environment carries, so
these tests stand a stub in for it. They cover the breadcrumb a finding ends with,
and its absence when the check cannot run (checks spec §3.3). Testing the script
against the real ``towncrier`` is #2704.

"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING

from click.testing import CliRunner
import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

#: The script under test, which is no importable module.
SCRIPT = Path(__file__).parents[1] / ".github" / "scripts" / "changelog.py"

#: The link a finding ends with, naming the changelog fragment check.
BREADCRUMB = "checks.html#gv-developer-checks-changelog-fragment"


class ConfigError(Exception):
    """Stand in for the error ``towncrier`` raises on a bad configuration."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@pytest.fixture
def summary(tmp_path, monkeypatch) -> Path:
    """Provide the job summary the script writes to, as it reads it at import."""
    path = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(path))
    return path


@pytest.fixture
def load(summary, monkeypatch) -> Callable[..., ModuleType]:  # noqa: ARG001
    """Provide a loader of the script, with ``towncrier`` stood in for."""

    def loader(config: Callable[..., object] | None = None) -> ModuleType:
        towncrier = ModuleType("towncrier")
        settings = ModuleType("towncrier._settings")
        settings.ConfigError = ConfigError
        settings.load_config_from_options = config or (
            lambda **_: (".", SimpleNamespace(types={}))
        )
        monkeypatch.setitem(sys.modules, "towncrier", towncrier)
        monkeypatch.setitem(sys.modules, "towncrier._settings", settings)
        spec = importlib.util.spec_from_file_location("changelog", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        # a dataclass resolves its annotations through sys.modules
        monkeypatch.setitem(sys.modules, spec.name, module)
        spec.loader.exec_module(module)
        return module

    return loader


def test_finding_prints_the_breadcrumb(load, summary, capsys):
    """A broken rule ends with the breadcrumb, in the log and the job summary."""
    script = load()
    with pytest.raises(SystemExit):
        script.failure(["Found invalid news fragment **type**."])
    out = capsys.readouterr().out
    written = summary.read_text(encoding="utf-8")
    assert BREADCRUMB in out
    assert BREADCRUMB in written
    assert "towncrier.html#changelog" not in out + written


def _raise(**_: object) -> object:
    """Raise the configuration error ``towncrier`` would."""
    message = "no configuration"
    raise ConfigError(message)


@pytest.mark.parametrize(
    ("pr", "config"),
    [
        pytest.param("", None, id="no-pull-request"),
        pytest.param("1234", _raise, id="bad-configuration"),
        pytest.param("1234", None, id="no-types"),
    ],
)
def test_failure_to_run_prints_none(load, summary, pr, config):
    """A check that cannot run has found nothing, so it names no rule."""
    script = load(config)
    result = CliRunner().invoke(script.main, [pr, "changelog/1234.bugfix.rst"])
    written = summary.read_text(encoding="utf-8") if summary.exists() else ""
    assert result.exit_code == 1
    assert "gv-developer-checks-" not in result.output + written
