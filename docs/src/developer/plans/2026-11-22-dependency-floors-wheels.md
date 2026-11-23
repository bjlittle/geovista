# The Release Floors Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 4 of floors spec §9: the `test-floors` job of `ci-wheels.yml`, which runs the `floors-pypi` action against the built wheel on each `v*` tag and by hand, gates `publish-artifacts-pypi`, raises each floor it disproves, and is described on its page. Settle #3000 (floors spec §8 item 2) on the way.

**Architecture:** The `floors-pypi` action sets `PYVISTA_OFF_SCREEN` and `GEOVISTA_POOCH_MUTE` on the step that runs the suite, so it no longer leans on its caller's workflow `env`. `ci-wheels.yml` gains a `workflow_dispatch` trigger and a `test-floors` job that downloads the built artifacts, finds the one wheel, and runs the action with that wheel as its `target`; `publish-artifacts-pypi` needs it. `tests/test_ci_floors.py` holds both to the specification, as it holds row 3's job.

**Tech Stack:** GitHub Actions (composite actions, `actions/download-artifact`), `uv`, bash, pytest, PyYAML, Sphinx.

**Spec:** `docs/src/developer/specs/2026-11-15-dependency-floors-design.md` (`floors spec §…`): §2 decisions 7 and 10, §4.2, §4.3 (the action and `ci-wheels.yml`), §4.5 (the row marked 4), §6, §8 item 2, §9 row 4.

## Global Constraints

- The action's `tests floors pypi` step carries `env` with `PYVISTA_OFF_SCREEN: "true"` and `GEOVISTA_POOCH_MUTE: "true"`, literal strings. No other step of the action changes, and `ci-floors.yml` keeps its workflow `env`.
- `ci-wheels.yml` gains `workflow_dispatch:` beside its `pull_request` and `push` triggers, which are unchanged.
- Its new job is `test-floors`, named `test wheel (floors)`, on `ubuntu-22.04` as the other jobs at the floors run, with `needs: [build-artifacts]` and no `permissions` block, as `test-artifacts` has none (the workflow grants `{}`).
- It runs `if: ${{ github.event_name == 'workflow_dispatch' || (github.event_name == 'push' && startsWith(github.event.ref, 'refs/tags/v')) }}`, so never on a pull request or a push to `main` (§4.3).
- Its steps: `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` with `fetch-depth: 0` and `persist-credentials: false`; `actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333` with `pattern: pypi-artifacts-*`, `path: ${{ github.workspace }}/dist`, `merge-multiple: true`, as `test-artifacts` has it; `environment configure`, computing `CACHE_PERIOD` as `ci-floors.yml` does; `find wheel` (`id: wheel`), which writes the path of the one `*.whl` in `dist/` as the output `path`, and otherwise exits non-zero by its own `exit 1`, since the workflow's `bash -l {0}` drops errexit; and `floors pypi`, `uses: $/.github/workflows/composite/floors-pypi` with `target: ${{ steps.wheel.outputs.path }}` and `cache_period: ${{ env.CACHE_PERIOD }}`.
- `publish-artifacts-pypi` has `needs: [test-artifacts, test-floors]`. `publish-artifacts-test-pypi` keeps `needs: [test-artifacts]`, since `test-floors` is skipped on the pushes to `main` it publishes. Both publish jobs keep an `if` that requires `github.event_name == 'push'`, so a run by hand publishes nothing.
- A failure is read from its run (§2 decision 6): the job opens no issue.
- Every action is pinned by its commit SHA, and an expression reaches a shell only through `env`, so `zizmor` passes. A floor is raised on both sides in one commit and followed by `pixi lock`, and the pull request names each floor it raises (§4.2).
- `pixi lock` is the only command run without `--frozen`. Warnings are errors under pytest. Every Python file carries the copyright header and `from __future__ import annotations`. `AGENTS.md` and `tests/AGENTS.md` stay under 200 lines.
- Commit through `pixi run --frozen -e geovista git commit ...`, after `pixi run --frozen -e devs pre-commit run --files <paths>`. The fragment is `changelog/3007.internal.rst`, crediting ``(:user:`claude`)``. The pull request carries `agentic`, `type: gha`, `type: testing` and `type: documentation`, and closes #3000.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-22 that the specification fixes how row 4 behaves (workflow rule 2.7), with two calls made then: the two variables of #3000 move into the action, on the steps that need them, rather than onto the new job; and, since `ci-wheels.yml` on `main` has no `workflow_dispatch` to run by hand, a throwaway commit runs `test-floors` on this pull request to watch it pass and fail, the pull request amends §6 to say so, and `ci-wheels.yml` is run by hand once it merges, to see `test-floors` pass and nothing publish. The rest are mine.

1. **The variables go on `tests floors pypi` alone.** It is the step that imports `geovista` and `pyvista` to test them. In the cache actions before it, `GEOVISTA_POOCH_MUTE` only quietens the log of a download, so a caller without it logs more and tests the same. A step writing `GITHUB_ENV` would leak both into the caller's later steps.
2. **The wheel's path comes from a step output**, checked to be the only `*.whl` in `dist/`, so a build that ever emits two wheels fails loudly rather than testing whichever `ls` lists first.
3. **The tests join `tests/test_ci_floors.py`**, whose docstring already names `ci-wheels.yml` as the action's second caller. Row 4 verifies §2 decision 7 with it, and §2 decision 10 with it and `tests/test_floors.py`, since `test-floors` is the last job of §4.3 to run the suite. §2 decision 6 stays pending until a failure has been read.
4. **The throwaway runs the job and expects its own test to fail, in one commit.** Row 3 found that a job running the whole suite fails the test that holds its trigger while the throwaway stands, so the commit widening `test-floors`' `if` also marks that test `xfail(strict=True)`. Both throwaway commits are reverted, not rewritten away, so nothing is force-pushed.
5. **The fragment is `internal`**, as rows 1 and 3 were: a user installs the same wheel, now tested at its floors first.
6. **The branch is `floors/row4-wheels`.** The plan is the first commit of draft pull request {pull}`3007` (workflow rule 2.3), which also marks row 4 `🚧 in progress ({pull}`3007`)` (workflow rule 2.4).

## Review Focus

1. **A wheel path with extras.** `uv pip install --resolution lowest-direct "dist/geovista-<version>-py3-none-any.whl[test,exam]"` is untried. If the first run fails at `uv install` on the form, rule for `geovista[test,exam] @ file://<absolute wheel path>` when the target is a wheel, add that case to `test_the_install_takes_the_extras_at_their_lowest`, and keep `.` as it is (Task 3, Step 2).
2. **`lowest-direct` reaching the wheel's `Requires-Dist`.** With `.`, `uv` treated `geovista`'s own requirements as direct. The first green run's freeze must show each at its floor again, as row 3's did (Task 3, Step 3).
3. **The suite testing the wheel, not the checkout.** The freeze must list `geovista` from the downloaded wheel, and the version `geovista --report` prints must be the wheel's. `testpaths = "tests"` and the `src` layout keep the checkout's copy off `sys.path` (Task 3, Step 3).
4. **The push to `main` that publishes to Test PyPI.** `test-floors` is skipped there, so a `publish-artifacts-test-pypi` that needed it would be skipped too, and silently. `test_the_test_pypi_upload_does_not_wait_for_the_floors` pins it (Task 2).
5. **The throwaway `if` left behind.** `test_the_gate_runs_on_a_tag_and_by_hand_alone` fails while `pull_request` is in the `if`, so the reverted state is checked by the suite, not by memory (Tasks 2 and 3).

---

### Task 1: The Action Sets Its Own Environment

**Files:**
- Modify: `.github/workflows/composite/floors-pypi/action.yml`
- Modify: `tests/test_ci_floors.py`

**Interfaces:**
- Consumes: `_steps()`, `_step(steps, name)` and `TESTS` of `tests/test_ci_floors.py`.

- [ ] **Step 1: Write the failing test** `test_the_action_sets_the_environment_the_suite_needs`: the `env` of `_step(_steps(), TESTS)` maps each of `PYVISTA_OFF_SCREEN` and `GEOVISTA_POOCH_MUTE` to `"true"` (compared as `str(value).lower()`), its docstring citing floors spec §8 item 2.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_ci_floors.py -k environment_the_suite`. Expected: FAIL, as the step has no `env`.
- [ ] **Step 3: Add the `env`** to `tests floors pypi`, with a comment saying that a caller need set neither.
- [ ] **Step 4: Run Step 2's command.** Expected: PASS. Break each clause once: drop either variable, then set one to `"false"`. Watch each fail, then restore.
- [ ] **Step 5: Commit** as `ci: the floors action sets the environment its suite needs (floors spec §8 item 2)`.

### Task 2: The test-floors Job

**Files:**
- Modify: `.github/workflows/ci-wheels.yml`
- Modify: `tests/test_ci_floors.py`

**Interfaces:**
- Consumes: `stub`, `run_step`, `_step`, `_triggers`' reading of `on` (PyYAML keys it by `True`), and `FLOORS` of `tests/test_ci_floors.py`; the action's inputs `target` and `cache_period`.
- Produces: constants `WHEELS` (the path of `ci-wheels.yml`), `GATE = "test-floors"` and `GATE_WHEN`, the `if` of Global Constraints; `_wheels() -> dict[Any, Any]`, the parsed workflow, cached as `_workflow` is.

- [ ] **Step 1: Write the failing tests:**
  - `test_the_wheels_can_be_run_by_hand`: the triggers include `workflow_dispatch`, `pull_request` and `push`, and `push` keeps its `tags: ["v*"]`.
  - `test_the_gate_runs_on_a_tag_and_by_hand_alone`: the `test-floors` job's `if`, whitespace collapsed, equals `GATE_WHEN`. A trigger left from watching the job on its pull request fails here.
  - `test_the_gate_tests_the_built_wheel`: the job needs `build-artifacts`; its steps run checkout, then the download of `pypi-artifacts-*` into `dist`, then a step using the `floors-pypi` action with `target` equal to `${{ steps.wheel.outputs.path }}` (the output of the step with `id: wheel`) and `cache_period` equal to `${{ env.CACHE_PERIOD }}`, in that order; it has no `permissions` key.
  - `test_the_gate_finds_the_one_wheel`, parametrized over `dist/` holding one wheel and an sdist (passes, `path=dist/<wheel>` in `GITHUB_OUTPUT`), none (fails) and two (fails). Run `find wheel` with `run_step` in `tmp_path`, its `run` prefixed with `set +e`, as `bash -l {0}` runs it, so a step leaning on errexit fails the test.
  - `test_a_release_waits_for_the_floors`: `publish-artifacts-pypi` needs exactly `test-artifacts` and `test-floors`.
  - `test_the_test_pypi_upload_does_not_wait_for_the_floors`: `publish-artifacts-test-pypi` needs exactly `test-artifacts`.
  - `test_a_run_by_hand_publishes_nothing`, parametrized over both publish jobs: the job's `if` contains `github.event_name == 'push'`, joined by `&&` to the rest, so `workflow_dispatch` cannot satisfy it.
- [ ] **Step 2: Run** `pixi run --frozen -e test pytest tests/test_ci_floors.py`. Expected: FAIL, as `ci-wheels.yml` has neither the trigger nor the job.
- [ ] **Step 3: Add the trigger and the job** to Global Constraints, and `test-floors` to `publish-artifacts-pypi`'s `needs`. Extend the `# Reference:` header with `astral-sh/setup-uv`, which the job now runs through the action.
- [ ] **Step 4: Run Step 2's command, and** `pixi run --frozen -e devs pre-commit run --files .github/workflows/ci-wheels.yml`. Expected: PASS, `zizmor` included. Break each clause once: add `|| github.event_name == 'pull_request'` to the `if`, set `target: "."`, drop `test-floors` from `publish-artifacts-pypi`'s `needs`, add it to `publish-artifacts-test-pypi`'s, let `publish-artifacts-test-pypi` run on `workflow_dispatch`, make `find wheel` take the first of two, and drop its `exit 1`. Watch each fail, then restore.
- [ ] **Step 5: Commit** as `ci: no release reaches PyPI until its wheel passes at its floors (floors spec row 4)`.

### Task 3: The First Runs

**Files:**
- Modify (throwaway, then reverted): `.github/workflows/ci-wheels.yml`, `tests/test_ci_floors.py`, one `requirements/pypi-*.txt`
- Modify (as found): `requirements/pypi-*.txt`, `pyproject.toml`, `pixi.lock`

- [ ] **Step 1: Run the gate on this pull request**, as one throwaway commit: append `|| github.event_name == 'pull_request'` inside `test-floors`' `if`, and mark `test_the_gate_runs_on_a_tag_and_by_hand_alone` `xfail(strict=True)`, with a reason naming the throwaway. Commit as `ci: throwaway, run test-floors on this pull request`, and push.
- [ ] **Step 2: Read the `test wheel (floors)` run.** If `uv install` rejects the wheel form, rule as Review Focus 1, fix it in a commit of its own with its test, and push. If a test fails at a floor, find by hand the lowest release under which the job passes (§4.2), raise it in `requirements/pypi-*.txt` and the `pixi` table in one commit naming each raised floor, run `pixi lock`, and push. Repeat until the job is green. Ledger each run's URL.
- [ ] **Step 3: Read the green run's freeze and log.** Each requirement sits at its floor, or the lowest release that resolves (Review Focus 2), and `geovista` comes from the wheel at the wheel's version (Review Focus 3). If `uv` resolved them at their highest, stop and ask. Account for each skip beyond the last weekly `floors pypi` run's.
- [ ] **Step 4: Break one floor**, as a throwaway commit: lower one `pip` floor alone, such as `pyvista`'s, as row 3 did. Watch `test wheel (floors)` go red at `tests floors pypi`, not at `uv install`, with at least one failure from the floor itself rather than the Dependency Floors check (workflow rule 2.6). Ledger the run.
- [ ] **Step 5: Revert both throwaway commits**, the broken floor first, and push. Confirm `pixi run --frozen -e test pytest tests/test_ci_floors.py` passes, and that no `pull_request` remains in `test-floors`' `if`.

### Task 4: The Guide and the Record

**Files:**
- Modify: `docs/src/developer/packaging.rst`
- Modify: `docs/src/developer/specs/2026-11-15-dependency-floors-design.md`
- Create: `changelog/3007.internal.rst`

- [ ] **Step 1: Extend the `ci-wheels.yml` row of `packaging.rst`'s Continuous Integration grid** (§4.5), keeping its width: no release reaches `PyPI` until its `test-floors` job has installed the wheel with its `test` and `exam` extras at their floors, with `uv` on the **oldest** supported Python, and passed the tests without the image tests. It runs on each `tag` and by hand, publishing nothing then, with `gh workflow run ci-wheels.yml`. A failure is read from its run, and the floor that fails is raised on both sides in one commit, then `pixi lock`.
- [ ] **Step 2: Amend the specification.** §4.3 says the action sets `PYVISTA_OFF_SCREEN` and `GEOVISTA_POOCH_MUTE` for the suite itself. §6 says row 4 lands once `test-floors` has passed and been seen to fail on its pull request through a throwaway commit that runs it there, reverted before the row lands, and that `ci-wheels.yml` is run by hand once it merges, `test-floors` passing and nothing published. §8 item 2 becomes `🏁 Resolved (<date>, {pull}`3007` · 🔎 2026-11-19, {pull}`2996` · 🎫 {issue}`3000`)`, saying the action now sets both (workflow rule 4.7). §11 marks §2 decision 7 `✅ verified (<date>, {pull}`3007`)`, citing `tests/test_ci_floors.py`, and §2 decision 10 likewise, citing `tests/test_ci_floors.py` and `tests/test_floors.py`, once Step 3 has broken each clause.
- [ ] **Step 3: Prove §2 decision 10 by breaking it** (workflow rule 2.6): drop `-m "not image"` from the action, then from the `floors` job of `ci-tests.yml`, then run the image marker in either. Watch `test_the_action_leaves_out_the_image_tests` and `test_the_floors_job_leaves_out_the_image_tests` fail each time, then restore.
- [ ] **Step 4: Write the fragment**, humanized: the release gate at the `pip` floors, the variables the action now sets, and each floor raised. Run `pixi run --frozen -e docs python .github/scripts/changelog.py 3007 "changelog/3007.internal.rst"`, then `pixi run --frozen -e docs make`. Expected: both pass, and the build is strict.
- [ ] **Step 5: Run the suite** `pixi run --frozen -e geovista pytest -m "not image" --numprocesses logical --dist worksteal`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status 3007`. Expected: both pass, judged by exit code.
- [ ] **Step 6: Commit** the guide, specification and fragment as `docs: the guide and the record for the release floors gate (floors spec row 4)`. Then mark the row `✅ landed (<date>, {pull}`3007`)` in §9 as the last commit, `docs: mark row 4 of the floors spec landed` (workflow rule 2.4).
