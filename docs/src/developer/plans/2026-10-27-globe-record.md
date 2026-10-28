# Globe Record Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 1 of scene spec §9: `geovista.Globe`, the four fields a mesh records it in, reading meshes that record none, the `mesh.gv` namespace, the table of retired fields with `sanitize_legacy`, and the round trip of crs spec §6. It is additive and breaks nothing.

**Architecture:** A new module, `src/geovista/globe.py`, holds the immutable `Globe` and its `from_mesh` and `to_mesh`. `src/geovista/common.py` gains the four field names, the table of retired fields and `sanitize_legacy`. A new module, `src/geovista/accessor.py`, registers the `gv` namespace on `pyvista.DataSet`, and `geovista/__init__.py` imports it eagerly, as it does `themes`. Nothing in `geovista` is wired to the globe yet: the 33 functions keep `radius=` and keep writing `gvRadius` until row 2.

**Tech Stack:** `pyvista` 0.49.1 (`register_dataset_accessor`, since 0.48.0), VTK 9.7.1, NumPy 2.5.4, `pint` 0.26.2 through `geovista.units`, pytest.

**Spec:** `docs/src/developer/specs/2026-10-27-globe-scene-design.md` (`scene spec §…`, #2757): §2 decisions 3 to 9, §4.1, §4.3 to §4.6, §5, §6 and §9 row 1, with globe spec §4.2 and crs spec §6.

## Global Constraints

- `Globe` lives in `geovista.globe` and is exported as `geovista.Globe`. It is immutable and hashable, and takes four keyword arguments: `radius`, by default the WGS84 semi-major axis, 6,378,137 m; `render_radius`, by default `common.RADIUS`; `exaggeration`, by default 1; and `exaggeration_below`, by default the `exaggeration` (scene spec §4.1).
- Each value must be finite and positive, or a `ValueError` names the value. A factor is an int or a float, kept as a float, and need not be whole (scene spec §4.1).
- `Globe.radius` returns a `pint` quantity in metres, in `pint`'s application registry. `render_radius`, `exaggeration` and `exaggeration_below` return plain floats. A globe reports its `scale`, the render radius over the radius. Building a globe and reading its plain values never imports `pint`; the first read of `radius` does (scene spec §4.1).
- Two globes are equal when their four values are, exactly (scene spec §4.1).
- A mesh records its globe in four float64 field arrays of one value each: `gvGlobeRadius` (metres), `gvGlobeRenderRadius`, `gvGlobeExaggerationAbove` and `gvGlobeExaggerationBelow`, named by four constants in `geovista.common` (scene spec §2 decision 3, §4.3).
- `Globe.to_mesh` writes the four fields in place and removes `gvRadius`. `Globe.from_mesh` never changes the mesh. A mesh with some of the four fields but not all is refused, naming what is missing (scene spec §4.3, §4.4).
- A mesh without the four fields is read as `Globe(render_radius=r)` for a `gvRadius` of `r`; otherwise, when `crs.projected` does not call it projected and its points lie at one radius `r` within a relative spread of 10⁻⁶, as `Globe(render_radius=r)`; otherwise its globe is `None` (scene spec §4.4).
- One table in `geovista.common` lists every retired field: its name, whether it is field, point or cell data, what replaced it, the last release that wrote it, and how to translate it. `gvRadius` is the first: field data, replaced by the globe, last written by 0.5.3, translated as scene spec §4.4 item 1 says (scene spec §4.5).
- `sanitize_legacy(*meshes)` translates and removes every retired field in place, with the signature of `sanitize_vtk`. `sanitize` gains `legacy: bool = True`. Reading a retired field raises no warning (scene spec §4.5).
- `mesh.gv` is registered with `pyvista.register_dataset_accessor` on `pyvista.DataSet` when `geovista` is imported. `mesh.gv.globe` and `mesh.gv.crs` are read at every access and cannot be set; assigning to `mesh.gv.globe` raises an `AttributeError` that names `resize(mesh, globe=...)`. `mesh1.gv == mesh2.gv` compares CRSs and globes, never geometry. The namespace's docstring and repr name `geovista` (scene spec §4.6).
- Only `geovista.units` may import `pint`, `pint_cf` or `lark`, as `tests/units/test_import.py` enforces over every import in the package, type-only imports included.
- New public names go in `__all__`, sorted (`RUF022`), with NumPy docstrings and `.. versionadded:: 0.6.0` under `Notes`. `mypy` runs strict over the whole package, with no new override. Warnings are errors under pytest.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: enhancement`, `feature: crs` and `agentic`.
- Cite a specification section in plain text (`scene spec §4.4`), never with a `{ref}` role.

## Calls Made in This Plan

Calls 1 and 2 were put to {user}`bjlittle` before planning, on 2026-10-27. Calls 3 to 11 are made here. Calls 3, 4 and 8 amend the scene specification, in Task 6.

1. **The row is bounded.** It is planned from the scene specification, which is the child specification of globe spec §9 row 2, with no further one.
2. **No `pyvista.accessors` entry point.** `mesh.gv` exists once `geovista` is imported, as scene spec §4.6 says. Through an entry point, a script that imported only `pyvista` would load `geovista` on its first `.gv`, and importing `geovista` sets `pyvista`'s global plot theme.
3. **A radius takes forms 1 and 2 of globe spec §4.2**: a plain number in metres, or a `pint` quantity from any registry. A magnitude with a CF unit string reaches a globe through `to_metres`, as `Globe(radius=to_metres(6371, "km"))`, since `Globe` takes four keywords and a radius with a CF unit string would need a fifth. This amends scene spec §4.1 and the globe item of §6.
4. **A value of the wrong type raises a `TypeError` naming its keyword**: a `bool`, a `str`, a `pint` quantity given as a render radius or a factor, and an array given as a radius. A string would otherwise reach `to_metres` and be read as metres. This amends scene spec §4.1.
5. **`geovista.units` gains `as_quantity(metres)`**, which returns a length in metres as a quantity in `pint`'s application registry, read at each call so that `pint.set_application_registry` is honoured, and a public type alias, `Quantity`, for annotations elsewhere. `Globe.radius` uses them, since no other module may import `pint`.
6. **A globe's repr rebuilds it**, with its radius as a plain number in metres: `Globe(radius=6378137.0, render_radius=1.0, exaggeration=1.0, exaggeration_below=1.0)`.
7. **The relative spread is `(max - min) <= 1e-6 * max`** over the float64 norms of the points. A mesh with no points, or a point that is not finite, or a largest radius that is not positive, has no globe.
8. **A radius read from float32 points is rounded to float32.** `pv.Sphere()` stores float32 points, whose mean radius is 1 ± 6 × 10⁻¹⁰ (measured below), so that without rounding `Globe.from_mesh(pv.Sphere()) != Globe()`. This amends scene spec §4.4 item 2.
9. **A recorded field that is not one finite number is refused**, with a `ValueError` naming the field, before the values are checked as a globe's.
10. **The table** is `RETIRED_FIELDS`, a tuple of `RetiredField`, a frozen dataclass with `name`, `association` (`"field"`, `"point"` or `"cell"`), `replacement`, `last_written` and `translate`, a callable that writes the replacement onto a mesh. `gvRadius` translates as `Globe.from_mesh(mesh).to_mesh(mesh)`, importing `Globe` inside the function, as `transform.py` imports `core`, since `geovista.globe` imports `geovista.common`.
11. **The namespace** is `geovista.accessor.GeoVistaAccessor`. Its module imports only `pyvista` at the top, and imports `geovista.globe` and `geovista.crs` as they are used, so that `import geovista` loads neither `pyproj` nor `pint`. Assigning to `mesh.gv.crs` names `geovista.transform.transform_mesh`. `resize` takes `globe=` only from row 2, but both rows land before 0.6, so no release names a call that does not exist.

## Review Focus

1. **A float32 sphere.** `pv.Sphere().gv.globe` must equal `Globe()`. `test_a_float32_sphere_reads_at_its_radius` (Task 3).
2. **A copied mesh.** `pyvista` caches the accessor on the mesh, so a copy's `gv` must read the copy's record, never the original's. `test_a_copy_reads_its_own_record` (Task 5).
3. **A degenerate mesh**, with no points, every point at the origin, or a point that is NaN. Its globe must be `None`, never an exception. `test_a_degenerate_mesh_has_no_globe` (Task 3).
4. **A value of the wrong type**, such as `radius="6371 km"` or `exaggeration=True`. It must raise a `TypeError`, never build a globe of 6,371 m or a factor of 1. `test_a_value_of_the_wrong_type_is_refused` (Task 2).
5. **A mesh with the four fields and a `gvRadius`.** The four fields win, and cleaning keeps the globe they record. `test_the_four_fields_win_over_gvradius` (Task 3) and `test_keeps_a_recorded_globe` (Task 4).

---

Measured on 2026-10-27 at `801616b1`, with Python 3.14.9, `pyvista` 0.49.1, VTK 9.7.1, NumPy 2.5.4 and `pint` 0.26.2, in the `geovista` environment:

- `pv.Sphere()` stores float32 points. At resolutions of 30 and 100, their radii spread by 6.4 × 10⁻⁸ and 7.1 × 10⁻⁸, and their float64 means are 1.0000000003660252 and 0.9999999994261561, which round to exactly 1.0 in float32.
- `Transform.from_1d` stores float64 points at one radius, with a spread of 0, and writes `gvCRS` and `gvRadius`.
- The four fields, as float64 arrays of one value, the CRS and the points of a `from_1d` mesh read back bit for bit from binary legacy `.vtk`, `.vtp`, `.vtu` (as an `UnstructuredGrid`) and `.vtkhdf`, through `mesh.save` and `pv.read`.
- `import geovista` took 0.64 s, warm, and loaded `pyvista` and VTK, but neither `pyproj`, `pint`, `geovista.common` nor `geovista.crs`.
- `to_metres(6378.137, "km")` and a `pint` quantity of 6378.137 km both give exactly 6378137.0.
- `pyvista.register_dataset_accessor(name, target_cls, *, override=False)` warns and replaces on a clash with another accessor, and no `pyvista` mesh class has an attribute named `gv`.

### Task 1: A Length as a Quantity

**Files:**
- Modify: `src/geovista/units.py`
- Create: `tests/units/test_as_quantity.py`

**Interfaces:**
- Produces: `as_quantity(metres: float) -> Quantity`, and `type Quantity = pint.Quantity`, both in `__all__`.

- [ ] **Step 1: Write the failing tests**

```python
import pint
import pytest

from geovista.units import as_quantity


def test_a_length_in_metres_in_the_application_registry():
    quantity = as_quantity(6378137.0)
    assert format(quantity.units, "D") == "meter"
    assert quantity.magnitude == 6378137.0
    other = pint.get_application_registry().Quantity(1, "km")
    assert (quantity + other).to("m").magnitude == 6379137.0


def test_the_magnitude_is_a_float():
    assert type(as_quantity(1).magnitude) is float


def test_honours_the_application_registry_set():
    previous = pint.get_application_registry().get()
    registry = pint.UnitRegistry()
    pint.set_application_registry(registry)
    try:
        assert (as_quantity(1.0) + registry.Quantity(1, "m")).magnitude == 2.0
    finally:
        pint.set_application_registry(previous)
```

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/units/test_as_quantity.py -q`
Expected: FAIL, with `ImportError: cannot import name 'as_quantity'`.

- [ ] **Step 3: Implement `as_quantity` and `Quantity` in `src/geovista/units.py`**

`import pint` inside the function, with `# noqa: PLC0415`, and return `pint.get_application_registry().Quantity(float(metres), "m")`. Declare `type Quantity = pint.Quantity` beside the `TYPE_CHECKING` import of `pint`, which a `type` statement never evaluates at runtime. Add both to `__all__` and the module docstring.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/units -q`
Expected: PASS, including `test_plain_numbers_never_import_pint` and `test_only_units_imports_pint`.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/units.py tests/units/test_as_quantity.py
git add src/geovista/units.py tests/units/test_as_quantity.py
pixi run --frozen -e geovista git commit -m "feat: give a length in metres as a quantity in pint's application registry"
```

### Task 2: The Globe

**Files:**
- Create: `src/geovista/globe.py`
- Modify: `src/geovista/__init__.pyi` (import `Globe` from `.globe`, and add it to `__all__`)
- Create: `tests/globe/__init__.py` (the licence header and `"""Unit-tests for :mod:`geovista.globe`."""`)
- Create: `tests/globe/test_Globe.py`
- Create: `tests/globe/test_import.py`

**Interfaces:**
- Consumes: `to_metres` (`geovista.units`); `as_quantity` and `Quantity` (Task 1); `RADIUS` (`geovista.common`).
- Produces: `class Globe` with `__init__(self, *, radius: float | Quantity = 6378137.0, render_radius: float = RADIUS, exaggeration: float = 1.0, exaggeration_below: float | None = None) -> None`, and the read-only properties `radius -> Quantity`, `render_radius -> float`, `exaggeration -> float`, `exaggeration_below -> float` and `scale -> float`. It keeps its radius as a float in metres, privately.

- [ ] **Step 1: Write the failing tests**

`tests/globe/test_Globe.py`, with `EARTH = 6378137.0`:

```python
def test_the_defaults():
    globe = Globe()
    assert globe.radius.to("m").magnitude == EARTH
    assert (globe.render_radius, globe.exaggeration, globe.exaggeration_below) == (
        RADIUS,
        1.0,
        1.0,
    )


@pytest.mark.parametrize(
    "radius",
    [
        6371000,
        6371000.0,
        np.float32(6371000.0),
        pint.UnitRegistry().Quantity(6371, "km"),
        pint.get_application_registry().Quantity(6371000, "m"),
        to_metres(6371, "km"),
    ],
)
def test_a_radius_in_each_form_reads_as_metres(radius):
    assert Globe(radius=radius).radius.to("m").magnitude == 6371000.0


KEYWORDS = ["radius", "render_radius", "exaggeration", "exaggeration_below"]


@pytest.mark.parametrize("keyword", KEYWORDS)
@pytest.mark.parametrize("value", [0, -1.0, math.inf, math.nan])
def test_a_value_not_finite_and_positive_is_refused(keyword, value):
    with pytest.raises(ValueError, match=f"{keyword} must be finite and positive"):
        Globe(**{keyword: value})


@pytest.mark.parametrize("keyword", KEYWORDS)
@pytest.mark.parametrize("value", [True, "6371 km", "20"])
def test_a_value_of_the_wrong_type_is_refused(keyword, value):
    with pytest.raises(TypeError, match=keyword):
        Globe(**{keyword: value})


def test_a_radius_is_one_length():
    with pytest.raises(TypeError, match="radius"):
        Globe(radius=np.array([1.0, 2.0]))


@pytest.mark.parametrize("keyword", KEYWORDS[1:])
def test_a_ratio_is_a_plain_number(keyword):
    with pytest.raises(TypeError, match=keyword):
        Globe(**{keyword: pint.UnitRegistry().Quantity(2, "m")})


def test_exaggeration_alone_sets_both_factors():
    globe = Globe(exaggeration=20)
    assert (globe.exaggeration, globe.exaggeration_below) == (20.0, 20.0)


def test_exaggeration_below_sets_the_factor_below_alone():
    globe = Globe(exaggeration_below=100)
    assert (globe.exaggeration, globe.exaggeration_below) == (1.0, 100.0)


def test_an_int_factor_reads_back_as_a_float():
    globe = Globe(exaggeration=20, exaggeration_below=100)
    assert type(globe.exaggeration) is float
    assert type(globe.exaggeration_below) is float


def test_a_factor_below_one_is_accepted():
    assert Globe(exaggeration=0.5).exaggeration == 0.5


@pytest.mark.parametrize("render_radius", [1.0, EARTH])
def test_the_scale(render_radius):
    assert Globe(render_radius=render_radius).scale == render_radius / EARTH


def test_equal_values_make_equal_globes():
    one = Globe(
        radius=6371000, render_radius=2, exaggeration=20, exaggeration_below=100
    )
    two = Globe(
        radius=pint.UnitRegistry().Quantity(6371, "km"),
        render_radius=2.0,
        exaggeration=20.0,
        exaggeration_below=100.0,
    )
    assert one == two
    assert hash(one) == hash(two)
    assert one != Globe(radius=6371000, render_radius=2, exaggeration=20)
    assert Globe() != object()


def test_a_globe_cannot_be_changed():
    with pytest.raises(AttributeError):
        Globe().render_radius = 2.0


def test_the_repr_rebuilds_the_globe():
    globe = Globe(
        radius=6371000, render_radius=2, exaggeration=20, exaggeration_below=100
    )
    assert eval(repr(globe), {"Globe": Globe}) == globe  # noqa: S307
    assert repr(Globe()) == (
        "Globe(radius=6378137.0, render_radius=1.0, exaggeration=1.0, "
        "exaggeration_below=1.0)"
    )


def test_the_radius_adds_to_a_quantity_of_the_application_registry():
    other = pint.get_application_registry().Quantity(1, "km")
    assert (Globe().radius + other).to("m").magnitude == 6379137.0


def test_exported_at_the_top_level():
    assert geovista.Globe is Globe
```

`tests/globe/test_import.py` runs this script with `subprocess.run([sys.executable, "-c", PLAIN], check=True)  # noqa: S603`, as `tests/units/test_import.py` does, in `test_a_globe_imports_no_pint`:

```python
PLAIN = """
import sys

from geovista.globe import Globe

globe = Globe(radius=6371000, exaggeration=20)
globe.render_radius, globe.exaggeration, globe.exaggeration_below, globe.scale
globe == Globe(), hash(globe), repr(globe)
loaded = [name for name in sys.modules if name == "pint" or name.startswith("pint.")]
assert not loaded, loaded
"""
```

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/globe -q`
Expected: FAIL, with `ModuleNotFoundError: No module named 'geovista.globe'`.

- [ ] **Step 3: Implement `Globe` in `src/geovista/globe.py`**

Check the type of each value before `to_metres` sees it: a `bool`, a `str`, or for the three ratios anything but a real number (`numbers.Real`, which NumPy's scalars register as) raises `TypeError(f"{keyword} must be a plain number, got {value!r}")`; a radius may also be a `pint` quantity, and one that converts to an array raises `TypeError` that it must be one length. Then a value that is not finite, or not positive, raises `ValueError(f"{keyword} must be finite and positive, got {value!r}")`. Keep the four values as floats; equality and hashing use them as a tuple, and assignment to any attribute raises `AttributeError`. The class docstring says that land below sea level, such as the Dead Sea, takes the factor below (globe spec §4.1). `__all__ = ["Globe"]`.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/globe tests/units -q`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/globe.py src/geovista/__init__.pyi tests/globe/__init__.py tests/globe/test_Globe.py tests/globe/test_import.py
git add src/geovista/globe.py src/geovista/__init__.pyi tests/globe
pixi run --frozen -e geovista git commit -m "feat: add the globe a scene is drawn on"
```

### Task 3: The Globe on a Mesh

**Files:**
- Modify: `src/geovista/common.py` (four constants, after `GV_FIELD_CRS`, and `__all__`)
- Modify: `src/geovista/crs.py` (`projected` takes `pv.DataSet`, which it already handles, reading only `bounds` and field data)
- Modify: `src/geovista/globe.py`
- Create: `tests/globe/test_from_mesh.py`
- Create: `tests/globe/test_to_mesh.py`
- Create: `tests/globe/test_round_trip.py`
- Modify: `tests/globe/test_import.py`

**Interfaces:**
- Consumes: `Globe` (Task 2); `crs.projected`; `common.GV_FIELD_RADIUS`.
- Produces: `GV_FIELD_GLOBE_RADIUS = "gvGlobeRadius"`, `GV_FIELD_GLOBE_RENDER_RADIUS = "gvGlobeRenderRadius"`, `GV_FIELD_GLOBE_EXAGGERATION_ABOVE = "gvGlobeExaggerationAbove"` and `GV_FIELD_GLOBE_EXAGGERATION_BELOW = "gvGlobeExaggerationBelow"` in `geovista.common`; `Globe.from_mesh(cls, mesh: pv.DataSet) -> Globe | None`, a classmethod; `Globe.to_mesh(self, mesh: pv.DataSet) -> None`.

- [ ] **Step 1: Write the failing tests**

The tests build meshes with `Transform.from_1d(LONS, LATS, radius=r)`, where `LONS = np.linspace(-180, 180, 9)` and `LATS = np.linspace(-90, 90, 5)`, which writes `gvCRS` and `gvRadius`, and parametrize `r` over `RADII = [1.0, 6378137.0]` (scene spec §6, the radius). `FIELDS` is the four constants, in the order above.

`tests/globe/test_to_mesh.py`:

```python
def test_writes_four_float64_fields_and_no_gvradius():
    mesh = Transform.from_1d(LONS, LATS)
    Globe(exaggeration=20, exaggeration_below=100).to_mesh(mesh)
    for name, value in zip(FIELDS, [6378137.0, 1.0, 20.0, 100.0], strict=True):
        assert mesh.field_data[name].dtype == np.float64
        assert mesh.field_data[name].tolist() == [value]
    assert GV_FIELD_RADIUS not in mesh.field_data
```

`tests/globe/test_from_mesh.py`:

- `test_the_four_fields_give_the_globe[r]`: `Globe(radius=6371000, render_radius=r, exaggeration=20, exaggeration_below=100).to_mesh(pv.PolyData())`, then `from_mesh` returns an equal globe.
- `test_the_four_fields_win_over_gvradius`: a mesh recording `Globe(render_radius=2)`, given a `gvRadius` of `[3.0]` after, reads as `Globe(render_radius=2)`.
- `test_a_partial_record_is_refused`: a mesh with only `gvGlobeRadius` and `gvGlobeRenderRadius` raises `ValueError` matching `"gvGlobeExaggerationAbove"`.
- `test_a_recorded_field_is_one_number`: `gvGlobeRadius` of `[1.0, 2.0]` raises `ValueError` matching `"gvGlobeRadius"`.
- `test_a_recorded_value_is_checked`: `gvGlobeRenderRadius` of `[0.0]` raises `ValueError` matching `"render_radius must be finite and positive"`.
- `test_gvradius_gives_the_render_radius[r]`: the `from_1d` mesh reads as `Globe(render_radius=r)`.
- `test_a_sphere_reads_at_its_radius[r]`: the `from_1d` mesh, with `gvRadius` deleted, reads as `Globe(render_radius=r)`.
- `test_a_float32_sphere_reads_at_its_radius`: `from_mesh(pv.Sphere()) == Globe()`, and `from_mesh(pv.Sphere(radius=2.0)) == Globe(render_radius=2.0)`.
- `test_a_flat_mesh_has_no_globe`: `from_mesh(pv.Plane())` is `None`.
- `test_a_warped_mesh_has_no_globe`: `geovista.pantry.meshes.lfric_orog()` with `gvRadius` deleted reads as `Globe()`, and once warped as its example warps it, with `compute_normals(cell_normals=False, point_normals=True, inplace=True)` and `warp_by_scalar(inplace=True, factor=2e-5)`, as `None` (scene spec §3.4).
- `test_a_degenerate_mesh_has_no_globe`: `pv.PolyData()`, `pv.PolyData(np.zeros((3, 3)))`, and a sphere from `from_1d` with `gvRadius` deleted and one point set to NaN each read as `None`.
- `test_reading_leaves_the_mesh_unchanged`: for the `from_1d` mesh, with and without its `gvRadius`, `from_mesh` leaves `mesh == mesh.copy()` taken before, and the field data names the same.

`tests/globe/test_round_trip.py`, the round trip of crs spec §6 as scene spec §4.3 has it:

```python
@pytest.mark.parametrize("suffix", [".vtk", ".vtp", ".vtu", ".vtkhdf"])
@pytest.mark.parametrize("render_radius", RADII)
def test_the_crs_and_globe_survive_a_file(tmp_path, suffix, render_radius):
    mesh = Transform.from_1d(LONS, LATS, radius=render_radius)
    globe = Globe(
        radius=6371000,
        render_radius=render_radius,
        exaggeration=20,
        exaggeration_below=100,
    )
    globe.to_mesh(mesh)
    if suffix == ".vtu":
        mesh = mesh.cast_to_unstructured_grid()
    path = tmp_path / f"mesh{suffix}"
    mesh.save(path)  # binary, by default
    back = pv.read(path)
    assert from_wkt(back) == from_wkt(mesh)
    assert Globe.from_mesh(back) == globe
    assert back.points.dtype == mesh.points.dtype
    assert np.array_equal(back.points, mesh.points)
```

`tests/globe/test_import.py`: `PLAIN` also builds `mesh = pv.Sphere()`, calls `globe.to_mesh(mesh)` and `Globe.from_mesh(mesh)`, and reads `Globe.from_mesh(pv.Sphere())`, before the assertion.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/globe -q`
Expected: FAIL, with `ImportError` for `GV_FIELD_GLOBE_RADIUS`.

- [ ] **Step 3: Implement the constants, `to_mesh` and `from_mesh`**

`to_mesh` writes each value as `np.array([value], dtype=np.float64)` and deletes `GV_FIELD_RADIUS` when present. `from_mesh` reads the four fields when all are present, each as one finite number or a `ValueError` naming the field, then builds the globe, whose own checks name a bad value. With some of them, it raises `ValueError` naming those missing. With none, it reads `gvRadius` as `cls(render_radius=float(value[0]))`, and otherwise measures:

```python
if mesh.n_points == 0 or projected(mesh):
    return None
radii = np.linalg.norm(np.asarray(mesh.points, dtype=np.float64), axis=1)
if not np.all(np.isfinite(radii)):
    return None
low, high = float(radii.min()), float(radii.max())
if high <= 0 or high - low > _SPREAD * high:
    return None
radius = float(radii.mean())
if mesh.points.dtype == np.float32:
    radius = float(np.float32(radius))
return cls(render_radius=radius)
```

`_SPREAD = 1e-6` is private to the module, with a comment citing scene spec §4.4. Each constant's docstring names what it records.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/globe tests/crs tests/common -q`
Expected: PASS. The round trip passes as soon as `to_mesh` exists, since it guards the formats rather than new code.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/common.py src/geovista/crs.py src/geovista/globe.py tests/globe/*.py
git add src/geovista/common.py src/geovista/crs.py src/geovista/globe.py tests/globe
pixi run --frozen -e geovista git commit -m "feat: record a globe on a mesh, and read one that records none"
```

### Task 4: Retired Fields

**Files:**
- Modify: `src/geovista/common.py`
- Create: `tests/common/test_sanitize_legacy.py`
- Modify: `tests/common/test_sanitize.py`

**Interfaces:**
- Consumes: `Globe.from_mesh` and `Globe.to_mesh` (Task 3), imported inside the translation with `# noqa: PLC0415`.
- Produces: `RetiredField`, a frozen dataclass with `name: str`, `association: Literal["field", "point", "cell"]`, `replacement: str`, `last_written: str` and `translate: Callable[[pv.DataSet], None]`; `RETIRED_FIELDS: tuple[RetiredField, ...]`; `sanitize_legacy(*meshes: pv.DataSet) -> None`; and `sanitize(*meshes, extra=None, vtk=True, legacy=True)`. All are in `__all__`.

- [ ] **Step 1: Write the failing tests**

`tests/common/test_sanitize_legacy.py`, with the `from_1d` meshes and `RADII` of Task 3:

```python
def test_the_table_lists_gvradius():
    (entry,) = [e for e in RETIRED_FIELDS if e.name == GV_FIELD_RADIUS]
    assert (entry.association, entry.last_written) == ("field", "0.5.3")
    assert len({e.name for e in RETIRED_FIELDS}) == len(RETIRED_FIELDS)


@pytest.mark.parametrize("render_radius", RADII)
def test_translates_and_removes_gvradius(render_radius):
    mesh = Transform.from_1d(LONS, LATS, radius=render_radius)
    points = mesh.points.copy()
    sanitize_legacy(mesh)
    assert GV_FIELD_RADIUS not in mesh.field_data
    assert Globe.from_mesh(mesh) == Globe(render_radius=render_radius)
    assert np.array_equal(mesh.points, points)


def test_cleans_every_mesh():
    meshes = [Transform.from_1d(LONS, LATS, radius=r) for r in RADII]
    sanitize_legacy(*meshes)
    assert not any(GV_FIELD_RADIUS in m.field_data for m in meshes)


def test_keeps_a_recorded_globe():
    mesh = Transform.from_1d(LONS, LATS)
    Globe(render_radius=2).to_mesh(mesh)
    mesh.field_data[GV_FIELD_RADIUS] = np.array([3.0])
    sanitize_legacy(mesh)
    assert Globe.from_mesh(mesh) == Globe(render_radius=2)
    assert GV_FIELD_RADIUS not in mesh.field_data


def test_a_mesh_with_no_retired_field_is_unchanged():
    mesh = pv.Sphere()
    sanitize_legacy(mesh)
    assert list(mesh.field_data) == []


def test_needs_a_mesh():
    with pytest.raises(ValueError, match="Expected one or more meshes to sanitize"):
        sanitize_legacy()
```

`tests/common/test_sanitize.py` gains `test_legacy_by_default`, after which a `from_1d` mesh has no `gvRadius` and records `Globe()`, and `test_legacy_off`, after which `sanitize(mesh, legacy=False)` leaves its `gvRadius` and records no globe fields.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/common/test_sanitize_legacy.py tests/common/test_sanitize.py -q`
Expected: FAIL, with `ImportError` for `RETIRED_FIELDS`.

- [ ] **Step 3: Implement the table, `sanitize_legacy` and `legacy=`**

The `gvRadius` entry has `replacement="the globe, in gvGlobeRadius, gvGlobeRenderRadius, gvGlobeExaggerationAbove and gvGlobeExaggerationBelow"`. Its `translate` reads `Globe.from_mesh(mesh)`, which a `gvRadius` always answers, and writes it back with `to_mesh`. `sanitize_legacy` raises the `ValueError` of `sanitize_vtk` for no meshes; for each mesh and entry present in the data its `association` names, it translates, then deletes the field if still present, warning nothing. `sanitize` calls it when `legacy` is true. The docstring of `GV_FIELD_RADIUS` names it retired, last written by 0.5.3, and points to `RETIRED_FIELDS`.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/common tests/globe -q`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/common.py tests/common/test_sanitize_legacy.py tests/common/test_sanitize.py
git add src/geovista/common.py tests/common
pixi run --frozen -e geovista git commit -m "feat: list retired fields in one table, and clean them with sanitize_legacy"
```

### Task 5: The `gv` Namespace

**Files:**
- Create: `src/geovista/accessor.py`
- Modify: `src/geovista/__init__.py` (import `accessor` eagerly, after `themes`, with a comment that it registers `mesh.gv`)
- Create: `tests/accessor/__init__.py`
- Create: `tests/accessor/test_GeoVistaAccessor.py`
- Create: `tests/accessor/test_import.py`
- Modify: `tests/globe/test_import.py`

**Interfaces:**
- Consumes: `Globe.from_mesh` (Task 3); `crs.from_wkt`.
- Produces: `GeoVistaAccessor`, registered as `gv` on `pv.DataSet`, with `__init__(self, mesh: pv.DataSet) -> None` and the read-only properties `globe -> Globe | None` and `crs -> CRS | None`. It is equal to another when their CRSs and globes are, and unhashable.

- [ ] **Step 1: Write the failing tests**

`tests/accessor/test_GeoVistaAccessor.py`, with the `from_1d` meshes and `RADII` of Task 3:

- `test_every_mesh_has_the_namespace`: `pv.PolyData()`, `pv.UnstructuredGrid()`, `pv.StructuredGrid()` and `pv.ImageData()` each have a `gv` that is a `GeoVistaAccessor`.
- `test_reads_what_the_mesh_records[r]`: `mesh.gv.crs == from_wkt(mesh)` and `mesh.gv.globe == Globe(render_radius=r)`.
- `test_follows_a_change_to_its_field_data`: after a first read, `Globe(exaggeration=20).to_mesh(mesh)` makes `mesh.gv.globe == Globe(exaggeration=20)`, and deleting `gvCRS` makes `mesh.gv.crs` `None`.
- `test_a_copy_reads_its_own_record`: after `mesh.gv.globe` is read, `other = mesh.copy()` given `Globe(render_radius=2).to_mesh(other)` reads `Globe(render_radius=2)`, while `mesh.gv.globe` is still `Globe()`.
- `test_the_globe_cannot_be_set`: `mesh.gv.globe = Globe()` raises `AttributeError` matching `re.escape("resize(mesh, globe=...)")`.
- `test_the_crs_cannot_be_set`: `mesh.gv.crs = None` raises `AttributeError` matching `"transform_mesh"`.
- `test_equal_when_the_crs_and_globe_are`: `from_1d(LONS, LATS).gv == from_1d(LONS[:5], LATS).gv`; it is unequal to a mesh recording `Globe(render_radius=2)`, and to one with `gvCRS` deleted; and `(mesh.gv == object()) is False`.
- `test_is_unhashable`: `hash(mesh.gv)` raises `TypeError`.
- `test_the_repr_names_geovista`: `"geovista"` is in `repr(mesh.gv)`, and in that of a mesh with a partial record, whose repr does not raise.

`tests/accessor/test_import.py`, `test_importing_geovista_registers_the_namespace`, runs in a subprocess:

```python
LIGHT = """
import sys

import pyvista as pv

import geovista

assert type(pv.PolyData().gv).__name__ == "GeoVistaAccessor"
heavy = {"pyproj", "pint", "geovista.globe", "geovista.crs"} & set(sys.modules)
assert not heavy, heavy
"""
```

`tests/globe/test_import.py`: `PLAIN` also reads `mesh.gv.globe` before its assertion.

- [ ] **Step 2: Run them to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/accessor tests/globe/test_import.py -q`
Expected: FAIL, with `ModuleNotFoundError: No module named 'geovista.accessor'`.

- [ ] **Step 3: Implement `GeoVistaAccessor` in `src/geovista/accessor.py`**

Decorate the class with `@pv.register_dataset_accessor("gv", pv.DataSet)`. Each property imports what it reads inside itself, with `# noqa: PLC0415`. Assigning `globe` raises `AttributeError("mesh.gv.globe cannot be set, since a globe describes where a mesh's points are: use geovista.core.resize(mesh, globe=...) to move them and record it")`, and assigning `crs` names `geovista.transform.transform_mesh` the same way. `__eq__` returns `NotImplemented` for anything else, and `__hash__ = None`. The repr is `<geovista namespace: globe=..., crs=...>`, with the CRS by its name, and a globe that cannot be read shown by its error. The class docstring calls it the `gv` namespace that `geovista` adds to every `pyvista` mesh. `__all__ = ["GeoVistaAccessor"]`.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/accessor tests/globe tests/units -q`
Expected: PASS.

- [ ] **Step 5: Run the hooks and commit**

```bash
pixi run --frozen -e geovista pre-commit run --files src/geovista/accessor.py src/geovista/__init__.py tests/accessor/*.py tests/globe/test_import.py
git add src/geovista/accessor.py src/geovista/__init__.py tests/accessor tests/globe/test_import.py
pixi run --frozen -e geovista git commit -m "feat: add the gv namespace to every pyvista mesh"
```

### Task 6: Land the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-10-27-globe-scene-design.md` (§4.1, §4.4 item 2, §4.6, §6 and §9 row 1)
- Modify: `AGENTS.md` (the architecture tree gains `globe.py`, `accessor.py` and `units.py`, and stays under 200 lines)
- Modify: `tests/AGENTS.md` (`accessor/` and `globe/` join the test directories, and it stays under 200 lines)
- Create: `changelog/<PR>.feature.rst`

- [ ] **Step 1: Amend the scene specification for calls 3, 4 and 8, humanized, and the guides**

§4.1: a radius is a plain number in metres or a `pint` quantity from any registry, forms 1 and 2 of globe spec §4.2, and a magnitude with a CF unit string reaches a globe through `geovista.units.to_metres`; a value of the wrong type, such as a string or `True`, raises a `TypeError`. §4.4 item 2: the radius read from float32 points is rounded to float32, with the measurement of this plan. §4.6 names the class `geovista.accessor.GeoVistaAccessor`. §6, the globe: a radius in either form, and one read through `to_metres` from a CF unit string, reads as metres. Then the two `AGENTS.md` changes of **Files**.

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py tests/test_status_references.py tests/test_renumbering.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-renumbering`.
Expected: the tests pass, and no citation went stale.

```bash
git add docs/src/developer/specs/2026-10-27-globe-scene-design.md AGENTS.md tests/AGENTS.md
pixi run --frozen -e geovista git commit -m "docs: amend the scene spec for the calls row 1 made"
```

- [ ] **Step 2: Run the whole suite, on the committed tree**

Run: `CI=true LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe pixi run --frozen -e geovista tests-unit`
Expected: PASS, with no new skips. `test_option_version` fails on a dirty tree, so commit first.

- [ ] **Step 3: Build the docs strictly, after the suite**

Run the strict `sphinx-build` of `AGENTS.md` with `-W --keep-going`, then `ls docs/_build/html/reference/generated/api/geovista/globe docs/_build/html/reference/generated/api/geovista/accessor`.
Expected: the build succeeds, and the API reference has a page for each new module.

- [ ] **Step 4: Open the pull request**

Push `feat/globe-record` and open it with the labels of the Global Constraints, and a humanized body listing calls 3 to 11.

- [ ] **Step 5: Write the fragment, and mark the row**

`changelog/<PR>.feature.rst`, humanized:

```rst
Added :class:`geovista.Globe`, the globe a scene is drawn on: the Earth's
radius, the radius it is drawn at, and the exaggeration of heights above and
below sea level. A mesh records its globe in four fields, and one saved before
the globe is read from its ``gvRadius``. Every ``pyvista`` mesh gains a
read-only ``gv`` namespace, holding its globe and CRS, and
:func:`geovista.common.sanitize_legacy` cleans retired fields from a mesh.
(:user:`claude`)
```

Mark scene spec §9 row 1 ``✅ landed (YYYY-MM-DD, {pull}`<PR>`)``. Globe spec §9 row 2 stays `not started` until scene spec §9 row 2 lands with it.

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py <PR> "changelog/<PR>.feature.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>`.
Expected: the fragment passes, the tests pass, and every status reference holds.

- [ ] **Step 6: Commit and push**

```bash
git add changelog/<PR>.feature.rst docs/src/developer/specs/2026-10-27-globe-scene-design.md
pixi run --frozen -e geovista git commit -m "docs: mark scene spec row 1 landed, and add the changelog fragment"
git push
```
