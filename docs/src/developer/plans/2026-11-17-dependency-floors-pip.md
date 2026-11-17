# The pip Floors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 2 of floors spec §9: a floor on every `pip` requirement, equal to its `pixi` floor, the Dependency Floors check that holds the two equal, and their pages, with the sign-off of §2 decision 11.

**Architecture:** The readers of both declaration sites move out of `tests/test_dependency_ceilings.py` into two session fixtures of `tests/conftest.py`, which the ceilings check and a new `tests/test_dependency_floors.py` both take. The floors check reads each package's floor in every `pip` file and `pixi` table that declares it, as a `Version`, and fails on a requirement without one, on one it cannot read, and on floors that differ. Each of the 58 floorless `pip` lines gains the floor of its `pixi` declaration.

**Tech Stack:** pytest, `packaging` (`Requirement`, `SpecifierSet`, `Version`, `canonicalize_name`), `tomllib`, pixi 0.84.2 or later, Sphinx.

**Spec:** `docs/src/developer/specs/2026-11-15-dependency-floors-design.md` (`floors spec §…`): §2 decisions 5 and 11, §3.1, §4.2, §4.4, §4.5 (the rows marked 2, and the `AGENTS.md` note), §6, §9 row 2.

## Global Constraints

- Each of the 58 floorless lines of `requirements/pypi-core.txt` and the `devs`, `docs`, `exam` and `test` files becomes `<name> >=F,<C`: `F` copied verbatim from its `pixi` declaration, `C` its ceiling as it stands, as `click >=8.2.1,<8.6`, `lazy-loader >=0.4.0,<0.7`, `h3 >=4.2.2,<4.6` and `pyarrow >=18.0.0,<26.1` (§4.4, and §4.2 for `pyarrow`). Comments and line order stay; `pypi-optional-all.txt` is left alone. The 13 lines with a floor already equal their `pixi` floors (measured 2026-11-17).
- The check is `tests/test_dependency_floors.py`, with `CHECK = "dependency-floors"`. Its section, "Dependency Floors", follows "Dependency Ceilings" in `docs/src/developer/checks.rst`, labelled `gv-developer-checks-dependency-floors` and `tippy-gv-developer-checks-dependency-floors`, and its row follows that check's in the table, with the exception "none".
- A floor is the version of a spec's single `>=`, compared as a `packaging.version.Version`, so `0.4` and `0.4.0` agree. `<`, `<=` and `!=` do not bear on it. `>`, `==`, `===`, `~=`, a wildcard, a second `>=`, or a spec `packaging` cannot parse makes it unreadable, which is reported (§4.4).
- Only a package declared on both sides is compared. A `pixi` declaration with no `pip` counterpart (§3.1: `python`, `pip`, `setuptools`, `setuptools-scm`, `make`) is never read.
- Each failure ends with the remedy: put the floor back where a dependabot pull request moved it, or raise it on both sides in one commit and run `pixi lock` (§4.4). A floor lowered also needs `pixi update --environment floors <package>` (§4.1).
- `pixi lock` is the only command run without `--frozen`, under pixi 0.84.2 or later, which `requires-pixi` enforces. Its diff touches only the `requires_dist` of the lock's `- pypi: ./` record.
- Warnings are errors under pytest. Every Python file carries the copyright header and `from __future__ import annotations`. `AGENTS.md` and `tests/AGENTS.md` stay under 200 lines.
- Commit through `pixi run --frozen -e geovista git commit ...`, after `pixi run --frozen -e devs pre-commit run --files <paths>`. The fragment is `changelog/2985.dependency.rst`, crediting ``(:user:`claude`)``. The pull request carries `agentic`, `type: dependencies`, `type: testing` and `type: documentation`, and closes no issue.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-17 that the specification fixes how row 2 behaves (workflow rule 2.7), and chose on 2026-11-16 that the sign-off of §2 decision 11 goes in this pull request. The rest are mine.

1. **The readers are shared, as fixtures.** `_pip()` and `_pixi()` become the session fixtures `pip_specs` and `pixi_specs` of `tests/conftest.py`, rather than being copied into the new check. Under the `importlib` import mode no test module can import another, and the root `conftest.py` is where shared fixtures live (`tests/AGENTS.md`).
2. **Each clause of §4.4 is demonstrated by a test that stays.** The check's helpers take the two maps as arguments, so a counterexample is a small map handed to one (§6, workflow rule 2.6). The real files are broken once as well, in Task 2.
3. **A `pixi` declaration without a floor, for a package `pip` declares, disagrees.** It is shown as `none` among the floors that differ, rather than reported as unreadable.
4. **Row 2 verifies §2 decision 5** with `tests/test_dependency_floors.py`, and records §2 decision 11 as `✍️ signed off` for {user}`bjlittle` to attest with the `signed-off` label (workflow rule 2.5), citing the branch protection of `main`.
5. **One fragment, of type `dependency`**, since what a user sees is that `pip install geovista` no longer admits a release below a floor. It names the check in its second sentence.
6. **The branch is `floors/row2-pip`.** The plan is the first commit of draft pull request {pull}`2985` (workflow rule 2.3), which also marks row 2 `🚧 in progress ({pull}`2985`)` (workflow rule 2.4).

## Review Focus

1. **A `pixi` declaration without a floor**, as `numpy = "<3"`, for a package `pip` declares: reported among the floors that differ, as `none`, never passed over. `test_a_pixi_declaration_without_a_floor_is_reported` (Task 2).
2. **One floor written two ways**, as `>=0.4` beside `>=0.4.0`: they agree. `test_floors_written_differently_agree` (Task 2).
3. **An exclusion beside a floor**, as `>=1.0,!=1.2,<2`: the floor is 1.0, and nothing is reported. `test_an_exclusion_leaves_the_floor_readable` (Task 2).
4. **A conda wildcard on the `pixi` side**, as `1.7.*`, for a compared package: reported as unreadable, rather than crashing the check. A case of `test_a_floor_the_check_cannot_read_is_reported` (Task 2).
5. **A package in two `pip` files, one without a floor**, as `towncrier`: the failure names that file alone. `test_a_second_file_without_a_floor_is_named` (Task 2).

---

### Task 1: Share the Readers

**Files:**
- Modify: `tests/conftest.py`
- Modify: `tests/test_dependency_ceilings.py`
- Modify: `tests/AGENTS.md`

**Interfaces:**
- Produces: the session fixtures `pip_specs` and `pixi_specs` in `tests/conftest.py`, each a `dict[str, dict[str, str]]` mapping a canonical package name to the spec each declaring `pip` file (by file name) or `pixi` table (as `dependencies` or `feature.<name>.<table>`) gives it. `pip_specs` skips `-r` lines and `geovista`, and maps a name through `RENAMED = {"h3": "h3-py"}`. They return what `_pip()` and `_pixi()` return today.

- [ ] **Step 1: Move the readers**, with `PYPROJECT`, `REQUIREMENTS`, `TABLES` and `RENAMED`, into `tests/conftest.py` as the two fixtures, their bodies unchanged. The ceilings tests and `_unreadable` take them as parameters, and the message naming `RENAMED` says it is in `tests/conftest.py`. No assertion changes.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_dependency_ceilings.py tests/test_repository_checks.py`. Expected: PASS, the same four ceilings tests.
- [ ] **Step 3: Break the wiring** once: drop `h3` from `RENAMED` and watch `test_every_pip_requirement_is_a_pixi_dependency` fail naming `h3`, then restore.
- [ ] **Step 4: Name the fixtures** in the list of the root `conftest.py`'s fixtures in `tests/AGENTS.md`.
- [ ] **Step 5: Commit** as `tests: share the readers of the pip and pixi declarations (floors spec row 2)`.

### Task 2: The Dependency Floors Check

**Files:**
- Create: `tests/test_dependency_floors.py`
- Modify: `requirements/pypi-core.txt`, `requirements/pypi-optional-devs.txt`, `requirements/pypi-optional-docs.txt`, `requirements/pypi-optional-exam.txt`, `requirements/pypi-optional-test.txt`
- Modify: `pixi.lock`
- Modify: `docs/src/developer/checks.rst`

**Interfaces:**
- Consumes: `pip_specs` and `pixi_specs` (Task 1).
- Produces, in `tests/test_dependency_floors.py`: `Specs = dict[str, dict[str, str]]`; `_floor(spec: str) -> Version | None`, `None` for no floor, raising `ValueError` for one it cannot read; `_floorless(pip: Specs) -> dict[str, list[str]]`, each package to its files without a floor, passing over a spec `_unreadable` reports; `_unreadable(pip: Specs, pixi: Specs) -> dict[str, str]`, keyed `"<package> (<where>)"` as the ceilings check keys it; `_disagreements(pip: Specs, pixi: Specs) -> dict[str, dict[str, str]]`, each package whose floors differ to its floor at each place, as `str(Version)` or `"none"`, passing over a place `_unreadable` reports.

- [ ] **Step 1: Write the tests**, each citing its clause in its docstring:
  - On the source tree: `test_every_pip_requirement_declares_a_floor` (§2 decision 5), `_floorless(pip_specs) == {}`; `test_every_floor_is_one_the_check_can_read`, `_unreadable(pip_specs, pixi_specs) == {}`; `test_every_floor_is_the_same_on_both_sides` (§2 decision 5), `_disagreements(pip_specs, pixi_specs) == {}`.
  - On counterexamples (§6): `test_a_requirement_without_a_floor_is_reported`, `_floorless({"pooch": {"pypi-core.txt": "<1.10"}}) == {"pooch": ["pypi-core.txt"]}`; `test_a_floor_unlike_the_pixi_one_is_reported`, `pip` numpy `>=2.2.6,<2.6` against `pixi` `>=2.2.5,<3` gives `{"numpy": {"pypi-core.txt": "2.2.6", "dependencies": "2.2.5"}}`; `test_pip_files_that_disagree_are_reported`, towncrier at `>=24.8.0` in `pypi-optional-docs.txt` and `>=24.7.0` in `pypi-optional-test.txt`, beside a `pixi` `>=24.8.0`, is reported; `test_a_floor_the_check_cannot_read_is_reported`, parametrized over `pip` specs `>2.2`, `==2.2.6`, `~=2.2`, `==2.*`, `===2.2.6` and `>=2.2,>=2.3`, and the `pixi` spec `1.7.*` (Review Focus 4), each reported under its package and place; `test_a_pixi_only_dependency_is_not_compared`, `python` at `3.13.*` in `feature.py313.dependencies` alone gives `{}` from `_unreadable` and `_disagreements`.
  - For the Review Focus: `test_a_pixi_declaration_without_a_floor_is_reported` (1), `pixi` `<3` against `pip` `>=2.2.6,<2.6` shows `"none"`; `test_floors_written_differently_agree` (2), `>=0.4` and `>=0.4.0` give `{}`; `test_an_exclusion_leaves_the_floor_readable` (3), `_floor(">=1.0,!=1.2,<2") == Version("1.0")`; `test_a_second_file_without_a_floor_is_named` (5), towncrier with a floor in `pypi-optional-docs.txt` alone gives `{"towncrier": ["pypi-optional-test.txt"]}`.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_dependency_floors.py`. Expected: FAIL, the helpers undefined.
- [ ] **Step 3: Write the helpers** to the Interfaces and Global Constraints, with `REMEDY` ending each source-tree failure. `_floor` reads `SpecifierSet(spec)` and turns `InvalidSpecifier` into `ValueError`.
- [ ] **Step 4: Write the section** of `checks.rst` and its row, in the form of "Dependency Ceilings": the rule of §4.4; why, {pull}`2219` raising `pip` floors and {pull}`2226` dropping them, so a `pip` floor drifts from the `pixi` floor CI tests; what enforces it; when it fails, the remedy; no exception; more, the Dependabot section and floors spec §4.4.
- [ ] **Step 5: Run** the file again. Expected: only `test_every_pip_requirement_declares_a_floor` fails, naming 58 lines in five files.
- [ ] **Step 6: Copy the floors** onto those lines, as Global Constraints give them, then `pixi lock` and `git diff pixi.lock`. Expected: changes inside the `- pypi: ./` record alone; if anything else moves, stop and report it.
- [ ] **Step 7: Run** `pixi run --frozen -e test pytest tests/test_dependency_floors.py tests/test_dependency_ceilings.py tests/test_repository_checks.py tests/test_python_support.py tests/test_floors.py`, then `pixi run --frozen -e floors pytest tests/test_dependency_floors.py`, which installs the editable `geovista` under its new floors in the `floors` environment. Expected: PASS.
- [ ] **Step 8: Break the source tree** (workflow rule 2.6), one at a time: `numpy`'s floor dropped, towncrier's floor in `pypi-optional-test.txt` lowered to `24.7.0`, `pyproj`'s `pip` floor set to `3.7.2`, and `pooch ~=1.8`. Watch the named source-tree test fail under each, then restore.
- [ ] **Step 9: Commit** as `deps: give every pip requirement its pixi floor, held by a check (floors spec row 2)`.

### Task 3: The Guide

**Files:**
- Modify: `docs/src/developer/packaging.rst` (Python Package Index)
- Modify: `docs/src/developer/codecraft.rst` (Dependabot)
- Modify: `AGENTS.md`

- [ ] **Step 1: Describe the floors** in Python Package Index, after the paragraph on maximum capping pins: every requirement carries a floor, `>=F,<C`, equal to its `pixi` floor, which the Dependency Floors check holds; a floor is raised on both sides in one commit, then `pixi lock`, and a floor lowered also needs `pixi update --environment floors <package>`. It cites floors spec §4.4.
- [ ] **Step 2: Describe the failure** in the Dependabot dropdown, after the ceilings: a `dependabot` pull request that moves a `pip` floor, as its `increase-if-necessary` strategy did in {pull}`2219`, fails the Dependency Floors check, and the floor is put back on that pull request.
- [ ] **Step 3: Update `AGENTS.md`**, within its lines: under Build and Test, a floor moves on both sides in one commit and is followed by `pixi lock` (§4.5); in Conventions, the Dependencies line says each `pip` requirement carries its `pixi` floor.
- [ ] **Step 4: Build** with `pixi run --frozen -e docs make`. Expected: no warning.
- [ ] **Step 5: Commit** as `docs: describe the pip floors and their check (floors spec row 2)`.

### Task 4: The Record

**Files:**
- Modify: `docs/src/developer/specs/2026-11-15-dependency-floors-design.md` (§9 row 2, §11)
- Create: `changelog/2985.dependency.rst`

- [ ] **Step 1: Mark §2 decision 5 verified**, `✅ verified (<date>, {pull}`2985`)`, with `tests/test_dependency_floors.py`.
- [ ] **Step 2: Record §2 decision 11 signed off**, `✍️ signed off (<date>, {user}`bjlittle`, {pull}`2985`)`, with "Checked in review that `tests floors` is a required status check of the branch protection of `main`, added once row 1 landed." First confirm with `gh api repos/bjlittle/geovista/branches/main/protection/required_status_checks --jq '.checks[].context'` that it lists `tests floors`, and quote the output in the pull request. The `signed-off` label is {user}`bjlittle`'s to add.
- [ ] **Step 3: Write the fragment**, humanized, and check it with `pixi run --frozen -e docs python .github/scripts/changelog.py 2985 "changelog/2985.dependency.rst"`.
- [ ] **Step 4: Run** `pixi run --frozen -e test pytest tests/test_spec_conventions.py tests/test_renumbering.py tests/test_workflow_rules.py tests/test_verification_report.py` and `pixi run --frozen -e test check-spec-status 2985`. Expected: PASS.
- [ ] **Step 5: Mark row 2 landed** in the last commit, `✅ landed (<date>, {pull}`2985`)`, once CI has passed on the pull request, and correct the date if the merge slips a day (workflow rule 2.4). Commit as `docs: land row 2 of floors spec §9`.
