---
orphan: true
---

# type coverage change 7 — the gallery, and the ratchet retired

```{readingtime}
```

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** type check the example gallery in full, retire the typing ratchet that held its
errors, and keep the guards on the CI arrangement that the ratchet's test also carried.

**Architecture:** row 7 of typing spec §4, the last. `geovista.examples.*` is the ratchet's
only entry. Its errors are fixed in the examples themselves, as published example code a
reader copies: no `type: ignore`, no typed `Callable` locals. The pantry samples keep their
`ArrayLike` fields, and the four examples that do arithmetic on one convert it with
`np.asanyarray` ({user}`bjlittle`, 2026-10-21). Then the ratchet block and
`tests/test_typing_ratchet.py` go, as typing spec §3.2 has always said they would, but the
file's guards on `ci-typing.yml`, the `mypy` hook and the global configuration move to
`tests/test_ci_typing.py`, beside a new guard that no override ignores errors.

**Tech Stack:** `mypy` 2.x in strict mode, `pytest`, `pyvista` 0.49.1, sphinx-gallery.

**Spec:** `docs/src/developer/specs/2026-10-06-type-coverage-design.md`, cited throughout
as `typing spec §…`. This plan implements row 7 of §4.

**Branch:** `debt/typing-gallery`. The plan is committed first and the pull request held in
draft until the implementation lands on it. `{PR}` below is that pull request's number.

## Global Constraints

- **Copyright header** and `from __future__ import annotations` on every Python file
  (root `AGENTS.md`). **Line length 88.**
- **The strictness settings stay as they are** (typing spec §7), and so does typing spec
  §3.4's gallery override, which disables `call-arg` and `no-untyped-call` for
  `geovista.examples.*` until the `pyvista` floor rises ({issue}`2568`).
- **No `type: ignore`, no `typing.cast`, no new `noqa`, and no typed `Callable` locals in
  the gallery.** A reader copies example code, so each fix is the code a reader would
  write: a conversion, a keyword argument, an annotated local, a check.
- **The gallery avoids `TYPE_CHECKING` blocks**, which is why `ruff` ignores `TC002` there;
  an annotation in an example uses built-in types rather than importing from
  `collections.abc`, which `TC003` would move into such a block.
- **Every commit passes the `mypy` hook.** While the ratchet stands the gallery's errors are
  invisible to it, so task 1 measures with a probe configuration that lifts the ratchet.
- **Run the full non-image suite before each commit, and the image tests too**, which run
  every gallery example: `CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e geovista pytest -n auto -m image tests`.
- **A probe of a scratch tree never runs `python -I`**, which ignores `PYTHONPATH`.
- **Changelog.** One fragment, `{PR}.contributor.rst`, signed ``:user:`claude` ``; the
  `agentic` label on the pull request.
- **Every deferred item gets an `agentic` issue**, linked from the Follow-ups below and
  from the pull request's description.
- **Prose for other readers is humanized:** the spec's new text, `AGENTS.md`, the code
  comments, commit messages, the fragment and the pull request body. This plan is not.

## What the dry run measured

Measured on 2026-10-21 against `main` at `fa1a9812`, with the ratchet block removed and
every fix below applied to a scratch tree, which `mypy` then passed, with the hooks, the
non-image suite and all 92 image tests green.

1. **The gallery reports 36 errors on 28 lines in 10 files.** Typing spec §3.2 counted 8
   untyped imports and 20 lines; the imports reproduce (`cmocean` five, `cartopy` two, `h3`
   one, on 7 lines), and the code is 21 lines.
2. **Three of the 21 are `pyvista`'s,** and vanish against a clone of `pyvista` `main`
   (`fbc11b53`): `add_logo_widget` in `from_tiff__dem.py` and `add_checkbox_button_widget` in
   `uber_h3.py`, where `_Wrapped` reads the first positional argument as `self` and reports
   `arg-type` rather than §3.4's suppressed `call-arg`; and `append_polydata` in `uber_h3.py`,
   unannotated in 0.49, returned where a `PolyData` is promised. Passing the first argument
   by keyword turns the first two into `call-arg`, which §3.4 already covers, and an
   annotated local takes the third.
3. **The pantry samples are `ArrayLike` because they are.** Of the 22 loaders in
   `geovista.pantry.data`, the six `lam_*` return netCDF `Variable`s for `lons` and `lats`,
   `dynamico` one for `data`, and `dynamico`, `icon_soil` and `ww3_global_smc` tuples for
   `connectivity`. Four examples do arithmetic on a field every loader happens to fill with
   an array: `wind_arrows_uvw.py` (`sample.w * 1500.0`, six errors), both ORCA cloud examples
   (`-sample.zlevel`) and `from_unstructured__fvcom.py` (`sample.node` into point data).
   Each converts with `np.asanyarray`, and imports `numpy` to do so.
4. **`uber_h3.py` holds the rest, and §3.4's seven.** `H3Asset` keeps colours, meshes and
   actors under `H3AssetLike = str | PolyData`, and `add_mesh` returns `Actor | None`
   (seven lines). `GeoSurface` annotates its tuples of floats and list of lists as
   `ArrayLike`, which cannot be indexed or iterated as the example does (five lines).
5. **`true_winds.py`** rebinds `xs` and `ys` from the 2D grid to its flattened form.
6. **A misattributed override.** `geovista.examples.grid.*` disables `union-attr`, "caused by
   geopy being untyped". It hides four errors in `reykjanes.py` and `reykjanes_contour.py`,
   which read `sample.poi.longitude` where `poi` is `Point | None`; `geopy` is `Any` under
   §8 item 9's override either way. Each example marks the release location only when the
   sample records it, and the override goes.
7. **`cmocean`, `cartopy` and `h3` ship no annotations and have no stub package** (latest
   4.0.3, 0.26.0 and 4.5.0, all locked). Upstream, `cartopy` issue 2304 and `h3-py` issue
   327 ask for them; `cmocean` has none. They join §8 item 9's override, which grows from
   three names to six.
8. **The ratchet's test file holds 18 tests, and 13 outlive it.** Five are the ratchet's
   own: `test_ratchet_only_shrinks`, `test_ratchet_entry_resolves`,
   `test_ratchet_is_not_empty`, and the two `_drift` tests. The others guard `ci-typing.yml`
   and the `mypy` hook (three), how a workflow command counts as run (eight), the global
   `[tool.mypy]` table, and the reading of an override's `module`. With a new guard that no
   override ignores errors, `tests/test_ci_typing.py` holds 14, and the suite goes from 2950
   to 2946 (with a docs build present).

## Review Focus

1. **Every gallery example still runs and draws the same scene.** → each task's image suite;
   `tests/plotting/test_examples.py` runs them all.
2. **The Reykjanes examples still mark the release location**, now behind
   `if sample.poi is not None:`. → the image tests of both.
3. **`uber_h3.py`'s checkboxes still toggle each layer**, with the callback passed by
   keyword. → its image test draws the scene; the reviewer should exercise a checkbox.
4. **Nothing that guarded `ci-typing.yml` is lost** with `tests/test_typing_ratchet.py`. →
   task 2 carries each guard across by name; the reviewer should diff the two files.
5. **A future `ignore_errors` cannot return unnoticed.** → task 2's
   `test_no_module_ignores_errors`, which fails while the ratchet stands.

---

### Task 1: type check the gallery

**Files:**
- Modify: `pyproject.toml` (§8 item 9's override; drop the `examples.grid.*` override)
- Modify: `src/geovista/examples/vector_data/wind_arrows_uvw.py`,
  `point_cloud/from_points__orca_cloud.py`, `point_cloud/from_points__orca_cloud_eqc.py`,
  `warp/from_unstructured__fvcom.py`, `vector_data/true_winds.py`,
  `scalar_data/from_tiff__dem.py`, `spatial_index/uber_h3.py`, `grid/reykjanes.py`,
  `grid/reykjanes_contour.py`

**Interfaces:**
- Consumes: nothing.
- Produces: a gallery that `mypy` passes with the ratchet lifted.

- [ ] **Step 1: Measure the gallery's errors**

Write a probe configuration that lifts the ratchet, in the plan's workspace `$W`:

```bash
sed '/^ignore_errors = true$/d' pyproject.toml > $W/lifted.toml
pixi run --frozen -e geovista mypy --config-file $W/lifted.toml
```

Expected: exits 1, `Found 36 errors in 10 files`.

- [ ] **Step 2: The untyped imports, and the grid override**

In §8 item 9's override, `module = ["cartopy.*", "cmocean.*", "fastparquet", "geopy.*",
"h3", "pooch"]`, and its comment says six distributions. Delete the `examples.grid.*`
override block.

- [ ] **Step 3: The pantry samples**

Import `numpy as np` where missing (in the third-party block; `wind_arrows_uvw.py` beside
`pyvista`), and convert: `np.asanyarray(sample.w) * 1500.0`,
`zlevel=-np.asanyarray(sample.zlevel)` in both ORCA examples, and
`mesh.point_data["node"] = np.asanyarray(sample.node)`.

- [ ] **Step 4: The Reykjanes release location**

In both examples, change the comment to "Mark the event release location, which the sample
records." and nest the `p.add_points(...)` call under `if sample.poi is not None:`.

- [ ] **Step 5: `true_winds.py`**

`xx, yy = np.meshgrid(x, y)`, and later `xs, ys = xx.flatten(), yy.flatten()`.

- [ ] **Step 6: `uber_h3.py` and `from_tiff__dem.py`**

- `type H3AssetLike = str | PolyData | Actor | None`.
- `GeoSurface`: `lons: tuple[float, ...]`, `lats: tuple[float, ...]`,
  `connectivity: list[list[int]]`; drop the now unused `ArrayLike` import.
- `mesh: PolyData = meshes[0].append_polydata(*meshes[1:])`, then `return mesh`.
- `add_checkbox_button_widget(callback=partial(...), ...)` and
  `p.add_logo_widget(logo=fetch_raster("japan_map.png"), position=(0.8, 0.8))`.

- [ ] **Step 7: Verify, and commit**

Run the step 1 probe again. Expected: `Success: no issues found in 86 source files`.

Run `pixi run --frozen -e geovista mypy` (the ratchet still stands). Expected: `Success`.

Run the full non-image suite (expected: 2950 passed, unchanged) and the image suite
(expected: 92 passed). Run pre-commit on the changed files. Expected: every hook passes.

Message, humanized: `fix: type check the gallery in full`.

---

### Task 2: retire the ratchet

**Files:**
- Create: `tests/test_ci_typing.py`
- Delete: `tests/test_typing_ratchet.py`
- Modify: `pyproject.toml` (the ratchet block)

**Interfaces:**
- Consumes: task 1's clean gallery.
- Produces: no `ignore_errors` anywhere in `[tool.mypy]`.

- [ ] **Step 1: Write the new test module, with its failing guard**

Create `tests/test_ci_typing.py`, docstring
`"""Tests that "mypy" checks the whole package, in CI as in the hook."""` with a paragraph
saying the modules once listed under `ignore_errors` were retired one change at a time
until none was left, and pointing at typing spec §3.2. Carry across from
`tests/test_typing_ratchet.py`, verbatim unless noted:

- the constants `ROOT`, `PYPROJECT`, `PRE_COMMIT`, `WORKFLOW` (not `SOURCE`, nor
  `RATCHET_BASELINE`);
- the helpers `_modules`, `_ignored` (its docstring no longer mentions the baseline),
  `_commands`, `_steps` and `_hook` (not `_drift` or `_resolve`);
- `test_mypy_hook_is_skipped_on_pre_commit_ci`, `test_ci_typing_names_a_declared_environment`,
  `test_ci_typing_runs_the_hook_command`, `test_only_an_executed_command_counts` (six cases),
  `test_the_last_command_of_an_enabled_step_counts` and
  `test_ci_typing_cannot_tolerate_its_own_failure`;
- `test_ratchet_reads_a_bare_module_string` as `test_a_bare_module_string_is_read_whole`;
- `test_the_ratchet_is_the_only_suppression` as `test_no_global_suppression`, its docstring
  pointing at `test_no_module_ignores_errors` rather than `test_ratchet_only_shrinks`.

And add:

```python
def test_no_module_ignores_errors():
    """No override may tell "mypy" to ignore a module's errors.

    The typing ratchet listed every module that reported errors under
    ``ignore_errors`` and only ever shrank, until change 7 of the roadmap
    retired its last entry. An override that brought ``ignore_errors`` back
    would hand back the coverage those changes won, in one line of the
    manifest.

    """
    assert not _ignored(), f"errors ignored in: {sorted(_ignored())}"
```

Run: `pixi run --frozen -e geovista pytest tests/test_ci_typing.py`

Expected: 13 pass, and `test_no_module_ignores_errors` FAILS naming
`geovista.examples.*`.

- [ ] **Step 2: Retire the ratchet**

Delete the ratchet's whole `[[tool.mypy.overrides]]` block, its comment included, and
`git rm tests/test_typing_ratchet.py`.

Run: `pixi run --frozen -e geovista pytest tests/test_ci_typing.py`. Expected: 14 pass.

Run: `pixi run --frozen -e geovista mypy`. Expected: `Success`.

- [ ] **Step 3: Verify, and commit**

Run the full non-image suite (expected: 2946 passed) and pre-commit on the changed files.
Expected: every hook passes; `taplo` may reformat `pyproject.toml`.

Message, humanized: `fix: retire the typing ratchet, which the gallery leaves empty`.

---

### Task 3: the spec, the guides and the changelog

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md`: §3.2, §3.4, §8
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (the paragraph
  naming `tests/test_typing_ratchet.py`)
- Modify: `AGENTS.md` (the `mypy` paragraph)
- Create: `changelog/{PR}.contributor.rst`

- [ ] **Step 1: Typing spec §3.2**

Replace "Since change 6c the list holds the gallery alone." with, humanized: "Change 7
retired the last entry, the gallery, and with it the block and its test. The test's guards
on `ci-typing.yml`, the `mypy` hook and the top of `[tool.mypy]` moved to
`tests/test_ci_typing.py`, beside one that refuses any override carrying
`ignore_errors`, so the ratchet's end state is held as firmly as its descent was."

- [ ] **Step 2: Typing spec §3.4**

After "and change 7 corrects them with the rest of the gallery.", add, humanized: "It did,
by letting `uber_h3.py`'s asset type hold an actor or `None`. Change 7 also found that
`pyvista`'s `_Wrapped` reports `arg-type`, not `call-arg`, when the call passes its first
argument positionally; the two gallery calls that did pass it by keyword instead, which the
override already covers. The `union-attr` override on `geovista.examples.grid.*`, which
blamed `geopy`, hid four reads of an optional point of interest, and goes."

- [ ] **Step 3: Typing spec §8 item 9**

It covers six distributions: add `cmocean` (4.0.3, no upstream issue), `cartopy` (0.26.0,
issue 2304) and `h3` (4.5.0, `h3-py` issue 327), imported only by the gallery, which change 7
took out of the ratchet. Keep `pooch`'s upstream sentence.

- [ ] **Step 4: The published-specs spec and `AGENTS.md`**

In the published-specs spec, "which puts it beside `tests/test_typing_ratchet.py`. That is
the right neighbourhood: both exist" becomes "which puts it beside
`tests/test_ci_typing.py`. That is the right neighbourhood: both exist".

In `AGENTS.md`, replace the paragraph that opens "`mypy` is green because modules are
ratcheted, not because they pass." with one of the same length, humanized, saying: `mypy`
checks the whole package; the hook is `local`, running the locked environment, and
`ci-typing.yml` carries it for `pre-commit.ci`; `tests/test_ci_typing.py` refuses any
`ignore_errors`; and keep the closing advice on `name?` annotations and `pyproj`'s thin types.
`AGENTS.md` stays under 200 lines.

- [ ] **Step 5: The changelog, and verify**

Create `changelog/{PR}.contributor.rst`, humanized:

```rst
The example gallery is type checked in full, and the typing ratchet that held its
errors is retired, so ``mypy`` now checks every module in ``src/geovista``.
``tests/test_ci_typing.py`` keeps the ratchet's guards on the CI workflow, and
refuses any override that would ignore a module's errors again.
(:user:`claude`)
```

Run the changelog script, the spec convention and status-reference tests,
`check-spec-status {PR}`, and the `-W` documentation build. Expected: all pass.

Message, humanized: `docs: record the gallery's typing and the ratchet's retirement`.

---

### Task 4: land row 7

After the final review, its fixes, CI and any Codex round, as the pull request's last
commit: row 7's Status becomes `` ✅ landed (YYYY-MM-DD, {pull}`{PR}`) `` with
`date -u +%F`, and `check-spec-status {PR}` runs again. If the merge slips a day, correct
the date first.

Message, humanized: `docs: land typing roadmap row 7`.

---

## Done when

- `[tool.mypy]` has no `ignore_errors`, `tests/test_typing_ratchet.py` is gone, and
  `pixi run --frozen -e geovista mypy` exits 0.
- The suite passes, image tests included, locally and in CI, and the documentation builds
  with `-W`.
- Typing spec §3.2, §3.4 and §8, the published-specs spec and `AGENTS.md` describe the
  checked package, and row 7 reads landed.
- Every deferred item has an `agentic` issue, linked below and from the pull request.

## During execution

Tasks 1 to 3 ran natively in one session, and each step's output matched its `Expected:`
line. Task 3 also put typing spec §6 into the past tense: it said `tests/test_typing_ratchet.py`
holds the ratchet, and that CI fails on errors outside it. Git records the old test file's
move to `tests/test_ci_typing.py` as a rename.

## After the final review

The whole-branch review on Opus 5.5 found nothing critical, one important finding and four
minors. It reproduced the gallery against `pyvista` `main` with no errors, exercised each of
`uber_h3.py`'s seven checkboxes off-screen, diffed the thirteen carried tests against their
originals, and showed `test_no_module_ignores_errors` failing on every way of writing an
`ignore_errors` override.

The important finding and three minors were statements this change made or left that were
not true, so all four were fixed: §3.4 still described the `examples.grid.*` override as
present; §8 item 9 and the #2629 comment said `cmocean` has no upstream issue, where
`matplotlib/cmocean` issue 120 asks for type checker support; §8 item 8 did not count the
annotated local for `append_polydata`, which makes ten; and §3.2 described the deleted test
in the present tense. The fourth minor was that `AGENTS.md` said nothing may ignore a module,
while an inline `# mypy: ignore-errors` comment still can, as can a per-module
`disable_error_code`. Both predate this change. `AGENTS.md` now says no override may, and
{issue}`2687` tracks guarding the other two.

## Follow-ups

- {issue}`2629`: comment that §8 item 9's override now covers `cmocean`, `cartopy` and `h3`
  as well, with their upstream status.
- {issue}`2568`: §3.4's gallery override stays until the `pyvista` floor carries the
  `_Wrapped` and `Camera.zoom` fixes; nothing changes there.
- {issue}`2687`: guard the two ways to silence `mypy` that `tests/test_ci_typing.py` doesn't
  see, an inline `# mypy:` comment and a per-module `disable_error_code`.
