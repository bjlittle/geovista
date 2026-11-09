# Missing Positions and the Speed of a Line Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 7 of positions spec §9. `npoints` and `npoints_by_idx` test a position given as two plain numbers for a missing one without building masked arrays, so `geodesic.line` builds as fast as it did before row 5 (§8 item 5, {issue}`2913`).

**Architecture:** A new `common._missing_pair` reads one position given as two values. When both are plain real numbers it reads them with `math`, refusing an infinite one as `_missing` does and giving NaN in both when either is NaN; anything else, a masked value or `None` among them, goes to `_missing_as_nan` as today. `npoints` reads each end with it, and `npoints_by_idx` the two positions it indexes. Nothing a caller sees changes but the time.

**Tech Stack:** Python's `math` and `numbers`, NumPy, pytest with `pytest-mock`.

**Spec:** `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (`positions spec §…`): §2 decisions 1, 2 and 8, §4.1, §4.7, §8 item 5, §9 row 7.

## Global Constraints

- A position is missing when either of its coordinates is masked or NaN, and a `None` is missing (positions spec §2 decision 1, §4.1). A missing end gives NaN at every point (§4.7).
- An infinite coordinate is refused with a `ValueError` naming it, as `"'start_lon' cannot be infinite, got inf."`, the message `_missing` gives a value of no dimension (§2 decision 2).
- What a caller gets is unchanged: every test of `npoints`, `npoints_by_idx` and `line` passes as it is.
- No new public name. `mypy` runs strict over the whole package, and warnings are errors under pytest. Docstrings are NumPy style, and `.. versionchanged::` is not used.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: performance` and `agentic`, and closes {issue}`2913` alone.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-09 that the specification fixes how row 7 behaves (workflow rule 2.7). The calls are mine.

1. **One helper for one position.** `common._missing_pair(x: object, y: object, *, x_name: str, y_name: str) -> tuple[float, float]` takes the fast path when both values are `numbers.Real`, which holds for `int`, `float` and NumPy's scalars, and not for `None`, a masked value or an array. It refuses an infinite value with `_missing`'s message of no dimension, and returns `(nan, nan)` when either is NaN. Anything else goes to `_missing_as_nan`, read back as floats, so a masked end still gives NaN with no NumPy warning.
2. **`npoints` and `npoints_by_idx` use it.** Each call of `_missing_as_nan` in `geodesic.py` becomes one of `_missing_pair`, with the same names. `npoints_by_idx` passes the values it indexes, which are NumPy scalars for a plain array.
3. **No timing test.** A test of wall time would fail on a slow runner. `test_line_reads_plain_numbers_without_masked_arrays` spies `common._missing_as_nan` and asserts `line` never calls it, and the landing measures `line` against `main` and against `daca7540`, before row 5, and records both in §8 item 5 and the pull request.
4. **One fragment, `2922.internal.rst`**, since the slowdown never shipped: row 5 is unreleased. The branch is `fix/missing-positions-line-speed`, and the plan is the first commit of draft pull request {pull}`2922` (workflow rule 2.3), which marks row 7 in progress (workflow rule 2.4) and closes {issue}`2913`, resolving §8 item 5 (workflow rule 4.7).

## Review Focus

1. **A NumPy scalar.** `np.float64(10.0)`, as `npoints_by_idx` indexes from an array, takes the fast path. `test_missing_pair_reads_numpy_scalars_without_masked_arrays` (Task 1).
2. **A masked end.** `np.ma.masked` goes to `_missing_as_nan`, and gives NaN with no warning. `test_missing_pair_reads_a_masked_value_as_before` (Task 1).
3. **Negative infinity.** `-inf` is refused as `"'start_lon' cannot be infinite, got -inf."`. A case of `test_missing_pair_refuses_infinite` (Task 1).
4. **One coordinate missing.** NaN in one value gives NaN in both. A case of `test_missing_pair_agrees_with_missing_as_nan` (Task 1).
5. **A line through `npoints_by_idx`.** `line` over plain arrays never calls `_missing_as_nan`. `test_line_reads_plain_numbers_without_masked_arrays` (Task 2).

---

Measured on 2026-11-09 at `72c1c026` (`main` after {pull}`2917`), best of three: `line(np.linspace(-170, 170, 2000), np.zeros(2000))` takes 0.38 s, against 0.16 s at `daca7540`, before row 5. Of its profiled time, 65% is in 7,996 calls of `_missing_as_nan`, four for each pair of vertices, nearly all of it building masked arrays around single numbers.

### Task 1: One Position, Read Fast

**Files:**
- Modify: `src/geovista/common.py` (a new `_missing_pair`, beside `_missing_as_nan`)
- Modify: `tests/common/test__missing_positions.py`

**Interfaces:**
- Consumes: `common._missing_as_nan(xs, ys, *, x_name, y_name)`, from row 5.
- Produces: `common._missing_pair(x: object, y: object, *, x_name: str, y_name: str) -> tuple[float, float]`, which Task 2 uses.

- [ ] **Step 1: Write the tests**

- `test_missing_pair_agrees_with_missing_as_nan(x, y)`, with ids `floats` (`10.0, 20.0`), `ints` (`10, 20`), `numpy` (`np.float64(10.0), np.float32(20.0)`), `x-nan`, `y-nan`, `x-none` and `y-masked` (`np.ma.masked`): the result equals `tuple(float(v) for v in _missing_as_nan(x, y, ...))`, NaN compared as NaN, and each item is a `float`.
- `test_missing_pair_refuses_infinite(name, value)`, over `start_lon` and `start_lat` and `np.inf` and `-np.inf`: `ValueError` matching `"'{name}' cannot be infinite, got {value}."`, as `-inf` for the negative.
- `test_missing_pair_reads_numpy_scalars_without_masked_arrays(mocker)`: with `mocker.spy(common, "_missing_as_nan")`, `_missing_pair(np.float64(10.0), np.float64(20.0), ...)` returns `(10.0, 20.0)` and the spy is never called.
- `test_missing_pair_reads_a_masked_value_as_before(mocker)`: with the spy and warnings as errors, `_missing_pair(np.ma.masked, 20.0, ...)` returns NaN in both, and the spy is called once.

- [ ] **Step 2: Run the tests to watch them fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/common/test__missing_positions.py -k missing_pair`
Expected: FAIL, as `_missing_pair` cannot be imported.

- [ ] **Step 3: Implement Call 1**

The docstring says it is the fast form of `_missing_as_nan` for one position, which `geodesic.line` reads once for each pair of its vertices (positions spec §8 item 5).

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/common/`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/geovista/common.py tests/common/test__missing_positions.py
pixi run --frozen -e geovista git commit -m "fix: read one position given as two numbers without masked arrays"
```

### Task 2: The Points of a Line

**Files:**
- Modify: `src/geovista/geodesic.py` (`npoints`, `npoints_by_idx`)
- Modify: `tests/geodesic/test_missing_positions.py`

**Interfaces:**
- Consumes: `common._missing_pair`, from Task 1.

- [ ] **Step 1: Write the test**

`test_line_reads_plain_numbers_without_masked_arrays(mocker)`: with `mocker.spy(common, "_missing_as_nan")`, `line(np.linspace(-170, 170, 20), np.zeros(20))` builds, and the spy is never called. Its docstring says it settles positions spec §8 item 5.

- [ ] **Step 2: Run it to watch it fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/geodesic/test_missing_positions.py -k without_masked_arrays`
Expected: FAIL, the spy called 76 times, four for each of the 19 pairs.

- [ ] **Step 3: Implement Call 2**

`geodesic.py` imports `_missing_pair` in place of `_missing_as_nan`, and drops the `map(float, ...)` the helper's floats make needless.

- [ ] **Step 4: Run the tests to watch them pass, and measure**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/geodesic/ tests/common/`, then time `line` over 2,000 vertices, best of three, here and on `main`.
Expected: PASS, and `line` within 10% of 0.16 s.

- [ ] **Step 5: Commit**

```bash
git add src/geovista/geodesic.py tests/geodesic/test_missing_positions.py
pixi run --frozen -e geovista git commit -m "fix: read the ends of npoints without masked arrays"
```

### Task 3: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (§8 item 5, §9 row 7)
- Modify: this plan's Follow-ups, before merge
- Create: `changelog/2922.internal.rst`

- [ ] **Step 1: Watch each clause fail when it regresses**

Mutate one at a time, run the named tests, see them fail, and revert:
- the fast path reads NaN as present: the `x-nan` and `y-nan` cases of `test_missing_pair_agrees_with_missing_as_nan`, and `test_npoints_gives_nan_for_a_missing_end`;
- it skips the refusal of an infinite value: `test_missing_pair_refuses_infinite` and `test_npoints_refuses_infinite`;
- `npoints` goes back to `_missing_as_nan`: `test_line_reads_plain_numbers_without_masked_arrays`.

- [ ] **Step 2: Settle the item, mark the row, and add the fragment**

§8 item 5 becomes ``🏁 Resolved (<DATE>, {pull}`2922` · 🔎 2026-11-09, {pull}`2912` · 🎫 {issue}`2913`)``, its `🎯` dropped, ending "Row 7 settled it." and, humanized, how: `npoints` and `npoints_by_idx` read two plain numbers without masked arrays, and the line of 2,000 vertices takes the time measured in Task 2. Row 7 of §9 becomes ``✅ landed (<DATE>, {pull}`2922`)``, `<DATE>` the day of this commit, corrected if the merge slips (workflow rule 2.4). `changelog/2922.internal.rst`, humanized, says that `geovista.geodesic.line` builds as fast again as before row 5, and names the row as `row 7 of positions spec §9` on one line.

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py 2922 "changelog/2922.internal.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py tests/test_renumbering.py tests/test_verification_report.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status 2922` and `pixi run --frozen -e test check-spec-renumbering`.
Expected: all pass.

- [ ] **Step 3: Commit, then run the whole suite and the docs build on that commit**

```bash
git add changelog/2922.internal.rst
pixi run --frozen -e geovista git commit -am "docs: mark positions spec row 7 landed, resolve §8 item 5, and add the fragment"
```

Run: the strict `sphinx-build` with `-E`, then `CI=true GALLIUM_DRIVER=llvmpipe pixi run --frozen -e test-py313 tests-unit` and the same with `-e test-py314`.
Expected: the build succeeds, and the suites PASS with no new skips.

- [ ] **Step 4: Push, and mark the pull request ready**

Push, confirm it with `git ls-remote` (workflow rule 4.6), check `gh pr view 2922 --json closingIssuesReferences` lists {issue}`2913` alone, and mark the pull request ready once the final review's fixes have landed.

## Follow-ups

None. The final review found nothing critical or important, and {user}`bjlittle` asked for its four minor points to be made in this pull request: `np.float32` and `np.int64` cases for the spy test of Task 1, why the spy test of Task 2 patches both modules, and two fixes to the wording of §8 item 5.
