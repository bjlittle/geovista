# Heights on a Mesh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 1 of heights spec §9. A mesh carries the height of each point in the point array `gvHeight`. The bridge takes `height=`, `depth=` and `vertical_units=`. `to_structured_grid` reads its `zs` as heights. `resize` and `transform_mesh` position a mesh from the heights it carries, on the globe and on a map. `mesh.gv.height` and `mesh.gv.depth` read them back, missing heights are drawn at sea level, heights survive the filters and `combine`, and the refusals of heights spec §4.4 hold.

**Architecture:** `geovista.globe` gains the private helpers that read heights given as keywords, check them, record them on a mesh and map them through a globe's vertical mapping. Every function that builds or positions a mesh calls them. On the globe a point lies at `s (R + V(h))`, built by `_to_cartesian` with the render radius and a level of `V(h) / R` at a `zscale` of 1. On a map, `transform.py` sets `z` from the heights in the unit of the target CRS. `GeoPlotter` is unchanged: its keywords are row 2.

**Tech Stack:** `pyvista` 0.49.1, VTK 9.7.1, NumPy 2.5.4, `pyproj` 3.8.0, PROJ 9.9.0, `pint` through `geovista.units`, pytest.

**Spec:** `docs/src/developer/specs/2026-10-28-heights-as-data-design.md` (`heights spec §…`): §2, §4.1 to §4.5, §6 and §9 row 1, with globe spec §4.4 and scene spec §4.4.

## Global Constraints

- `gvHeight` is a float64 point array, in metres above mean sea level, one value for each point, set with `point_data.set_array` so that it never becomes the active scalars. A mesh without it is at sea level (heights spec §4.1).
- A masked or NaN height is missing: stored as NaN and drawn as a height of 0. Only an infinite height is refused (heights spec §2 decision 3).
- `V(h)` is `exaggeration * h` at or above sea level and `exaggeration_below * h` below it. On the globe a point lies at a radius of `s (R + V(h))`. On a map it lies at `z = V(h)` in the length unit of the CRS's horizontal axes, or, where those are angular, at the angle `V(h)` subtends at `R`, in their angular unit (heights spec §4.3).
- `height=` and `depth=` are never given together, and heights are never given with a z-level other than 0. A z-level of `None`, 0 or an array of zeros counts as none (heights spec §2 decisions 5 and 6, §4.4).
- `resize` and `transform_mesh` take no heights, and `Transform.from_tiff` takes none (heights spec §2 decision 4, §4.2).
- `from_cartesian`'s third column is 0 for a mesh with heights (heights spec §2 decision 8).
- Heights for each cell are refused, naming {issue}`2728` (heights spec §2 decision 9).
- A CRS with an axis named "Ellipsoidal height" is refused only when heights are given (heights spec §2 decision 10, §3.4).
- `vertical_units` is a CF unit string read by `geovista.units.to_metres` (heights spec §2 decision 11).
- Heights given as plain numbers never import `pint` (scene spec §2 decision 8).
- Every image test passes against its existing baseline, none regenerated.
- `mypy` runs strict over the whole package, with no new override. Warnings are errors under pytest. Docstrings are NumPy style; a new public name carries `.. versionadded:: 0.6.0`, and `.. versionchanged::` is not used.
- Every test of a position holds at a render radius of 1 and at the Earth's radius, `RADII = [1.0, 6378137.0]` (heights spec §6).
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. Fragments credit ``(:user:`claude`)``. The pull request carries `type: enhancement` and `agentic`.
- Cite a specification section in plain text (`heights spec §4.3`), never with a `{ref}` role.

## Calls Made in This Plan

{user}`bjlittle` made calls 1 and 2 on 2026-10-29, before planning. The rest are made here. Calls 2, 6, 7 and 8 amend the heights specification, in Task 8.

1. **The row is bounded.** It is planned straight from the heights specification, the child specification of globe spec §9 row 3, and executed inline, with a self-review of the whole branch at the end.
2. **The Reykjanes examples state their exaggeration.** `grid/reykjanes` and `grid/reykjanes_contour` pass `zs` of 0 to 10,000 m, which today are drawn half a cell of latitude apart, an exaggeration of 22.338 (measured below). Read as heights at the default globe, the plume would lie almost flat. Both examples therefore build `globe = gv.Globe(exaggeration=22.34)` and pass it to `to_structured_grid` and to `GeoPlotter`, so that their images stand and row 2 will draw them the same way. This amends heights spec §4.5, which said row 3 changes no example. {user}`bjlittle` plans to redesign `to_structured_grid` once this row lands, so the row changes only what reading its `zs` as heights needs.
3. **The helpers live in `geovista.globe`.** That module owns the vertical mapping, every function that positions a mesh imports it already, and row 2's scene will call the same helpers. The `z` of a map lives in `transform.py`, beside `_earth_radius`, which `geovista.globe` cannot import.
4. **`GV_POINT_HEIGHT = "gvHeight"`** is public in `geovista.common`, beside `GV_POINT_ZLEVEL`, and in its `__all__`.
5. **Each refusal names the keyword and the value given,** such as `zlevel=2`, the unit `'hPa'`, or 12 values for 12 cells.
6. **An array of one value is one height for the whole mesh,** as a scalar is. Heights are refused as heights for each cell when their size is the number of faces given and not the number of points.
7. **A point cloud with heights carries no z-level.** `from_points` given heights records no `gvZScale`, and `transform_mesh` writes no `gvZLevel` for one. `from_cartesian` reports a third column of 0 for any mesh with `gvHeight`, whatever else it carries.
8. **`zscale` given with heights is ignored,** since it scales no z-level.
9. **Vectors built with heights** are built at the render radius, as they are with no z-level, so they keep their components (heights spec §4.5).
10. **`resize` rebuilds a mesh with heights** from its longitudes, latitudes and heights, and returns it unchanged only when it already records exactly the globe asked for. The check is exact: a new exaggeration on small heights moves the points by less than `np.allclose` resolves at the Earth's radius.
11. **`transform_mesh` with no transform to make moves no point,** with heights or without, as scene spec §4.2 has it.
12. **`combine` writes `gvHeight` apart from the point data the meshes share,** whenever any mesh has heights, with 0 for each point of a mesh without them.
13. **A `Transform` call copies the `gvHeight` of its mesh,** since `copy_structure` keeps no point data (measured below).
14. **One fragment, `<PR>.feature.rst`.** Removing `zlevel` and `zscale` from `to_structured_grid` breaks no release (heights spec §9).

## Review Focus

1. **A mesh with heights added to a scene on a map.** `add_mesh` passes `transform_mesh` a z-level of 0, or the zeros the seam cut carried, which must count as none. The mesh is drawn with `z = V(h)`, with no refusal. `test_heights_on_a_map_scene` (Task 6).
2. **Integer or float32 heights,** as bathymetry often arrives (`int16`). They are stored as float64, with the same values. `test_integers_read_as_float64` (Task 1).
3. **A round trip through a map.** A surface or a cloud with heights, projected and brought back at the same globe, lies where it started, with its heights unchanged. `test_round_trip` (Task 6).
4. **Heights given as nested lists.** They build the mesh that arrays do (typing spec §3.3). The `from_points_heights` case of `test_lists` (Task 3).
5. **A missing height on a map, and through the seam cut.** It is drawn at `z = 0`, and a point the cut adds between a missing height and a given one is drawn at 0 and reads back NaN. `test_missing_heights_on_a_map` (Task 6).

---

Measured on 2026-10-29 at `7491fea4`, with Python 3.14.9, `pyvista` 0.49.1, VTK 9.7.1 and NumPy 2.5.4, in the `geovista` environment:

- A `gvHeight` set with `set_array` survives `slice_cells`, `slice_mesh`, `slice_lines`, `cast_UnstructuredGrid_to_PolyData` of extracted cells, `BBox.enclosed`, `add_texture_coords(antimeridian=True)`, every mesh of `filters.remesh`, `MeridianSlice.extract`, `mesh.clean()` and `transform_mesh` to `"+proj=eqc"` with its seam cut. `slice_cells` interpolates it at the points it adds. None of them makes it the active scalars.
- `combine` drops it with `data=False`, and with `data=True` when one mesh has no `gvHeight`.
- `Transform(lons, lats)(data=...)` returns a mesh with no point data apart from its data.
- `name_reykjanes()` has 41 `zs` from 0 to 10,000 m, 250 m apart, as a masked array with no masked element. Its `ys` step by 0.10033446° on average, so `to_structured_grid` spaces the levels 8.7558 × 10⁻⁴ of the render radius apart, 5,584.59 m at the default globe, an exaggeration of 22.338362.
- `_vectors_to_cartesian` scales each vector by the radius its z-level lifts.
- `BRIDGE_CLEAN` is `False`, so a bridge mesh keeps the order of the points given unless asked to clean.
- `"+proj=eqc +units=km"` has a first axis in kilometres, with a factor of 1000. `"+proj=longlat +ellps=GRS80 +no_defs"` is geographic, in degrees, and not WGS84.

### Task 1: Reading Heights, and the Vertical Mapping

**Files:**
- Modify: `src/geovista/common.py` (`GV_POINT_HEIGHT`, `__all__`)
- Modify: `src/geovista/crs.py` (`_ellipsoidal_height`)
- Modify: `src/geovista/globe.py` (`_heights`, `_for_points`, `_refuse_zlevel`, `_record_heights`, `_carried_heights`, `_mapped`, `_on_globe`)
- Modify: `tests/conftest.py` (the `at_heights` fixture)
- Create: `tests/globe/test_heights.py`, `tests/globe/test_vertical.py`, `tests/crs/test__ellipsoidal_height.py`

**Interfaces:**
- Consumes: `Globe`, `units.to_metres`, `common._to_cartesian`.
- Produces, in `geovista.globe`:
  - `_heights(height: object, depth: object, vertical_units: str | None, /, *, crs: CRSLike | None = None) -> float | NDArray[np.float64] | None`: the heights in metres, NaN where missing, or `None` when neither is given.
  - `_for_points(heights: float | NDArray[np.float64], n_points: int, n_cells: int, /) -> NDArray[np.float64]`: one height for each point.
  - `_refuse_zlevel(zlevel: object, /) -> None`.
  - `_record_heights(mesh: pv.DataSet, heights: ArrayLike, /) -> None`.
  - `_carried_heights(mesh: pv.DataSet, /) -> NDArray[np.float64] | None`.
  - `_mapped(globe: Globe, heights: ArrayLike, /) -> NDArray[np.float64]`: `V(h)`, with a missing height as 0.
  - `_subtended(globe: Globe, heights: ArrayLike, /) -> NDArray[np.float64]`: `V(h) / R`, the angle in radians that `V(h)` subtends at `R`, so that `transform.py` never reads the private `Globe._radius`, which ruff's `SLF001` refuses in `src`.
  - `_on_globe(globe: Globe, lons: ArrayLike, lats: ArrayLike, heights: ArrayLike, /) -> NDArray[np.float64]`: the `(N, 3)` points, each argument read flattened.
- Produces, elsewhere: `GV_POINT_HEIGHT: str = "gvHeight"` in `geovista.common`; `_ellipsoidal_height(crs: CRSLike, /) -> bool` in `geovista.crs`; the fixture `at_heights(lons, lats, heights, globe) -> NDArray`, the reference points worked out with NumPy alone from the globe's public values: `V` by the formula with NaN as 0, `R = globe.radius.m_as("m")`, `r = globe.render_radius * (1 + V / R)`, and `x = r cos(lat) cos(lon)`, `y = r cos(lat) sin(lon)`, `z = r sin(lat)`, in degrees converted to radians.

- [ ] **Step 1: Write the failing tests**

`tests/globe/test_heights.py`:

```python
def test_metres_by_default():
    assert _heights(100, None, None) == 100.0
    np.testing.assert_array_equal(_heights([1, 2], None, None), [1.0, 2.0])


@pytest.mark.parametrize(
    ("value", "units", "metres"),
    [(1000, "ft", 304.8), (2, "km", 2000.0), (5, "m", 5.0)],
)
def test_vertical_units(value, units, metres):
    assert _heights(value, None, units) == pytest.approx(metres)


def test_a_quantity_from_any_registry():
    feet = pint.UnitRegistry().Quantity(1000, "foot")
    assert _heights(feet, None, None) == pytest.approx(304.8)


def test_depth_is_negated():
    assert _heights(None, 4000, None) == -4000.0
    assert _heights(None, -10, None) == 10.0
    assert _heights(None, 1000, "ft") == pytest.approx(-304.8)
```

Also, in the same module:

- `test_masked_and_nan_are_missing`: `np.ma.masked_array([1.0, 2.0, 3.0], mask=[0, 1, 0])` reads `[1.0, nan, 3.0]`, and a NaN stays NaN.
- `test_integers_read_as_float64`: `np.array([-4000, 0, 120], dtype=np.int16)` reads as float64 `[-4000.0, 0.0, 120.0]`.
- `test_none_given`: `_heights(None, None, None) is None`.
- The refusals, each a `ValueError`:
  - `test_height_with_depth`, matching `"height"` and `"depth"`;
  - `test_infinite[inf, -inf]`, matching `"infinite"`;
  - `test_not_a_length`, `vertical_units="hPa"`, matching `"'hPa' is not a length"`;
  - `test_vertical_units_with_a_quantity` and `test_vertical_units_alone`, each matching `"vertical_units"`;
  - `test_an_ellipsoidal_height[EPSG:4979]`, with `height=1`, matching `"Ellipsoidal height"`.
- `test_no_heights_with_an_ellipsoidal_height`: `_heights(None, None, None, crs="EPSG:4979") is None`.
- `test_a_gravity_related_height[EPSG:9705, EPSG:4326+3855]`: `_heights(1, None, None, crs=...) == 1.0`.
- `test_a_scalar_for_every_point`: `_for_points(5.0, 4, 1)` is `[5.0] * 4`.
- `test_one_value_for_the_whole_mesh`: `_for_points(np.array([5.0]), 4, 1)` is the same.
- `test_one_for_each_point`: a `(2, 2)` array is read in C order.
- `test_cells_are_refused`: 12 values for 20 points and 12 cells raise, matching `"2728"`.
- `test_points_win_over_cells`: 4 values for 4 points and 4 cells are read as points.
- `test_the_wrong_size_is_refused`: 7 values for 20 points raise, matching `"20 points"` and `"7"`.
- `test_zero_counts_as_none[None, 0, 0.0, zeros]`: `_refuse_zlevel` raises nothing.
- `test_a_zlevel_is_refused[2, [0, 1]]`: raises, matching `"z-level"` and the value.

`tests/globe/test_vertical.py`:

- `test_mapped`: with `Globe(exaggeration=20, exaggeration_below=100)`, `_mapped(globe, [1000, 0, -4000, nan])` is `[20000, 0, -400000, 0]`, and `_subtended` of the same is that over 6378137.0.
- `test_on_globe[r]`: for `Globe(render_radius=r, exaggeration=20, exaggeration_below=100)`, `_on_globe(globe, lons, lats, heights)` matches `at_heights` to `rtol=1e-12`, with heights of `[1000, 0, -4000, nan]` over four points.
- `test_recorded_never_active`: on `pv.PolyData` of four points with no data, `_record_heights` leaves `active_scalars_name` `None` and stores float64. On a mesh whose active point data is `"data"`, it stays `"data"`.
- `test_carried`: `_carried_heights(pv.Sphere()) is None`, and after `_record_heights(mesh, [1, 2, ...])` it returns those values as float64.

`tests/crs/test__ellipsoidal_height.py`: `EPSG:4979` is `True`, and `EPSG:4326`, `EPSG:9705`, `"EPSG:4326+3855"` and `"+proj=eqc"` are `False`.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/globe/test_heights.py tests/globe/test_vertical.py tests/crs/test__ellipsoidal_height.py -q`
Expected: FAIL, with `ImportError` for `_heights` and `_ellipsoidal_height`.

- [ ] **Step 3: Implement**

`_ellipsoidal_height` reads `pyproj.CRS.from_user_input(crs).axis_info` for an axis named `"Ellipsoidal height"`. `_heights` refuses in this order: both keywords given, `vertical_units` with neither, `vertical_units` with a quantity (`isinstance(value, units._Quantity)`, before `to_metres` can refuse it under the name `units`), then a CRS with an ellipsoidal height. It then reads the value through `to_metres(value, vertical_units)`, negates a depth, and refuses an infinite value, naming the first one's index for an array. `_mapped` uses `np.where(h >= 0, exaggeration * h, exaggeration_below * h)`, with NaN set to 0. `_subtended` divides it by `globe._radius`, never `globe.radius`, so that no `pint` is imported. `_on_globe` calls `_to_cartesian(np.ravel(lons), np.ravel(lats), radius=globe.render_radius, zlevel=_subtended(globe, np.ravel(heights)), zscale=1.0)`. `_record_heights` uses `mesh.point_data.set_array(np.asarray(heights, dtype=np.float64), GV_POINT_HEIGHT)`.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/globe tests/crs tests/common tests/units -q`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/common.py src/geovista/crs.py src/geovista/globe.py tests/conftest.py tests/globe/test_heights.py tests/globe/test_vertical.py tests/crs/test__ellipsoidal_height.py
git add tests/globe/test_heights.py tests/globe/test_vertical.py tests/crs/test__ellipsoidal_height.py
pixi run --frozen -e geovista git commit -am "feat: read heights, and map them through a globe"
```

### Task 2: Reading Heights Back

**Files:**
- Modify: `src/geovista/accessor.py` (`height`, `depth`)
- Modify: `src/geovista/globe.py` (`Globe.from_mesh`)
- Modify: `src/geovista/common.py` (`from_cartesian`)
- Create: `tests/accessor/test_heights.py`
- Modify: `tests/globe/test_from_mesh.py`, `tests/common/test_from_cartesian.py`

**Interfaces:**
- Consumes: `_record_heights`, `_carried_heights` (Task 1).
- Produces: the read-only properties `GeoVistaAccessor.height -> NDArray[np.float64] | None` and `GeoVistaAccessor.depth -> NDArray[np.float64] | None`, each with `.. versionadded:: 0.6.0`. `Globe.from_mesh` returns `None` for a mesh with `gvHeight` that records no globe and has no `gvRadius`. `from_cartesian` reports a third column of 0 for a mesh with `gvHeight`.

- [ ] **Step 1: Write the failing tests**

`tests/accessor/test_heights.py`, on `pv.Sphere()` given heights by `_record_heights`:

- `test_height_reads_back`: `[100, -4000, nan, ...]` read back from `mesh.gv.height`, as float64.
- `test_none_without_heights`: `pv.Sphere().gv.height is None`, and the same for `depth`.
- `test_depth_is_the_negation`: heights `[100, -4000, nan]` give a depth of `[-100, 4000, nan]`.
- `test_cannot_be_set[height, depth]`: `setattr(mesh.gv, name, ...)` raises `AttributeError`, matching `"cannot be set"`.
- `test_cannot_be_written[height, depth]`: `getattr(mesh.gv, name)[0] = 1.0` raises `ValueError`, and `mesh.point_data["gvHeight"]` is unchanged.
- `test_heights_stay_out_of_equality`: two meshes with the same globe and CRS and different heights have equal `gv`.

`tests/globe/test_from_mesh.py`, `test_heights_are_never_read_as_a_globe`: `pv.Sphere(radius=1.0)` given a height of 1000 at every point reads as `None`. With a `gvRadius` of 2 it reads `Globe(render_radius=2)`, and with `Globe(render_radius=3).to_mesh(mesh)` it reads that globe.

`tests/common/test_from_cartesian.py`, `test_a_mesh_with_heights_reports_no_level`: a cloud from `from_points(..., zlevel=[1, 2, 3])`, given heights by `_record_heights`, reads a third column of zeros.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/accessor/test_heights.py tests/globe/test_from_mesh.py tests/common/test_from_cartesian.py -q`
Expected: FAIL, with `AttributeError` for `height`, and the sphere with heights read at a globe.

- [ ] **Step 3: Implement**

`height` returns a float64 copy of `_carried_heights(mesh)` with `setflags(write=False)`, or `None`. `depth` returns the negation, made read-only the same way. Each setter raises `AttributeError`: heights say where a mesh's points are drawn, so they are given where the mesh is built, as `Transform.from_1d(..., height=...)`. `from_mesh` returns `None` after its `gvRadius` check when `GV_POINT_HEIGHT` is in the point data, citing scene spec §4.4 item 2 and heights spec §4.3 in a comment. `from_cartesian` leaves the z-level at zeros when `GV_POINT_HEIGHT` is in the point data.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/accessor tests/globe tests/common -q`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/accessor.py src/geovista/globe.py src/geovista/common.py tests/accessor/test_heights.py tests/globe/test_from_mesh.py tests/common/test_from_cartesian.py
git add tests/accessor/test_heights.py
pixi run --frozen -e geovista git commit -am "feat: read a mesh's heights and depths back, and never read its globe from them"
```

### Task 3: The Bridge Takes Heights

**Files:**
- Modify: `src/geovista/bridge.py` (`from_1d`, `from_2d`, `from_points`, `from_unstructured`, `Transform.__init__`, `Transform.__call__`)
- Create: `tests/bridge/test_heights.py`, `tests/bridge/test_import.py`
- Modify: `tests/bridge/test_lists.py`

**Interfaces:**
- Consumes: every helper of Task 1; `mesh.gv.height` and `mesh.gv.depth` (Task 2).
- Produces: `from_1d`, `from_2d`, `from_points`, `from_unstructured` and `Transform.__init__` each take `height: ArrayLike | Quantity | None = None`, `depth: ArrayLike | Quantity | None = None` and `vertical_units: str | None = None`, keyword-only. A `Transform` call carries the heights of its mesh (call 13).

- [ ] **Step 1: Write the failing tests**

`tests/bridge/test_heights.py` parametrizes `build` over `from_1d`, `from_2d`, `from_points`, `from_unstructured` and a `Transform` call, each with `clean=False` on small fixed coordinates whose points it knows in order, as the flattened `meshgrid(xs, ys, indexing="xy")` for `from_1d`. `HEIGHTS` holds one value for each point, mixing heights above and below sea level and one NaN.

- `test_reads_back_in_metres[build-given]`: `height=1000` with `vertical_units="ft"`, `height=pint.UnitRegistry().Quantity(1, "km")` and `height=1000.0` read back from `mesh.gv.height` as 304.8, 1000 and 1000 at every point.
- `test_placed_by_the_formula[build-r]`: at `Globe(render_radius=r, exaggeration=20, exaggeration_below=100)`, `mesh.points` matches `at_heights(lons, lats, HEIGHTS, globe)` to `rtol=1e-9`, and the mesh records the globe.
- `test_depth_gives_the_negated_height[build]`: the points of `build(depth=d)` equal those of `build(height=-d)`, and `mesh.gv.depth` is `d`.
- `test_missing_heights_at_sea_level[build]`: a masked height and a NaN read back as NaN, at the render radius.
- `test_never_the_active_scalars[build]`: with no data, `active_scalars_name` is `None`; with data, it is the data's name.
- `test_a_cloud_records_no_zscale`: `from_points(..., height=HEIGHTS)` has no `gvZScale`, and `from_cartesian` reads a third column of zeros (call 7).
- `test_vectors_keep_their_components`: `from_points(..., vectors=(u, v, w), height=1000.0)` has the vectors of the same call with no height (call 9).
- `test_the_factory_carries_heights[r]`: `Transform(LONS, LATS, height=h, globe=g)(data=...)` has the `gvHeight` and the points of `from_1d(LONS, LATS, height=h, globe=g)`.
- `test_threshold_keeps_the_sea_at_its_depths`, as heights spec §3.2 measured: `from_1d` over 5 longitudes and 4 latitudes, with cell data whose western column is masked and depths whose western column of points is masked, at `Globe(exaggeration_below=100)`. `mesh.threshold()` keeps 9 cells and 16 points, no NaN height, and each point at `at_heights` of its depth.
- The refusals, each a `ValueError` that names what was given, `[build]` where it applies: `height` with `depth`; `height` with `zlevel=2`, and with `zlevel=[0, 1]` for `from_points`; a height for each cell of `from_1d`, matching `"2728"`; the wrong number of heights; an infinite height; `vertical_units` alone; and `crs="EPSG:4979"` with heights, matching `"Ellipsoidal height"`. `crs="EPSG:4979"` with no heights builds as today.
- `test_zero_zlevel_with_heights`: `height=HEIGHTS` with `zlevel=0` builds.

`tests/bridge/test_lists.py` gains the case `"from_points_heights"`: `Transform.from_points` with `([0.0, 10.0], [0.0, 10.0])` and `{"data": [1.0, 2.0], "height": [10.0, -20.0]}`.

`tests/bridge/test_import.py`, `test_plain_heights_import_no_pint`, runs in a subprocess as `tests/globe/test_import.py` does: `Transform.from_1d([0, 10], [0, 10], height=[[1.0, 2.0], [3.0, 4.0]])`, `Transform.from_points([0, 10], [0, 10], depth=[5.0, 6.0])`, then `mesh.gv.height` and `mesh.gv.depth`, and asserts that no `pint` module is loaded.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/bridge -q`
Expected: FAIL, with `TypeError: ... unexpected keyword argument 'height'`.

- [ ] **Step 3: Implement**

`from_1d` and `from_2d` pass the three keywords on. `from_unstructured` reads `_heights(height, depth, vertical_units, crs=crs)` before transforming its points. When heights are given, it calls `_refuse_zlevel(zlevel)`, takes `_for_points(heights, xs.size, connectivity_array.shape[0])`, the faces given before any masked one is dropped, and places its points with `_on_globe`. It records them with `_record_heights` before it attaches data and cleans. `from_points` does the same over its flattened points with `n_cells=0`, builds its vectors with no z-level, and records no `gvZScale` (calls 7 to 9). `__init__` passes the keywords to the builder it calls. `__call__` copies the heights of `self._mesh` with `_record_heights`. Each docstring gains entries for `height` ("the height of each point above mean sea level"), `depth` ("positive downward, the negation of a height") and `vertical_units`, citing `geovista.units.to_metres`.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/bridge tests/pantry tests/globe tests/accessor -q`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/bridge.py tests/bridge/test_heights.py tests/bridge/test_import.py tests/bridge/test_lists.py
git add tests/bridge/test_heights.py tests/bridge/test_import.py
pixi run --frozen -e geovista git commit -am "feat: build bridge meshes at their heights and depths"
```

### Task 4: The Structured Grid's Levels Are Heights

**Files:**
- Modify: `src/geovista/bridge.py` (`to_structured_grid`)
- Modify: `src/geovista/examples/grid/reykjanes.py`, `src/geovista/examples/grid/reykjanes_contour.py`
- Create: `tests/bridge/test_to_structured_grid.py`

**Interfaces:**
- Consumes: `_heights`, `_on_globe`, `_record_heights` (Task 1).
- Produces: `to_structured_grid(xs, ys, zs, /, *, data=None, name=None, crs=None, globe: Globe | None = None, vertical_units: str | None = None) -> pv.StructuredGrid`, with no `zlevel` and no `zscale`.

- [ ] **Step 1: Write the failing tests**

`tests/bridge/test_to_structured_grid.py`, with `ZS = [0.0, 100.0, 1000.0, 5000.0]`, which are uneven:

- `test_levels_at_their_heights[r]`: at `Globe(render_radius=r, exaggeration=20)`, every point lies at `at_heights` of its level, and `grid.gv.height` holds each point's level, in the grid's point order.
- `test_levels_in_another_unit`: `zs=[0, 1, 3]` with `vertical_units="km"`, and `zs` as a `pint` quantity in feet, read back in metres.
- `test_a_grid_of_depths_passes_their_negation`: `zs=-np.array([0.0, 10.0, 50.0])` at `Globe(exaggeration_below=100)` lies below the render radius by the formula.
- `test_levels_must_be_finite[nan, inf, masked]`: raises `ValueError`, matching `"finite"`.
- `test_zlevel_is_gone[zlevel, zscale]`: each raises `TypeError`, naming the keyword.
- `test_heights_are_not_the_data`: with `data`, the active scalars are the data, and `grid.threshold()` thresholds on them.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/bridge/test_to_structured_grid.py -q`
Expected: FAIL: the levels are spaced evenly, whatever their heights.

- [ ] **Step 3: Implement, and give the examples their globe**

Read `zs` with `_heights(zs, None, vertical_units, crs=crs)` before the shape checks, and refuse any level that is not finite, naming its index: a level is a coordinate, so it cannot be missing. Build `meshgrid(xs, ys, zs, indexing="ij")` and place the points with `_on_globe`. Record the heights ravelled in the grid's point order, which is Fortran order, as `zv.ravel(order="F")`; `test_levels_at_their_heights` confirms it. Rewrite the docstring's `zs` entry as the heights of the bounds of the layers. Remove `zlevel` and `zscale`, with their entries and the TODO on vertical support.

In both Reykjanes examples, build `globe = gv.Globe(exaggeration=22.34)` and pass it to `to_structured_grid` and to `gv.GeoPlotter`. Put a comment above it saying that it draws the plume's 250 m levels as far apart as they were drawn before they were heights (call 2).

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/bridge -q`, then `CI=true LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe pixi run --frozen -e geovista pytest tests/plotting/test_examples.py -k reykjanes -q`
Expected: PASS, both examples against their existing images.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/bridge.py src/geovista/examples/grid/reykjanes.py src/geovista/examples/grid/reykjanes_contour.py tests/bridge/test_to_structured_grid.py
git add tests/bridge/test_to_structured_grid.py
pixi run --frozen -e geovista git commit -am "feat: read the levels of a structured grid as heights"
```

### Task 5: Resizing a Mesh with Heights

**Files:**
- Modify: `src/geovista/core.py` (`resize`)
- Modify: `tests/core/test_resize.py`

**Interfaces:**
- Consumes: `_carried_heights`, `_on_globe`, `_refuse_zlevel` (Task 1); `Globe.from_mesh` (Task 2); `height=` on the bridge (Task 3).
- Produces: `resize` positions a mesh with heights from them, with its signature unchanged.

- [ ] **Step 1: Write the failing tests**

In `tests/core/test_resize.py`, with `mesh = from_1d(LONS, LATS, height=HEIGHTS)` at `Globe()`:

- `test_heights_placed_by_the_formula[r]`: `resize(mesh, globe=Globe(render_radius=r, exaggeration=20, exaggeration_below=100))` matches `at_heights` to `rtol=1e-9`, records the globe, and reads back `HEIGHTS`.
- `test_a_new_mapping_moves_by_the_formula`: at `Globe(render_radius=6378137.0)`, heights of 1 m resized to `exaggeration=2` move each point 1 m outward, to `atol=1e-6` (call 10).
- `test_heights_lift_once`: a mesh with a height of 1000 at every point, its four globe fields deleted, reads as no globe, and `resize(mesh)` puts it at `1 + 1000 / 6378137.0` (heights spec §6).
- `test_the_same_globe_returns_the_mesh`: `resize(mesh) is mesh` when the mesh records `Globe()`.
- `test_a_zlevel_is_refused_with_heights`: `resize(mesh, zlevel=1)` raises `ValueError`, matching `"z-level"`; `zlevel=0` resizes.
- `test_a_cloud_with_heights[r]`: `from_points(..., height=HEIGHTS)` resized lies at `at_heights`, with no `gvZScale`.
- `test_missing_heights_at_sea_level`: NaN heights resize to the render radius.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/core/test_resize.py -q`
Expected: FAIL: a mesh with heights is scaled from its mean radius, and the z-level is accepted.

- [ ] **Step 3: Implement**

After resolving the globe, a mesh with `_carried_heights` calls `_refuse_zlevel(zlevel)`. It returns the mesh when `_records(mesh, globe)` holds. Otherwise it reads its longitudes and latitudes with `from_cartesian`, places them with `_on_globe`, copies unless `inplace`, records the globe and runs `sanitize_legacy` (call 10). Every other mesh takes the path it takes today.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/core tests/geoplotter -q`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/core.py tests/core/test_resize.py
pixi run --frozen -e geovista git commit -am "feat: resize a mesh from the heights it carries"
```

### Task 6: Transforming a Mesh with Heights

**Files:**
- Modify: `src/geovista/transform.py` (`transform_mesh`, `_heights_z`)
- Create: `tests/transform/test_heights.py`
- Modify: `tests/geoplotter/test_add_mesh.py`

**Interfaces:**
- Consumes: `_carried_heights`, `_mapped`, `_subtended`, `_on_globe`, `_refuse_zlevel` (Task 1); `height=` on the bridge (Task 3).
- Produces: `_heights_z(globe: Globe, heights: ArrayLike, crs: pyproj.CRS, /) -> NDArray[np.float64]` in `geovista.transform`: `_mapped` over the first axis's `unit_conversion_factor` for a projected CRS, and `_subtended(globe, heights) * _earth_radius(crs)` for a geographic one.

- [ ] **Step 1: Write the failing tests**

`tests/transform/test_heights.py`, at `Globe(render_radius=r, exaggeration=20, exaggeration_below=100)`:

- `test_on_a_map_by_the_formula[crs-r]`: a mesh built with `HEIGHTS` and transformed to `"+proj=eqc"` lies at `z = V(h)`; to `"+proj=eqc +units=km"`, at `V(h) / 1000`; and to `"+proj=longlat +ellps=GRS80 +no_defs"`, at `np.degrees(V(h) / 6378137.0)`. Each `V` is worked out in the test with NumPy, and each `z` is read beside the mesh's own `gvHeight`, since the seam cut reorders the points.
- `test_back_to_the_globe[r]`: a mesh built at a map's coordinates with `HEIGHTS`, transformed to `WGS84` at the globe, matches `at_heights` of its longitudes and latitudes.
- `test_round_trip[surface, cloud]`: transformed to `"+proj=eqc"` and back at the same globe, a mesh lies where it started to `rtol=1e-9`, its heights unchanged (Review Focus 3).
- `test_the_seam_cut_keeps_heights`: a global `from_1d` mesh with heights equal to `1000 * z` of its unlifted points, transformed to `"+proj=eqc"`, keeps `gvHeight` at every point, with no NaN.
- `test_missing_heights_on_a_map`: a NaN height is drawn at `z = 0` and reads back NaN, and so is a point the seam cut adds between a NaN height and a given one (Review Focus 5).
- `test_a_zlevel_is_refused_with_heights`: `transform_mesh(mesh, "+proj=eqc", zlevel=1)` raises `ValueError`, matching `"z-level"`. `zlevel=0` and `zlevel=np.zeros(mesh.n_points)` transform.
- `test_a_cloud_carries_no_levels`: a cloud with heights transformed to `"+proj=eqc"` has neither `gvZLevel` nor `gvZScale` (call 7).
- `test_no_transform_moves_no_point`: a `WGS84` mesh with heights transformed to `WGS84` at another globe keeps its points and its globe (call 11).
- `test_no_globe_is_the_default`: a mesh with heights whose four globe fields are deleted, transformed to `"+proj=eqc"`, lies at `z = h` and records `Globe()` (heights spec §4.3).

`tests/geoplotter/test_add_mesh.py`, `test_heights_on_a_map_scene`: `GeoPlotter(crs="+proj=eqc", off_screen=True).add_mesh(mesh)` of a mesh with heights draws `actor.mapper.dataset` with `z` equal to its own `gvHeight`, with NaN as 0, at the default globe (Review Focus 1).

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/transform/test_heights.py tests/geoplotter/test_add_mesh.py -q`
Expected: FAIL: on a map `z` is 0, and back on the globe each point is placed at the render radius.

- [ ] **Step 3: Implement**

`transform_mesh` reads `_carried_heights(mesh)` before it transforms, and when the mesh has heights it calls `_refuse_zlevel(zlevel)`. After the seam cut it reads the heights again from the mesh it now holds, whose cut has interpolated them. A `WGS84` target places the points with `_on_globe(globe, xs, ys, heights)`. Any other target sets `z` to `_heights_z(globe, heights, tgt_crs)`. A cloud with heights skips `_record_zlevels`. A mesh without heights takes the path it takes today.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/transform tests/geoplotter tests/core -q`, then `CI=true LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe pixi run --frozen -e geovista pytest tests/plotting -q`
Expected: PASS, every image against its existing baseline.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/transform.py tests/transform/test_heights.py tests/geoplotter/test_add_mesh.py
git add tests/transform/test_heights.py
pixi run --frozen -e geovista git commit -am "feat: transform a mesh from the heights it carries, on the globe and on a map"
```

### Task 7: Heights Through the Filters and `combine`

**Files:**
- Modify: `src/geovista/core.py` (`combine`)
- Create: `tests/core/test_carried_heights.py`

**Interfaces:**
- Consumes: `_record_heights`, `_carried_heights` (Task 1).
- Produces: `combine` carries `gvHeight` whatever its `data` (call 12).

- [ ] **Step 1: Write the failing tests**

`tests/core/test_carried_heights.py`. Each mesh is given heights of `1000 * z` of its points with `_record_heights`, without moving them. Every interpolation along a chord is linear in position, so every point of a result must carry `1000 * z` of its own position.

- `test_carried[case]`, over `slice_cells`, `slice_mesh`, `slice_lines` (on a `geodesic.line` across the antimeridian), `cast_UnstructuredGrid_to_PolyData` of extracted cells, `BBox.enclosed`, `add_texture_coords(antimeridian=True)`, each mesh of `filters.remesh` and `MeridianSlice.extract`. Each result carries float64 `gvHeight` equal to `1000 * points[:, 2]` to `atol=1e-9`, and it is never the active scalars.
- `test_combine_keeps_heights[data]`, with `data` `True` and `False`: one mesh with heights and one without combine to the first mesh's heights followed by zeros. Two meshes with heights combine to both, NaN kept. `gvHeight` is not the active scalars.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/core/test_carried_heights.py -q`
Expected: FAIL for `combine` alone, which drops the heights. Every other case passes as measured above, and guards it from here.

- [ ] **Step 3: Implement**

`combine` removes `GV_POINT_HEIGHT` from the point data the meshes share. When any mesh carries heights, it writes them with `_record_heights` before any clean, as each mesh's heights, or zeros for a mesh without them, in the order of their points.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/core tests/common tests/geodesic tests/filters -q`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/core.py tests/core/test_carried_heights.py
git add tests/core/test_carried_heights.py
pixi run --frozen -e geovista git commit -am "feat: carry heights through combine, and guard them through the filters"
```

### Task 8: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-10-28-heights-as-data-design.md` (§4.2, §4.3, §4.5, §9 row 1)
- Modify: `AGENTS.md` (the `globe.py` line of the architecture, staying under 200 lines)
- Create: `changelog/<PR>.feature.rst`

- [ ] **Step 1: Amend the specification, humanized**

§4.2: an array of one value is one height for the whole mesh, a height for each cell is one whose size is the number of faces given, and `zscale` given with heights is ignored (calls 6 and 8). §4.3: a point cloud with heights records no `gvZScale` and carries no `gvZLevel` on a map (call 7). §4.5: the gallery keeps its z-levels and hand-warped orography, except `grid/reykjanes` and `grid/reykjanes_contour`. Those give their scene and grid `Globe(exaggeration=22.34)`, the exaggeration their evenly spaced levels were drawn at, so their images stand (call 2). In `AGENTS.md`, the `globe.py` line becomes "The Globe, how a mesh records it, and its heights".

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py tests/test_status_references.py tests/test_renumbering.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-renumbering`.
Expected: the tests pass, and no citation went stale.

```bash
pixi run --frozen -e geovista git commit -am "docs: amend the heights spec for the calls row 1 made"
```

- [ ] **Step 2: Run the whole suite, on the committed tree**

Run: `CI=true LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe pixi run --frozen -e geovista tests-unit`
Expected: PASS, with no new skips and no image baseline regenerated. `test_option_version` fails on a dirty tree, so commit first.

- [ ] **Step 3: Build the docs strictly, after the suite**

Run the strict `sphinx-build` of `AGENTS.md`, with `-W --keep-going`.
Expected: the build succeeds, with the new docstrings and properties rendered.

- [ ] **Step 4: Open the pull request**

Push `feat/heights-on-a-mesh` and open it with the labels of the Global Constraints. Its body is humanized and lists calls 2 to 14, call 2 first.

- [ ] **Step 5: Write the fragment, and mark the row**

`changelog/<PR>.feature.rst`, humanized, citing `geovista.bridge.Transform`, `geovista.bridge.Transform.to_structured_grid` and `geovista.accessor.GeoVistaAccessor` by their documented paths. It says that a mesh carries the height of each point above mean sea level, that the bridge takes `height=`, `depth=` and `vertical_units=`, that `to_structured_grid` reads its `zs` as heights, that `mesh.gv.height` and `mesh.gv.depth` read them back, and that a missing height is drawn at sea level.

Mark heights spec §9 row 1 ``✅ landed (YYYY-MM-DD, {pull}`<PR>`)``.

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py <PR> "changelog/<PR>.feature.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>`, then the strict docs build again.
Expected: the fragment passes, the tests pass, every status reference holds, and the fragment's references resolve.

- [ ] **Step 6: Commit and push**

```bash
git add changelog/<PR>.feature.rst
pixi run --frozen -e geovista git commit -am "docs: mark heights spec row 1 landed, and add the fragment"
git push
```
