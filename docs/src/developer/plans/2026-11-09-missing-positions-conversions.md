# Missing Positions in the Conversions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 5 of positions spec §9, its last. `transform_points` and `vectors_to_cartesian` return NaN for a missing position (§4.7), every component of it; `to_cartesian`, `transform_point`, `geodesic.npoints` and `npoints_by_idx` return NaN for one, and are tested for it; every conversion refuses an infinite coordinate, naming it (§2 decision 2); and `Transform.from_points` names a `zlevel` refused with `vectors` in the shape it was given (§8 item 4, {issue}`2901`).

**Architecture:** One helper in `geovista.common`, `_missing_as_nan`, reads two coordinates with row 1's `_missing`, which refuses an infinite one, and returns them as new float arrays with NaN in both at each missing position. `to_cartesian`, `vectors_to_cartesian`, `npoints` and `npoints_by_idx` read their positions through it, so NaN flows through their arithmetic into every component. `transform_points` reads the missing positions before it flattens them, transforms only the positions present, and gives each missing one a row of NaN. A new `common._refuse_multiple_zlevel` holds the refusal of `_vectors_to_cartesian`, which `from_points` now makes before it drops a point.

**Tech Stack:** NumPy masked arrays, `pyproj`, `pint` through `geovista.units`, pytest.

**Spec:** `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (`positions spec §…`): §2 decisions 1, 2 and 8, §4.1, §4.7, §6, §8 item 4, §9 row 5 and §11.

## Global Constraints

- A position is missing when either of its coordinates is masked or NaN (positions spec §2 decision 1). A masked array whose mask is `nomask` has no missing position, and a `None` is missing (§4.1).
- An infinite coordinate is refused with a `ValueError` naming the argument as the function calls it (§2 decision 2, §4.1): `xs` or `ys` for `transform_points`, `x` or `y` for `transform_point`, `lons` or `lats` for `to_cartesian`, `vectors_to_cartesian` and `npoints_by_idx`, and `start_lon`, `start_lat`, `end_lon` or `end_lat` for `npoints`. A value under a mask is never read, so an infinite one there is missing.
- A conversion carries a missing position through as NaN (§2 decision 8), and every component of a missing position's result is NaN, as {user}`bjlittle` chose on 2026-11-09: x, y and z, including a z given as `zs`.
- `transform_points` leaves a missing position out of the transform, so a value under a mask outside the domain of the target CRS raises nothing (§4.7).
- The test reads coordinates after a `pint` quantity is read in its units and before any position is built (§4.1). A NaN that a transform produces is not a missing position (§4.8).
- No new public name. `mypy` runs strict over the whole package, with no new override, and `ruff` allows 91 statements in a function. Warnings are errors under pytest. Docstrings are NumPy style, and `.. versionchanged::` is not used.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: bug` and `agentic`, and closes {issue}`2901` and no other issue.
- A test file named as evidence in §11 cites its decision, as "Holds positions spec §2 decision 8." in a test's docstring (ledger spec §3.4).
- Cite a specification section in plain text (`positions spec §4.7`), never with a `{ref}` role.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-09 that the specification fixes how row 5 behaves (workflow rule 2.7), once they chose that every component of a missing position's result is NaN. The other calls are mine.

1. **Every component is NaN, and §4.7 says so.** `to_cartesian` given a missing longitude gives NaN for z too, where z comes from the latitude alone today, and `vectors_to_cartesian` NaN for its z component. §4.7 gains the sentence, citing the choice, in this pull request: an edit in place, since §2 decision 8 already says a conversion carries a missing position through as NaN.
2. **One helper pairs the coordinates.** `common._missing_as_nan(xs, ys, *, x_name, y_name) -> tuple[NDArray[np.float64], NDArray[np.float64]]` calls `_missing` on each, and returns new float arrays, never the arrays given, NaN wherever either coordinate is missing. It pairs them only when their shapes match: given two shapes that do not, it NaNs each where it is missing, and leaves its caller's own check to refuse them with today's message, such as "Require longitudes and latitudes with same shape, got (10,) and (5, 2) respectively.".
3. **`transform_points` reads each coordinate as given.** It calls `_missing` on `xs` and `ys` before it flattens them, so an infinite value is named at its index as given, and pairs the two after its check of their sizes, since it takes two shapes of one size. Only the positions present reach `_transformer` and the transform, and each missing one gives a row of NaN. When none is missing, today's path runs on the arrays given, unchanged; when every one is, nothing is transformed. Its body after the checks moves to a private `_transform_flat(src_crs, tgt_crs, xs, ys, zs, *, trap) -> NDArray[Any]`, which today's 1D path becomes.
4. **`transform_point` names `x` and `y`.** It calls `_missing_positions(x, y, x_name="x", y_name="y")` once it reads its quantities, before it calls `transform_points`. A `None` gives a row of NaN, where `pyproj` raises "input must be a scalar" today, since §4.1 reads `None` as missing (a widening, workflow rule 1.2).
5. **`npoints` pairs each end.** Once `_angle` reads its four angles, `_missing_as_nan` reads the start and the end as pairs, naming `start_lon` and `start_lat`, or `end_lon` and `end_lat`. A missing end gives NaN at every point between, and `(nan, nan)` for itself under `include_start` or `include_end`. A masked end gives no NumPy warning, and a `None` gives NaN, where it raises "must be real number, not NoneType" today.
6. **`npoints_by_idx` reads only its two positions.** It indexes `lons` and `lats` first, then reads the two pairs with `_missing_as_nan`, naming `lons` and `lats`, without the index the caller gave. `geodesic.line` calls it for each pair of its vertices, so a check of the whole arrays would cost a line of N vertices N squared reads.
7. **The `zlevel` is refused as given.** `common._refuse_multiple_zlevel(zlevel: float | ArrayLike | None) -> None` raises today's "'zlevel' may not be multiple, has shape (2, 1).". `_vectors_to_cartesian` calls it in place of its own check, and `from_points` calls it before `_drop_missing` when `vectors` is given, so the refusal names the shape given and comes before any warning of a point dropped.
8. **What stays.** An infinite `zs`, `zlevel` or vector component is not a coordinate of a position, and is left alone. A masked or NaN vector component is data (§4.8). `wrap` is untouched.
9. **Evidence.** New `tests/transform/test_missing_positions.py` and `tests/common/test_missing_positions.py` hold the conversions, and `tests/geodesic/test_missing_positions.py` gains `npoints` and `npoints_by_idx`; each cites decisions 1, 2 and 8. `tests/bridge/test_missing_mesh_positions.py` gains a citation of decision 2 on its tests of an infinite coordinate. §11 marks decisions 1, 2 and 8 verified, naming every test file of rows 1 to 5 that cites each.
10. **One fragment, `2912.bugfix.rst`.** The branch is `fix/missing-positions-conversions`, and the plan is the first commit of draft pull request {pull}`2912` (workflow rule 2.3), which marks row 5 in progress (workflow rule 2.4) and closes {issue}`2901`, resolving §8 item 4 (workflow rule 4.7).

## Review Focus

1. **The arrays given are left alone.** `to_cartesian(lons, lats)` with a NaN longitude leaves the NaN out of the caller's `lats`. `test_leaves_the_arrays_given_alone` (Task 1).
2. **Every position missing.** `transform_points` gives only NaN and never builds a transformer, and `to_cartesian` gives only NaN. `test_transforms_nothing_when_every_position_is_missing` (Task 2), and `test_gives_nan_for_every_missing_position` (Task 1).
3. **Shapes that do not pair.** `to_cartesian` and `vectors_to_cartesian` given a masked longitude and coordinates of different shapes refuse them with today's messages. `test_refuses_shapes_that_do_not_pair_as_before` (Task 1).
4. **One position, given as numbers.** `transform_points(WGS84, ORTHO, np.nan, 10.0)` gives one row of NaN, of shape `(1, 3)`. `test_gives_nan_for_one_missing_position_given_as_numbers` (Task 2).
5. **A grid with heights.** `transform_points` given a 2D grid with `zs` and one missing position keeps the shape `(M, N, 3)`, with a row of NaN at it, z included. `test_gives_a_grid_nan_where_a_position_is_missing` (Task 2).

---

Measured on 2026-11-09 at `daca7540` (`main` after {pull}`2908`), with Python 3.14.10, NumPy 2.5.4, `pyproj` 3.8.0 (PROJ 9.9.0) and `pint` 0.26.2, in the `geovista` environment, on the positions `[0, 10, 20]` by `[0, 10, 20]`, the second missing:

- `transform_points` to an orthographic CRS transforms the value under a masked longitude, giving `(1090835.8, 1100248.5, 0)`, and raises "transform error: Point outside of projection domain" when that value is 170. A NaN longitude gives `(nan, nan, 0)`, and between two equal CRSs `(nan, 10, 0)`. An infinite one gives `(inf, inf, 0)`, or between equal CRSs `(nan, 10, 0)` with NumPy's "invalid value encountered in remainder". A grid with `zs` in the orthographic CRS gives `(nan, nan, nan)` at a NaN position. Integers between equal CRSs come back as float64.
- `transform_point` gives `(nan, nan, 0)` for `np.ma.masked`, with NumPy's "Warning: converting a masked element to nan.", `(inf, inf, 0)` for an infinite `x`, and raises `TypeError: input must be a scalar` for `None`.
- `to_cartesian` gives `(nan, nan, 0.17)` for a missing longitude at latitude 10, and `(nan, nan, nan)` for a missing latitude; an infinite one gives NaN, with NumPy's "invalid value encountered in cos".
- `vectors_to_cartesian` computes the vector at the value under a masked longitude. Given a NaN longitude, its x and y components are NaN and its z component is `1.158`.
- `npoints` and `npoints_by_idx` give NaN at every point for a missing end, the other end's too under `include_end`. A masked end warns "Warning: converting a masked element to nan.", an infinite one gives NaN, and `npoints` raises "must be real number, not NoneType" for `None`.
- Over the whole suite at `daca7540`, on `test-py314`, no caller inside `geovista` gave `transform_points` or `to_cartesian` an infinite coordinate. Only `from_points` gave `transform_points` a NaN or masked one, where it refuses coordinates of two sizes, and `transform_points` refuses them by their sizes as before.

### Task 1: The Cartesian Conversions

**Files:**
- Modify: `src/geovista/common.py` (a new `_missing_as_nan`, `to_cartesian`, `vectors_to_cartesian`, and their docstrings)
- Create: `tests/common/test_missing_positions.py`
- Modify: `tests/common/test__missing_positions.py` (the helper)

**Interfaces:**
- Consumes: `common._missing(values, *, name) -> NDArray[np.bool_]`, from row 1.
- Produces: `common._missing_as_nan(xs: ArrayLike, ys: ArrayLike, *, x_name: str, y_name: str) -> tuple[NDArray[np.float64], NDArray[np.float64]]`, which Task 3 uses.

- [ ] **Step 1: Write the tests**

In `tests/common/test__missing_positions.py`:
- `test_missing_as_nan_pairs_the_coordinates()`: xs `[0.0, nan, 20.0]`, ys masked at 2: both results are `[0.0, nan, nan]`, with the values given elsewhere.
- `test_missing_as_nan_leaves_the_arrays_given_alone()`: xs NaN at 1, ys a plain float array: `ys` holds no NaN after the call, and neither result is an array given.
- `test_missing_as_nan_leaves_shapes_that_differ_unpaired()`: xs of shape `(3,)` NaN at 1, ys of shape `(2,)`: the x result is NaN at 1 alone, the y result equals ys.
- `test_missing_as_nan_refuses_infinite()`: `"'lons' cannot be infinite, got inf at index 1."`.

`tests/common/test_missing_positions.py` is new. Constants: `LONS = np.array([0.0, 10.0, 20.0])`, `LATS` the same, `VECTORS = ([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0])`, and `UREG = pint.UnitRegistry()`; helpers `masked` and `nan` as in `tests/bridge/test_missing_mesh_positions.py`. `CONVERT` parametrizes over `to_cartesian` and over `vectors_to_cartesian` with its components stacked as `np.column_stack`, each a function of `lons`, `lats` and the indices `keep` of the vectors to give, so both give `(N, 3)`. The reference is the same conversion of the positions present alone, `[0, 2]`.

- `test_gives_nan_for_a_missing_position(convert, lons, lats)`, with ids `lon-masked`, `lat-masked`, `both-masked`, `lon-nan`, `lat-nan`, `lon-none` (`[0.0, None, 20.0]`) and `quantity` (both `UREG.Quantity(..., "degree")`, the longitudes masked at 1): every component of row 1 is NaN, and rows 0 and 2 match the reference with `np.testing.assert_allclose`. Its docstring holds decisions 1 and 8.
- `test_gives_nan_for_every_missing_position(convert)`: longitudes all NaN: every value is NaN.
- `test_reads_nomask_as_present(convert)`: `np.ma.masked_array(LONS)`: no value is NaN.
- `test_refuses_infinite(convert, name)`, with ids `lons`, `lats`, an infinite value at 1: `ValueError` matching `"'{name}' cannot be infinite, got inf at index 1."`. It holds decision 2.
- `test_leaves_the_arrays_given_alone(convert)`: a NaN longitude at 1: `LATS`, given as a copy, holds no NaN after the call.
- `test_refuses_shapes_that_do_not_pair_as_before()`: `to_cartesian(masked(np.arange(10.0), 1), np.arange(10.0).reshape(5, 2))` raises "Require longitudes and latitudes with same shape", and `vectors_to_cartesian(masked(LONS, 1), LATS[:2], VECTORS)` raises "'lons' and 'lats' do not have same shape".

- [ ] **Step 2: Run the tests to watch them fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/common/test_missing_positions.py tests/common/test__missing_positions.py`
Expected: FAIL. `_missing_as_nan` cannot be imported; `to_cartesian` keeps a real z for a missing longitude; `vectors_to_cartesian` computes the vector at the value under the mask; nothing refuses an infinite coordinate.

- [ ] **Step 3: Implement `_missing_as_nan`, and read the positions of both conversions through it**

`_missing_as_nan` follows Call 2: `_missing` on each coordinate, then `np.ma.filled(np.ma.asanyarray(values, dtype=float), np.nan)` copied, NaN in both where either is missing when their shapes match. `to_cartesian` calls it in place of its two calls of `nan_mask`, naming `lons` and `lats`, and `vectors_to_cartesian` calls it after `_lonlats`. Each docstring gains: "A position is missing when its longitude or latitude is masked or NaN, and gives NaN in every component (positions spec §4.7). An infinite longitude or latitude is refused.", humanized.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/common/`
Expected: PASS, `test_a_masked_coordinate_is_read_as_nan` and `test_shape_fail` of `tests/common/test_to_cartesian.py` with them.

- [ ] **Step 5: Commit**

```bash
git add src/geovista/common.py tests/common/test_missing_positions.py tests/common/test__missing_positions.py
pixi run --frozen -e geovista git commit -m "fix: give a missing position NaN in every component of the cartesian conversions"
```

### Task 2: The Transforms

**Files:**
- Modify: `src/geovista/transform.py` (`transform_points`, `transform_point`, a new `_transform_flat`, and their docstrings)
- Create: `tests/transform/test_missing_positions.py`

**Interfaces:**
- Consumes: `common._missing` and `common._missing_positions(xs, ys, *, x_name, y_name) -> NDArray[np.bool_]`, from row 1.
- Produces: `transform._transform_flat(src_crs: pyproj.CRS, tgt_crs: pyproj.CRS, xs: NDArray[Any], ys: NDArray[Any], zs: NDArray[Any] | None, *, trap: bool) -> NDArray[Any]`, used inside this task only.

- [ ] **Step 1: Write the tests**

Constants: `ORTHO = "+proj=ortho +lat_0=0 +lon_0=0"`, `XS = np.array([0.0, 10.0, 20.0])`, `YS` the same, and `HIDDEN = 170.0`, a longitude beyond the disk of `ORTHO`. The reference is `transform_points` of the positions present alone.

- `test_gives_nan_for_a_missing_position(tgt, xs, ys)`, with `tgt` ids `same` (`WGS84`) and `ortho`, and the cases of Task 1's test: every value of row 1 is NaN, and rows 0 and 2 match the reference. It holds decisions 1 and 8.
- `test_reads_nomask_as_present(tgt)`: `np.ma.masked_array(XS)`: no value is NaN.
- `test_leaves_a_missing_position_out_of_the_transform()`: the longitudes masked at 1 over `HIDDEN`: `transform_points(WGS84, ORTHO, ...)` raises nothing and gives row 1 NaN, and `transform_point(WGS84, ORTHO, np.ma.masked_array(HIDDEN, mask=True), 0.0)` gives NaN.
- `test_transforms_nothing_when_every_position_is_missing(mocker)`: longitudes all NaN, with `mocker.spy(transform, "_transformer")`: a `(3, 3)` result of NaN, and the spy never called.
- `test_gives_nan_for_one_missing_position_given_as_numbers()`: `transform_points(WGS84, ORTHO, np.nan, 10.0)` has shape `(1, 3)`, all NaN.
- `test_gives_a_grid_nan_where_a_position_is_missing(tgt)`: a `(2, 3)` grid NaN at `(1, 2)`, `zs` of 5.0: shape `(2, 3, 3)`, `result[1, 2]` all NaN, and `result[0, 0]` the reference's.
- `test_refuses_infinite(name)`, with ids `xs`, `ys`: a `(2, 3)` grid infinite at `(1, 2)` raises `"'{name}' cannot be infinite, got inf at index (1, 2)."`. It holds decision 2.
- `test_transform_point_gives_nan(x)`, with ids `masked` (`np.ma.masked`), `nan` and `none`: `transform_point(WGS84, ORTHO, x, 10.0)` is all NaN, with no warning.
- `test_transform_point_refuses_infinite(name)`, with ids `x`, `y`: `"'{name}' cannot be infinite, got inf."`.

- [ ] **Step 2: Run the tests to watch them fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/transform/test_missing_positions.py`
Expected: FAIL. The value under the mask is transformed, or raises `ProjError`; a NaN x keeps a real y between equal CRSs; `None` raises `TypeError`; nothing refuses an infinite coordinate.

- [ ] **Step 3: Implement Calls 3 and 4**

`transform_points` reads `_missing` on `xs` and `ys` once their quantities are read, keeps its checks of dimensions and sizes and their messages, then pairs the two raveled. The 1D path after the checks moves to `_transform_flat`, called on the arrays given when nothing is missing; otherwise on the present values as floats, its rows scattered into an `(N, 3)` array of NaN, and not at all when no position is present. The reshape of a 2D grid follows, as today. `transform_point` calls `_missing_positions(x, y, x_name="x", y_name="y")` after `_coordinates`. Each docstring gains: "A position is missing when its x or y value is masked or NaN, and gives a row of NaN, z included, without being transformed (positions spec §4.7). An infinite x or y value is refused.", humanized.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/transform/ tests/bridge/ tests/search/ tests/geodesic/`
Expected: PASS, the callers of `transform_points` with them.

- [ ] **Step 5: Commit**

```bash
git add src/geovista/transform.py tests/transform/test_missing_positions.py
pixi run --frozen -e geovista git commit -m "fix: give a missing position a row of NaN in transform_points and transform_point"
```

### Task 3: The Geodesic Points

**Files:**
- Modify: `src/geovista/geodesic.py` (`npoints`, `npoints_by_idx`, and their docstrings)
- Modify: `tests/geodesic/test_missing_positions.py`

**Interfaces:**
- Consumes: `common._missing_as_nan`, from Task 1.

- [ ] **Step 1: Write the tests**

- `test_npoints_gives_nan_for_a_missing_end(name, value)`, over the four names of the ends and the values `np.ma.masked`, `np.nan` and `None`, the others `-10`, `20`, `10` and `30`: with `npts=3`, `include_start=True` and `include_end=True`, every longitude and latitude is NaN, with no warning. It holds decisions 1 and 8.
- `test_npoints_refuses_infinite(name)`, over the four names: `"'{name}' cannot be infinite, got inf."`. It holds decision 2.
- `test_npoints_by_idx_gives_nan_for_a_missing_end(lons, lats)`, with ids `lon-masked`, `lat-nan` and `quantity`, on four positions missing at 1: `npoints_by_idx(lons, lats, 0, 1, npts=3)` is all NaN, with no warning.
- `test_npoints_by_idx_reads_only_its_two_positions()`: longitudes NaN at 2 and infinite at 3: `npoints_by_idx(lons, lats, 0, 1, npts=3)` equals `npoints` of those two positions.
- `test_npoints_by_idx_refuses_infinite(name)`, with ids `lons`, `lats`, infinite at 1: `npoints_by_idx(..., 0, 1)` raises `"'{name}' cannot be infinite, got inf."`.

- [ ] **Step 2: Run the tests to watch them fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/geodesic/test_missing_positions.py -k npoints`
Expected: FAIL. A masked end warns, `None` raises `TypeError`, and nothing refuses an infinite one.

- [ ] **Step 3: Implement Calls 5 and 6**

`npoints` reads its start and its end through `_missing_as_nan` after `_angle`, passing `geod.npts` plain floats. `npoints_by_idx` indexes first, then reads each pair through `_missing_as_nan` naming `lons` and `lats`. Each docstring gains: "An end whose longitude or latitude is masked or NaN is missing, and gives NaN at every point (positions spec §4.7). An infinite one is refused.", humanized.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/geodesic/`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/geovista/geodesic.py tests/geodesic/test_missing_positions.py
pixi run --frozen -e geovista git commit -m "fix: read a missing end of npoints as NaN, and refuse an infinite one"
```

### Task 4: The `zlevel` Refused With `vectors`

**Files:**
- Modify: `src/geovista/common.py` (a new `_refuse_multiple_zlevel`, `_vectors_to_cartesian`)
- Modify: `src/geovista/bridge.py` (`from_points`)
- Modify: `tests/bridge/test_missing_positions.py`

**Interfaces:**
- Produces: `common._refuse_multiple_zlevel(zlevel: float | ArrayLike | None) -> None`.

- [ ] **Step 1: Write the test**

`test_refuses_a_zlevel_with_vectors_in_the_shape_given(ys)`, with ids `none-missing` and `one-missing` (`ys[1, 0]` NaN), on the points of {issue}`2901`: `xs = [[0, 10, 20], [30, 40, 50]]`, `ys = [[0, 5, 10], [15, 20, 25]]`, `vectors` two components of ones of shape `(2, 3)`, and `zlevel=[[1], [2]]`. `from_points` raises `ValueError` matching `"'zlevel' may not be multiple, has shape \(2, 1\)\."`, with no warning. Its docstring says it settles positions spec §8 item 4.

- [ ] **Step 2: Run the test to watch it fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/bridge/test_missing_positions.py -k zlevel_with_vectors`
Expected: FAIL for `one-missing`, warning of the point dropped and naming `(5,)`.

- [ ] **Step 3: Implement Call 7**

The check of `_vectors_to_cartesian` moves to `_refuse_multiple_zlevel`, with its message, and `_vectors_to_cartesian` calls it. `from_points` calls it before `_drop_missing` when `vectors` is given.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/bridge/ tests/common/ tests/geoplotter/test_add_points.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/geovista/common.py src/geovista/bridge.py tests/bridge/test_missing_positions.py
pixi run --frozen -e geovista git commit -m "fix: refuse a zlevel given with vectors in the shape it was given"
```

### Task 5: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (§4.7, §8 item 4, §9 row 5, §11)
- Modify: `tests/bridge/test_missing_mesh_positions.py` (citations of decision 2)
- Modify: this plan's Follow-ups, before merge
- Create: `changelog/2912.bugfix.rst`

- [ ] **Step 1: Cite decision 2 where row 4 tests it**

`test_refuses_infinite`, `test_from_1d_refuses_an_infinite_bound` and `test_to_structured_grid_refuses_infinite` in `tests/bridge/test_missing_mesh_positions.py` each gain "Holds positions spec §2 decision 2." in their docstrings.

- [ ] **Step 2: Watch each clause fail when it regresses**

Mutate one at a time, run the named tests, see them fail, and revert:
- `_missing` stops reading NaN: the `lon-nan` and `lat-nan` cases of the evidence of decision 1, across rows 1 to 5;
- `_missing` stops reading a mask: their `lon-masked` cases;
- `_missing` stops refusing an infinite value: the tests of decision 2's evidence that refuse one;
- `transform_points` transforms every position: `test_gives_nan_for_a_missing_position[ortho-lon-masked]` and `test_leaves_a_missing_position_out_of_the_transform`;
- `_missing_as_nan` stops pairing: the `to_cartesian` and `vectors_to_cartesian` cases of `lon-nan`;
- `npoints` reads its ends as given: `test_npoints_gives_nan_for_a_missing_end`;
- `npoints_by_idx` reads its whole arrays: `test_npoints_by_idx_reads_only_its_two_positions`;
- `from_points` refuses the `zlevel` after the drop: `test_refuses_a_zlevel_with_vectors_in_the_shape_given[one-missing]`.

- [ ] **Step 3: Record the choice, settle the item, and mark the decisions and the row**

§4.7 gains a sentence, humanized: every component of a missing position's result is NaN, as {user}`bjlittle` chose on 2026-11-09, x, y and z, including a z given as `zs`, so `to_cartesian` now gives NaN for the z it took from the latitude alone. §8 item 4 becomes ``🏁 Resolved (<DATE>, {pull}`2912` · 🔎 2026-11-08, {pull}`2899` · 🎫 {issue}`2901`)``, ending "Row 5 settled it." and how: `from_points` refuses a `zlevel` array given with `vectors` before it drops a point, so the message names the shape given, `(2, 1)`.

In §11, each becomes ``✅ verified (<DATE>, {pull}`2912`)``:
- §2 decision 1: `tests/common/test__missing_positions.py`, `tests/search/test_missing_positions.py`, `tests/geodesic/test_missing_positions.py`, `tests/bridge/test_missing_positions.py`, `tests/bridge/test_missing_mesh_positions.py`, `tests/common/test_missing_positions.py`, `tests/transform/test_missing_positions.py`;
- §2 decision 2: `tests/common/test__missing_positions.py`, `tests/search/test_missing_positions.py`, `tests/geoplotter/test_view_poi.py`, `tests/geodesic/test_missing_positions.py`, `tests/bridge/test_missing_positions.py`, `tests/bridge/test_missing_mesh_positions.py`, `tests/common/test_missing_positions.py`, `tests/transform/test_missing_positions.py`;
- §2 decision 8: `tests/common/test_missing_positions.py`, `tests/transform/test_missing_positions.py`, `tests/geodesic/test_missing_positions.py`.

Last, row 5 of §9 becomes ``✅ landed (<DATE>, {pull}`2912`)``. `<DATE>` is the day of this commit, corrected if the merge slips to another day (workflow rule 2.4).

`changelog/2912.bugfix.rst`, humanized, cites each function by its documented path (`geovista.transform.transform_points`, `geovista.common.to_cartesian`, `geovista.geodesic.npoints`, `geovista.bridge.Transform.from_points` and the rest), and names the row as `row 5 of positions spec §9` on one line. It says that `transform_points` transformed the value under a mask, or raised beyond a CRS's domain, and `vectors_to_cartesian` computed the vector at it; that each conversion now gives NaN in every component of a missing position, `to_cartesian`'s z included, and refuses an infinite coordinate; that `transform_point` and `npoints` give NaN for `None`, and a masked end no NumPy warning; and that `from_points` names a `zlevel` refused with `vectors` in the shape given.

List any issue this pull request raises under Follow-ups below, and in the pull request's description (workflow rule 4.5); each one deferred from this row is an open item of the spec, in this pull request (workflow rule 2.8).

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py 2912 "changelog/2912.bugfix.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py tests/test_renumbering.py tests/test_verification_report.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status 2912` and `pixi run --frozen -e test check-spec-renumbering`.
Expected: the fragment passes, the tests pass, every status reference holds, and no citation went stale.

- [ ] **Step 4: Commit, then run the whole suite and the docs build on that commit**

```bash
git add changelog/2912.bugfix.rst
pixi run --frozen -e geovista git commit -am "docs: mark positions spec row 5 landed, verify §2 decisions 1, 2 and 8, and add the fragment"
```

Run: the strict `sphinx-build` of `AGENTS.md` with `-E`, `--fail-on-warning` and `--keep-going`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/test_geovista_ledger.py`, then `CI=true GALLIUM_DRIVER=llvmpipe pixi run --frozen -e test-py313 tests-unit` and the same with `-e test-py314`.
Expected: the build succeeds, each file of evidence links to its citing line, and the suites PASS with no new skips and no image baseline regenerated.

- [ ] **Step 5: Push, and mark the pull request ready**

Push, confirm it with `git ls-remote` (workflow rule 4.6), check `gh pr view 2912 --json closingIssuesReferences` lists {issue}`2901` alone, and mark the pull request ready once the final review's fixes have landed.

## Follow-ups

None yet.
