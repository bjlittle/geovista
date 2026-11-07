# Missing Positions in the Queries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 1 of positions spec §9. One private test in `geovista.common` reads a position as missing when either coordinate is masked or NaN, and refuses an infinite coordinate. `KDTree.query` answers that a missing point has no neighbour, and `find_nearest_cell` and `GeoPlotter.view_poi` refuse a missing position.

**Architecture:** `geovista.common` gains `_missing` (one coordinate), `_missing_positions` (the helper of positions spec §4.1, built on it) and `_refuse_missing_poi` (the refusal of a single position). Each caller reads `pint` quantities first, as today, then calls them before any position is built. `KDTree.query` queries only the present points and scatters pykdtree's answers into arrays that give each missing point the answer for a point beyond `distance_upper_bound`.

**Tech Stack:** NumPy masked arrays, `pykdtree` 1.4.3, `pyvista` 0.49.2, `pint` through `geovista.units`, pytest.

**Spec:** `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (`positions spec §…`): §2 decisions 1 to 4, §4.1 to §4.3, §6, §9 row 1 and §11.

## Global Constraints

- A position is missing when either of its coordinates is masked or NaN (positions spec §2 decision 1). A masked array whose mask is `nomask` has no missing position (§4.1).
- An infinite coordinate is refused with a `ValueError` naming the argument as the function calls it: `lons` or `lats` for `KDTree.query`, `x` or `y` for `find_nearest_cell` and `view_poi` (§2 decision 2, §4.1).
- The test reads coordinates after a `pint` quantity is read in its units and before any position is built. A value under a mask is never read as a coordinate (§4.1).
- A missing point of a query answers a distance of `inf` and an index equal to the number of points in the tree, for every one of its `k` neighbours. The other points answer what they answer today (§2 decision 3, §4.2).
- `find_nearest_cell` and `view_poi` raise a `ValueError` naming `x` or `y` when their point-of-interest is missing. The default position of `view_poi`, the centre of the last mesh added, is out of scope (§2 decision 4, §4.3).
- No new public name. `mypy` runs strict over the whole package, with no new override. Warnings are errors under pytest. Docstrings are NumPy style, and `.. versionchanged::` is not used.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: bug` and `agentic`, and names {issue}`2849` without closing it, as it closes when rows 1 and 2 have landed (§9).
- A test named as evidence in §11 cites its decision in its docstring, as "Holds positions spec §2 decision 3." (ledger spec §3.4).
- Cite a specification section in plain text (`positions spec §4.2`), never with a `{ref}` role.

## Calls Made in This Plan

None was discussed. Calls 3 and 4 amend positions spec §4.1 and §4.3, in Task 4.

1. **The helper is built from a test of one coordinate.** `_missing` decides for one coordinate, and `_missing_positions`, the helper of §4.1, is the two combined. A single position must name which coordinate is missing (§6), and row 2 must name and count them (§4.4), so both need the test of one coordinate. The rule lives in `_missing` alone.
2. **The refusal of a single position is shared.** `_refuse_missing_poi` in `geovista.common` serves `find_nearest_cell` and `view_poi`, and names `'x'`, `'y'` or `'x' and 'y'`.
3. **A masked infinite value is missing, not refused,** since a value under a mask is never read.
4. **The coordinate `view_poi` fills in is a present 0.** Given one coordinate, `view_poi` sets the other to `0 * given`, which is masked for a masked `given` and NaN for a NaN one, so the refusal would name a coordinate the caller never gave. It becomes plain 0, or 0 in the units of `given` when that is a quantity.
5. **The messages.** An infinite value gives `"'lons' cannot be infinite, got inf at index 1."`, or `"'x' cannot be infinite, got inf."` for a scalar, as heights spec §2 decision 3 words its refusal. A missing single position gives `"The point-of-interest is missing, as 'x' is masked or NaN."`, with `'x' and 'y' are` for both. Coordinates that do not broadcast give `"Cannot pair 'lons' of shape (3,) with 'lats' of shape (2,)."`.
6. **A query with no missing point returns pykdtree's own answer,** untouched. With one, the answer keeps pykdtree's dtypes and shapes: `(N,)` for `k` of 1, `(N, k)` above it, in the raveled order of the positions.
7. **A NaN `zlevel` is not a missing position,** and queries as today.
8. **One fragment, `<PR>.bugfix.rst`.** The branch is `fix/missing-positions-queries`.

## Review Focus

1. **A tree of cell centres.** Its point count is the mesh's cell count, so a missing point answers `kdtree.n_points`, which is `n_cells`, not the mesh's `n_points`. `test_a_tree_of_centres` (Task 2).
2. **A query of only missing points.** pykdtree is asked an empty query, which answers arrays of shape `(0,)`, and every answer is `(inf, n_points)` with pykdtree's dtypes, float64 and uint32. `test_every_point_missing` (Task 2).
3. **Points-of-interest as a 2-D grid.** The answers follow the raveled order of the grid, a missing point at its raveled index. `test_a_grid_of_points` (Task 2).
4. **`view_poi` given one coordinate, which is missing.** The refusal names that coordinate alone. `test_one_coordinate_given_missing` (Task 3).
5. **A quantity of a masked array.** `_lonlats` and `_coordinates` keep its mask, so it is missing as a plain masked array is. `test_a_masked_quantity` (Task 2) and `test_find_nearest_cell_refuses_a_masked_quantity` (Task 3).

---

Measured on 2026-11-06 at `54a5acc9`, with Python 3.14.10, NumPy 2.5.4, `pykdtree` 1.4.3, `pyvista` 0.49.2, VTK 9.7.1 and `pint` 0.26.2, in the `geovista` environment:

- pykdtree answers a point beyond `distance_upper_bound` with `(inf, n)`, and a NaN or infinite point with `(1.3407807929942596e154, 4294967295)`. It answers `(n,)` arrays for `k=1` and `(n, k)` for `k=3`, float64 and uint32, and an empty query with arrays of shape `(0,)` of the same dtypes.
- `KDTree(lam_uk()).query` of longitudes `[-2, masked 0]` at latitudes `[52, 53]` answers indices `[11, 14]`, reading the value under the mask. A NaN longitude answers index 4294967295.
- `find_nearest_cell(lam_uk(), np.ma.masked, 52.0)` and `find_nearest_cell(lam_uk(), np.nan, 52.0)` both answer `[0]`.
- `view_poi(x=np.ma.masked)` puts the camera where `view_poi(x=0.0, y=0.0)` does, and `view_poi(x=np.nan)` puts it at `(nan, nan, nan)`.
- `np.ma.asanyarray([30, np.ma.masked], dtype=float)` keeps the mask of the masked element, and `np.ma.masked` reads as a 0-d masked array. `np.ma.filled` of a masked `inf` hides it from `np.isinf`.
- `_lonlats` given a quantity of a masked array returns a `MaskedArray` with that mask.

### Task 1: The Test of a Missing Position

**Files:**
- Create: `docs/src/developer/plans/2026-11-06-missing-positions-queries.md` (this plan)
- Modify: `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (§9 row 1)
- Modify: `src/geovista/common.py` (`_missing`, `_missing_positions`, `_refuse_missing_poi`)
- Create: `tests/common/test__missing_positions.py`

**Interfaces:**
- Produces:
  - `_missing(values: ArrayLike, *, name: str) -> NDArray[np.bool_]`: `True` where `values` is masked or NaN, in the shape of `values` (0-d for a scalar). Raises `ValueError` for an unmasked infinite value, naming `name`.
  - `_missing_positions(xs: ArrayLike, ys: ArrayLike, *, x_name: str, y_name: str) -> NDArray[np.bool_]`: `_missing(xs) | _missing(ys)`, broadcast. Raises `ValueError` when they do not broadcast, naming both.
  - `_refuse_missing_poi(x: ArrayLike, y: ArrayLike, *, x_name: str, y_name: str) -> None`: raises `ValueError` naming each missing coordinate, and refuses an infinite one through `_missing`.

- [ ] **Step 1: Branch, and mark the row in progress**

Create `fix/missing-positions-queries` from `main`. Find the next free number with `gh api 'repos/bjlittle/geovista/issues?state=all&per_page=1&sort=created&direction=desc' --jq '.[0].number'`, plus 1: this is `<PR>` until the pull request is opened. Mark positions spec §9 row 1 ``🚧 in progress ({pull}`<PR>`)``. This commit is the first of the branch (docs/AGENTS.md).

```bash
git add docs/src/developer/plans/2026-11-06-missing-positions-queries.md
pixi run --frozen -e geovista git commit -am "docs: plan positions spec row 1, and mark it in progress"
```

- [ ] **Step 2: Write the failing tests**

`tests/common/test__missing_positions.py`, whose module docstring holds positions spec §2 decisions 1 and 2. Each case gives three positions and expects the mask shown:

- `test_present`: `[1, 2, 3]` and `[4, 5, 6]`, integers, give `[False, False, False]`.
- `test_missing[case]`, over a longitude masked alone, a latitude masked alone, both masked, a NaN longitude and a NaN latitude, each at index 1: `[False, True, False]`.
- `test_nomask`: `np.ma.masked_array([1.0, 2.0, 3.0])` gives no missing position.
- `test_a_masked_element_of_a_list`: `[1.0, np.ma.masked, 3.0]` gives `[False, True, False]`.
- `test_scalar[value]`, over `np.ma.masked` and `np.nan` as `xs` with `ys=1.0`: a 0-d `True`.
- `test_infinite_refused[name, value]`, over `xs` and `ys`, `inf` and `-inf` at index 1: `pytest.raises(ValueError, match=r"'ys' cannot be infinite, got -inf at index 1\.")` and so on. A scalar: `match=r"'xs' cannot be infinite, got inf\."`.
- `test_masked_infinite_is_missing`: `np.ma.masked_array([1.0, np.inf, 3.0], mask=[0, 1, 0])` gives `[False, True, False]`, with no error (call 3).
- `test_a_masked_quantity`: `_missing_positions(*_lonlats(UREG.Quantity(np.ma.masked_array([1.0, 2.0, 3.0], mask=[0, 1, 0]), "degree"), UREG.Quantity([4.0, 5.0, 6.0], "degree")), x_name="lons", y_name="lats")` gives `[False, True, False]`.
- `test_shapes_that_do_not_pair`: shapes `(3,)` and `(2,)` raise `match=r"Cannot pair 'xs' of shape \(3,\) with 'ys' of shape \(2,\)\."`.
- `test_refuse_missing_poi[x, y, named]`: a masked or NaN `x` matches `r"as 'x' is masked or NaN\."`, a masked or NaN `y` matches `r"as 'y' is masked or NaN\."`, and both match `r"as 'x' and 'y' are masked or NaN\."`. `(30.0, 52.0)` returns `None`.

- [ ] **Step 3: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/common/test__missing_positions.py -q`
Expected: FAIL with `ImportError` for `_missing_positions`.

- [ ] **Step 4: Implement `_missing`, `_missing_positions` and `_refuse_missing_poi` in `src/geovista/common.py`**

`_missing` reads `values` with `np.ma.asanyarray(values, dtype=float)`. Its mask is `np.ma.getmaskarray` of that, and `np.isnan` and `np.isinf` read `np.ma.filled(..., 0.0)`, so a value under a mask is never read. None is in `__all__`. Each docstring cites positions spec §4.1.

- [ ] **Step 5: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/common -q`
Expected: PASS.

- [ ] **Step 6: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/common.py tests/common/test__missing_positions.py
git add tests/common/test__missing_positions.py
pixi run --frozen -e geovista git commit -am "feat: read a position as missing when either coordinate is masked or NaN"
```

### Task 2: A Query Answers That a Missing Point Has No Neighbour

**Files:**
- Modify: `src/geovista/search.py` (`KDTree.query` and its docstring)
- Create: `tests/search/test_missing_positions.py`

**Interfaces:**
- Consumes: `_missing_positions` (Task 1).
- Produces: `KDTree.query` answers `(inf, kdtree.n_points)` for each missing point.

- [ ] **Step 1: Write the failing tests**

`tests/search/test_missing_positions.py`. Its query tests hold positions spec §2 decision 3, in their docstrings. The tree is `KDTree(lam_uk)`, and the positions are `lons = [-2.0, 0.0, 1.0]`, `lats = [52.0, 53.0, 54.0]` with index 1 made missing.

- `test_missing_point_has_no_neighbour[case, k]`, over the five cases of `test_missing` in Task 1 and `k` of 1 and 3: the missing point's distances are all `inf` and its indices all `kdtree.n_points`.
- `test_other_points_answer_as_alone[k]`, `k` of 1 and 3: the answer of each present point equals `kdtree.query(lons[i], lats[i], k=k)` for it alone (`np.testing.assert_array_equal`).
- `test_beyond_the_bound`: with `distance_upper_bound=1e-9` and a NaN longitude at index 1, the present points and the missing point all answer `(inf, kdtree.n_points)`.
- `test_every_point_missing[k]`: all three masked give `inf` and `kdtree.n_points` everywhere, of shape `(3,)` for `k=1` and `(3, 2)` for `k=2`, float64 and uint32 (Review Focus 2).
- `test_a_tree_of_centres`: `KDTree(lam_uk, preference="center")` answers a missing point with index `lam_uk.n_cells` (Review Focus 1).
- `test_a_grid_of_points`: `lons` and `lats` of shape `(2, 2)` with `[0, 1]` masked answer four rows, row 1 missing and each other row as `kdtree.query` of its point alone (Review Focus 3).
- `test_a_masked_quantity`: lons as `UREG.Quantity(np.ma.masked_array(lons, mask=[0, 1, 0]), "degree")` and lats as a quantity answer what the plain masked arrays answer (Review Focus 5).
- `test_infinite_refused[name]`: an `inf` longitude or latitude raises `match=r"'lons' cannot be infinite"`, or `'lats'`.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/search/test_missing_positions.py -q`
Expected: FAIL. A masked point answers the cell under its mask, a NaN one answers index 4294967295, and an infinite one is not refused. `test_other_points_answer_as_alone` passes already: it guards what must not change, and Task 4 watches it fail by mutation.

- [ ] **Step 3: Implement in `KDTree.query`**

After `_lonlats`, compute `missing = _missing_positions(lons, lats, x_name="lons", y_name="lats")`, raveled to one entry for each row of `xyz` (broadcast first with a `zlevel` array that `_to_cartesian` broadcasts the positions to). With nothing missing, return pykdtree's answer as today. Otherwise query `xyz[~missing]` and scatter its answers into arrays of pykdtree's dtypes, of shape `(N,)` or `(N, k)`, filled with `np.inf` and `self._n_points` (call 6). The docstring's Returns says what a missing point answers, and a Raises section names the `ValueError` for an infinite coordinate.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/search tests/units -q`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/search.py tests/search/test_missing_positions.py
git add tests/search/test_missing_positions.py
pixi run --frozen -e geovista git commit -am "fix: answer that a missing point of a query has no neighbour"
```

### Task 3: A Single Position Refuses a Missing One

**Files:**
- Modify: `src/geovista/search.py` (`find_nearest_cell` and its docstring)
- Modify: `src/geovista/geoplotter.py` (`GeoPlotterBase.view_poi` and its docstring)
- Modify: `tests/search/test_missing_positions.py`, `tests/geoplotter/test_view_poi.py`

**Interfaces:**
- Consumes: `_refuse_missing_poi` (Task 1).

- [ ] **Step 1: Write the failing tests**

Each holds positions spec §2 decision 4, in its docstring.

In `tests/search/test_missing_positions.py`, on `lam_uk`:
- `test_find_nearest_cell_refuses[x, y, named]`: `x` or `y` as `np.ma.masked` or `np.nan`, the other present, raises `match=r"point-of-interest is missing, as 'x' is masked or NaN"` or `'y'`. Both missing match `'x' and 'y' are`.
- `test_find_nearest_cell_refuses_a_masked_quantity`: `x=UREG.Quantity(np.ma.masked_array(30.0, mask=True), "degree")`, `y=UREG.Quantity(52.0, "degree")` names `'x'` (Review Focus 5).
- `test_find_nearest_cell_refuses_on_a_map`: `lam_uk` transformed with `transform_mesh(lam_uk, "+proj=eqc")`, given `x=np.nan`, names `'x'`.
- `test_find_nearest_cell_refuses_infinite`: `x=np.inf` raises `match=r"'x' cannot be infinite"`.

In `tests/geoplotter/test_view_poi.py`, on a `GeoPlotter()` with `lam_uk` added:
- `test_refuses_missing[x, y, named]`: as `test_find_nearest_cell_refuses`, through `p.view_poi(x=..., y=...)`, and the camera's position is unchanged afterwards.
- `test_one_coordinate_given_missing[given]`: `view_poi(x=np.ma.masked)` and `view_poi(x=np.nan)` match `as 'x' is masked`, and `view_poi(y=np.nan)` matches `as 'y' is masked` (call 4, Review Focus 4).
- `test_refuses_infinite`: `view_poi(x=np.inf, y=0.0)` raises `match=r"'x' cannot be infinite"`.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/search/test_missing_positions.py tests/geoplotter/test_view_poi.py -q`
Expected: FAIL. `find_nearest_cell` answers `[0]`, and `view_poi` moves the camera.

- [ ] **Step 3: Implement**

`find_nearest_cell` calls `_refuse_missing_poi(px, py, x_name="x", y_name="y")` after `_coordinates`. `view_poi` fills a coordinate it is not given with plain 0, or `given.units * 0` for a quantity (call 4), then calls `_refuse_missing_poi` after `_coordinates` and before reading either as a float. Each docstring gains a Raises section naming the `ValueError` for a masked, NaN or infinite `x` or `y`.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/search tests/geoplotter tests/units -q`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/search.py src/geovista/geoplotter.py tests/search/test_missing_positions.py tests/geoplotter/test_view_poi.py
pixi run --frozen -e geovista git commit -am "fix: refuse a missing point-of-interest in find_nearest_cell and view_poi"
```

### Task 4: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (§4.1, §4.3, §9 row 1, §11)
- Create: `changelog/<PR>.bugfix.rst`

- [ ] **Step 1: Watch each clause fail when it regresses**

Mutate one at a time, run the named test, see it fail, and revert:
- the index of a missing point is `self._n_points - 1`: `test_missing_point_has_no_neighbour`;
- its distance is 0: `test_missing_point_has_no_neighbour`;
- the missing points are queried with the rest: `test_missing_point_has_no_neighbour` and `test_other_points_answer_as_alone`;
- the present answers are scattered in reverse order: `test_other_points_answer_as_alone`;
- `find_nearest_cell` makes no refusal: `test_find_nearest_cell_refuses`;
- `view_poi` makes no refusal: `test_refuses_missing`;
- `_refuse_missing_poi` always names `'x'`: `test_refuse_missing_poi` and `test_find_nearest_cell_refuses`;
- `view_poi` fills with `0 * given` again: `test_one_coordinate_given_missing`.

- [ ] **Step 2: Amend the specification, humanized**

§4.1: a masked infinite value is missing, not refused, as the value under a mask is never read (call 3). §4.3: given one coordinate, `view_poi` fills in the other as a present 0, in the units of the one given, so its refusal names only the coordinate the caller gave (call 4).

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py tests/test_status_references.py tests/test_renumbering.py`, then `pixi run --frozen -e test check-spec-renumbering`.
Expected: the tests pass, and no citation went stale.

```bash
pixi run --frozen -e geovista git commit -am "docs: amend the positions spec for the calls row 1 made"
```

- [ ] **Step 3: Run the whole suite and the docs build, on the committed tree**

Run: `CI=true GALLIUM_DRIVER=llvmpipe pixi run --frozen -e test-py313 tests-unit`, then the same with `-e test-py314`, then the strict `sphinx-build` of `AGENTS.md` with `--fail-on-warning --keep-going`.
Expected: PASS, with no new skips and no image baseline regenerated, and the build succeeds.

- [ ] **Step 4: Open the pull request**

Push `fix/missing-positions-queries` and open it, titled `fix: answer and refuse missing positions in the queries (positions spec row 1)`, with the labels of the Global Constraints. Its body is humanized, names {issue}`2849` without a closing keyword, and lists calls 1 to 8. If its number is not `<PR>`, correct row 1's citation in its own commit.

- [ ] **Step 5: Write the fragment, and mark the decisions and the row**

`changelog/<PR>.bugfix.rst`, humanized, citing `geovista.search.KDTree.query`, `geovista.search.find_nearest_cell` and `geovista.geoplotter.GeoPlotterBase.view_poi` by their documented paths, and naming the row as `row 1 of positions spec §9`. It says that a query answers a point-of-interest whose longitude or latitude is masked or NaN with a distance of `inf` and an index equal to the number of points in the tree, that `find_nearest_cell` and `view_poi` refuse such a point, naming the coordinate, and that all three refuse an infinite coordinate.

In §11, §2 decision 3 becomes ``✅ verified (<DATE>, {pull}`<PR>`)`` with evidence `tests/search/test_missing_positions.py`, and §2 decision 4 the same with `tests/geoplotter/test_view_poi.py` and `tests/search/test_missing_positions.py`. Decisions 1 and 2 stay pending, for rows 2 to 5. Last, row 1 of §9 becomes ``✅ landed (<DATE>, {pull}`<PR>`)``. `<DATE>` is the day of this commit.

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py <PR> "changelog/<PR>.bugfix.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>`, then the strict docs build again.
Expected: the fragment passes, the tests pass, every status reference holds, and the fragment's references resolve.

- [ ] **Step 6: Commit and push**

```bash
git add changelog/<PR>.bugfix.rst
pixi run --frozen -e geovista git commit -am "docs: mark positions spec row 1 landed, and add the fragment"
git push
```
