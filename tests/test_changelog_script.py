# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for ``.github/scripts/changelog.py``.

The script is the changelog fragment check that ``ci-changelog.yml`` runs on every
pull request. These tests run it against ``towncrier`` itself, in a project of
their own built in a temporary directory, and once against this repository's
configuration. A finding ends with the breadcrumb to the check's section, and a
failure to run the check ends with none (checks spec §3.3).

"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

from click.testing import CliRunner
import pytest

if TYPE_CHECKING:
    from types import ModuleType

#: The repository root.
REPO = Path(__file__).parents[1]

#: The script under test, which is no importable module.
SCRIPT = REPO / ".github" / "scripts" / "changelog.py"

#: The link a finding ends with, naming the changelog fragment check.
BREADCRUMB = "checks.html#gv-developer-checks-changelog-fragment"

#: The configuration of the project the tests build, with two fragment types.
CONFIG = """\
[tool.towncrier]
directory = "changelog"
template = "changelog/template.rst"

[[tool.towncrier.type]]
directory = "bugfix"
name = "Bug Fixes"
showcontent = true

[[tool.towncrier.type]]
directory = "feature"
name = "New Features"
showcontent = true
"""

#: The text of a fragment that credits its author.
CREDITED = "Fixed a thing. (:user:`someone`)\n"


@pytest.fixture
def summary(tmp_path, monkeypatch) -> Path:
    """Provide the job summary the script writes to, as it reads it at import."""
    path = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(path))
    return path


@pytest.fixture
def script(summary, monkeypatch) -> ModuleType:  # noqa: ARG001
    """Load the script, once the job summary it writes to is set."""
    spec = importlib.util.spec_from_file_location("changelog", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # a dataclass resolves its annotations through sys.modules
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def project(tmp_path, monkeypatch) -> Path:
    """Build a project with a towncrier configuration, and work from it."""
    root = tmp_path / "project"
    (root / "changelog").mkdir(parents=True)
    (root / "pyproject.toml").write_text(CONFIG, encoding="utf-8")
    (root / "changelog" / "template.rst").write_text("", encoding="utf-8")
    monkeypatch.chdir(root)
    return root


def _run(script: ModuleType, pr: str, *fragments: str) -> tuple[int, str]:
    """Run the check for a pull request, given its fragments as the workflow does."""
    paths = ",".join(f"changelog/{fragment}" for fragment in fragments)
    result = CliRunner().invoke(script.main, [pr, paths])
    return result.exit_code, result.output


def _write(project: Path, fragment: str, text: str = CREDITED) -> str:
    """Write a fragment into the project's changelog, and return its name."""
    (project / "changelog" / fragment).write_text(text, encoding="utf-8")
    return fragment


def test_a_valid_fragment_passes(script, project, summary):
    """A fragment named for its pull request, of a known type, credited, passes."""
    code, out = _run(script, "1234", _write(project, "1234.bugfix.rst"))
    assert code == 0, out
    assert "looks good" in out
    assert BREADCRUMB not in out + summary.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("fragment", "text", "expected"),
    [
        pytest.param("999.bugfix.rst", CREDITED, "for **[PR#1234]", id="other-pr"),
        pytest.param("1234.nonsense.rst", CREDITED, "**type**", id="type"),
        pytest.param("1234.bugfix.md", CREDITED, "**extension**", id="extension"),
        pytest.param("1234.rst", CREDITED, "**format**", id="format"),
        pytest.param("x1234.bugfix.rst", CREDITED, "**PR number**", id="pr-number"),
        pytest.param("1234.bugfix.rst", "Fixed a thing.\n", ":user:", id="author"),
    ],
)
def test_a_finding_names_the_rule_and_ends_with_the_breadcrumb(
    script, project, summary, fragment, text, expected
):
    """Each rule a fragment breaks is reported, in the log and the job summary."""
    code, out = _run(script, "1234", _write(project, fragment, text))
    written = summary.read_text(encoding="utf-8")
    assert code == 1
    assert expected in out
    assert expected in written
    assert BREADCRUMB in out
    assert BREADCRUMB in written


@pytest.mark.usefixtures("project")
def test_the_template_alone_is_no_fragment(script):
    """The template sits beside the fragments, but does not count as one."""
    code, out = _run(script, "1234", "template.rst")
    assert code == 1
    assert "Please provide a **changelog news fragment file**" in out
    assert BREADCRUMB in out


def test_no_pull_request_number_prints_no_breadcrumb(script, project, summary):
    """Without its number the check cannot run, so it names no rule."""
    code, out = _run(script, "", _write(project, "1234.bugfix.rst"))
    written = summary.read_text(encoding="utf-8") if summary.exists() else ""
    assert code == 1
    assert "Unable to collect PR number" in out
    assert "gv-developer-checks-" not in out + written


def test_no_configuration_prints_no_breadcrumb(script, tmp_path, monkeypatch, summary):
    """Without a towncrier configuration the check cannot run either."""
    bare = tmp_path / "bare"
    (bare / "changelog").mkdir(parents=True)
    _write(bare, "1234.bugfix.rst")
    monkeypatch.chdir(bare)
    code, out = _run(script, "1234", "1234.bugfix.rst")
    written = summary.read_text(encoding="utf-8") if summary.exists() else ""
    assert code == 1
    assert "No configuration file found" in out
    assert "gv-developer-checks-" not in out + written


def test_the_repository_configuration_is_read(script, monkeypatch):
    """The repository's own configuration and fragments pass the check.

    A fragment already merged is valid by construction, so this holds the check
    to the configuration it really runs with.

    """
    fragment = next(
        path
        for path in sorted((REPO / "changelog").glob("*.*.rst"))
        if path.name.partition(".")[0].isdigit()
        and ":user:" in path.read_text(encoding="utf-8")
    )
    monkeypatch.chdir(REPO)
    code, out = _run(script, fragment.name.partition(".")[0], fragment.name)
    assert code == 0, out
