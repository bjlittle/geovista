# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests that "mypy" checks the whole package, in CI as in the hook.

GeoVista type checks in strict mode against the locked pixi environment, where
the third-party types are real. The modules that once reported errors were
listed under ``ignore_errors`` and retired one change at a time, until none was
left. These tests keep it that way: no override may ignore a module's errors,
no module may configure "mypy" inline, the per-module relaxations stay the
ones the specification gives reasons for, and the workflow that runs "mypy"
for "pre-commit.ci" must keep running it.

See "docs/src/developer/specs/2026-10-06-type-coverage-design.md", section 3.2.

"""

from __future__ import annotations

from functools import cache
import io
from pathlib import Path
import re
import tokenize
import tomllib
from typing import Any

import pytest
import yaml

#: The section of the repository checks page that documents this check.
CHECK = "strict-typing"

#: The repository root, holding the manifest.
ROOT = Path(__file__).parents[1]
#: The manifest declaring the "mypy" configuration and its overrides.
PYPROJECT = ROOT / "pyproject.toml"
#: The hook configuration, which must skip "mypy" on "pre-commit.ci".
PRE_COMMIT = ROOT / ".pre-commit-config.yaml"
#: The workflow carrying the coverage "pre-commit.ci" cannot provide.
WORKFLOW = ROOT / ".github" / "workflows" / "ci-typing.yml"
#: The package "mypy" checks, as "[tool.mypy]" names it in "files".
PACKAGE = ROOT / "src" / "geovista"
#: The gallery, whose scripts are published as example code.
GALLERY = PACKAGE / "examples"

#: Every per-module setting that relaxes strict mode, by the module it is set
#: for. "pyproject.toml" gives the reason for each, citing typing spec §3.1 for
#: the first two and typing spec §3.4 for the gallery. Adding, changing or
#: withdrawing one is a change to this table, as a ratchet entry was.
RELAXED = {
    "geovista.cli": {"disallow_untyped_decorators": False},
    "geovista.examples.*": {"disable_error_code": ["call-arg", "no-untyped-call"]},
    "geovista.qt": {"disallow_subclassing_any": False},
}

#: A line that reads as inline "mypy" configuration. "mypy" honours one only at
#: the start of a line and spelled exactly ``# mypy:``, but an indented or
#: respaced one is as likely a mistake, so this matches more than "mypy" does.
INLINE = re.compile(r"^\s*#\s*mypy\s*:", flags=re.IGNORECASE)

#: A comment silencing "mypy" on its line, with or without an error code.
IGNORE = re.compile(r"#\s*type\s*:\s*ignore\b", flags=re.IGNORECASE)

#: Lines that do and do not configure "mypy", for holding :data:`INLINE` to
#: the parser "mypy" itself uses.
SAMPLES = (
    "# mypy: ignore-errors",
    'x = 1\n# mypy: disable-error-code="arg-type"',
    "    # mypy: ignore-errors",
    "#mypy: ignore-errors",
    "x = 1  # mypy: ignore-errors",
    "# not mypy: ignore-errors",
)

#: The override settings that relax nothing "mypy" checks in a module: which
#: modules a block applies to, and whether an import of them may be missing.
NEUTRAL = frozenset({"ignore_missing_imports", "module"})


def _modules(override: dict[str, Any]) -> tuple[str, ...]:
    """Return the modules an override applies to.

    Parameters
    ----------
    override : dict
        One ``[[tool.mypy.overrides]]`` block, as parsed.

    Returns
    -------
    tuple of str
        The modules named, however they were written. "mypy" accepts a bare
        string as well as an array, and the "geovista.cli" override uses one,
        so iterating the value directly would yield its characters.

    """
    module = override.get("module", ())
    return (module,) if isinstance(module, str) else tuple(module)


@cache
def _ignored() -> frozenset[str]:
    """Return every module "mypy" is told to ignore errors in.

    Returns
    -------
    frozenset of str
        Collected from every override block, so that no block carrying
        ``ignore_errors`` goes unseen.

    """
    manifest = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    overrides = manifest["tool"]["mypy"].get("overrides", [])
    return frozenset(
        module
        for override in overrides
        if override.get("ignore_errors", False)
        for module in _modules(override)
    )


def _relaxed(overrides: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return every setting an override relaxes, by module.

    Parameters
    ----------
    overrides : list of dict
        The ``[[tool.mypy.overrides]]`` blocks, as parsed.

    Returns
    -------
    dict
        For each module named by a block carrying anything but the settings in
        :data:`NEUTRAL`, those settings, merged across every block that names
        it. ``disable_error_code`` is one of them, and silences a code for a
        module as surely as ``ignore_errors`` silences them all.

    """
    relaxed: dict[str, dict[str, Any]] = {}
    for override in overrides:
        settings = {k: v for k, v in override.items() if k not in NEUTRAL}
        if settings:
            for module in _modules(override):
                relaxed.setdefault(module, {}).update(settings)
    return relaxed


def _inline(path: Path) -> list[tuple[int, str]]:
    """Return the inline configuration "mypy" reads from a module.

    Parameters
    ----------
    path : Path
        The module.

    Returns
    -------
    list of tuple
        The line number and text of each line :data:`INLINE` matches.

    """
    return _matches(path.read_text(encoding="utf-8"))


def _matches(text: str) -> list[tuple[int, str]]:
    """Return each line of ``text`` that reads as inline configuration.

    Parameters
    ----------
    text : str
        The source of a module.

    Returns
    -------
    list of tuple
        The line number, counted from one, and text of each matching line.

    """
    return [
        (number, line)
        for number, line in enumerate(text.splitlines(), start=1)
        if INLINE.match(line)
    ]


def _ignores(root: Path) -> dict[str, str]:
    """Return each type-ignore comment in the scripts under a directory.

    Parameters
    ----------
    root : Path
        The directory to search.

    Returns
    -------
    dict of str to str
        The text of each comment carrying one, by its path relative to
        ``root`` and its line number, counted from one. Only a comment token
        counts, as only a comment silences "mypy": the same text in a string
        or a docstring suppresses nothing.

    """
    return {
        f"{script.relative_to(root).as_posix()}:{token.start[0]}": token.string
        for script in sorted(root.rglob("*.py"))
        for token in tokenize.generate_tokens(
            io.StringIO(script.read_text(encoding="utf-8")).readline
        )
        if token.type == tokenize.COMMENT and IGNORE.search(token.string)
    }


def _commands(step: dict[str, Any]) -> tuple[str, ...]:
    """Return the commands a step really runs.

    Parameters
    ----------
    step : dict
        One workflow step, as parsed.

    Returns
    -------
    tuple of str
        One entry per line of ``run``, stripped, with blanks and comments
        dropped, so that a command matches as a whole line rather than as a
        substring: ``echo``-ing it, commenting it out or appending
        ``|| true`` then no longer reads as running it. A step carrying
        ``if`` or ``continue-on-error`` may be skipped or may fail
        harmlessly, and yields nothing — the workflow cannot be held to a
        step that need not run. Adding either deliberately means revisiting
        this test.

    """
    if "if" in step or step.get("continue-on-error"):
        return ()
    return tuple(
        line
        for raw in step.get("run", "").splitlines()
        if (line := raw.strip()) and not line.startswith("#")
    )


def _steps() -> tuple[dict[str, Any], ...]:
    """Return every step of every job in the typing workflow.

    Returns
    -------
    tuple of dict
        The steps, flattened. A job that calls a reusable workflow carries
        ``uses`` instead of ``steps``, and contributes nothing.

    """
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return tuple(
        step for job in workflow["jobs"].values() for step in job.get("steps", [])
    )


def _hook() -> dict[str, Any]:
    """Return the "local" "mypy" hook.

    Returns
    -------
    dict
        The hook, as parsed.

    """
    config = yaml.safe_load(PRE_COMMIT.read_text(encoding="utf-8"))
    hooks = [
        hook
        for repo in config["repos"]
        if repo["repo"] == "local"
        for hook in repo["hooks"]
        if hook["id"] == "mypy"
    ]
    assert hooks, "no local 'mypy' hook: is the skip still needed?"
    return hooks[0]


def test_no_module_ignores_errors():
    """No override may tell "mypy" to ignore a module's errors.

    The typing ratchet listed every module that reported errors under
    ``ignore_errors`` and only ever shrank, until change 7 of the roadmap
    retired its last entry. An override that brought ``ignore_errors`` back
    would hand back the coverage those changes won, in one line of the
    manifest.

    """
    assert not _ignored(), f"errors ignored in: {sorted(_ignored())}"


def test_no_module_configures_mypy_inline():
    """No module may carry a ``# mypy:`` comment.

    ``# mypy: ignore-errors`` at the head of a module stops it being checked,
    and ``# mypy: disable-error-code=...`` silences a code in it, yet neither
    touches the manifest the other tests read, and the hook refusing a bare
    type-ignore comment does not match them. Any other inline flag changes how
    one module is checked out of sight of "[tool.mypy]", so none is allowed.

    """
    modules = sorted({*PACKAGE.rglob("*.py"), *PACKAGE.rglob("*.pyi")})
    assert modules, f"no modules found under {PACKAGE}"
    found = {
        f"{module.relative_to(ROOT)}:{line}": text
        for module in modules
        for line, text in _inline(module)
    }
    assert not found, f"configure mypy in pyproject.toml, not inline: {found}"


def test_no_gallery_script_ignores_a_type_error():
    """No gallery script may carry a type-ignore comment.

    The gallery is rendered into the documentation and readers are invited to
    copy it, so a comment silencing "mypy" in one is a directive published as
    example code. A defect a script cannot fix is suppressed in "[tool.mypy]"
    instead, where ``RELAXED`` pins it (typing spec §3.4). The hook refusing a
    bare type-ignore comment passes one that names its error code, and strict
    mode refuses only one that has become unused.

    Holds typing spec §2 decision 4.

    """
    assert any(GALLERY.rglob("*.py")), f"no gallery scripts found under {GALLERY}"
    ignored = _ignores(GALLERY)
    assert not ignored, f"suppress in pyproject.toml, not the script: {ignored}"


def test_a_type_ignore_in_a_gallery_script_is_found(tmp_path):
    """A type-ignore comment is found however it is spelled or placed.

    The comments are built, since the hook refusing a bare one reads this module.

    """
    ignore = "type" + ":" + "ignore"
    (tmp_path / "plain.py").write_text('"""Doc."""\n\nx = 1\n', encoding="utf-8")
    (tmp_path / "scene").mkdir()
    spaced = ignore.replace(":", ": ")
    (tmp_path / "scene" / "camera.py").write_text(
        f"x: int = 'a'  # {spaced}[assignment]\ny = 1  #{ignore}\n# {spaced}\n",
        encoding="utf-8",
    )
    expected = {"scene/camera.py:1", "scene/camera.py:2", "scene/camera.py:3"}
    assert set(_ignores(tmp_path)) == expected


def test_a_type_ignore_in_a_string_is_not_a_comment(tmp_path):
    """Only a comment silences "mypy", so the text in a string or docstring passes.

    A script may print the directive, or a docstring describe it, without
    suppressing anything.

    """
    spaced = "type" + ": " + "ignore"
    (tmp_path / "label.py").write_text(
        f'"""Say why a script never carries ``# {spaced}``."""\n\n'
        f'label = "# {spaced}[attr-defined]"\n'
        f"text = '''\n# {spaced}\n'''\n",
        encoding="utf-8",
    )
    assert _ignores(tmp_path) == {}


def test_inline_configuration_is_found(tmp_path):
    """A ``# mypy:`` comment is found wherever "mypy" would honour it."""
    module = tmp_path / "module.py"
    module.write_text('"""Doc."""\n\nx = 1\n# mypy: ignore-errors\n', encoding="utf-8")
    assert _inline(module) == [(4, "# mypy: ignore-errors")]


@pytest.mark.parametrize("sample", SAMPLES)
def test_inline_matches_whatever_mypy_honours(sample):
    """Every line "mypy" reads as configuration, :data:`INLINE` matches too.

    "mypy" is in the pixi environments, where this runs, but not in the
    ``test`` extra the "pip" workflow installs, so the guard itself carries
    its own pattern rather than importing the parser.

    """
    util = pytest.importorskip("mypy.util")
    honoured = {line for line, _ in util.get_mypy_comments(sample)}
    assert honoured <= {line for line, _ in _matches(sample)}


def test_only_the_known_overrides_relax_strict():
    """Each per-module relaxation of strict mode is one the specification gives.

    ``test_no_module_ignores_errors`` sees ``ignore_errors`` and nothing else,
    so a block disabling an error code for a module passed unseen. That is how
    a ``union-attr`` override on ``geovista.examples.grid.*`` hid four reads of
    an optional point of interest until change 7 of the roadmap removed it.
    Settings such as ``disallow_untyped_defs = false`` relax a module in the
    same way. Pinning them all means a new one cannot arrive unnoticed.

    Holds typing spec §2 decision 4.
    """
    manifest = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    relaxed = _relaxed(manifest["tool"]["mypy"].get("overrides", []))
    changed = {
        module: relaxed.get(module)
        for module in sorted(relaxed.keys() | RELAXED.keys())
        if relaxed.get(module) != RELAXED.get(module)
    }
    assert not changed, f"relaxations differ from RELAXED: {changed}"


def test_a_neutral_override_relaxes_nothing():
    """Only the settings that change what is checked count as relaxing it."""
    overrides = [
        {"module": "a", "ignore_missing_imports": True},
        {"module": ["b.*"], "disable_error_code": ["x"]},
        {"module": ["b.*"], "disallow_untyped_defs": False},
    ]
    assert _relaxed(overrides) == {
        "b.*": {"disable_error_code": ["x"], "disallow_untyped_defs": False}
    }


def test_mypy_hook_is_skipped_on_pre_commit_ci():
    """The local "mypy" hook needs "pixi", which "pre-commit.ci" has not got.

    Without the skip every "pre-commit.ci" run fails with "pixi: command not
    found", which reads as infrastructure flake rather than configuration.
    The coverage moves to ".github/workflows/ci-typing.yml".

    """
    config = yaml.safe_load(PRE_COMMIT.read_text(encoding="utf-8"))
    assert _hook()["language"] == "system", "a managed environment needs no skip"
    assert "mypy" in config["ci"]["skip"]


def test_ci_typing_names_a_declared_environment():
    """The workflow's pixi environment must exist in the manifest.

    A name that does not resolve fails the job at setup, with a message about
    the environment rather than about the manifest that should have declared
    it.

    """
    manifest = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    declared = set(manifest["tool"]["pixi"]["environments"])
    named = {
        step["with"]["environments"]
        for step in _steps()
        if "setup-pixi" in str(step.get("uses", ""))
    }
    assert named, "ci-typing.yml sets up no pixi environment"
    assert named <= declared, f"undeclared: {sorted(named - declared)}"


def test_ci_typing_runs_the_hook_command():
    """The workflow must run the command "pre-commit.ci" is skipping.

    "mypy" is skipped on "pre-commit.ci" on the understanding that this
    workflow carries it instead, and nothing else holds it to that. The step
    can be deleted, or reduced to something that always succeeds, and the skip
    then retires the check outright while both jobs stay green. So the command
    has to end an enabled step, not merely appear somewhere in its script:
    this job overrides the shell to ``bash -l {0}``, dropping the ``-e`` that
    GitHub's default carries, and a command with anything after it can then
    fail while the step succeeds. ``frozen`` is part of the command too — it
    resolves from "pixi.lock" rather than re-solving the manifest, which is
    what makes the two environments the same one.

    Holds typing spec §2 decision 1.
    """
    entry = _hook()["entry"]
    endings = [script[-1] for step in _steps() if (script := _commands(step))]
    assert entry in endings, f"no enabled step ends by running {entry!r}"
    setup = [step for step in _steps() if "setup-pixi" in str(step.get("uses", ""))]
    assert all(step["with"].get("frozen") for step in setup), "install from the lock"


def test_a_bare_module_string_is_read_whole():
    """A "module" written as a string yields the module, not its characters."""
    assert _modules({"module": "geovista.cli"}) == ("geovista.cli",)
    assert _modules({"module": ["geovista.qt"]}) == ("geovista.qt",)
    assert _modules({}) == ()


@pytest.mark.parametrize(
    "step",
    [
        pytest.param({"run": 'echo "check"'}, id="echoed"),
        pytest.param({"run": "# check"}, id="commented-out"),
        pytest.param({"run": "check || true"}, id="swallowed"),
        pytest.param({"run": "check &"}, id="backgrounded"),
        pytest.param({"if": "false", "run": "check"}, id="conditional"),
        pytest.param({"continue-on-error": True, "run": "check"}, id="tolerated"),
    ],
)
def test_only_an_executed_command_counts(step):
    """A command the step does not really run must not read as run.

    Each of these keeps the text of the command in the workflow while
    disposing of its effect: ``echo`` prints it, ``#`` comments it out,
    ``|| true`` and ``&`` discard its exit status, and ``if`` or
    ``continue-on-error`` excuse the step from mattering at all. Matching
    the command as a substring of the script accepts every one of them.

    """
    assert "check" not in _commands(step)


def test_the_last_command_of_an_enabled_step_counts():
    """The command ending an enabled step is the one whose failure lands."""
    assert _commands({"run": "echo starting\ncheck\n"})[-1] == "check"


def test_ci_typing_cannot_tolerate_its_own_failure():
    """No job may carry ``continue-on-error``.

    Such a job is green whatever "mypy" reports, which is the same outcome
    as having no job at all, and no guard written against a step can see it.

    """
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    tolerated = sorted(
        name for name, job in workflow["jobs"].items() if job.get("continue-on-error")
    )
    assert not tolerated, f"green whatever happens: {tolerated}"


def test_no_global_suppression():
    """Nothing at the top of "[tool.mypy]" may silence a module's errors.

    ``test_no_module_ignores_errors`` reads the override blocks, so a
    suppression written above them is invisible to it. A top-level
    ``ignore_errors`` silences every module at once, ``disable_error_code``
    silences a class of error everywhere, and narrowing ``files`` or filling
    ``exclude`` drops modules from the run altogether. Each would otherwise
    leave the whole suite green.

    """
    manifest = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    mypy = manifest["tool"]["mypy"]
    assert not mypy.get("ignore_errors", False), "this silences every module"
    assert not mypy.get("disable_error_code", []), "disable per module, not globally"
    assert mypy["files"] == ["src/geovista"], "the whole package is checked"
    assert mypy["exclude"] == [], "an exclude drops modules from the run"
