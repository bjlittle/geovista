# Heights in the Scene Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 2 of heights spec §9, and with it row 3 of globe spec §9. `GeoPlotter.add_mesh` and `GeoPlotter.add_points` take `height=`, `depth=` and `vertical_units=`, and a scene draws a mesh with heights that records another globe from its heights, at the scene's globe. The same pull request settles heights spec §8 item 4 ({issue}`2838`): `mesh.gv.height` and `mesh.gv.depth` return `pint` quantities.

**Architecture:** Row 1 built every piece a scene needs: `_heights` reads what is given, `_for_points` fits it to the points, `_record_heights` stores it, `_on_globe` places points on the sphere and `transform._heights_z` above a map. The scene gains one private helper, `_place_by_heights`, which rebuilds a mesh's points from its heights at a globe, on the sphere or on a map. `add_mesh` records heights on its copy and places it with that helper. `_at_scene_globe` uses the same helper in place of the ratio of render radii, for a mesh with heights. `add_points` passes heights to `from_points` or on to `add_mesh`. `geovista.units` gains a private constructor for a quantity of lengths, which the accessor returns.

**Tech Stack:** `pyvista` 0.49.2, NumPy 2.5.4, `pint` 0.26.2 through `geovista.units`, pytest.

**Spec:** `docs/src/developer/specs/2026-10-28-heights-as-data-design.md` (`heights spec §…`): §2 decisions 4, 5 and 7, §4.1 to §4.4, §6, §8 item 4, §9 row 2 and §11. Also globe spec §2 decision 7 and row 3 of globe spec §9, and scene spec §2 decision 8, whose verification is pending on this row.

## Global Constraints

- Heights are metres above mean sea level, in the point array `gvHeight`, float64, set with `set_array` so they never become the active scalars (heights spec §2 decision 1, §4.1).
- `add_mesh(mesh, height=...)` writes the heights to the copy it draws, never to the mesh given (§4.2).
- A point is drawn at a radius of `s (R + V(h))` on the globe, and at `z = V(h)` in the length unit of the CRS on a map, or the angle `V(h)` subtends at `R` where the axes are angular. A missing height is drawn as 0 (§4.3).
- A scene's globe is fixed when the scene is made, and positions are built from heights when a mesh is added (§2 decision 7).
- Refused with a `ValueError` naming what was given (§4.4): `height=` with `depth=`; heights given to a mesh that carries them, to `add_mesh` or, as a cloud, to `add_points`; heights with a z-level other than 0, including a cloud whose points carry levels other than 0; heights for each cell; an infinite height; an array fitting neither the points nor the whole mesh; a height that is not a length; `vertical_units` with a quantity or with no height; heights with a CRS whose axis is "Ellipsoidal height".
- `mesh.gv.height` and `mesh.gv.depth` return a quantity in metres in `pint`'s application registry, whose magnitude is a float64 array that cannot be written, or `None` (call 1).
- Building a mesh or drawing a scene with heights given as plain numbers imports no `pint`. Reading heights back does, as reading `Globe.radius` does.
- No new public name. `mypy` strict over the whole package, with no new override. Warnings are errors under pytest. NumPy docstrings, no `.. versionchanged::`.
- Every heights test of the scene holds at a render radius of 1 and at the Earth's radius (§6, the radius).
- Commit through `PATH="$PWD/.pixi/envs/geovista/bin:$PATH" git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: enhancement` and `agentic`, and closes {issue}`2838` and no other issue.
- A test named as evidence in §11 cites its decision in its docstring, as "Holds heights spec §2 decision 5." (ledger spec §3.4).
- Cite a specification section in plain text (`heights spec §4.2`), never with a `{ref}` role.

## Calls Made in This Plan

Call 1 was put to {user}`bjlittle`; the rest are mine.

1. **Heights read back are quantities.** {user}`bjlittle` chose on 2026-11-10, of the two answers §8 item 4 offers, that `mesh.gv.height` and `mesh.gv.depth` return `pint` quantities, as scene spec §2 decision 8 asks, over an exception that keeps `pint` unloaded. No decision is retired. §4.1 is edited to say so, and the item is resolved. `tests/bridge/test_import.py` stops reading heights back in its script, which now checks that building with plain heights imports no `pint`.
2. **Heights given to `add_mesh` are placed at the scene's globe, whatever the mesh records.** Its points are rebuilt from their directions and their heights, on the sphere, or given a `z` from their heights on a map in the scene's CRS. A mesh that records no globe, or no CRS, is placed the same way, since heights given to the scene say where to draw it (§2 decision 7). A mesh in another CRS is placed the same way first, in its own CRS, and then rebuilt by `transform_mesh` at the scene's, as row 1 built it.
3. **One helper places by heights.** `_place_by_heights(mesh, globe, /) -> None`, a module function in `geoplotter.py`, rebuilds the points of a mesh that carries heights at `globe`, in place, and records the globe: through `from_cartesian` and `globe._on_globe` when the mesh is not projected, and by setting its third column to `transform._heights_z(globe, heights, crs)` when it is. `add_mesh` and `_at_scene_globe` both call it, so the two cannot disagree.
4. **A mesh with heights that records another globe** is rebuilt at the scene's, on the globe and on a map, in place of the ratio of render radii that row 2 of scene spec §9 left (§4.3). A mesh with heights that records the scene's globe or none is drawn where its points lie, as today.
5. **Any dataset takes heights.** A `StructuredGrid` from `to_structured_grid`, which `add_mesh` does not cast, takes `height=` and is placed by the same helper, as the spec names no exception.
6. **The refusals.** Heights given to a mesh that carries them: `"The mesh given carries heights of its own, and heights are given once, got 'height'."`, naming `'depth'` when that was given. A z-level with heights uses row 1's `_refuse_zlevel`. A cloud whose points carry levels other than 0, read from `from_cartesian`'s third column, or from `gvZLevel` on a map: `"A height and a z-level are never given together, and the point cloud given carries z-levels other than 0."`. Everything else is `_heights`' and `_for_points`', as row 1 words it. The refusals come before any copy is made.
7. **`add_points`.** Given `xs` and `ys`, it passes `height`, `depth` and `vertical_units` to `Transform.from_points`, which places the points and drops a missing point with its height. Given `points`, it passes them to `add_mesh`, after refusing a z-level other than 0 with them, since that path drops `zlevel` today.
8. **A quantity of lengths.** `geovista.units._as_lengths(metres: NDArray[np.float64], /) -> Quantity` builds the quantity in the application registry, keeping the array it is given, as `as_quantity` does for one value. The accessor gives it a read-only copy, and for a depth the negation, made read-only before it is wrapped.
9. **Evidence.** `tests/geoplotter/test_add_mesh_heights.py` (new) for `add_mesh` and the scene's globe, `tests/geoplotter/test_add_points.py` for `add_points`, `tests/accessor/test_heights.py` for the quantities. Heights spec §2 decisions 4, 5 and 7, globe spec §2 decision 7 and scene spec §2 decision 8 are verified. Globe spec §2 decision 1 stays pending on rows 4 and 5.
10. **One fragment, `2942.feature.rst`.** The branch is `feat/heights-in-the-scene`, and the plan is the first commit of draft pull request {pull}`2942` (workflow rule 2.3), which marks both rows in progress (workflow rule 2.4).

## Review Focus

1. **A mesh that has no data.** `gvHeight` must not become its active scalars, or the scene colours it by height. `test_heights_are_never_the_active_scalars` (Task 3).
2. **A texture with heights.** `add_mesh(mesh, height=..., texture=...)` cuts the antimeridian, adding points along chords; they must lie at their heights. `test_texture_cut_points_lie_at_their_heights` (Task 3).
3. **A mesh with heights on a map scene, recording another globe.** Its `z` follows the scene's exaggeration, not the one it records. `test_another_globe_on_a_map` (Task 4).
4. **Masked heights.** `add_mesh(mesh, height=np.ma.masked_array(...))` draws a masked height at sea level and reads it back as NaN. `test_a_masked_height_is_drawn_at_sea_level` (Task 3).
5. **Plain heights stay `pint`-free in the scene.** `add_mesh(..., height=[...])` and `add_points(..., height=[...])` on a scene import no `pint`. `test_drawing_heights_imports_no_pint` (Task 5).

---

Measured on 2026-11-10 at `b623a468` (`main` after {pull}`2940`), with Python 3.14.10, NumPy 2.5.4, `pyvista` 0.49.2 and `pint` 0.26.2:

- `Transform.from_points` of heights `[1000, -4000, 0]` at `Globe(exaggeration=100)` puts its points at radii `1.01568, 0.93729, 1`. Added to a scene at `Globe()`, it is drawn at those radii, where the formula gives `1.00016, 0.99937, 1`: the render radii match, so the ratio leaves it unmoved.
- `add_mesh(pv.Sphere(), height=10.0)` and `add_points(xs=..., ys=..., height=...)` raise `TypeError: "height" is an invalid keyword argument for '_common_arg_parser'`, from `pyvista`.
- `mesh.gv.height` returns a NumPy array. `import geovista` loads no `pint`, and `import geovista.bridge` does, through the lazy proxy of `geovista.units`, which `tests/bridge/test_import.py` counts only once it has run.
- A `pint` quantity of a read-only array shares its memory, and both `q[0] = ...` and `q.magnitude[0] = ...` raise `ValueError: assignment destination is read-only`. Its negation is writeable.

### Task 1: The Plan, and Both Rows in Progress

**Files:**
- Create: `docs/src/developer/plans/2026-11-10-heights-in-the-scene.md` (this plan)
- Modify: `docs/src/developer/specs/2026-10-28-heights-as-data-design.md` (§9 row 2)
- Modify: `docs/src/developer/specs/2026-10-26-globe-heights-layers-design.md` (§9 row 3)

- [ ] **Step 1:** Set row 2 of heights spec §9 and row 3 of globe spec §9 to `` 🚧 in progress ({pull}`2942`) ``.
- [ ] **Step 2:** Run `pixi run --frozen -e geovista pre-commit run --files <the three paths>`. Expected: pass.
- [ ] **Step 3:** Commit, push, and open draft pull request {pull}`2942` with `--label agentic --label "type: enhancement"`. Confirm its number is 2942, or correct the plan and rows to the number given.

### Task 2: Heights Read Back as Quantities

**Files:**
- Modify: `src/geovista/units.py`, `src/geovista/accessor.py` (`height`, `depth`)
- Modify: `docs/src/developer/specs/2026-10-28-heights-as-data-design.md` (§4.1, §8 item 4)
- Test: `tests/accessor/test_heights.py`, `tests/bridge/test_import.py`, and every test reading `mesh.gv.height` or `mesh.gv.depth` as an array: `tests/bridge/test_heights.py`, `tests/bridge/test_to_structured_grid.py`, `tests/core/test_carried_heights.py`, `tests/core/test_resize.py`, `tests/transform/test_heights.py`

**Interfaces:**
- Produces: `geovista.units._as_lengths(metres: NDArray[np.float64], /) -> Quantity`; `mesh.gv.height -> Quantity | None`, `mesh.gv.depth -> Quantity | None`.

- [ ] **Step 1: Write the failing tests** in `tests/accessor/test_heights.py`:

```python
def test_height_is_a_quantity_in_metres():
    """Holds scene spec §2 decision 8."""
    import pint

    mesh = Transform.from_1d([0.0, 10.0], [0.0, 10.0], height=[1.0, 2.0, 3.0, 4.0])
    height = mesh.gv.height
    assert isinstance(height, pint.Quantity)
    assert height._REGISTRY is pint.application_registry.get()
    np.testing.assert_array_equal(height.m_as("m"), [1.0, 2.0, 3.0, 4.0])
    assert height.magnitude.dtype == np.float64
    np.testing.assert_array_equal(mesh.gv.depth.m_as("m"), [-1.0, -2.0, -3.0, -4.0])


@pytest.mark.parametrize("name", ["height", "depth"])
def test_quantities_cannot_be_written(name):
    """Neither the quantity nor its magnitude can be written."""
    import pint

    mesh = Transform.from_1d([0.0, 10.0], [0.0, 10.0], height=1.0)
    value = getattr(mesh.gv, name)
    with pytest.raises(ValueError, match="read-only"):
        value[0] = 5 * pint.application_registry.get().m
    with pytest.raises(ValueError, match="read-only"):
        value.magnitude[0] = 5.0
```

Update the existing tests of the file and the readers listed under **Test** to read `.m_as("m")`, and remove `mesh.gv.height, mesh.gv.depth, cloud.gv.height, cloud.gv.depth` from the script of `tests/bridge/test_import.py`, renaming its test `test_building_with_plain_heights_imports_no_pint`.

- [ ] **Step 2:** Run `pixi run --frozen -e geovista pytest tests/accessor/test_heights.py -q`. Expected: the two new tests fail, as `height` is an `ndarray`.
- [ ] **Step 3:** Implement `_as_lengths` in `geovista/units.py`, beside `as_quantity` and reading the application registry the same way, and return it from `height` (a read-only copy of `_carried_heights`) and `depth` (the negation, made read-only first). Update both docstrings' **Returns** to `pint.Quantity or None`, saying the first read imports `pint`.
- [ ] **Step 4:** Edit heights spec §4.1: "`mesh.gv.height` returns the heights, as a `pint` quantity in metres whose float64 magnitude cannot be written, or `None` …", and set heights spec §8 item 4 to `` 🏁 Resolved (2026-11-DD, {pull}`2942` · 🔎 2026-11-03, {pull}`2826` · 🎫 {issue}`2838`) ``, its text ending "They return quantities, as scene spec §2 decision 8 asks, chosen by {user}`bjlittle` on 2026-11-10."
- [ ] **Step 5:** Run `pixi run --frozen -e geovista pytest tests/accessor tests/bridge tests/core tests/transform tests/globe -q`. Expected: pass.
- [ ] **Step 6:** Commit.

### Task 3: Heights Given to `add_mesh`

**Files:**
- Modify: `src/geovista/geoplotter.py` (`add_mesh`, new `_place_by_heights`)
- Test: `tests/geoplotter/test_add_mesh_heights.py` (new)

**Interfaces:**
- Consumes: `globe._heights`, `_for_points`, `_record_heights`, `_carried_heights`, `_refuse_zlevel`, `_on_globe`; `transform._heights_z`; `common.from_cartesian`.
- Produces: `GeoPlotterBase.add_mesh(mesh, /, *, height=None, depth=None, vertical_units=None, zlevel=None, zscale=None, rtol=None, atol=None, **kwargs)`, with `height` and `depth` typed `ArrayLike | Quantity | None` and `vertical_units: str | None`; `_place_by_heights(mesh: pv.DataSet, globe: Globe, /) -> None`.

- [ ] **Step 1: Write the failing tests.** A reference `_radii(heights, globe)` computes `s (R + V(h))` with NumPy alone, as `tests/transform/test_heights.py` computes `V(h)`, and `RADII = [1.0, 6378137.0]` parametrizes every test that places points. The actor's mesh is `actor.mapper.dataset`.

- `test_drawn_at_the_scenes_globe_by_the_formula[radius]`: a `from_1d` grid at `Globe()`, added with `height=HEIGHTS` to a scene at `Globe(render_radius=radius, exaggeration=20, exaggeration_below=100)`, is drawn at `_radii`; `drawn.gv.height.m_as("m")` equals `HEIGHTS`, NaN included. "Holds heights spec §2 decision 4."
- `test_depth_is_a_negative_height`: `depth=d` draws the points `height=-d` draws.
- `test_vertical_units`: `height=[1, 2, ...]` with `vertical_units="km"`, and a quantity in feet from a registry of its own, read back in metres.
- `test_on_a_map_by_the_formula[radius]`: on a scene with `crs="+proj=eqc"`, the drawn `z` is `V(h)` in metres; with `"+proj=eqc +units=km"`, in kilometres.
- `test_a_mesh_without_a_globe_or_crs`: `pv.Sphere()` with `height=1000.0` is drawn at `_radii`, warning only as today that it has no CRS.
- `test_the_mesh_given_is_unchanged`: points, `point_data` keys and `field_data` of the mesh given are as before.
- `test_heights_are_never_the_active_scalars`: on a mesh with no data, and on one with cell data, the drawn mesh's active scalars are what they were before.
- `test_a_masked_height_is_drawn_at_sea_level`.
- `test_texture_cut_points_lie_at_their_heights`: a global `from_1d` grid with `texture=natural_earth_1()` and `height=1000.0`; every drawn point lies at `_radii(1000.0)`.
- `test_a_structured_grid_takes_heights`: a `pv.StructuredGrid` of points on the unit sphere, with a WGS 84 CRS and no heights, given `height=...`, is drawn at `_radii`.
- `test_refuses[case]`, each `ValueError` matching its message, before any copy is made: heights given to a mesh with `gvHeight` (both keywords); `height` with `depth`; `height` with `zlevel=1`; a cloud from `from_points(..., zlevel=1)` given `height`; heights for each cell; `inf`; an array of another size; `vertical_units="hPa"`; `vertical_units` with a quantity; `vertical_units` alone; a mesh whose CRS is `EPSG:4979`. "Holds heights spec §2 decision 5."

- [ ] **Step 2:** Run `pixi run --frozen -e geovista pytest tests/geoplotter/test_add_mesh_heights.py -q`. Expected: fail with `TypeError: "height" is an invalid keyword argument`.
- [ ] **Step 3:** Implement. In `add_mesh`, after the cast, read `_heights(height, depth, vertical_units, crs=from_wkt(mesh))` for a dataset; when there are heights, refuse as call 6, copy the mesh, record `_for_points(heights, mesh.n_points, mesh.n_cells)` on the copy, and place it with `_place_by_heights(copy, self.globe)`, before any seam cut or transform, so that the cut places the points it adds at the scene's globe and `transform_mesh` rebuilds from the heights. Add the three parameters to the docstring.
- [ ] **Step 4:** Run the tests. Expected: pass. Then `pixi run --frozen -e geovista pytest tests/geoplotter tests/plotting -q -m "not image"`: pass.
- [ ] **Step 5:** Commit.

### Task 4: A Mesh With Heights at Another Globe

**Files:**
- Modify: `src/geovista/geoplotter.py` (`_at_scene_globe`)
- Test: `tests/geoplotter/test_add_mesh_heights.py`

- [ ] **Step 1: Write the failing tests**, each at both radii.

- `test_another_globe_on_the_sphere[recorded]`: a grid with `HEIGHTS` built at a globe that differs from the scene's in its Earth radius, its render radius, its `exaggeration` or its `exaggeration_below`, one case each, is drawn at the scene's `_radii`, recording the scene's globe. "Holds heights spec §2 decision 7." and "Holds globe spec §2 decision 7."
- `test_another_globe_on_a_map`: the same mesh transformed to `+proj=eqc` at `Globe(exaggeration=100)`, added to an `eqc` scene at `Globe()`, is drawn at `z = V(h)` of the scene's globe.
- `test_the_scenes_globe_or_none_is_drawn_as_it_lies`: a mesh with heights recording the scene's globe, or no globe, is drawn with the points it has.
- `test_without_heights_the_ratio_stands`: a mesh without heights at `render_radius=2` is drawn scaled by the ratio, as today.

- [ ] **Step 2:** Run them. Expected: the first two fail at the recorded globe's radii, as measured above.
- [ ] **Step 3:** In `_at_scene_globe`, after the copy, call `_place_by_heights(mesh, self.globe)` when the mesh carries heights, and scale by the ratio of render radii only when it does not. Update its docstring.
- [ ] **Step 4:** Run `tests/geoplotter` and `tests/plotting` with `-m "not image"`. Expected: pass. A test that pinned the ratio for a mesh with heights is updated to the formula, and named in the pull request.
- [ ] **Step 5:** Commit.

### Task 5: Heights Given to `add_points`

**Files:**
- Modify: `src/geovista/geoplotter.py` (`add_points`)
- Test: `tests/geoplotter/test_add_points.py`, `tests/geoplotter/test_import.py`

- [ ] **Step 1: Write the failing tests.**

- `test_heights_with_xs_ys[radius]`: `add_points(xs=LONS, ys=LATS, height=[...])` is drawn at `_radii`; with `depth=` the negation; with `vertical_units="km"` in kilometres.
- `test_heights_drop_with_a_missing_point`: with `xs` masked at 1, the cloud drawn has three points and three heights, the dropped one's gone.
- `test_heights_with_points`: a cloud mesh from `from_points` without heights, given `height=` through `points=`, is drawn at `_radii`; one that carries heights is refused, naming `'height'`; one given `zlevel=1` with heights is refused.
- In `tests/geoplotter/test_import.py`, `test_drawing_heights_imports_no_pint`: the scene script adds `from_1d(...)` with `height=[...]` and `add_points(xs=..., ys=..., depth=[...])`, and asserts no `pint` ran.

- [ ] **Step 2:** Run them. Expected: fail with the `TypeError` of `pyvista`.
- [ ] **Step 3:** Add `height`, `depth` and `vertical_units` to `add_points`, passed as call 7 says, with their docstrings.
- [ ] **Step 4:** Run `tests/geoplotter -q`. Expected: pass.
- [ ] **Step 5:** Commit.

### Task 6: The Ledger, the Rows Landed, and the Fragment

**Files:**
- Modify: `docs/src/developer/specs/2026-10-28-heights-as-data-design.md` (§9 row 2, §11)
- Modify: `docs/src/developer/specs/2026-10-26-globe-heights-layers-design.md` (§9 row 3, §11)
- Modify: `docs/src/developer/specs/2026-10-27-globe-scene-design.md` (§11)
- Create: `changelog/2942.feature.rst`

- [ ] **Step 1: Prove each piece of evidence by breaking it** (workflow rule 2.6), one clause at a time, and watch a named test fail: heights not taken by `add_mesh`, or by `add_points` (heights §2 decision 4); heights given twice accepted, or `height` with `depth` (decision 5); a mesh with heights at another globe drawn at its own, for each of the four fields (decision 7, and globe §2 decision 7); `mesh.gv.height` returning an array, and `Globe.radius` returning a float (scene §2 decision 8). Record each break and the test it failed in the pull request.
- [ ] **Step 2:** In heights spec §11 set decisions 4, 5 and 7, in globe spec §11 decision 7, and in scene spec §11 decision 8 to `` ✅ verified (2026-11-DD, {pull}`2942`) ``, each with the test files that failed. Set both roadmap rows to `` ✅ landed (2026-11-DD, {pull}`2942`) ``.
- [ ] **Step 3:** Write `changelog/2942.feature.rst`: `GeoPlotter.add_mesh` and `add_points` take `height`, `depth` and `vertical_units`, a scene draws a mesh with heights from them at its own globe, and `mesh.gv.height` and `mesh.gv.depth` return quantities, citing heights spec §4.2 and ending ``(:user:`claude`)``.
- [ ] **Step 4:** Run `pixi run -e test check-spec-status 2942`, the strict incremental docs build, and then `CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e test-py314 tests-unit`. Expected: all pass, the image tests included.
- [ ] **Step 5:** Commit, push, confirm with `git ls-remote`, and ask {user}`bjlittle` to mark the pull request ready.
