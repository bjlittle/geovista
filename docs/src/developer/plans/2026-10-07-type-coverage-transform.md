---
orphan: true
---

# type coverage change 2 — `transform.py`

```{readingtime}
```

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** take `geovista.transform` out of the typing ratchet so that `mypy` checks it in
full, and make `transform_mesh` honour the `zlevel : int or ArrayLike` that its signature
and docstring promise.

**Architecture:** most of what `mypy` reports against `transform.py` is not a defect in
it. `numpy` and `pyproj` reach the module through `lazy_loader`, which ships no
annotations, so `mypy` types both as `Any` and cannot see the conversions the code already
makes: `transform_points` converts with `np.atleast_1d` on its first line. Importing both
under `TYPE_CHECKING`, as `common.py` already does for `numpy`, clears 102 of the 129
errors left once `lazy_loader`'s own import error is suppressed. The remainder is eleven
annotations to correct, one of them in `crs.py`, and one genuine `ArrayLike` defect:
`transform_mesh` mishandles any `zlevel` that is not a scalar.

**Tech Stack:** `mypy` 1.x in strict mode, `numpy`, `pyproj`, `pyvista` 0.49, `pytest` with
`pytest-xdist`, `pixi` (conda-forge).

**Spec:** `docs/src/developer/specs/2026-10-06-type-coverage-design.md`, cited throughout
as `typing spec §…`. This plan implements change 2 of typing spec §4.

**Branch:** `debt/typing-transform`, whose prefix earns `type: tech-debt` automatically.
The plan is committed first and the pull request held in draft until the implementation
lands on it.

## Global Constraints

- **Copyright header.** Every Python file opens with the four-line BSD header given in the
  root `AGENTS.md`, followed by `from __future__ import annotations`. Both are ruff-enforced.
- **Line length 88.** `[tool.ruff]` in `pyproject.toml`.
- **Docstrings.** NumPy style, validated by `numpydoc-validation` on `src/`.
  `--doctest-modules` is on, so a `>>>` in any docstring is executed.
- **The strictness settings stay as they are:** `strict`, `warn_unreachable` and the
  three `enable_error_code` entries (typing spec §7).
- **An `ArrayLike` parameter is converted at the boundary, never narrowed**, and a
  docstring that already promises `array_like` is unchanged (typing spec §3.3, §5).
  Behaviour only widens: no existing caller may break.
- **No `type: ignore`.** Each error is corrected at its cause. Where the cause is an
  upstream annotation, the workaround is a `typing.cast` whose comment names the defect,
  and typing spec §8 records the trigger that retires it.
- **The ratchet only shrinks, in step.** `geovista.transform` leaves the `ignore_errors`
  list in `pyproject.toml` and `RATCHET_BASELINE` in `tests/test_typing_ratchet.py` in the
  same change (typing spec §3.2).
- **Every commit passes the `mypy` hook**, so the module leaves the ratchet in the same
  commit that makes it pass. Task 2's intermediate counts are measurements, never commits.
- **Tests run in parallel.** Since #2578 `tests-unit` runs under `pytest-xdist`, while plain
  `pytest` stays serial. Every test this plan adds is a pure computation, touching no file
  and no cache, so it is safe either way. Run both.
- **Changelog.** One towncrier fragment, `{PR}.bugfix.rst`, signed ``:user:`claude` ``.
  Pass the `agentic` label explicitly to `gh pr create`.
- **Names.** Repository text names the reviewer as {user}`bjlittle`.

## Four corrections this plan makes to the spec

All four were measured on 2026-10-07 against `main` at `48fce4e7`. The spec is a living
document, so task 3 corrects it in place.

1. **Typed imports carry most of `transform.py`, not conversions.** Typing spec §3.3
   attributes 20 of the module's lines to the `ArrayLike` idiom and prescribes
   `np.asanyarray` at the boundary. But `transform_points` already converts, with
   `np.atleast_1d`; `mypy` cannot see it, because `np = lazy.load("numpy")` is `Any` to
   `mypy` and assigning an `Any` never narrows a parameter. Importing `numpy` and `pyproj`
   under `TYPE_CHECKING` clears 102 of 129 errors, 14 of 27 lines, with no runtime
   change. This matters beyond change 2: the conversion §3.3 prescribes narrows only where
   `numpy` is visible, and `core.py`, `crs.py`, `filters.py`, `geoplotter.py`,
   `gridlines.py`, `raster.py`, `pantry/data.py` and `pantry/meshes.py` load it lazily with
   no such import. §3.3 gains a paragraph saying so.
2. **The `lazy_loader` override moves from change 6 to change 2.** Typing spec §8 item 5
   gives the `ignore_missing_imports` override for `lazy_loader` to change 6, and §7 says
   the untyped imports are change 6's. But every library module imports `lazy_loader`, so
   the first module to leave the ratchet meets it: with `transform.py` checked, its
   `import lazy_loader as lazy` is the one error outside the code. The override item 5
   already describes clears it and moves no other error (130 to 129). Its withdrawal
   trigger is unchanged.
3. **One error is upstream, and shares #2568's trigger.** `pyvista` 0.49 annotates
   `pyvista_ndarray.__setitem__` with `key: int | NumpyArray[int]`, which refuses the tuple
   index of `mesh.points[:, 0] = xs` that it accepts at runtime. `pyvista` pull request
   9262 widens the key to `_Index | tuple[_Index, ...]`, merged on 2026-09-22, after
   0.49.0. A `typing.cast` bridges it. The same `pyvista` release carries the fix #2568
   waits on, so a new §8 item records the cast against #2568.
4. **Scope: one annotation outside `transform.py`.** `crs.from_wkt` is annotated `-> CRS`,
   but returns `None` for a mesh with no CRS attached, which
   `tests/crs/test_from_wkt.py::test__no_crs` asserts. `mypy` therefore reports
   `transform_mesh`'s own check for that case as unreachable. Change 2 corrects the
   annotation and its `Returns` docstring, though `crs.py` stays in the ratchet for
   change 6. No caller breaks, since `projected` already tests the result for `None`.

Row 2's count reproduces: with the entry lifted on `main`, `mypy` reports 144 errors on
30 distinct lines, one of them the `lazy_loader` import that §7 sets aside, which leaves
the 29 the roadmap states.

## Review Focus

Five inputs or failure modes the spec implies but does not pin, most likely to bite first.
Each gets a test in the task that owns the code.

1. **A `zlevel` that cannot broadcast to the points**, such as a list one element too long,
   with `inplace=True`. A reasonable caller expects a `ValueError` naming the shape, raised
   before any point is written, so that their mesh is untouched. Today the x and y columns
   are overwritten first and a `TypeError` follows. → task 1,
   `test_transform_mesh__zlevel_that_cannot_broadcast`.
2. **The caller's `zlevel` array is never modified.** The point-cloud path adds the encoded
   z-level to `zlevel`, and an in-place `+=` on the converted value would write into the
   caller's array, or fail outright on an integer one. → task 1,
   `test_transform_mesh__zlevel_left_untouched`.
3. **Other `ArrayLike` members behave as a list does:** a tuple per-point `zlevel`, and a
   numpy scalar. → task 1, the `tuple` cases of `test_transform_mesh__zlevel_per_point`,
   and `test_transform_mesh__zlevel_numpy_scalar`.
4. **`trap=None` still disables the error check.** The signature admits `None`, and task 2
   passes `errcheck=bool(trap)` where `trap` went through untouched. An unreachable point
   must still come back `inf` for `None` and `False`, and only `True` may raise `ProjError`.
   → task 2, `test_untrapped_point_is_inf` and `test_trapped_point_raises`.
5. **A mesh with no CRS still raises `ValueError`.** The fix for `mypy`'s unreachable
   statement is to `from_wkt`'s annotation, never to the check it reported. → task 2,
   `test_transform_mesh__no_crs`.

---

### Task 1: honour a per-point `zlevel`

The one behavioural change. `transform_mesh` converts `zlevel` at the boundary, so a list,
a tuple and an array all behave as the scalar does when it is repeated per point.

**Files:**
- Modify: `src/geovista/transform.py`, in `transform_mesh`
- Test: `tests/transform/test_transform_mesh.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the local `level`, an `ndarray` that task 2 annotates around, and the
  fixture `cloud` and constant `PLANAR` in `tests/transform/test_transform_mesh.py`, which
  task 2's `test_transform_mesh__no_crs` reuses. Task 2 also adds the `pyvista` import
  that test needs; added here, ruff would reject it as unused.

- [ ] **Step 1: Write the failing tests**

In `tests/transform/test_transform_mesh.py`, after the `REGIONAL_MERIDIAN` constant add:

```python
#: A planar target CRS, so that a z-level is scaled into each point's z-value.
PLANAR = "+proj=eqc"
```

After the `regional_mesh` fixture add:

```python
@pytest.fixture
def cloud():
    """Create a small point cloud, which ``transform_mesh`` never slices."""
    return gv.Transform.from_points([10.0, 20.0, 30.0], [30.0, 40.0, 50.0])
```

Append to the end of the file:

```python
@pytest.mark.parametrize("mesh", ["regional_mesh", "cloud"])
@pytest.mark.parametrize("sequence", [list, tuple, np.array])
def test_transform_mesh__zlevel_per_point(request, mesh, sequence):
    """A per-point zlevel is honoured whatever form of ArrayLike carries it.

    Typing spec §3.3: the signature promises ``ArrayLike``, but before the
    conversion at the boundary a list or tuple met ``zlevel * zscale`` with
    ``TypeError``, and an array of more than one element raised ``ValueError``.

    """
    mesh = request.getfixturevalue(mesh)
    expected = transform_mesh(mesh.copy(), PLANAR, zlevel=2)
    zlevel = sequence([2] * mesh.n_points)

    result = transform_mesh(mesh.copy(), PLANAR, zlevel=zlevel)

    np.testing.assert_array_equal(result.points, expected.points)


def test_transform_mesh__zlevel_numpy_scalar(regional_mesh):
    """A numpy scalar is a scalar zlevel like any other."""
    expected = transform_mesh(regional_mesh.copy(), PLANAR, zlevel=2)

    result = transform_mesh(regional_mesh.copy(), PLANAR, zlevel=np.float64(2))

    np.testing.assert_array_equal(result.points, expected.points)


def test_transform_mesh__zlevel_left_untouched(cloud):
    """The caller's zlevel is never mutated, though a cloud adds to it."""
    zlevel = np.full(cloud.n_points, 2.0)

    _ = transform_mesh(cloud.copy(), PLANAR, zlevel=zlevel)

    np.testing.assert_array_equal(zlevel, np.full(cloud.n_points, 2.0))


def test_transform_mesh__zlevel_that_cannot_broadcast(regional_mesh):
    """A zlevel of the wrong length fails before any point is written."""
    before = regional_mesh.points.copy()
    zlevel = [2] * (regional_mesh.n_points + 1)

    with pytest.raises(ValueError, match="does not broadcast to its 9 points"):
        _ = transform_mesh(
            regional_mesh, PLANAR, zlevel=zlevel, slice_connectivity=False, inplace=True
        )

    np.testing.assert_array_equal(regional_mesh.points, before)
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `pixi run --frozen -e geovista pytest tests/transform/test_transform_mesh.py -k zlevel -v`

Expected: **6 failed, 3 passed.**

- `zlevel_per_point[list-regional_mesh]` and `[tuple-regional_mesh]` fail with
  `TypeError: can't multiply sequence by non-int of type 'float'`.
- `[array-regional_mesh]`, `[array-cloud]` and `zlevel_left_untouched` fail with
  `ValueError: The truth value of an array with more than one element is ambiguous`,
  raised by `if zlevel or cloud:`.
- `zlevel_that_cannot_broadcast` fails with the same `TypeError`, after the mesh's x and y
  columns have already been overwritten.
- `[list-cloud]` and `[tuple-cloud]` pass, by accident. On the cloud path `zlevel +=
  xyz[:, 2]` runs first, and Python resolves `+=` on a list or tuple through numpy's
  reflected `__radd__` before it tries `list.extend`, so the sum is element-wise and
  already an array.
- `zlevel_numpy_scalar` passes: a numpy scalar was always a scalar.

- [ ] **Step 3: Convert `zlevel` at the boundary**

In `transform_mesh`, replace:

```python
if zlevel is None:
    zlevel = 0
```

with:

```python
level = np.asanyarray(0 if zlevel is None else zlevel)
```

A new name rather than the parameter's own: task 2 types `level` as an `ndarray`, and
re-binding the parameter would leave it typed as the declared union.

Replace:

```python
if not inplace and not slice_connectivity:
    mesh = mesh.copy(deep=True)
```

with:

```python
if not inplace and not slice_connectivity:
    mesh = mesh.copy(deep=True)

try:
    np.broadcast_shapes(level.shape, (mesh.n_points,))
except ValueError:
    emsg = (
        f"Cannot transform mesh, 'zlevel' with shape {level.shape} does not "
        f"broadcast to its {mesh.n_points:,} points."
    )
    raise ValueError(emsg) from None
```

The check sits after slicing, which can add points, and before the first point is
written. A WGS84 target reaches `to_cartesian`, which has a broadcast check of its own,
only after this one has passed.

Then, in the calls and expressions that follow, use `level`:

- `zlevel=zlevel, zscale=zscale, stacked=False` becomes
  `zlevel=level, zscale=zscale, stacked=False`
- `if zlevel or cloud:` becomes `if np.any(level) or cloud:`
- `zlevel += xyz[:, 2]` becomes `level = level + xyz[:, 2]`, which allocates a new array,
  so the caller's is never written and an integer `level` is promoted, not cast
- `zs = zlevel * zscale * delta` becomes `zs = level * zscale * delta`

- [ ] **Step 4: Run the tests to see them pass**

Run: `pixi run --frozen -e geovista pytest tests/transform/test_transform_mesh.py -v`

Expected: PASS, every test in the file, the nine new ones included.

- [ ] **Step 5: Run the transform tests together**

Run: `pixi run --frozen -e geovista pytest tests/transform tests/crs`

Expected: PASS, none failed.

- [ ] **Step 6: Commit**

```bash
git add src/geovista/transform.py tests/transform/test_transform_mesh.py
pixi run --frozen -e geovista git commit -m "fix: honour a per-point zlevel in transform_mesh"
```

The `mypy` hook passes, since `transform.py` is still in the ratchet.

---

### Task 2: retire `geovista.transform` from the ratchet

Driven by `mypy` itself, as change 1's ratchet was: the failing check is the red step, and
each correction is measured. Every count below was taken on 2026-10-07 with task 1
applied.

**Files:**
- Modify: `pyproject.toml`, the `[[tool.mypy.overrides]]` blocks
- Modify: `tests/test_typing_ratchet.py`, `RATCHET_BASELINE`
- Modify: `src/geovista/transform.py`
- Modify: `src/geovista/crs.py`, `from_wkt`
- Test: `tests/transform/test_transform_points.py`, `tests/transform/test_transform_point.py`,
  `tests/transform/test_transform_mesh.py`

**Interfaces:**
- Consumes: task 1's `level` and `PLANAR`.
- Produces: `transform_point` and `transform_points` returning `NDArray[Any]`;
  `crs.from_wkt` returning `CRS | None`; a ratchet without `geovista.transform`, which task
  3 documents.

- [ ] **Step 1: Pin the contract the annotations will state**

These tests pass on `main` already, because the conversions are already in the code. They
fix behaviour that steps 4 to 8 must not move.

In `tests/transform/test_transform_points.py`, change
`from pyproj.exceptions import CRSError` to
`from pyproj.exceptions import CRSError, ProjError`, and append:

```python
#: A planar target CRS.
PLANAR = "+proj=eqc"

#: An orthographic projection, which cannot reach the far side of the globe.
ORTHO = "+proj=ortho +lat_0=0 +lon_0=0"


@pytest.mark.parametrize("zs", [None, [1.0, 2.0]], ids=["xy", "xyz"])
def test_lists(zs):
    """Lists are accepted wherever arrays are (typing spec §3.3)."""
    xs, ys = [0.0, 90.0], [10.0, 20.0]
    expected = transform_points(
        src_crs=WGS84,
        tgt_crs=PLANAR,
        xs=np.array(xs),
        ys=np.array(ys),
        zs=None if zs is None else np.array(zs),
    )

    result = transform_points(src_crs=WGS84, tgt_crs=PLANAR, xs=xs, ys=ys, zs=zs)

    np.testing.assert_array_equal(result, expected)


def test_nested_lists():
    """Nested lists keep their 2D shape, as arrays do."""
    xs, ys = [[0.0, 90.0], [10.0, 20.0]], [[10.0, 20.0], [30.0, 40.0]]
    expected = transform_points(
        src_crs=WGS84, tgt_crs=PLANAR, xs=np.array(xs), ys=np.array(ys)
    )

    result = transform_points(src_crs=WGS84, tgt_crs=PLANAR, xs=xs, ys=ys)

    assert result.shape == (2, 2, 3)
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize("trap", [None, False])
def test_untrapped_point_is_inf(trap):
    """With the trap off, a point the projection cannot reach comes back inf."""
    result = transform_points(
        src_crs=WGS84, tgt_crs=ORTHO, xs=[180.0], ys=[0.0], trap=trap
    )

    assert np.isinf(result[0, :2]).all()


def test_trapped_point_raises():
    """With the trap on, a point the projection cannot reach raises."""
    with pytest.raises(ProjError, match="outside of projection domain"):
        _ = transform_points(
            src_crs=WGS84, tgt_crs=ORTHO, xs=[180.0], ys=[0.0], trap=True
        )
```

In `tests/transform/test_transform_point.py`, append:

```python
def test_single_valued_lists():
    """A single valued list is a point, and the result is a (3,) array."""
    expected = transform_point(WGS84, "+proj=eqc", x=10.0, y=20.0)

    result = transform_point(WGS84, "+proj=eqc", x=[10.0], y=[20.0])

    assert isinstance(result, np.ndarray)
    assert result.shape == (3,)
    np.testing.assert_array_equal(result, expected)
```

In `tests/transform/test_transform_mesh.py`, add `import pyvista as pv` after
`import pytest`, and append:

```python
def test_transform_mesh__no_crs():
    """A mesh without a CRS cannot be transformed.

    ``mypy`` reported this check as unreachable while ``from_wkt`` claimed always
    to return a CRS. The annotation was wrong, not the check.

    """
    with pytest.raises(ValueError, match="no coordinate reference system"):
        _ = transform_mesh(pv.Sphere(), PLANAR)
```

Run: `pixi run --frozen -e geovista pytest tests/transform -k "lists or trap or no_crs" -v`

Expected: PASS, 8 tests. That they pass before anything changes is the point: they hold
the behaviour still while its annotations are corrected.

- [ ] **Step 2: Take the module out of the ratchet, and watch the check fail**

In `pyproject.toml`, delete `  "geovista.transform",` from the `module` list of the
`ignore_errors = true` block. In `tests/test_typing_ratchet.py`, delete
`        "geovista.transform",` from `RATCHET_BASELINE`. Its other mentions, in the
`_drift` tests near the end of the file, are sample data, and stay.

Run: `pixi run --frozen -e geovista pytest tests/test_typing_ratchet.py`

Expected: PASS. Removing a name from both lists is the one move the ratchet allows.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 130 errors in 1 file (checked 86 source files)`, every one in
`src/geovista/transform.py`. If the count differs, stop: the measurement this task rests
on has moved, and the steps below need re-deriving.

- [ ] **Step 3: Suppress `lazy_loader`'s missing annotations**

In `pyproject.toml`, insert this block before the `geovista.cli` override, the first of
the `[[tool.mypy.overrides]]` blocks:

```toml
[[tool.mypy.overrides]]
# typing spec §8 item 5 -- "lazy_loader" ships no "py.typed" (lazy-loader
# issue 181). Withdraw when the floor reaches a release carrying one.
ignore_missing_imports = true
module = ["lazy_loader"]


```

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 129 errors in 1 file`. The `import-untyped` error on
`import lazy_loader as lazy` is gone, and nothing else moved.

- [ ] **Step 4: Let `mypy` see `numpy` and `pyproj`**

In `src/geovista/transform.py`, replace:

```python
if TYPE_CHECKING:
    from numpy.typing import ArrayLike
    import pyvista as pv
```

with:

```python
if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import ArrayLike, NDArray
    import pyproj
    import pyvista as pv
```

The runtime `np = lazy.load("numpy")` and `pyproj = lazy.load("pyproj")` below it stay:
`mypy` reads the imports, the interpreter the assignments, exactly as in `common.py`.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 27 errors in 1 file`, on 13 lines: the `unreachable` statement after
`if src_crs is None:`; the `zscale` assignment from `mesh[GV_FIELD_ZSCALE]`; the
`set_central_meridian` assignment; `transformed[:, 0]`; the three `mesh.points[:, i] =`
lines; `zs = level * zscale * delta`; `result.shape` and `result[0]` in
`transform_point`; the `transformer.transform` call and the unpacking after it; and
`result.reshape` at the end of `transform_points`.

- [ ] **Step 5: Correct `from_wkt`'s return annotation**

In `src/geovista/crs.py`, replace `def from_wkt(mesh: pv.PolyData) -> CRS:` with
`def from_wkt(mesh: pv.PolyData) -> CRS | None:`, and in its docstring replace:

```
    Returns
    -------
    :class:`~pyproj.crs.CRS`
        The Coordinate Reference System.
```

with:

```
    Returns
    -------
    :class:`~pyproj.crs.CRS` or None
        The Coordinate Reference System, or ``None`` when the mesh has none
        attached.
```

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 26 errors in 1 file`. The `unreachable` error is gone, because the check
it reported is now reachable.

- [ ] **Step 6: Correct the annotations inside `transform_mesh`**

In `src/geovista/transform.py`, change `from typing import TYPE_CHECKING` to
`from typing import TYPE_CHECKING, Any, cast`. Then:

Replace `            zscale = mesh[GV_FIELD_ZSCALE]` with
`            zscale = float(mesh[GV_FIELD_ZSCALE][0])`. The field holds one value, which
`common.py`, `core.py` and `geoplotter.py` each read with `[0]` already.

Replace:

```python
mesh.rotate_z(-central_meridian, inplace=True)
tgt_crs = set_central_meridian(tgt_crs, 0)
```

with:

```python
mesh.rotate_z(-central_meridian, inplace=True)
rebased = set_central_meridian(tgt_crs, 0)
# both helpers locate the same parameter, and refuse the same
# non-degree prime meridian, so one that reads can be rewritten
assert rebased is not None
tgt_crs = rebased
```

`get_central_meridian` and `set_central_meridian` both return `None` exactly when
`_find_central_meridian` finds nothing or finds a prime meridian in a non-degree unit, so a
truthy `central_meridian` guarantees a rewrite. Checked on 2026-10-07 against EPSG:4807,
4813, 4820, 27572, 4901 and 4902.

Replace `        zs = 0` with `        zs: float | NDArray[Any] = 0.0`.

Replace:

```python
mesh.points[:, 0] = xs
mesh.points[:, 1] = ys
```

with:

```python
# pyvista 0.49 annotates "pyvista_ndarray.__setitem__" to refuse the tuple
# index it accepts at runtime, so the points are set through a cast
points = cast("NDArray[Any]", mesh.points)
points[:, 0] = xs
points[:, 1] = ys
```

and replace `        mesh.points[:, 2] = zs` with `        points[:, 2] = zs`. The cast
changes nothing at runtime: `points` is still the `pyvista_ndarray`, so its `__setitem__`
still marks the dataset modified, which `mesh.bounds` between the two writes relies on.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 20 errors in 1 file`.

- [ ] **Step 7: Return arrays as arrays**

`transform_point`, `transform_points` and its inner `combine` always return an `ndarray`,
and their callers index it. In `src/geovista/transform.py`:

- In both `def transform_point(` and `def transform_points(`, replace the return
  annotation `) -> ArrayLike:` with `) -> NDArray[Any]:`, and in each docstring's `Returns`
  section replace the type line `    ArrayLike` with `    ndarray`.
- Replace `    def combine(xs: ArrayLike, ys: ArrayLike, zs: ArrayLike | None = None) -> ArrayLike:`
  with:

  ```text
      def combine(
          xs: ArrayLike, ys: ArrayLike, zs: ArrayLike | None = None
      ) -> NDArray[Any]:
  ```

  and in its docstring's `Returns` section replace `        ArrayLike` with
  `        ndarray`.
- Replace `    return result[0]` with `    return result[0, :]`. The same row, but numpy
  types an integer index as `Any` and a slice as an `ndarray`.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 3 errors in 1 file`, all on the `transformer.transform` call and the
unpacking after it.

- [ ] **Step 8: Call `pyproj` the way its overloads describe**

`Transformer.transform` is overloaded on whether `zz` is given, returning a 2-tuple or a
3-tuple, and its `errcheck` is a `bool`. Replace:

```python
transformed = transformer.transform(xs, ys, zs, errcheck=trap)

if zs is None:
    (txs, tys), tzs = transformed, None
else:
    txs, tys, tzs = transformed
```

with:

```python
if zs is None:
    txs, tys = transformer.transform(xs, ys, errcheck=bool(trap))
    tzs = None
else:
    txs, tys, tzs = transformer.transform(xs, ys, zs, errcheck=bool(trap))
```

The behaviour is unchanged: `pyproj` read a `zz` of `None` as absent, and a `trap` of
`None` as false.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`.

- [ ] **Step 9: Run the tests, serial and parallel**

Run: `pixi run --frozen -e geovista pytest tests/transform tests/crs tests/test_typing_ratchet.py`

Expected: PASS, 198 passed and 1 xfailed.

Run: `pixi run --frozen -e geovista tests-unit "not image"`

Expected: PASS under `pytest-xdist`, none failed. Image tests segfault without a GPU, and
CI is where they run: the `zscale` read and the cast both sit on paths the image tests of
`add_points` and `add_mesh` exercise.

- [ ] **Step 10: Run the hooks**

Run: `pixi run --frozen -e geovista pre-commit run --files src/geovista/transform.py src/geovista/crs.py pyproject.toml tests/test_typing_ratchet.py tests/transform/test_transform_mesh.py tests/transform/test_transform_point.py tests/transform/test_transform_points.py`

Expected: all pass, `mypy`, `numpydoc-validation` and `taplo-format` among them. Read the
full output, not its tail.

- [ ] **Step 11: Commit**

```bash
git add pyproject.toml tests/test_typing_ratchet.py src/geovista/transform.py \
  src/geovista/crs.py tests/transform/
pixi run --frozen -e geovista git commit -m "fix: type check transform.py in full, out of the ratchet"
```

---

### Task 3: the spec, the guide and the changelog

The spec is corrected against the four measurements above, and the pull request's
number enters it here.

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md`: §3.3, §4, §7,
  §8, §9
- Modify: `AGENTS.md`
- Create: `changelog/{PR}.bugfix.rst`

**Interfaces:**
- Consumes: the measurements in "Four corrections this plan makes to the spec".
- Produces: row 2's `in progress` status, which task 4 lands.

- [ ] **Step 1: Say where the §3.3 conversion narrows**

In typing spec §3.3, after the paragraph ending "so the hot paths are unaffected.",
insert:

```markdown
The conversion narrows only where `mypy` can see `numpy`. A module that loads it lazily,
with `np = lazy.load("numpy")`, hands `mypy` an `Any`, and assigning an `Any` never
narrows an `ArrayLike` parameter, so the module must also import `numpy` under
`TYPE_CHECKING`, as `common.py` does. Change 2 measured this on `transform.py`, which
already converted with `np.atleast_1d` and still reported the idiom: importing `numpy` and
`pyproj` that way cleared 102 of its 129 errors on its own. `core.py`, `crs.py`,
`filters.py`, `geoplotter.py`, `gridlines.py`, `raster.py`, `pantry/data.py` and
`pantry/meshes.py` still load `numpy` without one.
```

- [ ] **Step 2: Mark row 2 in progress**

In the typing spec §4 table, change row 2's Status from `not started` to
`` in progress ({pull}`PR`) ``, substituting the real pull request number.

- [ ] **Step 3: Move the `lazy_loader` override to change 2**

In typing spec §7, in the "untyped imports" bullet, replace the closing two sentences,
"The configuration carries no such entry today. Handling all of this is part of
change 6.", with the text below. Rewrap it into the bullet at the spec's width with its
two-space indent, keeping each code span and role on one line:

```markdown
The configuration carries none for them yet. Change 2 cleared `lazy_loader`'s 19 early,
with the override of {ref}`§8 <typing-spec-8>` item 5, because the first module to leave
the ratchet imports it; the rest is part of change 6.
```

In typing spec §8, replace item 5 in full with:

```markdown
5. **Open** ({issue}`2570`) — **The `lazy_loader` override comes out when upstream
   allows.** The `ignore_missing_imports` override for `lazy_loader` clears all 19
   locally. It was meant for change 6, and change 2 brought it in, since every module that
   leaves the ratchet imports `lazy_loader` and the first could not pass without it. It
   comes out when the floor reaches a release carrying the marker, or when PEP 810 replaces
   `lazy_loader`, whichever is first.
```

- [ ] **Step 4: Record the cast**

Append to typing spec §8:

```markdown
6. **Open** ({issue}`2568`) — **The cast in `transform_mesh` waits on the same `pyvista`
   release.** `pyvista` 0.49 annotates `pyvista_ndarray.__setitem__` with
   `key: int | NumpyArray[int]`, which refuses the tuple index of `mesh.points[:, 0]`
   that it accepts at runtime, so change 2 sets the points through a `typing.cast`.
   `pyvista` pull request 9262 widens the key, merged on 2026-09-22 after 0.49.0, so the
   cast comes out with the floor that carries it, the trigger item 2 already waits on.
```

In typing spec §9, after the bullet citing `pyvista` issue 6589 and pull request 9162,
add:

```markdown
- `pyvista` pull request 9262, which widens the index `pyvista_ndarray.__setitem__`
  accepts, cited by item 6 of {ref}`§8 <typing-spec-8>`:
  <https://github.com/pyvista/pyvista/pull/9262>
```

- [ ] **Step 5: Stop quoting counts in `AGENTS.md`**

Both counts in the root `AGENTS.md` go stale with every change, and this one makes them
wrong. Replace the first line of the `mypy` warning:

```markdown
⚠️ **`mypy` is green because 23 modules are ratcheted, not because they pass.**
```

with:

```markdown
⚠️ **`mypy` is green because modules are ratcheted, not because they pass.**
```

and, three lines below it, replace `` The 642 errors sit under `ignore_errors`, which ``
with `` Their errors sit under `ignore_errors`, which ``. The line count is unchanged; the
file sits at 199 of its 200. The lesson change 2 adds, that a lazily loaded module needs a
`TYPE_CHECKING` import before any conversion narrows, lives in typing spec §3.3, where the
plans for changes 3 to 6 start.

- [ ] **Step 6: Write the changelog fragment**

`bugfix`, not `contributor`: a caller passing the per-point `zlevel` the signature
promises now gets what it asked for.

Create `changelog/{PR}.bugfix.rst`, substituting the real number:

```rst
``transform_mesh`` now honours a per-point ``zlevel`` given as a list, tuple or
array, as its ``ArrayLike`` annotation and docstring promise. On anything but a
point cloud a list or tuple failed with ``TypeError``, and an array of more than
one element failed everywhere with ``ValueError``. A ``zlevel`` that does not
broadcast to the points now raises ``ValueError`` before any point is written.
``geovista.transform`` also leaves the typing ratchet, so ``mypy`` checks it in
full. (:user:`claude`)
```

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py {PR} "changelog/{PR}.bugfix.rst"`

Expected: `🆗 Your changelog contribution looks good to me.`

- [ ] **Step 7: Verify the spec and the docs**

Run: `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py`

Expected: PASS. Row 2's `in progress` carries its pull request, item 5 and the new item 6
each cite an issue, and every new code span stays on one line.

Run, from `docs/`:

```bash
pixi run --frozen -e docs sphinx-build -b html -W --keep-going \
  -D plot_docstring=False -D plot_gallery=False \
  -D plot_inline=False -D plot_tutorial=False \
  -d _build/doctrees src _build/html
```

Expected: `build succeeded`, with no warnings. The corrected `Returns` sections render in
the API reference.

- [ ] **Step 8: Commit and push**

```bash
git add docs/src/developer/specs/2026-10-06-type-coverage-design.md AGENTS.md changelog/
pixi run --frozen -e geovista git commit -m "docs: correct the typing spec against change 2's measurements"
git push
```

- [ ] **Step 9: Tell the two issues the plan touched**

Run, substituting the real number:

```bash
gh issue comment 2568 --repo bjlittle/geovista --body "Change 2 of the typing roadmap (#{PR}) gives this issue a second job. \`transform_mesh\` now sets its points through a \`typing.cast\`, because pyvista 0.49 annotates \`pyvista_ndarray.__setitem__\` to refuse a tuple index. pyvista pull request 9262 fixes that on \`main\`, after 0.49.0, so the cast comes out with the same floor this issue waits on. Typing spec §8 item 6 records it."
gh issue comment 2570 --repo bjlittle/geovista --body "Change 2 of the typing roadmap (#{PR}) added the \`ignore_missing_imports\` override for \`lazy_loader\` early. Every module that leaves the ratchet imports it, so the first could not pass without it. Typing spec §8 item 5 now records the override as in place, and this issue tracks when it comes out."
```

Expected: each prints the comment's URL.

---

### Task 4: land row 2

Done on {user}`bjlittle`'s approval and **before** the merge. Change 1 of the published
specifications roadmap merged ahead of this step and needed a follow-up pull request to
land its row (#2576), so ask for the merge to wait for this commit.

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md`: §4

- [ ] **Step 1: Mark the row landed**

In the typing spec §4 table, replace row 2's `` in progress ({pull}`PR`) `` with
`` ✅ landed (TODAY, {pull}`PR`) ``, where `TODAY` is the expected merge date as
`YYYY-MM-DD`: a status's date is the day the state changed.

- [ ] **Step 2: Verify, commit and push**

Run: `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py`

Expected: PASS. A terminal status needs a date and a reference, and this one has both.

```bash
git add docs/src/developer/specs/2026-10-06-type-coverage-design.md
pixi run --frozen -e geovista git commit -m "docs: mark row 2 of the typing roadmap landed"
git push
```

---

## Done when

- `pixi run --frozen -e geovista mypy` exits 0 with `geovista.transform` absent from both
  the ratchet and `RATCHET_BASELINE`.
- The six task 1 tests were seen failing as step 2 describes, and then passing.
- `tests-unit "not image"` passes under `pytest-xdist`, and CI is green, image tests
  included.
- Typing spec §3.3, §4, §7, §8 and §9 agree with the measurements, and row 2 reads landed
  before the merge.
- #2568 and #2570 each carry a comment naming what change 2 did to them.
- The pull request carries `agentic` and `type: tech-debt`.
