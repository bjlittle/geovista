# The Width of a Geodesic Wedge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 6 of positions spec §9. `geodesic.wedge` refuses a wedge of no width, as the message of its check says, which settles positions spec §8 item 3 ({issue}`2894`).

**Architecture:** One comparison in `geodesic.wedge` changes, from `0 < delta >= 180`, which Python reads as `0 < delta and delta >= 180`, to `not 0 < delta < 180`, the open interval its message names. The message, the refusal of a missing longitude before it, and everything `wedge` builds inside the interval stay as they are. A new test file pins both ends of the interval, which no test covers today.

**Tech Stack:** `pyproj`, `pyvista` 0.49.2, `pint` through `geovista.units`, pytest.

**Spec:** `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (`positions spec §…`): §4.4, §7, §8 item 3 and §9 row 6.

## Global Constraints

- The width of a wedge is `abs(lon1 - lon2)`, in degrees, read after a `pint` quantity is converted. It must lie in the open interval (0, 180) (positions spec §8 item 3, row 6 of §9).
- The message stays `"A geodesic wedge must have an absolute longitudinal difference (degrees) in the open interval (0, 180), got '<delta>'."`, with `<delta>` as Python prints it: `'0'` for integers, `'0.0'` for floats and quantities.
- A missing `lon1` or `lon2` is refused before the width is read, as row 2 made it (§4.4).
- No new public name. `mypy` runs strict over the whole package, with no new override. Warnings are errors under pytest. Docstrings are NumPy style, and `.. versionchanged::` is not used.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: bug` and `agentic`, and closes {issue}`2894` (§8 item 3). No other issue follows a closing keyword in the body or any commit message.
- Row 6 verifies no decision of §2, so §11 is unchanged.
- Cite a specification section in plain text (`positions spec §8 item 3`), never with a `{ref}` role.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-08 that the specification fixes how row 6 behaves (workflow rule 2.7). The calls are mine.

1. **The check is `if not 0 < delta < 180:`.** It reads as the message does, so `wedge(10, 10)` is refused with "... got '0'." and `wedge(10.0, 10.0)` with "... got '0.0'.". The upper end is refused as today.
2. **Any width above 0 builds, however thin.** `wedge(10, 10 + 1e-9)` builds its box of 132,098 points, as today. Row 6 refuses a wedge of no width, and the specification names no lower bound beyond 0.
3. **A wedge across the antimeridian stays as it is.** The width is the plain difference of the longitudes given, so `wedge(170, -170)` is refused as 340 degrees wide and `wedge(170, 190)` builds, as today. §8 item 3 asks only for the zero end.
4. **The Raises section** reads "If `lon1` or `lon2` is masked or NaN, or infinite, or they are equal or 180 degrees or more apart."
5. **The tests go in a new `tests/geodesic/test_wedge.py`.** No test covers the width check at either end today, and the width has nothing to do with a missing position, so they stay out of `tests/geodesic/test_missing_positions.py`.
6. **One fragment, `2905.bugfix.rst`**, typed as {pull}`2889`, {pull}`2893` and {pull}`2899` typed theirs, each of which refused input that built before. The branch is `fix/missing-positions-wedge-width`, and the plan is the first commit of draft pull request {pull}`2905` (workflow rule 2.3), which marks row 6 in progress (workflow rule 2.4).

## Review Focus

1. **Equal longitudes given as `pint` quantities**, in degrees or radians. The width is read after conversion, so they are refused like plain numbers. `test_refuses_no_width[degrees]` and `[radians]` (Task 1).
2. **A thin wedge**, 0.001 degrees wide. It builds, as every width above 0 does. `test_builds_inside_the_interval[thin]` (Task 1).
3. **Longitudes in either order.** `wedge(30, -30)` builds, as `wedge(-30, 30)` does. `test_builds_inside_the_interval[reversed]` (Task 1).
4. **Half a turn or more**, 180 or 360 degrees. Refused as before. `test_refuses_half_a_turn_or_more` (Task 1).
5. **A missing longitude whose hidden value equals the other.** `wedge(<10 masked>, 10)` is refused as missing, not as a wedge of no width, since the missing check comes first. `test_refuses_a_missing_longitude_first` (Task 1).

---

Measured on 2026-11-08 at `199a885d` (`main` after {pull}`2903`), with Python 3.14.10, NumPy 2.5.4, `pyvista` 0.49.2 and `pint` 0.26.2, in the `geovista` environment:

- `wedge(10, 10)`, `wedge(10.0, 10.0)`, and equal quantities of 10 degrees or of 0 radians each build a box of 132,098 points.
- `wedge(10, 10 + 1e-9)`, `wedge(10, 10.001)`, `wedge(0, 179.999)` and `wedge(30, -30)` build 132,098 points.
- `wedge(0, 180)` and `wedge(0, 360)` raise the message above, with `'180'` and `'360'`.
- No example, docstring or test calls `wedge` with equal longitudes.

### Task 1: The Width Check

**Files:**
- Create: `tests/geodesic/test_wedge.py`
- Modify: `src/geovista/geodesic.py` (`wedge`: its check and its Raises section)

**Interfaces:**
- Consumes: `geovista.geodesic.wedge(lon1, lon2, *, ellps, c, triangulate) -> BBox`, as today.
- Produces: nothing new.

- [ ] **Step 1: Write the tests**

The message as a pattern, `WIDTH = r"in the open interval \(0, 180\), got '{}'\."`, formatted with the width. A module-level `UREG = pint.UnitRegistry()`, as `tests/units/test_at_the_boundary.py` has.

- `test_refuses_no_width(lon1, lon2, width)`, parametrized with ids `ints` `(10, 10, "0")`, `floats` `(10.0, 10.0, "0.0")`, `degrees` `(UREG.Quantity(10, "degree"), UREG.Quantity(10, "degree"), "0.0")` and `radians` `(UREG.Quantity(0.0, "radian"), UREG.Quantity(0.0, "radian"), "0.0")`: `pytest.raises(ValueError, match=WIDTH.format(re.escape(width)))`.
- `test_refuses_half_a_turn_or_more(lon1, lon2, width)`, with ids `half` `(0, 180, "180")`, `reversed` `(90, -90, "180")` and `whole` `(0, 360, "360")`, the same way.
- `test_builds_inside_the_interval(lon1, lon2)`, with ids `thin` `(10, 10.001)`, `wide` `(0, 179.999)` and `reversed` `(30, -30)`: `isinstance(result, BBox)` and `result.mesh.n_points > 0`.
- `test_refuses_a_missing_longitude_first()`: `wedge(np.ma.masked_array(10.0, mask=True), 10.0)` raises `ValueError` matching `"A geodesic wedge needs both longitudes, but 'lon1' is masked or NaN."`.

- [ ] **Step 2: Run them to see the zero end fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/geodesic/test_wedge.py`
Expected: the four `test_refuses_no_width` cases FAIL with "DID NOT RAISE"; the rest PASS.

- [ ] **Step 3: Change the check and the Raises section of `wedge` in `src/geovista/geodesic.py`**

`if 0 < delta >= 180:` becomes `if not 0 < delta < 180:`, the message unchanged. The Raises section takes the wording of call 4.

- [ ] **Step 4: Run them to see them pass**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/geodesic`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/geodesic/test_wedge.py src/geovista/geodesic.py
pixi run --frozen -e geovista git commit -m "fix: refuse a geodesic wedge of no width"
```

### Task 2: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (§8 item 3, §9 row 6)
- Modify: this plan's Follow-ups, before merge
- Create: `changelog/2905.bugfix.rst`

- [ ] **Step 1: Watch each end fail when it regresses**

Mutate one at a time, run `tests/geodesic/test_wedge.py`, see it fail, and revert:
- the check reads `0 < delta >= 180` again: `test_refuses_no_width`;
- it reads `not 0 < delta <= 180`: `test_refuses_half_a_turn_or_more`;
- it reads `not 0 <= delta < 180`: `test_refuses_no_width`.

- [ ] **Step 2: Run the whole suite and the docs build, on the committed tree**

Run: `CI=true GALLIUM_DRIVER=llvmpipe pixi run --frozen -e test-py313 tests-unit`, then the same with `-e test-py314`, then the strict `sphinx-build` of `AGENTS.md` with `--fail-on-warning --keep-going`.
Expected: PASS, with no new skips and no image baseline regenerated, and the build succeeds.

- [ ] **Step 3: Write the fragment, settle the item, and mark the row**

`changelog/2905.bugfix.rst`, humanized, citing `geovista.geodesic.wedge` and naming the row as `row 6 of positions spec §9`. It says that `wedge` built a box for two equal longitudes, though its message asked for a width in the open interval (0, 180), and that it now refuses them.

§8 item 3 becomes ``🏁 Resolved (<DATE>, {pull}`2905` · 🔎 2026-11-07, {pull}`2893` · 🎫 {issue}`2894`)``, its text kept and followed by a sentence saying how row 6 settled it: calls 1 to 3. Last, row 6 of §9 becomes ``✅ landed (<DATE>, {pull}`2905`)``. `<DATE>` is the day of this commit, corrected if the merge slips to another day (workflow rule 2.4).

List any issue this pull request raises under Follow-ups below, and in the pull request's description (workflow rule 4.5); each one deferred from this row is an open item of the spec, in this pull request (workflow rule 2.8).

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py 2905 "changelog/2905.bugfix.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py tests/test_renumbering.py tests/test_verification_report.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status 2905`, then the strict docs build again.
Expected: the fragment passes, the tests pass, every status reference holds, and the fragment's references resolve.

- [ ] **Step 4: Commit, push, and mark the pull request ready**

```bash
git add changelog/2905.bugfix.rst
pixi run --frozen -e geovista git commit -am "docs: mark positions spec row 6 landed, settle §8 item 3, and add the fragment"
git push
```

Confirm the push with `git ls-remote` (workflow rule 4.6), check `gh pr view 2905 --json closingIssuesReferences` lists 2894 alone, and mark the pull request ready.

## Follow-ups

None. The final review left two minor points. The antimeridian cases of call 3 are now tested in `tests/geodesic/test_wedge.py`, as {user}`bjlittle` asked, and the other point stands: see the pull request's description.
