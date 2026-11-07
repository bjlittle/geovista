# Missing Positions in the Geodesic Shapes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 2 of positions spec §9. `geodesic.line`, `BBox` and `wedge` refuse a missing position with a `ValueError` naming the argument and counting the missing positions, and refuse an infinite coordinate. The same pull request settles positions spec §8 item 1, the four gaps row 1 left ({issue}`2890`).

**Architecture:** `geovista.common` gains `_refuse_missing_positions`, the refusal of a shape built from many positions, on the `_missing` that row 1 added, and two small helpers it shares: `_named`, the phrase naming the missing coordinates, and `_first_true`, the index of the first infinite value. `line` and `BBox` call the refusal after their existing count checks and before any geodesic, wrap or transform. `wedge` refuses its two longitudes itself with `_missing` and `_named`. Row 1's remaining gaps are closed by three tests and the per-dimension index.

**Tech Stack:** NumPy masked arrays, `pyproj` geodesics, `pyvista` 0.49.2, `pint` through `geovista.units`, pytest.

**Spec:** `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (`positions spec §…`): §2 decisions 1, 2 and 5, §4.1, §4.4, §6, §8 item 1, §9 row 2 and §11.

## Global Constraints

- A position is missing when either of its coordinates is masked or NaN (positions spec §2 decision 1). A masked array whose mask is `nomask` has no missing position (§4.1).
- An infinite coordinate is refused with a `ValueError` naming the argument as the function calls it: `lons` or `lats` for `line`, `xs` or `ys` for `BBox`, `lon1` or `lon2` for `wedge` (§2 decision 2, §4.1).
- `line` and `BBox` raise a `ValueError` when any position given is missing, before any geodesic is computed, naming the argument and counting the missing positions. `wedge` raises the same way for a missing `lon1` or `lon2` (§2 decision 5, §4.4).
- `geodesic.panel`, `npoints` and `npoints_by_idx` are out of scope (§4.4); the last two are row 5.
- The test reads coordinates after a `pint` quantity is read in its units and before any position is built or transformed (§4.1).
- No new public name. `mypy` runs strict over the whole package, with no new override. Warnings are errors under pytest. Docstrings are NumPy style, and `.. versionchanged::` is not used.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: bug` and `agentic`, and closes {issue}`2849` (rows 1 and 2 have then landed, §9) and {issue}`2890` (§8 item 1). No other issue follows a closing keyword in the body or any commit message.
- A test named as evidence in §11 cites its decision in its docstring, as "Holds positions spec §2 decision 5." (ledger spec §3.4).
- Cite a specification section in plain text (`positions spec §4.4`), never with a `{ref}` role.

## Calls Made in This Plan

None was discussed.

1. **One refusal serves `line` and `BBox`.** `_refuse_missing_positions(xs, ys, *, x_name, y_name, shape)` in `geovista.common`, built on `_missing`, counts the positions either coordinate makes missing and names each coordinate that has any. `wedge` takes two longitudes as separate arguments, so it names them itself with `_missing` and `_named`. `_refuse_missing_poi` is rewritten on `_named`, its messages unchanged.
2. **The messages.** `"A geodesic line needs every position given, but 1 of 3 is missing, as 'lons' is masked or NaN."`, with `2 of 4 are missing` and `'lons' and 'lats' are` in the plural, and `A bounding-box` for `BBox`. `wedge` gives `"A geodesic wedge needs both longitudes, but 'lon1' is masked or NaN."`, or `'lon1' and 'lon2' are`.
3. **Where the refusal sits.** In `line`, after the auto-repeat and the two count checks, so a mismatch keeps today's message and a single missing coordinate counts every position it is repeated into, and before `wrap`, the loop check and the first `npoints_by_idx`. In `BBox`, after its three count checks and before the closing check of five values and `transform_points`. In `wedge`, after `_angle` and before the width check.
4. **`_angle` reads a masked quantity as NaN.** It ends in `float()`, and `float()` of a masked scalar warns "converting a masked element to nan". It fills the mask with NaN first, so `wedge` given a masked quantity reaches its refusal. This reaches every caller of `_angle`, which gets the NaN it got before, without the warning.
5. **An infinite value in an array of more than one dimension is placed by an index per dimension**, `at index (1, 1)`, in `_missing` and in the refusal of an infinite height in `geovista.globe` alike, as {issue}`2890` asks of both. A one-dimensional array keeps `at index 1`, and a scalar names no index. Both use `_first_true`.
6. **§8 item 1 is settled here**, as row 2 owes it: the per-dimension index (call 5), and tests of `KDTree.query` broadcasting its missing points against a `zlevel`, of `view_poi` given one coordinate alone as a missing quantity, and of a NaN `zlevel` that is not a missing position. The tests of row 1's code pass before they are written, so each is watched to fail by removing what it holds.
7. **A list holding `np.ma.masked` warns in NumPy**, "converting a masked element to nan", when `line` or `BBox` reads it; that warning is NumPy's, as row 1 ruled, and no test here gives one.
8. **One fragment, `<PR>.bugfix.rst`.** The branch is `fix/missing-positions-geodesic`.

## Review Focus

1. **`line` given one missing coordinate and many of the other.** The auto-repeat makes every position missing, and the refusal counts them all, naming only the coordinate given once. `test_line_refuses_a_repeated_missing_coordinate` (Task 2).
2. **A closed `BBox` of five values whose last corner is missing.** Today the closing check raises a `TypeError`; the refusal comes first and counts 1 of 5. `test_bbox_refuses_a_missing_closing_corner` (Task 2).
3. **A `BBox` in a projected CRS.** The refusal comes before `transform_points`, which would carry a NaN through silently. `test_bbox_refuses_on_a_map` (Task 2).
4. **Counts that differ, with a missing value among them.** The existing count message, not the refusal. `test_line_counts_before_refusing` (Task 2).
5. **A quantity of a masked array**, refused as a plain masked array is, by all three. `test_line_refuses_a_masked_quantity`, `test_bbox_refuses_a_masked_quantity` (Task 2) and `test_wedge_refuses_a_masked_quantity` (Task 3).

---

Measured on 2026-11-07 at `43f74594` (`main` after {pull}`2889`), with Python 3.14.10, NumPy 2.5.4, `pyvista` 0.49.2 and `pint` 0.26.2, in the `geovista` environment:

- `line([0, masked 10, 20], [0, 5, 10])` builds 129 points, 128 of them NaN, warning "converting a masked element to nan". A NaN latitude builds the same without a warning; an infinite longitude the same, warning "invalid value encountered in remainder". `line(masked_array([10.0], mask=True), [0, 5, 10])` raises `TypeError` from `bitwise_and` in the loop check.
- `BBox` given a masked, NaN or infinite corner builds, saying nothing. Five values whose last is masked raise the same `TypeError`, in the closing check.
- `wedge(np.ma.masked, 30)` and `wedge` of a masked quantity build a `BBox`, warning "converting a masked element to nan"; `wedge(0, np.nan)` builds without a warning; `wedge(np.inf, 30)` raises the width check's `ValueError`, naming no argument.
- `np.repeat` of the one element of `masked_array([10.0], mask=True)` gives three masked values.
- `KDTree(lam_uk()).query([-2, 0, 1], [52, 53, 54], zlevel=np.nan)` answers distances `1.3407807929942596e154` and indices `4294967295`, without a warning.

### Task 1: The Refusal of a Shape, and the Index of an Infinite Value

**Files:**
- Create: `docs/src/developer/plans/2026-11-07-missing-positions-geodesic.md` (this plan)
- Modify: `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (§9 row 2)
- Modify: `src/geovista/common.py` (`_named`, `_first_true`, `_refuse_missing_positions`; `_missing` and `_refuse_missing_poi` use them)
- Modify: `src/geovista/globe.py` (the refusal of an infinite height uses `_first_true`)
- Test: `tests/common/test__missing_positions.py`, `tests/globe/test_heights.py`

**Interfaces:**
- Consumes: `_missing(values, *, name) -> NDArray[np.bool_]` (row 1).
- Produces:
  - `_named(names: Sequence[str]) -> str`: `"'x' is"` for one name, `"'x' and 'y' are"` for two.
  - `_first_true(flags: NDArray[np.bool_]) -> tuple[tuple[int, ...], str]`: the index of the first `True` of an array of at least one dimension, and its text, `"1"` for one dimension and `"(1, 1)"` for more.
  - `_refuse_missing_positions(xs: ArrayLike, ys: ArrayLike, *, x_name: str, y_name: str, shape: str) -> None`: raises the `ValueError` of call 2 when any position is missing, and refuses an infinite coordinate through `_missing`. `xs` and `ys` are of one size when it is called.

- [ ] **Step 1: Branch, and mark the row in progress**

Confirm {pull}`2892` has merged, so that §8 item 1 is on `main`; if not, stop and ask. Create `fix/missing-positions-geodesic` from `main`. `<PR>` is the next free number, from `gh api 'repos/bjlittle/geovista/issues?state=all&per_page=1&sort=created&direction=desc' --jq '.[0].number'` plus 1. Mark §9 row 2 ``🚧 in progress ({pull}`<PR>`)``. This commit is the first of the branch.

```bash
git add docs/src/developer/plans/2026-11-07-missing-positions-geodesic.md
pixi run --frozen -e geovista git commit -am "docs: plan positions spec row 2, and mark it in progress"
```

- [ ] **Step 2: Write the failing tests**

In `tests/common/test__missing_positions.py`, with positions `lons = [0.0, 10.0, 20.0, 30.0]` and `lats = [0.0, 5.0, 10.0, 15.0]` and `shape="geodesic line"`:

- `test_refuse_missing_positions[case]`: `lons` masked at 1 matches `r"A geodesic line needs every position given, but 1 of 4 is missing, as 'lons' is masked or NaN\."`; `lats` NaN at 2 and 3 matches `r"but 2 of 4 are missing, as 'lats' is masked or NaN\."`; `lons` masked at 1 and `lats` NaN at 1 matches `r"but 1 of 4 is missing, as 'lons' and 'lats' are masked or NaN\."`; `lons` masked at 0 and `lats` NaN at 3 matches `r"but 2 of 4 are missing, as 'lons' and 'lats' are"`.
- `test_refuse_missing_positions_passes_present_ones`: returns `None`, for plain lists and for `np.ma.masked_array(lons)`.
- `test_refuse_missing_positions_refuses_infinite`: `inf` at 2 of `lats` matches `r"'lats' cannot be infinite, got inf at index 2\."`.
- `test_infinite_in_a_grid[name]`: `_missing_positions` of `np.array([[0.0, 1.0], [2.0, np.inf]])` as `xs` or `ys`, the other `np.zeros((2, 2))`, matches `rf"'{name}' cannot be infinite, got inf at index \(1, 1\)\."`.

In `tests/globe/test_heights.py`, `test_infinite_in_a_grid`: `_heights([[0.0, 1.0], [2.0, np.inf]], None, None)` matches `r"cannot be infinite, got inf at index \(1, 1\)\."`, and `test_infinite` keeps its `index 1` for a list.

- [ ] **Step 3: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest -q tests/common/test__missing_positions.py tests/globe/test_heights.py`
Expected: FAIL, with `ImportError` for `_refuse_missing_positions` in the first module, and `test_infinite_in_a_grid` in the second failing on `at index 3`.

- [ ] **Step 4: Implement `_named`, `_first_true` and `_refuse_missing_positions` in `src/geovista/common.py`**

`_first_true` uses `np.unravel_index` of the first of `np.flatnonzero`. `_missing` and the height refusal in `globe.py` take their index and text from it, and the value from the array at that index. `_refuse_missing_positions` counts `np.count_nonzero(_missing(xs) | _missing(ys))` over `np.size` of the two broadcast, and names with `_named`. `_refuse_missing_poi` builds its phrase with `_named`. None is in `__all__`; each docstring cites positions spec §4.1, and `_refuse_missing_positions` §4.4 too.

- [ ] **Step 5: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q tests/common tests/globe tests/search/test_missing_positions.py tests/geoplotter/test_view_poi.py`
Expected: PASS.

- [ ] **Step 6: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/common.py src/geovista/globe.py tests/common/test__missing_positions.py tests/globe/test_heights.py
pixi run --frozen -e geovista git commit -am "feat: refuse a shape with a missing position, and place an infinite value by dimension"
```

### Task 2: `line` and `BBox` Refuse a Missing Position

**Files:**
- Modify: `src/geovista/geodesic.py` (`line`, `BBox.__init__`, and their docstrings' Raises sections)
- Create: `tests/geodesic/test_missing_positions.py`

**Interfaces:**
- Consumes: `_refuse_missing_positions` (Task 1).
- Produces: `line(...)` and `BBox(...)` raise the `ValueError` of call 2, with `shape="geodesic line"` and `shape="bounding-box"`.

- [ ] **Step 1: Write the failing tests**

`tests/geodesic/test_missing_positions.py`, whose refusal tests hold positions spec §2 decision 5, and whose infinite tests §2 decision 2, in their docstrings. `line` takes `LONS = [0.0, 10.0, 20.0]` and `LATS = [0.0, 5.0, 10.0]`; `BBox` takes `XS = [0.0, 10.0, 10.0, 0.0]` and `YS = [0.0, 0.0, 10.0, 10.0]`.

- `test_line_refuses[case]`, over the longitude masked, the latitude masked, the longitude NaN, the latitude NaN and both, at index 1, and the longitude masked at index 2: match `r"A geodesic line needs every position given, but 1 of 3 is missing, as 'lons' is masked or NaN\."`, or `'lats' is`, or `'lons' and 'lats' are`.
- `test_line_refuses_before_any_geodesic`: with `monkeypatch.setattr("geovista.geodesic.npoints_by_idx", <a function raising AssertionError>)`, a NaN longitude still raises the `ValueError`.
- `test_line_refuses_a_repeated_missing_coordinate`: `line(np.ma.masked_array([10.0], mask=True), LATS)` matches `r"but 3 of 3 are missing, as 'lons' is masked or NaN\."` (Review Focus 1).
- `test_line_counts_before_refusing`: `line(np.ma.masked_array(LONS, mask=[0, 1, 0]), [0.0, 5.0])` matches `r"Require the same number of longitudes \(3\) and latitudes \(2\)\."` (Review Focus 4).
- `test_line_refuses_a_masked_quantity`: `UREG.Quantity(np.ma.masked_array(LONS, mask=[0, 1, 0]), "degree")` and `UREG.Quantity(LATS, "degree")` match `as 'lons' is masked or NaN` (Review Focus 5).
- `test_line_refuses_infinite[name]`: `inf` at index 1 of `lons` or `lats` matches `rf"'{name}' cannot be infinite, got inf at index 1\."`.
- `test_bbox_refuses[case]`, over `xs` masked, `ys` masked, `xs` NaN, `ys` NaN and both, at index 2: match `r"A bounding-box needs every position given, but 1 of 4 is missing, as 'xs' is masked or NaN\."`, and so on.
- `test_bbox_refuses_a_missing_closing_corner`: five values, `XS + [0.0]` masked at 4 and `YS + [0.0]`, match `r"but 1 of 5 is missing, as 'xs' is"` (Review Focus 2).
- `test_bbox_refuses_on_a_map`: `BBox([0.0, 1e6, 1e6, 0.0], [0.0, 0.0, np.nan, 1e6], crs="+proj=eqc")` matches `as 'ys' is masked or NaN` (Review Focus 3).
- `test_bbox_refuses_a_masked_quantity`: `UREG.Quantity(XS, "degree")` and `UREG.Quantity(np.ma.masked_array(YS, mask=[0, 0, 1, 0]), "degree")` match `as 'ys' is masked or NaN` (Review Focus 5).
- `test_bbox_refuses_infinite[name]`: `inf` at index 2 matches `rf"'{name}' cannot be infinite, got inf at index 2\."`.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest -q tests/geodesic/test_missing_positions.py`
Expected: FAIL. `line` builds or warns, or raises `TypeError`; `BBox` builds, or raises `TypeError` for five values.

- [ ] **Step 3: Call `_refuse_missing_positions` in `line` and `BBox.__init__`, where call 3 places it**

Each docstring gains a Raises section naming the refusal of a missing position and of an infinite coordinate, beside the `ValueError`s each raises already.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q tests/geodesic tests/units/test_at_the_boundary.py`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/geodesic.py tests/geodesic/test_missing_positions.py
git add tests/geodesic/test_missing_positions.py
pixi run --frozen -e geovista git commit -am "fix: refuse a missing position in geodesic.line and BBox"
```

### Task 3: `wedge` Refuses a Missing Longitude

**Files:**
- Modify: `src/geovista/geodesic.py` (`wedge` and its docstring)
- Modify: `src/geovista/units.py` (`_angle`)
- Test: `tests/geodesic/test_missing_positions.py`

**Interfaces:**
- Consumes: `_missing` (row 1), `_named` (Task 1).
- Produces: `wedge(lon1, lon2)` raises the `ValueError` of call 2; `_angle` returns NaN for a masked quantity, without a warning.

- [ ] **Step 1: Write the failing tests**

- `test_wedge_refuses[lon1, lon2, named]`, over `(np.ma.masked, 30.0, "'lon1' is")`, `(np.nan, 30.0, "'lon1' is")`, `(0.0, np.ma.masked, "'lon2' is")`, `(0.0, np.nan, "'lon2' is")` and `(np.nan, np.ma.masked, "'lon1' and 'lon2' are")`: match `rf"A geodesic wedge needs both longitudes, but {named} masked or NaN\."`.
- `test_wedge_refuses_a_masked_quantity`: `wedge(UREG.Quantity(np.ma.masked_array(10.0, mask=True), "degree"), UREG.Quantity(30.0, "degree"))` matches `as 'lon1' is masked or NaN` (Review Focus 5).
- `test_wedge_refuses_infinite[name]`: `inf` as `lon1` or `lon2`, the other `0.0`, matches `rf"'{name}' cannot be infinite, got inf\."`.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest -q tests/geodesic/test_missing_positions.py -k wedge`
Expected: FAIL. The masked cases raise NumPy's `UserWarning`, the NaN cases build a `BBox`, and `inf` raises the width check's message.

- [ ] **Step 3: Refuse in `wedge` where call 3 places it, and fill a masked quantity with NaN in `_angle`**

`wedge` names each of `lon1` and `lon2` for which `np.any(_missing(value, name=...))`, with `_named`. Its docstring gains a Raises section.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q tests/geodesic tests/units`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/geodesic.py src/geovista/units.py tests/geodesic/test_missing_positions.py
pixi run --frozen -e geovista git commit -am "fix: refuse a missing longitude in geodesic.wedge"
```

### Task 4: The Gaps Row 1 Left

**Files:**
- Test: `tests/search/test_missing_positions.py`, `tests/geoplotter/test_view_poi.py`

**Interfaces:**
- Consumes: `KDTree.query` and `GeoPlotter.view_poi` as row 1 left them.

- [ ] **Step 1: Write the tests**

- `test_a_zlevel_that_broadcasts`, holding positions spec §2 decision 3: `kdtree.query(np.ma.masked_array(LONS, mask=SECOND), LATS, zlevel=np.array([[0.0], [1.0]]))` answers six rows; rows 1 and 4 have no neighbour (`no_neighbour`), and row `r` of the others equals `kdtree.query(LONS[r % 3], LATS[r % 3], zlevel=[0.0, 1.0][r // 3])`.
- `test_a_nan_zlevel_is_not_missing`, holding positions spec §2 decision 1: `kdtree.query(LONS, LATS, zlevel=np.nan)` answers no index equal to `kdtree.n_points` and no infinite distance.
- `test_one_coordinate_given_missing` gains the case `({"y": UREG.Quantity(np.nan, "degree")}, "'y'")`, id `y-nan-quantity`. `tests/geoplotter/test_view_poi.py` gains `import pint` and `UREG = pint.UnitRegistry()` if it has neither.

- [ ] **Step 2: Watch each fail when what it holds is removed**

Mutate one at a time, run the test, see it fail, and revert:
- drop the `np.broadcast_to` of the missing points in `KDTree.query`: `test_a_zlevel_that_broadcasts`;
- read a NaN `zlevel` as missing, `missing = missing | np.isnan(zlevel)` broadcast: `test_a_nan_zlevel_is_not_missing`;
- `view_poi` fills the coordinate left out with a plain `0`: `test_one_coordinate_given_missing[y-nan-quantity]`.

Run: `pixi run --frozen -e geovista pytest -q tests/search/test_missing_positions.py tests/geoplotter/test_view_poi.py`
Expected: PASS once each mutation is reverted.

- [ ] **Step 3: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files tests/search/test_missing_positions.py tests/geoplotter/test_view_poi.py
pixi run --frozen -e geovista git commit -am "test: close the gaps the final review of row 1 found"
```

### Task 5: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (§8 item 1, §9 row 2, §11)
- Create: `changelog/<PR>.bugfix.rst`

- [ ] **Step 1: Watch each clause fail when it regresses**

Mutate one at a time, run the named test, see it fail, and revert:
- `_refuse_missing_positions` counts the missing `xs` alone: `test_refuse_missing_positions[...]` and `test_line_refuses[lat-*]`;
- it names `x_name` whichever coordinate is missing: `test_refuse_missing_positions` and `test_bbox_refuses[ys-*]`;
- `line` refuses after the first `npoints_by_idx`: `test_line_refuses_before_any_geodesic`;
- `line` refuses before the auto-repeat: `test_line_refuses_a_repeated_missing_coordinate`;
- `BBox` makes no refusal: `test_bbox_refuses`;
- `wedge` makes no refusal: `test_wedge_refuses`;
- `_angle` calls `float()` on the masked quantity again: `test_wedge_refuses_a_masked_quantity`;
- `_first_true` gives the flat index: `test_infinite_in_a_grid` in both modules.

- [ ] **Step 2: Run the whole suite and the docs build, on the committed tree**

Run: `CI=true GALLIUM_DRIVER=llvmpipe pixi run --frozen -e test-py313 tests-unit`, then the same with `-e test-py314`, then the strict `sphinx-build` of `AGENTS.md` with `--fail-on-warning --keep-going`.
Expected: PASS, with no new skips and no image baseline regenerated, and the build succeeds.

- [ ] **Step 3: Open the pull request**

Push `fix/missing-positions-geodesic` and open it, titled `fix: refuse missing positions in the geodesic shapes (positions spec row 2)`, with the labels of the Global Constraints. Its body is humanized, says `Closes #2849.` and `Closes #2890.` on lines of their own, puts no closing keyword before any other issue, names any issue it raises, and lists calls 1 to 8. Check `gh pr view --json closingIssuesReferences` lists 2849 and 2890 alone. If its number is not `<PR>`, correct row 2's citation in its own commit.

- [ ] **Step 4: Write the fragment, settle the item, and mark the decision and the row**

`changelog/<PR>.bugfix.rst`, humanized, citing `geovista.geodesic.line`, `geovista.geodesic.BBox` and `geovista.geodesic.wedge` by their documented paths, and naming the row as `row 2 of positions spec §9`. It says that `line` built a line through NaN points for a masked or NaN position, or raised a `TypeError` naming no argument, and that `BBox` and `wedge` built a box around one; that all three now refuse a missing position, naming the argument, and an infinite coordinate; and that a refusal of an infinite coordinate or height in an array of more than one dimension now gives the index in each dimension.

§8 item 1 becomes ``🏁 Resolved (<DATE>, {pull}`<PR>` · 🔎 2026-11-06, {pull}`2889` · 🎫 {issue}`2890`)``, its text kept and followed by sentences saying what settled each gap: the three tests by name, and the index per dimension in both refusals. In §11, §2 decision 5 becomes ``✅ verified (<DATE>, {pull}`<PR>`)`` with evidence `tests/geodesic/test_missing_positions.py`. Decisions 1 and 2 stay pending, as row 1 left them, until rows 3 to 5 land. Last, row 2 of §9 becomes ``✅ landed (<DATE>, {pull}`<PR>`)``. `<DATE>` is the day of this commit.

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py <PR> "changelog/<PR>.bugfix.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py tests/test_renumbering.py tests/test_verification_report.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>`, then the strict docs build again.
Expected: the fragment passes, the tests pass, every status reference holds, and the fragment's references resolve.

- [ ] **Step 5: Commit and push**

```bash
git add changelog/<PR>.bugfix.rst
pixi run --frozen -e geovista git commit -am "docs: mark positions spec row 2 landed, settle §8 item 1, and add the fragment"
git push
```
