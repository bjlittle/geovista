# Globe Scene Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 2 of scene spec §9, and with it row 2 of globe spec §9: `globe=` in place of `radius=` on every function that sets the size of a sphere, `GeoPlotter(globe=...)` and `GeoPlotter.globe`, `combine` refusing meshes described differently, only current fields in every mesh returned or drawn, and the gallery, tests and documentation moved to `globe=`. It is breaking, and removes the stopgap that row 1 left in `geovista.common` (#2761).

**Architecture:** Every public function that took a `radius` takes `globe: Globe | None = None`, resolved by one private helper in `geovista.globe`. Inside, `geovista` keeps passing plain floats: the four conversion functions of `geovista.common` keep their float bodies as private functions, which internal code calls with a render radius. Each function that builds or positions a mesh records its globe with `Globe.to_mesh`, and each that works on a mesh reads one with `Globe.from_mesh`, which replaces the stopgap helpers `_read_radius` and `_write_radius`. `GeoPlotterBase` holds the scene's globe and draws every mesh at it.

**Tech Stack:** `pyvista` 0.49.1, VTK 9.7.1, NumPy 2.5.4, `pyproj`, `pint` 0.26.2 through `geovista.units`, pytest.

**Spec:** `docs/src/developer/specs/2026-10-27-globe-scene-design.md` (`scene spec §…`): §2 decisions 1, 2, 4, 5 and 8, §3.1, §4.2 to §4.5, §4.7, §4.8, §6 and §9 row 2, with globe spec §4.1, §4.4 and §9 row 2.

## Global Constraints

- Each function of scene spec §3.1, and `pantry.meshes.regular_grid` (call 2), takes `globe: Globe | None = None` where it took `radius`, except the methods of `GeoPlotter`. `radius=` is removed with no alias, so a caller still passing it gets a `TypeError` for an unexpected keyword (scene spec §2 decision 2, §4.2).
- `GeoPlotter` takes `globe=` when it is made, `Globe()` by default, and every layer it adds takes its geometry from that globe, the base layer, coastlines and graticule included. Its methods take no globe. `GeoPlotter.globe` reports it, read-only (scene spec §4.2).
- A function that builds a mesh uses `Globe()` when given none, and records the globe it used. A function given a mesh to work on uses the globe that mesh records (scene spec §4.4) when given none, and `Globe()` for a mesh with no globe. `KDTree.query` uses the globe of the mesh its tree was built from. `resize` takes the globe to resize a mesh to, and records it (scene spec §4.2, §4.4).
- A mesh added to a scene whose globe differs from the one it records is drawn at the scene's globe, and the mesh drawn records the scene's globe. On the globe that is a scale by the ratio of the two render radii, and on a projected map it changes no point. A mesh with no globe is drawn where its points are, and records no globe on the mesh drawn (scene spec §4.2, §4.4).
- Every function that builds or positions a mesh writes the four fields of scene spec §2 decision 3 and no `gvRadius` (scene spec §4.3).
- Every mesh `geovista` returns or draws carries only current fields. A mesh given only to read is never changed, unless the caller asked for the change in place. Reading a retired field raises no warning (scene spec §2 decision 5, §4.5).
- `core.combine` refuses meshes that `geovista` describes differently, by `mesh1.gv == mesh2.gv`, and names what differs, the CRS or the globe (scene spec §4.7).
- `zlevel` and `zscale` stay, and offset a point from the render radius as they offset it from the radius today (scene spec §4.2).
- Inside, `geovista` passes plain floats, and drawing a scene never imports `pint` (scene spec §2 decision 8, §4.1).
- The default globe draws a scene as today, so every image test passes against its existing baseline, with none regenerated (globe spec §4.1).
- `mypy` runs strict over the whole package, with no new override. Warnings are errors under pytest. Docstrings are NumPy style; a changed parameter's entry is rewritten, and `.. versionchanged::` is not used.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. Fragments credit ``(:user:`claude`)``. The pull request carries `type: enhancement`, `feature: crs`, `breaking-change` and `agentic`.
- Cite a specification section in plain text (`scene spec §4.4`), never with a `{ref}` role.

## Calls Made in This Plan

Call 1 was put to {user}`bjlittle` before planning, on 2026-10-28. Calls 2 to 16 are made here. Calls 2, 5, 6, 7, 8, 9 and 15 amend the scene specification, in Task 7. Call 5 qualifies the premise of scene spec §2 decision 4 that no position changes, so it was put to {user}`bjlittle` on review of this plan, who kept it on 2026-10-28.

1. **The row is bounded.** It is planned from the scene specification, the child specification of globe spec §9 row 2, with no further one.
2. **34 functions, in 10 modules.** `pantry.meshes.regular_grid` has taken a `radius` since #645, which it passes to `Transform.from_1d`, and the census of scene spec §3.1 missed it. It takes `globe=` too. The "3 pages of the documentation" of §3.1 are the pages the gallery generates from `vector_data/wind_arrows_uvw`, which move with the example. This amends scene spec §3.1.
3. **Plain floats inside.** `to_cartesian`, `vectors_to_cartesian` and `to_lonlats` keep their bodies as the private `_to_cartesian`, `_vectors_to_cartesian` and `_to_lonlats`, which take a float `radius` as the public functions do today. Internal code calls them with a render radius, a lifted radius, or the radius of each point. The public functions take `globe` and pass its render radius. `to_lonlats` no longer takes an array of radii; `from_cartesian` reads each point at its own radius through `_to_lonlats`.
4. **A number is not a globe.** The private `geovista.globe._resolve(globe)` returns `Globe()` for `None` and a `Globe` as given, and raises `TypeError` for anything else, naming `globe` and the call that draws a sphere of radius `r`, `Globe(render_radius=r)`. A caller who swaps `radius=2` for `globe=2` gets that error, not an `AttributeError` from deep inside. Every function that takes `globe=` resolves it so.
5. **A mesh records the globe it was positioned for, never a radius lifted by its z-level.** Today a surface or a line records the radius its points lie at, lift included, while a point cloud records its base radius (measured below). Were the lifted radius recorded as a render radius, every lifted layer, such as the coastlines a scene adds at a z-level of 1, would record a globe other than the scene's, and be scaled back down onto the surface. So `from_unstructured`, `load_coastlines`, `coastlines`, `resize` of a surface, `geodesic.line` and `BBox.boundary` record the globe, and their z-levels offset the points from its render radius, as a cloud's do. The consequence: a surface or line saved by 0.5 with a z-level carries its lifted radius as `gvRadius`, which scene spec §4.4 item 1 reads as its render radius. Drawn in a scene at another render radius, the default included, it is scaled onto that radius and loses its lift, which adding it with its z-level restores. A mesh saved without a z-level, the pantry's assets among them, is drawn where it was. This amends scene spec §4.3 and §4.4 item 1.
6. **A mesh placed on a surface takes the surface's globe.** `geodesic.line` and `BBox.boundary` given a surface, and the manifold `BBox.mesh` built around one, still measure the surface's mean radius, since they must sit where its points are, and record the surface's globe, or no globe when the surface has none. Given no surface, they use the globe given, or `Globe()`. This amends scene spec §4.2.
7. **`resize` defaults to the mesh's own globe, and always records one.** Given no globe, `resize` uses the globe the mesh records, else `Globe()`, for a surface too, where today it moved a surface to `RADIUS` whatever it recorded. It records the globe and drops retired fields on the mesh it returns even when no point moves, working on a copy unless `inplace=True`. A surface given a z-level at each point keeps its globe, since the globe is now the base its levels offset from; #2761 cleared it (c45f2677). This amends scene spec §4.2.
8. **`transform_mesh` records its globe, and moves no point it does not transform.** Given no globe, it uses the globe the mesh records, else `Globe()`, and records the globe it used on every mesh it transforms, a projected one included, so a mesh projected and brought back returns to its render radius. When no transform is needed it returns the mesh with its own globe, dropping retired fields from a copy unless `inplace=True`. `resize` changes a mesh's globe without changing its CRS. This amends scene spec §4.2.
9. **Drawing.** In `add_mesh`, a mesh on the globe whose globe differs from the scene's is drawn as a copy, its points scaled by the scene's render radius over its own, recording the scene's globe; a cloud's heights scale with it. On a map only the record changes. A mesh in another CRS is transformed onto the scene's globe, and records it. A z-level given to `add_mesh` resizes the mesh to the scene's globe, where today it lifted the mesh from its own mean radius, so the lines of `add_graticule`, `add_meridians` and `add_parallels` given a z-level are lifted once, to their labels, where today they are lifted twice and their labels once. This amends scene spec §4.2.
10. **The base layer** on the globe is built at the scene's globe and lowered by its z-level through `resize`, so it records the scene's globe rather than a lowered radius, at the same points as today.
11. **`KDTree`** keeps the globe of the mesh it is built from, `Globe.from_mesh(mesh)` or `Globe()`, places the points of a mesh in another CRS at its render radius, and `query` defaults to it. The distances `query` returns for a tree built from a mesh at a render radius other than 1 change, to the distances between the points as drawn.
12. **A `Transform` call records its CRS and globe.** `Transform(...)(data=...)` builds its mesh with `copy_structure`, which keeps no field data, so today the mesh it returns has neither a CRS nor a `gvRadius` (measured below). It carries the CRS and globe of the mesh it was built from.
13. **`combine` refuses whatever `data` is,** since meshes on different globes cannot share points. It raises `ValueError` naming the input, as `input mesh #2`, and what differs: its CRS, its globe, or its CRS and globe. With `data=True`, the combined mesh records the shared globe, and no retired field.
14. **The functions that return a mesh made from one they were given** drop retired fields from it: `resize`, `transform_mesh`, `combine`, `add_texture_coords`, `slice_cells`, `slice_lines`, `slice_mesh`, `BBox.enclosed` and `BBox.__call__`, `cast_UnstructuredGrid_to_PolyData`, and every mesh of `filters.remesh`. `add_texture_coords` attaches coordinates to the mesh it is given unless it cuts the antimeridian, as its docstring says, so it cleans that mesh in place.
15. **The stopgap goes.** `common._read_radius` and `common._write_radius` are removed. `distance` snaps to the render radius of `Globe.from_mesh(mesh)`, else `RADIUS`, and `from_cartesian` decodes a cloud's z-levels from it. Scene spec §4.5 loses its paragraph "Until row 2 of §9 lands".
16. **Two fragments**, `<PR>.breaking.rst` and `<PR>.feature.rst`, as scene spec §9 asks.

## Review Focus

1. **A number given as a globe**, as `GeoPlotter(globe=2)` or `to_cartesian(lons, lats, globe=2.0)` from a caller migrating from `radius=`. It must raise a `TypeError` naming `Globe(render_radius=...)`, never an `AttributeError`. `test_a_number_is_not_a_globe` (Tasks 1, 2 and 6).
2. **A layer lifted by a z-level**, such as the coastlines, a geodesic line or a `BBox` boundary. It records the globe it was built for, so in a scene at another render radius it keeps its lift in proportion, never sinking onto the surface. `test_a_lifted_mesh_records_its_globe` (Tasks 2 and 4) and `test_a_lifted_layer_keeps_its_lift` (Task 6).
3. **A mesh drawn, or a cached one.** `coastlines` and `_lfric_mesh` are cached and shared, so drawing or resizing must never change the mesh given. `test_drawing_leaves_the_mesh_unchanged` (Task 6) and `test_records_on_a_copy` (Task 3).
4. **A mesh saved by 0.5**, with a `gvRadius` and no globe, given to any function that returns or draws a mesh. The result carries only current fields, and the mesh given keeps its `gvRadius`. `test_only_current_fields` (Task 5) and `test_a_legacy_mesh_is_drawn_cleaned` (Task 6).
5. **A mesh with no globe**, warped outside `geovista` as the gallery's orography is. It is drawn where its points are at any scene globe, and resized, transformed or searched at `Globe()`. `test_a_mesh_with_no_globe_is_drawn_where_it_is` (Task 6) and `test_a_mesh_with_no_globe_is_resized_to_the_default` (Task 3).

---

Measured on 2026-10-28 at `af706299`, with Python 3.14.9, `pyvista` 0.49.1, VTK 9.7.1 and NumPy 2.5.4, in the `geovista` environment:

- 36 functions in the package take a `radius`: the 33 of scene spec §3.1, `pantry.meshes.regular_grid`, `Globe.__init__`, and the stopgap `common._write_radius`.
- `coastlines()`, `line([0, 10], [0, 10])` and `BBox([0, 10, 10, 0], [0, 0, 10, 10]).boundary()` record a `gvRadius` of 1.0001, and `from_unstructured(..., zlevel=2)` one of 1.0002, the radius their points lie at. `from_points` records the base radius under its points' z-levels.
- `Transform(lons, lats, radius=2.0)(data=...)` returns a mesh whose field data is `gvName` alone.
- `glyph` keeps a cloud's field data: `gvCRS`, `gvRadius` and `gvZScale`.
- For `lfric_winds`, `from_points(..., radius=1.1)` and `from_points(..., zlevel=1000)` give the same points, vectors and glyph points, bit for bit.
- `pyvista`'s `add_mesh` and `add_points` raise `TypeError: "radius" is an invalid keyword argument` for a `radius` keyword, so each `GeoPlotter` method refuses one, through its `**kwargs` or its signature.
- Every internal call of `resize` passes a radius, so none relies on its default.
- `GeoPlotter().add_meridians(zlevel=5)` draws its lines at a radius of 1.00100025, which is (1 + 5 × 10⁻⁴)², while `_add_graticule_labels` places their labels at 1.0005.
- No README example and no hand-written page of the documentation passes `radius=`. `tests/plotting/test_examples.py` compares an image of every gallery example, `wind_arrows_uvw` included.
- `ZLEVEL_SCALE` is 1e-4 and `BASE_ZLEVEL_SCALE` 1e-3, so no z-level of 1 or more leaves a mean radius within `np.isclose` of the render radius, and `distance` never snaps a lifted mean to it.

### Task 1: The Globe in the Conversions

**Files:**
- Modify: `src/geovista/globe.py` (`_resolve`)
- Modify: `src/geovista/common.py` (`_to_cartesian`, `_vectors_to_cartesian`, `_to_lonlats`; `globe=` on the public four)
- Modify: every internal call that passes `radius=` to the four, in `bridge.py`, `core.py`, `geodesic.py`, `geometry.py`, `gridlines.py`, `search.py`, `geoplotter.py` and `transform.py`, which calls the private function with the same arguments
- Create: `tests/globe/test_resolve.py`
- Modify: `tests/common/test_to_cartesian.py`, `test_vectors_to_cartesian.py`, `test_to_lonlat.py`, `test_to_lonlats.py`, and `tests/geodesic/test_line.py` (its call of `to_cartesian(..., radius=)`)

**Interfaces:**
- Consumes: `Globe` (row 1).
- Produces: `_resolve(globe: object, /) -> Globe` in `geovista.globe`; `_to_cartesian`, `_vectors_to_cartesian` and `_to_lonlats` in `geovista.common`, each with today's signature and body; `to_cartesian(lons, lats, *, globe: Globe | None = None, zlevel=None, zscale=None, stacked=True)`, `vectors_to_cartesian(lons, lats, vectors, *, globe=None, zlevel=None, zscale=None)`, `to_lonlat(xyz, /, *, radians=False, globe=None, rtol=None, atol=None)` and `to_lonlats(xyz, /, *, radians=False, globe=None, stacked=True, rtol=None, atol=None)`.

- [ ] **Step 1: Write the failing tests**

`tests/globe/test_resolve.py`:

```python
def test_none_is_the_default_globe():
    assert _resolve(None) == Globe()


def test_a_globe_is_itself():
    globe = Globe(render_radius=2)
    assert _resolve(globe) is globe


@pytest.mark.parametrize(
    "value", [2, 2.0, np.float64(2.0), "2", pint.UnitRegistry().Quantity(2, "m")]
)
def test_a_number_is_not_a_globe(value):
    with pytest.raises(TypeError, match=r"globe must be a geovista\.Globe") as info:
        _resolve(value)
    assert "Globe(render_radius=" in str(info.value)
```

In each of the four test modules, with `RADII = [1.0, 6378137.0]`: `test_the_globe_sets_the_radius[r]`, where `to_cartesian(LONS, LATS, globe=Globe(render_radius=r))` lies at `r`, and the others read or scale at `r` likewise; `test_a_number_is_not_a_globe`, where `globe=2.0` raises `TypeError`; and `test_radius_is_gone`, where `radius=2.0` raises `TypeError` matching `"radius"`. The existing tests of an array of radii move to `_to_lonlats`, unchanged.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/globe/test_resolve.py tests/common -q`
Expected: FAIL, with `ImportError` for `_resolve`.

- [ ] **Step 3: Implement**

`_resolve` raises `TypeError(f"globe must be a geovista.Globe, got {globe!r}. Draw a sphere of radius r with Globe(render_radius=r).")`. The public functions import it inside themselves, with `# noqa: PLC0415`, since `geovista.globe` imports `geovista.common`, and call the private form with `radius=_resolve(globe).render_radius`. Rewrite each `radius` entry of their docstrings as `globe : Globe, optional`, the globe whose render radius the points lie at, by default `Globe()`.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/globe tests/common tests/bridge tests/core tests/geodesic tests/geometry tests/gridlines tests/search tests/transform tests/geoplotter -q`
Expected: PASS. Every internal caller now uses a private form, so nothing else changes.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/*.py tests/globe/test_resolve.py tests/common/*.py tests/geodesic/test_line.py
git add tests/globe/test_resolve.py
pixi run --frozen -e geovista git commit -am "feat: take a globe, not a radius, in the conversions of geovista.common"
```

### Task 2: The Bridge Records Its Globe

**Files:**
- Modify: `src/geovista/bridge.py` (`Transform.__init__`, `__call__`, `from_1d`, `from_2d`, `from_points`, `from_tiff`, `from_unstructured`, `to_structured_grid`)
- Modify: `src/geovista/pantry/meshes.py` (`regular_grid`)
- Modify: `src/geovista/examples/vector_data/wind_arrows_uvw.py` (`radius=1.1` becomes `zlevel=1000`)
- Modify: `tests/conftest.py` (the `legacy` fixture)
- Create: `tests/bridge/test_records_the_globe.py`, `tests/pantry/test_regular_grid.py`
- Modify: `tests/bridge/test_from_points.py`, `test_from_tiff.py`; and every test that builds with `Transform.from_1d(..., radius=r)` or reads the `gvRadius` the bridge wrote: `tests/globe/test_from_mesh.py`, `test_round_trip.py`, `tests/accessor/test_GeoVistaAccessor.py`, `tests/common/test_sanitize_legacy.py`, `test_sanitize.py` and `test_from_cartesian.py`

**Interfaces:**
- Consumes: `_resolve`, `_to_cartesian`, `_vectors_to_cartesian` (Task 1); `Globe.to_mesh`.
- Produces: each builder takes `globe: Globe | None = None` where it took `radius`, records `_resolve(globe)` with `to_mesh`, and writes no `gvRadius`; `from_points` still writes `gvZScale`. A `Transform` call carries the CRS and globe of its mesh (call 12). The fixture `legacy`, a function `legacy(mesh: pv.DataSet, /, *, radius: float | None = None) -> pv.DataSet` that returns a copy of the mesh as 0.5 wrote it: the four globe fields removed, and a `gvRadius` of `radius`, else of the render radius the mesh recorded.

- [ ] **Step 1: Write the failing tests**

`tests/bridge/test_records_the_globe.py` parametrizes `build` over `from_1d`, `from_2d`, `from_points`, `from_unstructured`, `to_structured_grid`, a `Transform` call and `regular_grid`, each on small fixed coordinates, and `globe` over `None`, `Globe(render_radius=6378137.0)` and `Globe(render_radius=2, exaggeration=20, exaggeration_below=100)`:

- `test_records_the_globe[build-globe]`: `Globe.from_mesh(mesh) == (globe or Globe())`, `GV_FIELD_RADIUS not in mesh.field_data`, and the smallest radius of its points is the render radius, to `rtol=1e-6`.
- `test_a_lifted_mesh_records_its_globe[r]`: `from_unstructured(..., globe=Globe(render_radius=r), zlevel=2)` records `Globe(render_radius=r)`, its points at `r * (1 + 2 * ZLEVEL_SCALE)`; and `from_points` likewise, with `zlevel=[1, 2, 3]` (call 5).
- `test_a_call_records_the_crs_and_globe`: `Transform(LONS, LATS, globe=g)(data=...)` has `from_wkt(mesh) == WGS84` and records `g` (call 12).
- `test_radius_is_gone[build]`: `radius=1.0` raises `TypeError` matching `"radius"`.
- `test_a_number_is_not_a_globe`: `from_1d(LONS, LATS, globe=2.0)` raises `TypeError` matching `"geovista.Globe"`.

`tests/bridge/test_from_tiff.py` moves its `"radius": None` keywords to `"globe": None`, and gains `test_records_the_globe`, on the raster its tests already read. The tests that read a `gvRadius` written by the bridge take one from `legacy` instead, as `test_gvradius_gives_the_render_radius` does with `legacy(from_1d(LONS, LATS, globe=Globe(render_radius=r)))`. The stopgap tests of `test_sanitize_legacy.py` compare `legacy(mesh)` with `mesh`, where they compared a mesh with its cleaned copy.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/bridge tests/pantry -q`
Expected: FAIL, with `TypeError: ... unexpected keyword argument 'globe'`.

- [ ] **Step 3: Implement**

Each builder resolves its globe once and places its points with `_to_cartesian(..., radius=globe.render_radius, zlevel=..., zscale=...)`. `from_unstructured` passes its z-level to `_to_cartesian`, where it added it to the radius (call 5). `__init__` keeps the resolved globe and passes it to the builder it calls. `__call__` copies `gvCRS` and the globe of `self._mesh` onto the mesh it builds. `regular_grid` passes `globe` to `from_1d`. In `wind_arrows_uvw.py`, `radius=1.1` becomes `zlevel=1000`, under a comment that it floats the arrows a tenth of the radius above the surface; measured above, its points, vectors and glyphs are unchanged.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/bridge tests/pantry tests/globe tests/accessor tests/common -q`, then `CI=true LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe pixi run --frozen -e geovista pytest tests/plotting/test_examples.py -k wind_arrows_uvw -q`
Expected: PASS, the example against its existing image.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/bridge.py src/geovista/pantry/meshes.py src/geovista/examples/vector_data/wind_arrows_uvw.py tests/conftest.py tests/bridge/*.py tests/pantry/*.py tests/globe/*.py tests/accessor/*.py tests/common/*.py
git add tests/bridge/test_records_the_globe.py tests/pantry/test_regular_grid.py
pixi run --frozen -e geovista git commit -am "feat: build every bridge mesh on a globe, and record it"
```

### Task 3: Resize and Transform Take a Globe, and the Stopgap Goes

**Files:**
- Modify: `src/geovista/core.py` (`resize`)
- Modify: `src/geovista/transform.py` (`transform_mesh`, `_record_zlevels`)
- Modify: `src/geovista/common.py` (`distance`, `from_cartesian`; remove `_read_radius` and `_write_radius`)
- Modify: `src/geovista/geometry.py` and `src/geovista/geoplotter.py`, whose calls of `resize` pass `globe=None if radius is None else Globe(render_radius=radius)` until Tasks 4 and 6 replace them
- Modify: `tests/core/test_resize.py`, `tests/transform/test_transform_mesh.py`, `tests/common/test_distance.py`, `test_from_cartesian.py`, `test_sanitize_legacy.py`

**Interfaces:**
- Consumes: `_resolve` (Task 1); the `legacy` fixture (Task 2); `Globe.from_mesh`, `Globe.to_mesh`, `sanitize_legacy`.
- Produces: `resize(mesh, /, *, globe: Globe | None = None, zlevel=None, zscale=None, inplace=False)`; `transform_mesh(mesh, /, tgt_crs, *, slice_connectivity=True, globe: Globe | None = None, zlevel=None, zscale=None, rtol=None, atol=None, inplace=False)`; `_record_zlevels(mesh, levels, tgt_crs, *, globe: Globe, zscale: float) -> None`.

- [ ] **Step 1: Write the failing tests**

`tests/core/test_resize.py`, with `RADII`:

- `test_records_the_globe[r]`: `resize(lfric, globe=Globe(render_radius=r))` lies at `r` and records that globe, with no `gvRadius`.
- `test_records_on_a_copy`: for `mesh = from_1d(LONS, LATS)`, `result = resize(mesh, globe=Globe(exaggeration=20))` is not `mesh`, has its points, and records `Globe(exaggeration=20)`, while `mesh` still records `Globe()`; with `inplace=True` the result is `mesh` (call 7).
- `test_defaults_to_the_globe_the_mesh_records`: a mesh built at `Globe(render_radius=2)`, resized with `zlevel=1`, lies at `2 * (1 + ZLEVEL_SCALE)` and records `Globe(render_radius=2)` (calls 5 and 7).
- `test_a_mesh_with_no_globe_is_resized_to_the_default`: `lfric_orog()` with its `gvRadius` deleted and warped as its example warps it reads as no globe, and `resize` puts it at 1 and records `Globe()`.
- `test_levels_at_each_point_keep_the_globe`: `resize(mesh, globe=g, zlevel=np.arange(mesh.n_points) % 3)` records `g`.

`tests/transform/test_transform_mesh.py`:

- `test_records_the_globe_on_a_map`: a mesh at `Globe(render_radius=2)` projected to `"+proj=eqc"` records it, and transformed back to `WGS84` lies at 2 (call 8).
- `test_a_given_globe_places_the_points[r]`: a projected mesh transformed to `WGS84` with `globe=Globe(render_radius=r)` lies at `r` and records it.
- `test_no_transform_moves_no_point`: a `WGS84` mesh transformed to `WGS84` keeps its points and globe; given `legacy(mesh)`, the result has no `gvRadius` and the mesh given keeps its own.

`tests/common/test_distance.py`, `test_snaps_to_the_render_radius`: a mesh recording `Globe(render_radius=2)`, its points scaled by `1 + 1e-7`, has a `distance` of exactly 2, and so does `legacy` of it. `tests/common/test_from_cartesian.py`, `test_a_cloud_decodes_from_its_globe`: a cloud from `from_points(..., globe=Globe(render_radius=2), zlevel=[1, 2, 3], zscale=0.1)` reads back levels `[1, 2, 3]`, and so does `legacy` of it. `tests/common/test_sanitize_legacy.py` moves its `radius=` keywords to `globe=`, and gains `test_the_stopgap_is_gone`, asserting that `geovista.common` has neither `_read_radius` nor `_write_radius`.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/core/test_resize.py tests/transform/test_transform_mesh.py tests/common -q`
Expected: FAIL, with `TypeError: ... unexpected keyword argument 'globe'`.

- [ ] **Step 3: Implement**

`resize` resolves `globe` as `_resolve(globe)` when given, else `Globe.from_mesh(mesh) or Globe()`, places points at its render radius with the z-levels as today, records it with `to_mesh` and runs `sanitize_legacy` on the mesh it returns, copying first unless `inplace`. It updates when the points move or the record differs. `transform_mesh` resolves its globe the same way, places a `WGS84` target at its render radius, and records it on every mesh it transforms; with no transform it returns the mesh, cleaned on a copy unless `inplace`. `_record_zlevels` records the globe where it wrote a radius. `distance` and `from_cartesian` read `Globe.from_mesh(mesh)`. Delete the two stopgap helpers.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/core tests/transform tests/common tests/globe tests/geometry tests/geoplotter -q`, then `CI=true LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe pixi run --frozen -e geovista pytest tests/plotting -q`
Expected: PASS, every image against its existing baseline.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/core.py src/geovista/transform.py src/geovista/common.py src/geovista/geometry.py src/geovista/geoplotter.py tests/core/test_resize.py tests/transform/test_transform_mesh.py tests/common/*.py
pixi run --frozen -e geovista git commit -am "feat: resize and transform a mesh on a globe, and drop the stopgap radius helpers"
```

### Task 4: The Layers' Builders Take a Globe

**Files:**
- Modify: `src/geovista/geodesic.py` (`line`, `BBox.boundary`, `BBox._generate_bbox_mesh`)
- Modify: `src/geovista/geometry.py` (`coastlines`, `load_coastlines`)
- Modify: `src/geovista/gridlines.py` (`create_meridians`, `create_parallels`)
- Modify: `src/geovista/search.py` (`KDTree.__init__`, `KDTree.query`)
- Modify: `tests/geodesic/test_line.py`, `test_BBox.py`, `tests/geometry/test_coastlines.py`, `test_load_coastlines.py`, `tests/gridlines/test_create_meridians.py`, `test_create_parallels.py`, `tests/search/test_KDTree.py`

**Interfaces:**
- Consumes: `_resolve`, `_to_cartesian` (Task 1); `resize` with `globe=` (Task 3); `Globe.from_mesh`, `Globe.to_mesh`.
- Produces: `line(lons, lats, *, surface=None, globe: Globe | None = None, npts=None, ellps=None, close=False, zlevel=None, zscale=None)`; `BBox.boundary(surface=None, *, globe: Globe | None = None)`; `BBox._generate_bbox_mesh(surface=None, *, globe: Globe | None = None)`; `coastlines(*, resolution=None, globe: Globe | None = None, zlevel=None, zscale=None)` and `load_coastlines` alike, both cached on their arguments; `create_meridians(..., globe: Globe | None = None, zlevel=None, zscale=None)` and `create_parallels` alike; `KDTree.query(lons, lats, *, globe: Globe | None = None, zlevel=None, zscale=None, ...)`, with the rest of its keywords as today.

- [ ] **Step 1: Write the failing tests**

- `tests/geodesic/test_line.py`: `test_a_lifted_mesh_records_its_globe[r]`, where `line([0, 10], [0, 10], globe=Globe(render_radius=r))` records that globe and lies at `r * (1 + ZLEVEL_SCALE)` (call 5); `test_on_a_surface_records_its_globe`, where a line on a mesh built at `Globe(render_radius=2)` records it, and one on the warped orography of Task 3 records no globe (call 6).
- `tests/geodesic/test_BBox.py`: the same two tests for `boundary`, and `test_the_manifold_records_its_globe`, where `bbox.mesh` records `Globe()`.
- `tests/geometry/test_coastlines.py` and `test_load_coastlines.py`: their `radius` parameters become `globe=Globe(render_radius=r)`; `test_a_lifted_mesh_records_its_globe[r]`, where `coastlines(globe=Globe(render_radius=r))` records it and lies at `r * (1 + ZLEVEL_SCALE)`, with no `gvRadius`.
- `tests/gridlines/test_create_meridians.py` and `test_create_parallels.py`: `test_each_line_records_the_globe`, where every block of `create_meridians(globe=g)` records `g`.
- `tests/search/test_KDTree.py`: `test_query_uses_the_globe_of_the_tree[r]`, where a tree of the points of a mesh built at `Globe(render_radius=r)` finds a point of it at a distance of 0, to `atol=1e-9 * r`, and its index (call 11); `test_a_tree_of_a_projected_mesh`, whose `points` lie at the render radius the projected mesh records.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/geodesic tests/geometry tests/gridlines tests/search -q`
Expected: FAIL, with `TypeError: ... unexpected keyword argument 'globe'`.

- [ ] **Step 3: Implement**

`line`, `boundary` and `_generate_bbox_mesh` measure a surface's radius as today, and take the globe of call 6, recording it after the cache check of `_generate_bbox_mesh`, since the cache is keyed on the radius alone. `load_coastlines` places its points with `_to_cartesian(..., radius=globe.render_radius, zlevel=zlevel, zscale=zscale)`, where it added the z-level to the radius, and records the globe; `coastlines` resizes with `globe=_resolve(globe)`. `create_meridians` and `create_parallels` record the globe on each block. `KDTree` keeps `Globe.from_mesh(mesh) or Globe()`, and places a mesh in another CRS at its render radius. Remove the `Globe(render_radius=radius)` that Task 3 left in `geometry.py`.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/geodesic tests/geometry tests/gridlines tests/search tests/geoplotter -q`, then `CI=true LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe pixi run --frozen -e geovista pytest tests/plotting -q`
Expected: PASS, every image against its existing baseline.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/geodesic.py src/geovista/geometry.py src/geovista/gridlines.py src/geovista/search.py tests/geodesic/*.py tests/geometry/*.py tests/gridlines/*.py tests/search/*.py
pixi run --frozen -e geovista git commit -am "feat: build lines, coastlines, graticules and search trees on a globe"
```

### Task 5: Combining, and Only Current Fields

**Files:**
- Modify: `src/geovista/core.py` (`combine`, `add_texture_coords`, `slice_cells`, `slice_lines`, `slice_mesh`)
- Modify: `src/geovista/geodesic.py` (`BBox.enclosed`)
- Modify: `src/geovista/common.py` (`cast_UnstructuredGrid_to_PolyData`)
- Modify: `src/geovista/filters.py` (`remesh`)
- Modify: `tests/core/test_combine.py`
- Create: `tests/common/test_current_fields.py`

**Interfaces:**
- Consumes: `mesh.gv` (row 1); the `legacy` fixture (Task 2); `sanitize_legacy`.
- Produces: `combine` raising `ValueError` for meshes described differently (call 13); the functions of call 14 returning only current fields.

- [ ] **Step 1: Write the failing tests**

`tests/core/test_combine.py`, with two `from_1d` meshes over neighbouring longitudes:

- `test_refuses_a_different_globe`: one at `Globe()` and one at `Globe(render_radius=2)` raise `ValueError` matching `"input mesh #2"` and `"globe"`, with `data=True` and with `data=False`.
- `test_refuses_a_different_crs`: the second with its `gvCRS` deleted raises matching `"CRS"`.
- `test_names_the_crs_and_globe`: a second differing in both raises matching `"CRS and globe"`.
- `test_records_the_shared_globe`: `combine(legacy(a), b)`, both at `Globe()`, records `Globe()` and has no `gvRadius`.

`tests/common/test_current_fields.py`, `test_only_current_fields[case]`, parametrized over each function of call 14 (for `remesh`, each mesh it returns; for `add_texture_coords`, `antimeridian=True`), given `legacy` of a mesh it accepts: no mesh returned carries a field of `RETIRED_FIELDS`, each records the globe of the mesh given, and the mesh given still has its `gvRadius`. `test_texture_coordinates_clean_in_place`: `add_texture_coords(legacy(mesh))` returns that mesh, cleaned.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/core/test_combine.py tests/common/test_current_fields.py -q`
Expected: FAIL: `combine` accepts every pair, and each result keeps its `gvRadius`.

- [ ] **Step 3: Implement**

`combine` compares each mesh's `gv` with the first's before reading any, and builds its message from which of `crs` and `globe` differ. With `data=True` it writes the first mesh's globe with `to_mesh` after copying the common field data, then runs `sanitize_legacy`. Each function of call 14 runs `sanitize_legacy` on the mesh it returns, and on each in a `Remesh`. The documentation of `combine` says `pyvista`'s own `merge` keeps the first mesh's field data, and refuses nothing (scene spec §4.7).

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/core tests/common tests/geodesic tests/filters -q`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/core.py src/geovista/geodesic.py src/geovista/common.py src/geovista/filters.py tests/core/test_combine.py tests/common/test_current_fields.py
git add tests/common/test_current_fields.py
pixi run --frozen -e geovista git commit -am "feat: refuse to combine meshes described differently, and return only current fields"
```

### Task 6: The Scene's Globe

**Files:**
- Modify: `src/geovista/geoplotter.py` (`GeoPlotterBase.__init__` and `globe`; `add_base_layer`, `add_coastlines`, `add_graticule`, `add_mesh`, `add_meridian`, `add_meridians`, `add_parallel`, `add_parallels`, `add_points`; `_lfric_mesh`, `_add_graticule_labels`)
- Modify: `tests/geoplotter/test_GeoPlotterBase.py`, `test_add_mesh.py`, `test_add_base_layer.py`, `test_add_graticule.py`, `test_add_meridians.py`, `test_add_parallels.py`, `test_add_points.py`, `test__add_graticule_labels.py`
- Create: `tests/geoplotter/test_add_coastlines.py`, `tests/geoplotter/test_import.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `GeoPlotterBase.__init__(self, *args, crs=None, globe: Globe | None = None, manifold=None, theme=None, **kwargs)`; the read-only property `globe -> Globe`, with `.. versionadded:: 0.6.0`; no method taking `radius`; `_lfric_mesh(*, resolution=None, globe: Globe | None = None)`. `GeoQtInteractor` and `GeoBackgroundPlotter` inherit both.

- [ ] **Step 1: Write the failing tests**

The drawn mesh is `actor.mapper.dataset`. With `RADII`:

- `test_GeoPlotterBase.py`: `test_the_default_globe` (`GeoPlotter().globe == Globe()`), `test_a_given_globe`, `test_the_globe_cannot_be_set` (`AttributeError`), and `test_a_number_is_not_a_globe` (`GeoPlotter(globe=2)` raises `TypeError`).
- `test_add_mesh.py`:
  - `test_drawn_at_the_scenes_globe[r]`: a mesh built at `Globe()`, added to `GeoPlotter(globe=Globe(render_radius=r))`, is drawn at `r` and records `p.globe`;
  - `test_drawing_leaves_the_mesh_unchanged`: after that, the mesh given has its points and globe;
  - `test_a_cloud_keeps_its_heights_in_proportion`: a cloud at `Globe()` with `zlevel=[1, 2, 3]`, `zscale=0.1`, is drawn at a scene of 2 at radii `2 * (1 + 0.1 * [1, 2, 3])`;
  - `test_a_mesh_with_no_globe_is_drawn_where_it_is`: the warped orography of Task 3, at a scene of 2, is drawn at its own points and records no globe;
  - `test_on_a_map_only_the_record_changes`: a mesh projected to `"+proj=eqc"` at `Globe()`, added to `GeoPlotter(crs="+proj=eqc", globe=Globe(render_radius=2))`, is drawn at its points and records `p.globe`;
  - `test_a_legacy_mesh_is_drawn_cleaned`: `legacy` of a mesh is drawn with no `gvRadius`, and keeps its own;
  - `test_a_zlevel_lifts_from_the_scenes_globe`: a mesh at `Globe(render_radius=2)` in a default scene with `zlevel=1` is drawn at `1 + ZLEVEL_SCALE` (call 9);
  - `test_radius_is_gone`: `add_mesh(mesh, radius=1.0)` raises `TypeError` matching `"radius"`.
- `test_add_base_layer.py`: `test_at_the_scenes_globe[r]`, drawn at `r * (1 - BASE_ZLEVEL_SCALE)` and recording `p.globe`, and at `r` with `zlevel=0` (call 10).
- `test_add_coastlines.py`: `test_a_lifted_layer_keeps_its_lift[r]`, drawn at `r * (1 + ZLEVEL_SCALE)` and recording `p.globe`, which scene spec §6 asks of the pantry's coastlines.
- `test_add_meridians.py` and `test_add_parallels.py`: `test_at_the_scenes_globe[r]`; and `test_a_zlevel_lifts_the_lines_once`, where with `zlevel=5` the lines and their labels lie at `r * (1 + 5 * ZLEVEL_SCALE)` (call 9).
- `test_add_points.py`: its `radius` cases move to the scene's globe; `test_at_the_scenes_globe[r]`.
- `test_import.py`, `test_drawing_a_scene_imports_no_pint`, runs in a subprocess, as `tests/globe/test_import.py` does: `GeoPlotter(off_screen=True, globe=Globe(render_radius=2))`, `add_mesh` of a `from_1d` mesh and `add_graticule()`, then asserts no `pint` module is loaded.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/geoplotter -q`
Expected: FAIL, with `TypeError: ... unexpected keyword argument 'globe'` from `GeoPlotter`.

- [ ] **Step 3: Implement**

`__init__` keeps `_resolve(globe)`. Each built-in layer is built with `globe=self.globe`, `add_points` builds its cloud at it, and `_add_graticule_labels` places its labels at it. `_lfric_mesh` resizes its pantry mesh to the globe it is given, cached on it. In `add_mesh`, a mesh on the globe whose `Globe.from_mesh` is neither `None` nor the scene's is copied, its points scaled by `self.globe.render_radius / recorded.render_radius`, and recorded with `self.globe.to_mesh`; a projected one is copied and recorded alone; one in another CRS goes through `transform_mesh(..., globe=self.globe)`; a z-level resizes with `globe=self.globe`. The mesh drawn is cleaned by `sanitize_legacy`, on a copy whenever it is still the mesh given. Remove the `Globe(render_radius=radius)` that Task 3 left here.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/geoplotter tests/test_qt.py -q`, then `CI=true LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe pixi run --frozen -e geovista pytest tests/plotting -q`
Expected: PASS, every image against its existing baseline.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/geoplotter.py tests/geoplotter/*.py
git add tests/geoplotter/test_add_coastlines.py tests/geoplotter/test_import.py
pixi run --frozen -e geovista git commit -am "feat: give a scene one globe, and draw every layer at it"
```

### Task 7: The Guards, and Landing the Row

**Files:**
- Create: `tests/globe/test_no_radius.py`
- Modify: `docs/src/developer/specs/2026-10-27-globe-scene-design.md` (§3.1, §4.2, §4.3, §4.4 item 1, §4.5, §9 row 2)
- Modify: `docs/src/developer/specs/2026-10-26-globe-heights-layers-design.md` (§9 row 2)
- Modify: `tests/AGENTS.md` (the `legacy` fixture, staying under 200 lines)
- Create: `changelog/<PR>.breaking.rst`, `changelog/<PR>.feature.rst`

- [ ] **Step 1: Write the guards**

`tests/globe/test_no_radius.py`:

- `test_no_function_takes_a_radius`: every public function and method of every module that `geovista.common.get_modules("geovista")` lists, `pantry` and `examples` included and `__main__` skipped, has no parameter named `radius`, except `Globe.__init__`. The test imports each as `geovista.<name>`, and reads signatures with `inspect.signature`.
- `test_only_the_globe_reads_gvradius`: of the modules under `src/geovista`, only `common.py` and `globe.py` name `GV_FIELD_RADIUS`, read with `ast`.

- [ ] **Step 2: Watch each guard fail, then pass**

Tasks 1 to 6 have already done what the guards check, so each is shown to catch a regression by planting one. Add a keyword `radius: float | None = None` to `geovista.common.wrap`, and a line reading `GV_FIELD_RADIUS` to `geovista.core`, then run the guards.

Run: `pixi run --frozen -e geovista pytest tests/globe/test_no_radius.py -q`
Expected: FAIL, naming `geovista.common.wrap` and `core.py`. Revert both plants with `git checkout src/geovista/common.py src/geovista/core.py`, and run again: PASS.

- [ ] **Step 3: Amend the specifications, humanized, and the guide**

Scene spec §3.1: 34 functions in 10 modules, with a row for `pantry.meshes` and `regular_grid`, and the "3 pages" named as those the gallery generates from the example (call 2). §4.2: the defaults of `resize` and `transform_mesh`, a z-level in `add_mesh`, and a mesh placed on a surface (calls 6 to 9). §4.3: a mesh records the globe it was positioned for, and a z-level offsets its points from the render radius, never entering the record (call 5). §4.4 item 1: a `gvRadius` was the radius a surface or line lay at, its z-level included, so one saved with a z-level is drawn at a scene's render radius without its lift (call 5). §4.5: remove the paragraph that begins "Until row 2 of §9 lands" (call 15). `tests/AGENTS.md`: one line saying that the `legacy` fixture builds a mesh as 0.5 wrote it, for tests of retired fields.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py tests/test_status_references.py tests/test_renumbering.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-renumbering`.
Expected: the tests pass, and no citation went stale.

```bash
git add tests/globe/test_no_radius.py
pixi run --frozen -e geovista git commit -am "docs: amend the scene spec for the calls row 2 made, and guard against a radius"
```

- [ ] **Step 4: Run the whole suite, on the committed tree**

Run: `CI=true LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe pixi run --frozen -e geovista tests-unit`
Expected: PASS, with no new skips and no image baseline regenerated. `tests/test_readme_examples.py` runs the README's examples against the change, none of which passes `radius=`. `test_option_version` fails on a dirty tree, so commit first.

- [ ] **Step 5: Build the docs strictly, after the suite**

Run the strict `sphinx-build` of `AGENTS.md`, with `-W --keep-going`.
Expected: the build succeeds.

- [ ] **Step 6: Open the pull request**

Push `feat/globe-scene` and open it with the labels of the Global Constraints, and a humanized body listing calls 2 to 16, call 5 first.

- [ ] **Step 7: Write the fragments, and mark the rows**

`changelog/<PR>.breaking.rst` and `changelog/<PR>.feature.rst`, humanized, citing `geovista.globe.Globe`, `geovista.geoplotter.GeoPlotter` and `geovista.core.combine` by their documented paths:

```rst
``radius=`` is removed from every function that took it, with no alias. Each
takes ``globe=``, a :class:`geovista.globe.Globe`, in its place, and the methods
of :class:`geovista.geoplotter.GeoPlotter` take the globe of their scene. A mesh
records its globe, and no longer writes ``gvRadius``. A mesh saved by 0.5 after a
z-level lifted it is drawn at the scene's radius without its lift: add it with
its z-level, or fix the file once with
``resize(mesh, globe=Globe(), zlevel=...)``. (:user:`claude`)
```

```rst
:class:`geovista.geoplotter.GeoPlotter` takes the globe of its scene, and draws
every layer at it, the base layer, coastlines and graticule included, along with
any mesh recorded on another globe. :func:`geovista.core.combine` refuses meshes
in different CRSs or on different globes, and no mesh that geovista returns or
draws carries a retired field. (:user:`claude`)
```

Mark scene spec §9 row 2 and globe spec §9 row 2 ``✅ landed (YYYY-MM-DD, {pull}`<PR>`)``.

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py <PR> "changelog/<PR>.breaking.rst,changelog/<PR>.feature.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>`, then the strict docs build again.
Expected: the fragments pass, the tests pass, every status reference holds, and the fragments' references resolve.

- [ ] **Step 8: Commit and push**

```bash
git add changelog/<PR>.breaking.rst changelog/<PR>.feature.rst
pixi run --frozen -e geovista git commit -am "docs: mark scene spec row 2 and globe spec row 2 landed, and add the fragments"
git push
```
