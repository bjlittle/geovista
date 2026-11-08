# Missing Positions in the Point Clouds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 3 of positions spec §9. `Transform.from_points` drops a missing point before it transforms the rest, with its entry in every array given for each point, and warns once, counting the points dropped; `GeoPlotter.add_points` cuts its `scalars` by the same points. The same pull request settles positions spec §8 item 2, the four minor points row 2's final review left ({issue}`2895`).

**Architecture:** `geovista.common` gains `_missing_and_named`, which pairs two coordinates, finds the missing positions and names the coordinates that make them so. Row 2's `_refuse_missing_positions` is rebuilt on it, which gives a clear message for coordinates whose shapes do not pair, and `from_points` uses it to drop and to word its warning. `add_points` finds the same points with row 1's `_missing_positions` and cuts its `scalars` before they reach `add_mesh`. `BBox` pairs its corners in order again, which row 2 broke.

**Tech Stack:** NumPy masked arrays, `pyproj`, `pyvista` 0.49.2, `pint` through `geovista.units`, pytest.

**Spec:** `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (`positions spec §…`): §2 decisions 1, 2 and 6, §4.1, §4.5, §4.8, §6, §8 item 2, §9 row 3 and §11.

## Global Constraints

- A position is missing when either of its coordinates is masked or NaN (positions spec §2 decision 1). A masked array whose mask is `nomask` has no missing position, and a `None`, which NumPy reads as NaN, is missing (§4.1, call 1).
- An infinite coordinate is refused with a `ValueError` naming the argument, `xs` or `ys` (§2 decision 2, §4.1).
- `from_points` drops each missing point before it transforms the rest, and warns once, counting the points it dropped. `data`, `vectors`, the heights of `height` or `depth`, and a `zlevel` array lose the same entries; a value given once for every point is kept as it is. A cloud whose every point is missing is built with no points, and the warning says so (§2 decision 6, §4.5).
- `add_points` cuts an array of `scalars` by the same points. Points given as a mesh or as Cartesian `points` are out of scope (§4.5, §4.8).
- The test reads coordinates after a `pint` quantity is read in its units and before any point is transformed (§4.1).
- No new public name. `mypy` runs strict over the whole package, with no new override. Warnings are errors under pytest. Docstrings are NumPy style, and `.. versionchanged::` is not used.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: bug` and `agentic`, and closes {issue}`2895` (§8 item 2). No other issue follows a closing keyword in the body or any commit message.
- A test named as evidence in §11 cites its decision in its docstring, as "Holds positions spec §2 decision 6." (ledger spec §3.4).
- Cite a specification section in plain text (`positions spec §4.5`), never with a `{ref}` role.

## Calls Made in This Plan

Call 1 was put to {user}`bjlittle`; the rest are mine.

1. **A `None` coordinate is missing.** NumPy reads `None` as NaN, so the test of §4.1 has read it as missing since row 1: `wedge(None, 30)` is refused as masked or NaN, and `from_points` will drop it. {user}`bjlittle` chose this on 2026-11-08, over refusing `None` with a `TypeError`. §4.1 gains a sentence, and no code changes.
2. **A masked angle read as NaN without a warning stands.** Row 2's `_angle` fills a masked quantity with NaN, so its callers lose NumPy's warning and keep the NaN. The values of `gridlines` and `wrap` place gridlines and labels, not positions (§4.8), and `npoints` carries a missing position through as NaN by §2 decision 8, which row 5 tests by its result.
3. **One helper pairs, finds and names.** `_missing_and_named(xs, ys, *, x_name, y_name)` in `geovista.common` returns `_missing_positions`'s array and the names of the coordinates masked or NaN anywhere. `_refuse_missing_positions` is rebuilt on it, so two coordinates whose shapes do not pair get row 1's `"Cannot pair 'lons' of shape (2, 2) with 'lats' of shape (4,)."` in place of NumPy's broadcast message.
4. **`BBox` pairs its corners in order.** Its count checks read sizes, and before row 2 `BBox` built from `xs` of shape `(2, 2)` and `ys` of shape `(4,)`; row 2's refusal broke that with NumPy's broadcast message. It now refuses on its corners raveled, as it counts them. `line` given those shapes never built, and now gets the message of call 3.
5. **The Raises sections.** `line` adds "If only one of `lons` and `lats` is a ``pint`` quantity." `BBox` adds "If only one of `xs` and `ys` is a ``pint`` quantity, or a quantity is not of the kind the axes of the `crs` measure, such as an angle for a projected `crs`."
6. **The warning.** `"geovista dropped 1 of 4 points from the point cloud, where 'xs' is masked or NaN."`, with `'xs' and 'ys' are` when both have any. When every point goes: `"geovista dropped every point of the point cloud (3), where 'xs' is masked or NaN, so it has no points."` It is a `UserWarning` raised in `from_points` with `stacklevel=2`, so through `add_points` it names a line in `geoplotter.py`.
7. **What is cut, and how.** When no point is missing, `from_points` runs as today. When any is, the points are raveled and cut, since a cloud has no topology: `data` whose size is the number of points given, raveled; each component of `vectors`, after today's check against the shape of `xs`; the heights, after `_for_points` with the number of points given; and a `zlevel` of more than one value, broadcast to the shape of `xs` and raveled. Anything else passes on as given, to the checks that refuse it today.
8. **`add_points` cuts `scalars` before `add_mesh`.** Only when `scalars` is an array and `xs` and `ys` are given: it reads them with `_coordinates`, finds the missing points with `_missing_positions`, and cuts an array of one value per point, raveled, or one row per point, such as colours with `rgb=True`. `from_points` alone warns.
9. **Evidence.** `tests/bridge/test_missing_positions.py` (new) for `from_points`, and `tests/geoplotter/test_add_points.py` for `add_points`. §2 decision 6 is verified on both; decisions 1 and 2 stay pending until rows 4 and 5 land.
10. **One fragment, `2899.bugfix.rst`.** The branch is `fix/missing-positions-point-clouds`, and the plan is the first commit of draft pull request {pull}`2899` (workflow rule 2.3), which marks row 3 in progress (workflow rule 2.4).

## Review Focus

1. **Points in a grid**, `xs` and `ys` of shape `(2, 2)` with `data` in that shape. Each entry follows its point when the grid is raveled. `test_cuts_arrays_in_the_shape_of_xs` (Task 2).
2. **A `zlevel` that broadcasts**, of shape `(2, 1)` against points of shape `(2, 3)`. The dropped points' levels go with them. `test_cuts_a_zlevel_that_broadcasts` (Task 2).
3. **Vectors in another CRS.** With `vectors_crs` a rotated pole, the vectors are oriented at the points kept. `test_cuts_vectors_in_another_crs` (Task 2).
4. **A missing point whose hidden value lies outside the domain of the CRS.** It is dropped before the transform, so it raises nothing and stretches nothing. `test_drops_before_transforming` (Task 2).
5. **A cloud of only missing points, with data and heights.** It builds empty, with every array cut to nothing. `test_a_cloud_of_only_missing_points` (Task 2).

---

Measured on 2026-11-08 at `3a774d73` (`main` after {pull}`2898`), with Python 3.14.10, NumPy 2.5.4, `pyvista` 0.49.2 and `pint` 0.26.2, in the `geovista` environment:

- `Transform.from_points` of `xs` masked at 1 builds 3 points, the second at the value under the mask; of `ys` NaN at 1, 3 points, the second NaN. `from_points([0, None, 20], [0, 5, 10])` raises a `TypeError` from `radians`. Of empty `xs` and `ys`, it builds 0 points.
- `GeoPlotter.add_points(xs=<masked at 1>, ys=..., scalars=[1, 2, 3])` draws 3 points.
- `BBox(np.array([[0, 10], [10, 0]]), [0, 0, 10, 10])` raises "operands could not be broadcast together with shapes (2,2) (4,)"; at `43f74594`, before row 2, it built. `line` of the same shapes raises the same, and at `43f74594` raised "The truth value of an array with more than one element is ambiguous".
- `nemo_orca2_gradient` (265,791 points) and `lfric_winds` (864), the samples the point cloud and vector examples give `from_points`, have no missing position.

### Task 1: The Pairing of Positions, and Row 2's Minor Points

**Files:**
- Create: `docs/src/developer/plans/2026-11-08-missing-positions-point-clouds.md` (this plan)
- Modify: `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (§9 row 3)
- Modify: `src/geovista/common.py` (`_missing_and_named`; `_refuse_missing_positions` uses it)
- Modify: `src/geovista/geodesic.py` (`BBox` refuses on its corners raveled; the Raises sections of `line` and `BBox`)
- Test: `tests/common/test__missing_positions.py`, `tests/geodesic/test_missing_positions.py`

**Interfaces:**
- Consumes: `_missing(values, *, name)`, `_missing_positions(xs, ys, *, x_name, y_name)`, `_named(names)` (rows 1 and 2).
- Produces: `_missing_and_named(xs: ArrayLike, ys: ArrayLike, *, x_name: str, y_name: str) -> tuple[NDArray[np.bool_], list[str]]`: the missing positions, in the shape `xs` and `ys` broadcast to, and the names, in the order `x_name`, `y_name`, of those masked or NaN anywhere. It refuses an infinite coordinate as `_missing` does, and coordinates that do not broadcast with `"Cannot pair {x_name!r} of shape {...} with {y_name!r} of shape {...}."`.

- [x] **Step 1: Branch, and mark the row in progress**

Done before execution: `fix/missing-positions-point-clouds` from `main` at `3a774d73`, with this plan and §9 row 3 marked ``🚧 in progress ({pull}`2899`)`` as its first commit, opened as draft {pull}`2899`.

- [ ] **Step 2: Write the failing tests**

In `tests/common/test__missing_positions.py`:

- `test_none_is_missing`: `missing([1.0, None, 3.0], [4.0, 5.0, 6.0])` equals `SECOND`. Holds call 1.
- `test_missing_and_named[case]`: for `xs` masked at 1, `ys` NaN at 1, and both, the array equals `SECOND` and the names are `["xs"]`, `["ys"]` and `["xs", "ys"]`; for present positions, all `False` and `[]`.
- `test_refuse_missing_positions_names_shapes_that_do_not_pair`: `refuse(np.zeros((2, 2)), np.zeros(4))` matches `r"Cannot pair 'lons' of shape \(2, 2\) with 'lats' of shape \(4,\)\."`.

In `tests/geodesic/test_missing_positions.py`:

- `test_bbox_pairs_a_grid_of_corners`: `BBox(np.array([[0.0, 10.0], [10.0, 0.0]]), [0.0, 0.0, 10.0, 10.0])` has the points of `BBox([0.0, 10.0, 10.0, 0.0], [0.0, 0.0, 10.0, 10.0])`.
- `test_line_names_shapes_that_do_not_pair`: `line(np.array([[0.0, 10.0], [20.0, 30.0]]), [0.0, 5.0, 10.0, 15.0])` matches `r"Cannot pair 'lons' of shape \(2, 2\) with 'lats' of shape \(4,\)\."`.

- [ ] **Step 3: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest -q tests/common/test__missing_positions.py tests/geodesic/test_missing_positions.py`
Expected: FAIL, with `ImportError` for `_missing_and_named`, and the two shape tests on NumPy's broadcast message. `test_none_is_missing` passes before any change, as call 1 says; break it by reading `values` without `dtype=float` in `_missing`, watch it fail, and revert.

- [ ] **Step 4: Implement `_missing_and_named` in `src/geovista/common.py`, and use it**

It calls `_missing` on each coordinate, pairs them with row 1's message, and names with the flags of each. `_missing_positions` keeps its signature and calls it. `_refuse_missing_positions` counts and names from it, its messages unchanged, and its Raises gains "or `xs` and `ys` do not pair". In `BBox.__init__`, the refusal takes `xs.ravel()` and `ys.ravel()`. Add the Raises lines of call 5 to `line` and `BBox`. The docstring of `_missing_and_named` cites positions spec §4.1 and §4.5, with `.. versionadded:: 0.6.0`.

- [ ] **Step 5: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q tests/common tests/geodesic tests/search/test_missing_positions.py tests/geoplotter/test_view_poi.py`
Expected: PASS.

- [ ] **Step 6: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/common.py src/geovista/geodesic.py tests/common/test__missing_positions.py tests/geodesic/test_missing_positions.py
pixi run --frozen -e geovista git commit -am "fix: name coordinates that do not pair, and pair the corners of a BBox in order"
```

### Task 2: `from_points` Drops a Missing Point

**Files:**
- Modify: `src/geovista/bridge.py` (`Transform.from_points` and its docstring)
- Test: `tests/bridge/test_missing_positions.py` (new)

**Interfaces:**
- Consumes: `_missing_and_named` (Task 1); `_named` (row 2).
- Produces: `from_points` as §4.5 describes, warning as call 6 words it.

- [ ] **Step 1: Write the failing tests**

Create `tests/bridge/test_missing_positions.py` with `LONS = [0.0, 10.0, 20.0, 30.0]`, `LATS = [0.0, 5.0, 10.0, 15.0]`, and `KEPT = [0, 2, 3]`. Each case compares with `reference`, the cloud `from_points` builds from the entries at `KEPT` alone, by `np.testing.assert_allclose` of its points and of each array, and catches the warning with `pytest.warns(UserWarning, match=...)`. Every test of the drop says "Holds positions spec §2 decision 6."

- `test_drops_a_missing_point[case]`: `xs` masked, `ys` masked, `xs` NaN, `ys` NaN, `xs` `None` and both, at 1, match `r"geovista dropped 1 of 4 points from the point cloud, where 'xs' is masked or NaN\."`, with `'ys' is` or `'xs' and 'ys' are` as named; a quantity of a masked array is dropped the same.
- `test_warns_once_counting`: `xs` masked at 0 and `ys` NaN at 3 give exactly one warning, matching `r"dropped 2 of 4 points from the point cloud, where 'xs' and 'ys' are masked or NaN\."`.
- `test_cuts_data`, `test_cuts_vectors`, `test_cuts_heights` (both `height` and `depth`, of one value per point), `test_cuts_a_zlevel_array`: each array loses entry 1, and equals the reference's.
- `test_keeps_a_value_given_once`: `height=100.0`, and separately `zlevel=2`, apply to the three points kept.
- `test_cuts_arrays_in_the_shape_of_xs`: `xs`, `ys` and `data` of shape `(2, 2)`, `xs` masked at `(0, 1)`, equal the reference of the other three, raveled.
- `test_cuts_a_zlevel_that_broadcasts`: points of shape `(2, 3)`, `zlevel` `[[1], [2]]`, `ys` NaN at `(1, 0)`; the reference has the five others, each with its row's level.
- `test_cuts_vectors_in_another_crs`: `vectors_crs=ccrs.RotatedGeodetic(130.0, 65.0).to_wkt()`, as `tests/bridge/test_from_points.py` uses.
- `test_drops_before_transforming`: in `crs="+proj=eqc"`, `xs` `[0.0, 1e40, 2e5, 3e5]` masked at 1; the points equal the reference's and are finite.
- `test_a_cloud_of_only_missing_points`: three points, `xs` all masked, with `data` and `height` of three values; `n_points == 0`, matching `r"geovista dropped every point of the point cloud \(3\), where 'xs' is masked or NaN, so it has no points\."`.
- `test_refuses_infinite`: `xs` `inf` at 1 matches `r"'xs' cannot be infinite, got inf at index 1\."`.
- `test_keeps_present_points`: plain lists, and `xs` as `np.ma.masked_array(LONS)`, whose mask is `nomask`, build all four points without a warning.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest -q tests/bridge/test_missing_positions.py`
Expected: FAIL, with `Failed: DID NOT WARN`, or the point counts differing, in every test of the drop; `test_refuses_infinite` with `DID NOT RAISE`; `test_keeps_present_points` passes.

- [ ] **Step 3: Implement the drop in `Transform.from_points`**

As call 7 says: after `_coordinates` and before `_heights` reads its count, find the missing points with `_missing_and_named`, warn, and keep `kept` (flat, `True` for each point kept) and the shape of `xs` as given. The present path is unchanged. Take the values of `xs` and `ys` as floats, with `np.ma.getdata` and `dtype=float`, before raveling and cutting, so a list holding `None` reads as one of floats. The docstrings of `xs` and `ys` gain "A point whose `xs` or `ys` is masked or NaN is missing, and is dropped with a warning, with its entries in `data`, `vectors`, the heights and a `zlevel` array (positions spec §4.5)."

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q tests/bridge tests/geoplotter/test_add_points.py`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/bridge.py tests/bridge/test_missing_positions.py
git add tests/bridge/test_missing_positions.py
pixi run --frozen -e geovista git commit -am "fix: drop a missing point from a point cloud, with its data"
```

### Task 3: `add_points` Cuts Its Scalars

**Files:**
- Modify: `src/geovista/geoplotter.py` (`add_points` and its docstring; a private `_cut_scalars`)
- Test: `tests/geoplotter/test_add_points.py`

**Interfaces:**
- Consumes: `_missing_positions` (row 1), `_coordinates` (`geovista.transform`), `from_points` (Task 2).
- Produces: `_cut_scalars(scalars: ArrayLike, kept: NDArray[np.bool_]) -> ArrayLike`: one value per point, raveled, or one row per point, cut to the rows `kept`; anything else as given.

- [ ] **Step 1: Write the failing tests**

With `xs` masked at 1 of `LONS` and `ys` `LATS`, each drawn by `GeoPlotter().add_points(...)` and read from `.mapper.dataset`, under `pytest.warns(UserWarning, match=r"dropped 1 of 4 points")`; each says "Holds positions spec §2 decision 6.":

- `test_drops_a_missing_point_and_its_scalar`: `scalars=[1.0, 2.0, 3.0, 4.0]` draws 3 points, whose active scalars are `[1.0, 3.0, 4.0]`.
- `test_cuts_scalars_in_the_shape_of_xs`: `xs`, `ys` and `scalars` of shape `(2, 2)`, `xs` masked at `(0, 1)`.
- `test_cuts_colours`: `scalars` of shape `(4, 3)` with `rgb=True`; rows 0, 2 and 3 are drawn.
- `test_draws_present_points_as_before`: no point missing, `scalars` drawn whole, and no warning.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest -q tests/geoplotter/test_add_points.py`
Expected: FAIL, the first three in `add_mesh` on 4 scalars for 3 points; `test_draws_present_points_as_before` passes.

- [ ] **Step 3: Implement `_cut_scalars`, and call it in `add_points`**

As call 8 says, before `Transform.from_points` and only when `scalars` is an array. The docstring of `scalars` gains "An array given with `xs` and `ys` loses the entry of each missing point, as `Transform.from_points` drops it."

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q tests/geoplotter tests/bridge`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/geoplotter.py tests/geoplotter/test_add_points.py
pixi run --frozen -e geovista git commit -am "fix: cut the scalars of a missing point in add_points"
```

### Task 4: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (§4.1, §8 item 2, §9 row 3, §11)
- Modify: this plan's Follow-ups, before merge
- Create: `changelog/2899.bugfix.rst`

- [ ] **Step 1: Watch each clause fail when it regresses**

Mutate one at a time, run the named test, see it fail, and revert:
- `from_points` drops nothing: `test_drops_a_missing_point`;
- it cuts `data`, `vectors`, the heights or a `zlevel` array no more: the `test_cuts_*` of each;
- it warns twice, or not at all, or miscounts: `test_warns_once_counting`;
- it transforms before it drops: `test_drops_before_transforming`;
- `add_points` passes `scalars` uncut: `test_drops_a_missing_point_and_its_scalar`;
- `BBox` refuses on its corners unraveled: `test_bbox_pairs_a_grid_of_corners`.

- [ ] **Step 2: Run the whole suite and the docs build, on the committed tree**

Run: `CI=true GALLIUM_DRIVER=llvmpipe pixi run --frozen -e test-py313 tests-unit`, then the same with `-e test-py314`, then the strict `sphinx-build` of `AGENTS.md` with `--fail-on-warning --keep-going`.
Expected: PASS, with no new skips and no image baseline regenerated, and the build succeeds.

- [ ] **Step 3: Write the fragment, settle the item, and mark the decision and the row**

`changelog/2899.bugfix.rst`, humanized, citing `geovista.bridge.Transform.from_points` and `geovista.geoplotter.GeoPlotter.add_points` by their documented paths, and naming the row as `row 3 of positions spec §9`. It says that both drew a point at the value under a mask, or a NaN point, for a missing position; that they now drop it with its data and warn, counting the points; and that `BBox` pairs a grid of corners in order again.

§4.1 gains, after its first paragraph's last sentence, "A `None`, which NumPy reads as NaN, is missing too." §8 item 2 becomes ``🏁 Resolved (<DATE>, {pull}`2899` · 🔎 2026-11-07, {pull}`2893` · 🎫 {issue}`2895`)``, its text kept and followed by sentences saying how each point was settled: calls 1 to 5. In §11, §2 decision 6 becomes ``✅ verified (<DATE>, {pull}`2899`)`` with evidence `tests/bridge/test_missing_positions.py`, `tests/geoplotter/test_add_points.py`. Last, row 3 of §9 becomes ``✅ landed (<DATE>, {pull}`2899`)``. `<DATE>` is the day of this commit, corrected if the merge slips to another day (workflow rule 2.4).

List any issue this pull request raises under Follow-ups below, and in the pull request's description (workflow rule 4.5); each one deferred from this row is an open item of the spec, in this pull request (workflow rule 2.8).

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py 2899 "changelog/2899.bugfix.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py tests/test_renumbering.py tests/test_verification_report.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status 2899`, then the strict docs build again.
Expected: the fragment passes, the tests pass, every status reference holds, and the fragment's references resolve.

- [ ] **Step 4: Commit, push, and mark the pull request ready**

```bash
git add changelog/2899.bugfix.rst
pixi run --frozen -e geovista git commit -am "docs: mark positions spec row 3 landed, settle §8 item 2, and add the fragment"
git push
```

Confirm the push with `git ls-remote` (workflow rule 4.6), check `gh pr view 2899 --json closingIssuesReferences` lists 2895 alone, and mark the pull request ready.

## Follow-ups

None yet. Each issue this pull request raises is listed here before it merges.
