---
orphan: true
---

# type coverage change 3 — `bridge.py`

```{readingtime}
```

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** take `geovista.bridge` out of the typing ratchet so that `mypy` checks it in
full, `rasterio` included, and fix the two defects that checking it brings to light:
`Transform.from_points` refusing lists, and `Transform.from_unstructured` keeping masked
points in their faces.

**Architecture:** `bridge.py` already imports `numpy` under `TYPE_CHECKING`, so unlike
`transform.py` its errors are not an artefact of `lazy_loader`. Of the 23 lines `mypy`
reports with the entry lifted, 13 are the `ArrayLike` idiom of typing spec §3.3: one
conversion in `from_points` clears two of them and fixes a genuine `AttributeError`, and
the other eleven sit in private helpers past a boundary that already converts, so they
are annotated with the arrays they receive. Eight are `from_unstructured`'s masked
arrays: two read a mask from points that `transform_points` has already stripped of one,
an unreleased regression from #1977 that taking the mask first fixes, and six are
variables given one type in one place and another elsewhere. The last two
are `rasterio`'s missing annotations, which typeshed's `types-rasterio` supplies; checked
against those stubs `from_tiff` reports eleven lines of its own, ten corrected in place and
one bridged with a `typing.cast` that typing spec §8 records. `pyproj` joins `numpy` under
`TYPE_CHECKING`.

**Tech Stack:** `mypy` 2.x in strict mode, `numpy` 2.5, `pyproj`, `pyvista` 0.49,
`rasterio` 1.5 with typeshed's `types-rasterio`, `pytest` with `pytest-xdist`, `pixi`
(conda-forge).

**Spec:** `docs/src/developer/specs/2026-10-06-type-coverage-design.md`, cited throughout
as `typing spec §…`. This plan implements change 3 of typing spec §4.

**Branch:** `debt/typing-bridge`, whose prefix earns `type: tech-debt` automatically. The
plan is committed first and the pull request held in draft until the implementation lands
on it. `{PR}` below is that pull request's number.

## Global Constraints

- **Copyright header.** Every Python file opens with the four-line BSD header given in the
  root `AGENTS.md`, followed by `from __future__ import annotations`. Both are ruff-enforced.
- **Line length 88.** `[tool.ruff]` in `pyproject.toml`.
- **Docstrings.** NumPy style, validated by `numpydoc-validation` on `src/`.
  `--doctest-modules` is on, so a `>>>` in any docstring is executed.
- **The strictness settings stay as they are:** `strict`, `warn_unreachable` and the
  three `enable_error_code` entries (typing spec §7).
- **A published `ArrayLike` parameter is converted at the boundary, never narrowed**, and
  a docstring that already promises `array_like` is unchanged (typing spec §3.3, §5). A
  private helper that only ever receives what a boundary has converted is annotated with
  what it receives: sphinx-autoapi publishes no private members (`private-members` is
  commented out of `autoapi_options` in `docs/src/conf.py`). Behaviour only widens: no
  existing caller may break.
- **No `type: ignore`.** Each error is corrected at its cause. Where the cause is an
  upstream annotation, the workaround is a `typing.cast` whose comment names the defect,
  and typing spec §8 records the trigger that retires it.
- **The ratchet only shrinks, in step.** `geovista.bridge` leaves the `ignore_errors`
  list in `pyproject.toml` and `RATCHET_BASELINE` in `tests/test_typing_ratchet.py` in the
  same change (typing spec §3.2).
- **Every commit passes the `mypy` hook**, so the module leaves the ratchet in the same
  commit that makes it pass. Task 4's intermediate counts are measurements, never commits.
- **A dependency is locked before it is used.** After editing `pyproject.toml`, run
  `pixi lock` first, or `--frozen` keeps running the previous environment (root
  `AGENTS.md`). Mirror the pin in `requirements/pypi-optional-devs.txt`, which `pixi`
  neither reads nor updates, and regenerate the exports with the commands
  `.github/workflows/ci-locks.yml` runs.
- **Tests run in parallel.** Since #2578 `tests-unit` runs under `pytest-xdist`, while
  plain `pytest` stays serial. Every test this plan adds is a pure computation except
  `test_crs`, which writes a GeoTIFF into its own `tmp_path`, so all are safe either way.
- **Local suite runs deselect `tests/docs/test_gallery_scenes.py::test_show`**, which
  renders without the `image` marker and crashes without a display (#2596). Never pass
  `-p no:cacheprovider`, and read a run's result from its failures and exit code, never
  from `tail`.
- **Changelog.** Two towncrier fragments, `{PR}.bugfix.rst` and `{PR}.dependency.rst`,
  signed ``:user:`claude` ``. Pass the `agentic` label explicitly to `gh pr create`.
- **Prose for other readers is humanized before it goes out:** the spec's new text,
  commit messages, the fragments, the pull request body and both issues. This plan is
  not.
- **Names.** Repository text names the reviewer as {user}`bjlittle`.

## Five corrections this plan makes to the spec

All five were measured on 2026-10-09 against `main` at `3f08356a`. The spec is a living
document, so task 5 corrects it in place.

1. **Row 3's count reproduces, and change 2 moved it.** With the entry lifted on the tree
   change 2 started from, `b0b927e8~1`, `mypy` reports 134 errors on 28 distinct lines,
   the roadmap's 28. On `main` it reports 97 on 23: change 2's `-> NDArray[Any]` return
   for `transform_points` cleared six of `bridge.py`'s lines and its `lazy_loader`
   override a seventh, and exposed two, `vector_xs = xs` and `vector_ys = ys` in
   `from_points`. So 28 − 7 + 2 = 23.
2. **One conversion, and the rest of the idiom is private.** Typing spec §3.3 attributes 19
   of `bridge.py`'s lines to the `ArrayLike` idiom, and 13 remain on `main`. Two are
   `from_points`, a public boundary that never converted: given lists for `xs` and `ys`
   and `vectors` in their own latitude-longitude CRS other than WGS84, it hands the lists
   to `vectors_to_cartesian`, which raises `AttributeError: 'list' object has no attribute
   'shape'`. Every other entry point of `Transform` accepts lists and builds the mesh that
   arrays do, measured on every one. The other eleven are `_verify_2d`, which only
   `from_2d` calls, after converting, and the `_contiguous` helper nested in
   `_as_contiguous_1d`, called after it converts. Both are private, so they are annotated
   with the `ndarray` they receive, and §3.3 gains a sentence on where its rule applies.
3. **`rasterio`'s imports go with change 3, through typeshed's stubs.** Typing spec §7
   counts `rasterio` among the distributions that ship no annotations, its two errors part
   of change 6. Both are in `bridge.py`, so they come with it, and {user}`bjlittle` chose
   on 2026-10-09 to clear them with typeshed's `types-rasterio` instead of an override like
   `lazy_loader`'s. `rasterio` ships no `py.typed` (its issue 2322 is open), but typeshed
   has carried stubs for it since June 2026 (typeshed pull request 15884), and conda-forge
   has `types-rasterio` 1.5.2.20261005, versioned to the locked `rasterio` 1.5.2, so an
   override's withdrawal trigger would already be met. Checked against the stubs, `mypy`
   reports 111 errors on 32 lines: the two import errors go, and eleven lines of
   `from_tiff` appear. One is a stub defect: `rasterio.transform.xy` types its rows and
   columns as `int | Sequence[int]`, though `rasterio` takes arrays and gives arrays back,
   so a `typing.cast` bridges it and §8 gains item 7. Two more gaps in the stubs, a `crs`
   typed `CRS` that is `None` for a GeoTIFF without one, and `read(masked=True)` typed as
   a plain array, are met by code that holds whichever is true. `pixi lock` changes by that
   one package, in each of the twelve environments that include `devs`. conda-forge also
   carries `types-shapely`, `pandas-stubs` and `types-click-default-group`, which change 6
   can use; `geopy` and `pooch` have none there.
4. **`mypy` found an unreleased regression.** `from_unstructured` drops points masked
   alike in `xs` and `ys` from the faces they belong to, by masking the connectivity it
   derives from their shape. #1977 (2026-01-15, in no release) sent every point through
   `transform_points` and read the mask from what came back, which never carries one, and
   `mypy` reported the read once change 2 typed that result as a plain array. Since then a
   masked point stays in its face, with its underlying value as its coordinate: v0.5.3
   builds faces of 4 and 3 points where `main` builds 4 and 4. {user}`bjlittle` chose on
   2026-10-09 to fix it here. The mask is now taken before the transform, so it applies
   whatever the CRS; before #1977 it applied to WGS84 points alone, since any transform
   dropped it.
5. **A check in the masked-connectivity branch cannot run.** `from_unstructured` refuses
   any connectivity that is not 2D, in `_verify_connectivity`, before it reaches that
   branch, so the branch's `np.atleast_2d` and its "Masked connectivity must be at most
   2D" `ValueError` never act. They are also what keeps `mypy` from seeing the masked
   array as one, so task 4 removes both and pins the 2D refusal with a test.

## Review Focus

Five inputs or failure modes the spec implies but does not pin, most likely to bite first.
Each gets a test in the task that owns the code.

1. **A GeoTIFF without a CRS is still read as WGS84.** Task 4 passes `from_2d` the CRS as
   WKT, which must stay `None` for a file without one, as `rasterio` gives, whatever its
   stubs say. → task 4, `test_crs`.
2. **Points masked on one axis alone keep their faces**, as in v0.5.3: only points masked
   alike in `xs` and `ys` leave. → task 2, `test_points_masked_on_one_axis_stay`.
3. **A fully masked connectivity still raises `ValueError`.** Its smallest index is
   `masked`, and converting that with `int()` would raise `MaskError` instead. → task 4,
   `test_fully_masked_connectivity`.
4. **A 3D masked connectivity is refused before any face is built**, by
   `_verify_connectivity`, which is why task 4 may remove the branch's own check. → task 4,
   `test_masked_connectivity_must_be_2d`.
5. **An RGB GeoTIFF's bands still stack into one row of channels per pixel** through the
   typed `np.dstack(list(data))`. → `test_extract`, whose `rgb` cases run real arrays
   through it and compare against `np.dstack(data)`, and task 4's update of
   `test_rgb_band`.

---

### Task 1: honour `ArrayLike` in `from_points`

The one public boundary of `Transform` that never converted. With `vectors` in the
points' own latitude-longitude CRS, other than WGS84, it hands the caller's `xs` and `ys`
to `vectors_to_cartesian` as they came.

**Files:**
- Modify: `src/geovista/bridge.py`, `Transform.from_points`
- Test: `tests/bridge/test_from_points.py`

**Interfaces:**
- Consumes: nothing.
- Produces: a `from_points` whose `xs` and `ys` are arrays from its first statement, which
  clears `vector_xs = xs` and `vector_ys = ys` for task 4.

- [ ] **Step 1: Write the failing test**

In `tests/bridge/test_from_points.py`, insert this method into `class TestVectors`,
indented four spaces and followed by a blank line, immediately before
`def test__nonlatlon_crs__fail(self):`. `blacken-docs` keeps the block at the margin:

```python
def test_crs__lists(self):
    """Check lists in place of arrays with an alternate latlon-type CRS.

    The vectors are in the CRS of the points, so their points are those given,
    which were used unconverted (typing spec §3.3).

    """
    mesh = Transform.from_points(
        list(self.lons),
        list(self.lats),
        vectors=(self.u, self.v),
        crs=self.crs_rotatedlatlon,
    )
    result = mesh[NAME_VECTORS].T
    expected = np.array(
        [
            [-0.474, -17.651, -13.786, -32.429],
            [15.592, 13.943, -5.499, 21.403],
            [16.02, -13.529, -2.168, 12.461],
        ]
    )
    assert np.allclose(result, expected, atol=0.001)
```

The expected values are `test_crs`'s, which makes the same call with arrays.

- [ ] **Step 2: Run it, and watch it fail**

Run: `pixi run --frozen -e geovista pytest tests/bridge/test_from_points.py -k crs__lists -v`

Expected: FAIL, `AttributeError: 'list' object has no attribute 'shape'`, raised in
`vectors_to_cartesian`.

- [ ] **Step 3: Convert at the boundary**

In `Transform.from_points`, replace:

```text
        .. versionadded:: 0.2.0

        """
        if clean is None:
            clean = BRIDGE_CLEAN
```

with:

```text
        .. versionadded:: 0.2.0

        """
        xs, ys = np.asanyarray(xs), np.asanyarray(ys)

        if clean is None:
            clean = BRIDGE_CLEAN
```

`np.asanyarray` returns an array unchanged, so a caller passing arrays sees no difference,
and a scalar becomes a 0-d array, which `transform_points` already accepts (`test_scalar`).

- [ ] **Step 4: Run the module's tests**

Run: `pixi run --frozen -e geovista pytest tests/bridge/test_from_points.py -v`

Expected: PASS, 17 tests.

- [ ] **Step 5: Commit**

```bash
git add src/geovista/bridge.py tests/bridge/test_from_points.py
pixi run --frozen -e geovista git commit -F <message>
```

Message, humanized before committing: `fix: accept lists in from_points with vectors in
the points' own crs`, with a body naming the `AttributeError`, the CRS condition, and the
test that failed first. `geovista.bridge` is still ratcheted, so the `mypy` hook passes.

---

### Task 2: leave masked points out of their faces again

The regression of correction 4. The mask is copied before `transform_points` drops it,
and the shape-derived connectivity is masked with it.

**Files:**
- Modify: `src/geovista/bridge.py`, `Transform.from_unstructured`
- Create: `tests/bridge/test_from_unstructured.py`

**Interfaces:**
- Consumes: nothing.
- Produces: in `from_unstructured`, `mask: np.ndarray | None`, and `connectivity_array:
  np.ndarray` declared before the branches that assign it. Task 4 types the rest of the
  method around both.

- [ ] **Step 1: Write the failing tests**

Create `tests/bridge/test_from_unstructured.py`:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :meth:`geovista.Transform.from_unstructured`."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.bridge import Transform
from geovista.crs import WGS84
from geovista.transform import transform_points

#: A planar CRS, whose coordinates are metres.
PLANAR = "+proj=eqc"

#: Two quads, side by side, as (2, 4) longitudes and latitudes.
LONS = [[0.0, 10.0, 10.0, 0.0], [20.0, 30.0, 30.0, 20.0]]
LATS = [[0.0, 0.0, 10.0, 10.0], [0.0, 0.0, 10.0, 10.0]]

#: The last point of the second quad masked.
MASK = [[False, False, False, False], [False, False, False, True]]


def _points(crs: str) -> tuple[np.ndarray, np.ndarray]:
    """Return the two quads' points in the given CRS."""
    xyz = transform_points(
        src_crs=WGS84, tgt_crs=crs, xs=np.array(LONS), ys=np.array(LATS)
    )
    return xyz[..., 0], xyz[..., 1]


@pytest.mark.parametrize("crs", [WGS84, PLANAR], ids=["wgs84", "planar"])
def test_masked_points_leave_their_faces(crs):
    """Points masked alike in x and y are dropped from the faces they belong to.

    Regressed by #1977, which sent every point through ``transform_points``
    and read the mask from what came back, which never has one. A masked point
    then stayed in its face, with its underlying value as its coordinate.

    """
    xs, ys = _points(crs)
    xs, ys = np.ma.masked_array(xs, mask=MASK), np.ma.masked_array(ys, mask=MASK)

    mesh = Transform.from_unstructured(xs, ys, crs=crs)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3, 3, 4, 5, 6])


@pytest.mark.parametrize("masked", ["xs", "ys"])
def test_points_masked_on_one_axis_stay(masked):
    """A mask on only one of x and y is not a mask on the point."""
    xs, ys = np.array(LONS), np.array(LATS)
    if masked == "xs":
        xs = np.ma.masked_array(xs, mask=MASK)
    else:
        ys = np.ma.masked_array(ys, mask=MASK)

    mesh = Transform.from_unstructured(xs, ys)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3, 4, 4, 5, 6, 7])
```

- [ ] **Step 2: Run them, and watch the regression fail**

Run: `pixi run --frozen -e geovista pytest tests/bridge/test_from_unstructured.py -v`

Expected: 2 failed, 2 passed. Both cases of `test_masked_points_leave_their_faces` fail
with `(shapes (10,), (9,) mismatch)`, the masked eighth point still closing a second quad,
`ACTUAL: array([4, 0, 1, 2, 3, 4, 4, 5, 6, 7])`. Both cases of
`test_points_masked_on_one_axis_stay` pass: that is the rule restored, not changed.

- [ ] **Step 3: Take the mask before the transform**

In `Transform.from_unstructured`, replace:

```text
        # flatten the points to 1D with shape (M,)
        xs, ys = xs.ravel(), ys.ravel()

        if crs is None:
```

with:

```text
        # flatten the points to 1D with shape (M,)
        xs, ys = xs.ravel(), ys.ravel()

        # points masked alike in x and y are left out of their faces, so copy the
        # mask now, as the transform drops it
        mask: np.ndarray | None = None
        if (
            np.ma.is_masked(xs)
            and np.ma.is_masked(ys)
            and np.array_equal(np.ma.getmaskarray(xs), np.ma.getmaskarray(ys))
        ):
            mask = np.ma.getmaskarray(xs).copy()

        if crs is None:
```

The copy stands where `np.copy(xs.mask)` stood, so the connectivity never shares the
caller's mask. Then replace:

```python
if isinstance(connectivity, tuple):
    ignore_start_index = True
```

with:

```python
connectivity_array: np.ndarray
if isinstance(connectivity, tuple):
    ignore_start_index = True
```

and replace:

```python
# generate connectivity array
if np.ma.is_masked(xs) and np.ma.is_masked(ys) and np.array_equal(xs.mask, ys.mask):
    connectivity_array = np.ma.arange(npts, dtype=dtype).reshape(connectivity)
    connectivity_array.mask = np.copy(xs.mask)
else:
    connectivity_array = np.arange(npts, dtype=dtype).reshape(connectivity)
```

with:

```python
# generate connectivity array
connectivity_array = np.arange(npts, dtype=dtype).reshape(connectivity)
if mask is not None:
    connectivity_array = np.ma.masked_array(
        connectivity_array, mask=mask.reshape(connectivity)
    )
```

- [ ] **Step 4: Run them again**

Run: `pixi run --frozen -e geovista pytest tests/bridge/test_from_unstructured.py -v`

Expected: PASS, 4 tests.

- [ ] **Step 5: Commit**

```bash
git add src/geovista/bridge.py tests/bridge/test_from_unstructured.py
pixi run --frozen -e geovista git commit -F <message>
```

Message, humanized: `fix: leave points masked alike out of their faces in
from_unstructured`, with a body naming #1977 as the cause, v0.5.3's faces against
`main`'s, the widening to every CRS, and the test that failed first.

---

### Task 3: check `rasterio` against its typeshed stubs

**Files:**
- Modify: `pyproject.toml`, `[tool.pixi.feature.devs.dependencies]`
- Modify: `requirements/pypi-optional-devs.txt`
- Modify: `pixi.lock`
- Modify: `requirements/geovista.yml`, `requirements/locks/geovista_linux-64_conda_spec.txt`,
  `requirements/locks/geovista_linux-64_conda_spec.yml`

**Interfaces:**
- Consumes: nothing.
- Produces: `types-rasterio` in every environment that includes `devs`, which task 4's
  `mypy` runs need.

- [ ] **Step 1: Add the dependency**

In `pyproject.toml`, under `[tool.pixi.feature.devs.dependencies]`, insert between `ruff`
and `zizmor`, beside the `rasterio` it types:

```toml
types-rasterio = ">=1.5.2,<2"
```

In `requirements/pypi-optional-devs.txt`, insert between `ruff <0.17` and `zizmor <1.31`:

```text
types-rasterio <1.6
```

The ceiling follows `rasterio <1.6` in `requirements/pypi-optional-exam.txt`, since the
stubs are versioned to the release they type.

- [ ] **Step 2: Lock it**

Run: `pixi lock`

Expected: each of `devs`, `devs-py313`, `devs-py314`, `docs`, `docs-py313`, `docs-py314`,
`geovista`, `geovista-py313`, `geovista-py314`, `test`, `test-py313` and `test-py314`
reports `+ (conda) types-rasterio 1.5.2.20261005`, and nothing else.

Run: `git diff --stat pixi.lock`

Expected: `1 file changed, 28 insertions(+)`. Anything else moving means the solve has
changed since this plan was measured: stop.

- [ ] **Step 3: Regenerate the exports**

The commands of `.github/workflows/ci-locks.yml`, which would otherwise leave them stale
until its weekly run:

```bash
pixi workspace export conda-explicit-spec --environment geovista --frozen --ignore-pypi-errors requirements/locks
pixi workspace export conda-environment --environment geovista requirements/geovista.yml
cd requirements/locks && pixi run --frozen -e geovista python lock2yaml.py && cd ../..
```

Run: `git diff --stat requirements/`

Expected: `requirements/geovista.yml` 1 insertion, `- types-rasterio >=1.5.2,<2`, and
each `geovista_linux-64_conda_spec` file 11 insertions and 10 deletions. The explicit
spec is in install order, so ten unchanged packages move to make room. Confirm that
sorted, `types-rasterio` is the only difference:

```bash
for f in requirements/locks/geovista_linux-64_conda_spec.{txt,yml}; do
  comm -3 <(git show HEAD:$f | sort) <(sort $f)
done
```

Expected: one line per file, the `types-rasterio-1.5.2.20261005` URL.

- [ ] **Step 4: Verify the environment**

Run: `pixi list -e geovista types-rasterio`

Expected: `types-rasterio` `1.5.2.20261005`.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`. `geovista.bridge` is still
ratcheted, and no other module imports `rasterio`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml pixi.lock requirements/
pixi run --frozen -e geovista git commit -F <message>
```

Message, humanized: `deps: add types-rasterio to the devs environment`, with a body
saying why the stubs and not an override (correction 3) and that the lock moved by that
package alone.

---

### Task 4: retire `geovista.bridge` from the ratchet

Driven by `mypy` itself, as change 2's ratchet task was: the failing check is the red
step, and each correction is measured. Every count below was taken on 2026-10-09 with
tasks 1 to 3 applied.

**Files:**
- Modify: `pyproject.toml`, the `ignore_errors` block of `[[tool.mypy.overrides]]`
- Modify: `tests/test_typing_ratchet.py`, `RATCHET_BASELINE`
- Modify: `src/geovista/bridge.py`
- Modify: `tests/bridge/test_from_tiff.py`, `tests/bridge/test_from_unstructured.py`
- Create: `tests/bridge/test_lists.py`

**Interfaces:**
- Consumes: task 1's converted `xs` and `ys`; task 2's `mask` and `connectivity_array:
  np.ndarray`; task 3's `types-rasterio`.
- Produces: `bridge.py` checked in full; `from_tiff` passing `from_2d` its CRS as WKT, or
  `None`; the `typing.cast` that task 5 records as typing spec §8 item 7.

- [ ] **Step 1: Pin the contract the annotations will state**

These pass already. They hold behaviour still while its code is retyped, and give typing
spec §6 its list tests for every entry point.

Append to `tests/bridge/test_from_unstructured.py`:

```python
def test_masked_connectivity():
    """Masked connectivity builds faces of different sizes."""
    connectivity = np.ma.masked_array(
        [[0, 1, 2, 3], [1, 4, 5, 0]], mask=[[0, 0, 0, 0], [0, 0, 0, 1]]
    )
    xs = [0.0, 10.0, 10.0, 0.0, 20.0, 20.0]
    ys = [0.0, 0.0, 10.0, 10.0, 0.0, 10.0]

    mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3, 3, 1, 4, 5])


def test_masked_connectivity_drops_faces_of_two_points():
    """A face left with fewer than three points is dropped, with a warning."""
    connectivity = np.ma.masked_array(
        [[0, 1, 2, 3], [1, 4, 5, 0]], mask=[[0, 0, 0, 0], [0, 0, 1, 1]]
    )
    xs = [0.0, 10.0, 10.0, 0.0, 20.0, 20.0]
    ys = [0.0, 0.0, 10.0, 10.0, 0.0, 10.0]

    with pytest.warns(UserWarning, match="defines 1 face with no vertices"):
        mesh = Transform.from_unstructured(xs, ys, connectivity=connectivity)

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3])


def test_start_index_is_found():
    """One-based connectivity is found from its smallest index."""
    xs = [0.0, 10.0, 10.0, 0.0]
    ys = [0.0, 0.0, 10.0, 10.0]

    mesh = Transform.from_unstructured(xs, ys, connectivity=[[1, 2, 3, 4]])

    np.testing.assert_array_equal(mesh.faces, [4, 0, 1, 2, 3])


def test_fully_masked_connectivity():
    """A connectivity with every index masked has no start index to find."""
    connectivity = np.ma.masked_array([[0, 1, 2]], mask=True)

    with pytest.raises(ValueError, match=r"closed interval \[0, 1\], got '--'"):
        _ = Transform.from_unstructured(
            [0.0, 10.0, 10.0], [0.0, 0.0, 10.0], connectivity=connectivity
        )


def test_masked_connectivity_must_be_2d():
    """Masked connectivity is held to two dimensions before any face is built."""
    connectivity = np.ma.masked_array([[[0, 1, 2, 3]]], mask=[[[0, 0, 0, 1]]])

    with pytest.raises(ValueError, match="got 3D connectivity array"):
        _ = Transform.from_unstructured(
            [0.0, 10.0, 10.0, 0.0], [0.0, 0.0, 10.0, 10.0], connectivity=connectivity
        )
```

Create `tests/bridge/test_lists.py`:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for lists given to :class:`geovista.Transform` where arrays may be."""

from __future__ import annotations

import numpy as np
import pytest

from geovista.bridge import Transform

#: Each factory with arguments given as lists, where its signature says ArrayLike.
CASES = {
    "from_1d": (
        Transform.from_1d,
        ([0.0, 10.0, 20.0], [0.0, 10.0]),
        {"data": [1.0, 2.0]},
    ),
    "from_1d_bounds": (
        Transform.from_1d,
        ([[0.0, 10.0], [10.0, 20.0]], [[0.0, 10.0]]),
        {},
    ),
    "from_2d": (
        Transform.from_2d,
        ([[0.0, 10.0], [0.0, 10.0]], [[0.0, 0.0], [10.0, 10.0]]),
        {"data": [5.0]},
    ),
    "from_points": (
        Transform.from_points,
        ([0.0, 10.0], [0.0, 10.0]),
        {"data": [1.0, 2.0], "zlevel": [1, 2]},
    ),
    "from_unstructured": (
        Transform.from_unstructured,
        ([0.0, 10.0, 10.0, 0.0], [0.0, 0.0, 10.0, 10.0]),
        {"connectivity": [[0, 1, 2, 3]], "data": [1.0]},
    ),
    "to_structured_grid": (
        Transform.to_structured_grid,
        ([0.0, 10.0], [0.0, 10.0], [0.0, 1.0]),
        {"data": [7.0]},
    ),
}


@pytest.mark.parametrize(
    ("factory", "args", "kwargs"), CASES.values(), ids=CASES.keys()
)
def test_lists(factory, args, kwargs):
    """Lists build the mesh that arrays do (typing spec §3.3)."""
    expected = factory(
        *(np.array(arg) for arg in args),
        **{key: np.array(value) for key, value in kwargs.items()},
    )

    result = factory(*args, **kwargs)

    np.testing.assert_array_equal(result.points, expected.points)
    assert result.array_names == expected.array_names
    for name in expected.array_names:
        np.testing.assert_array_equal(result[name], expected[name])


def test_instance_lists():
    """An instance built from lists attaches data given as a list."""
    transform = Transform(
        [0.0, 10.0, 10.0, 0.0], [0.0, 0.0, 10.0, 10.0], connectivity=[[0, 1, 2, 3]]
    )

    mesh = transform(data=[3.0])

    np.testing.assert_array_equal(mesh["cell_data"], [3.0])
```

Append to `tests/bridge/test_from_tiff.py`:

```python
@pytest.mark.parametrize("crs", [None, "EPSG:4326"])
def test_crs(tmp_path, crs):
    """A GeoTIFF without a CRS is read as WGS84, as one in WGS84 is."""
    rasterio = pytest.importorskip("rasterio")
    path = tmp_path / "pixels.tif"
    profile = {
        "count": 1,
        "crs": crs,
        "driver": "GTiff",
        "dtype": "uint8",
        "height": 2,
        "transform": rasterio.transform.from_origin(10.0, 20.0, 1.0, 1.0),
        "width": 3,
    }
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(np.arange(6, dtype="uint8").reshape(1, 2, 3))

    mesh = Transform.from_tiff(path)

    expected = Transform.from_2d(
        [[10.5, 11.5, 12.5], [10.5, 11.5, 12.5]],
        [[19.5, 19.5, 19.5], [18.5, 18.5, 18.5]],
        data=np.arange(6, dtype="uint8"),
    )
    np.testing.assert_array_equal(mesh.points, expected.points)
    np.testing.assert_array_equal(mesh.faces, expected.faces)
```

Run: `pixi run --frozen -e geovista pytest tests/bridge/test_from_unstructured.py tests/bridge/test_lists.py tests/bridge/test_from_tiff.py -k "connectivity or start_index or lists or test_crs" -v`

Expected: PASS, 14 tests. That they pass before anything changes is the point.

- [ ] **Step 2: Take the module out of the ratchet, and watch the check fail**

In `pyproject.toml`, delete `  "geovista.bridge",` from the `module` list of the
`ignore_errors = true` block. In `tests/test_typing_ratchet.py`, delete
`        "geovista.bridge",` from `RATCHET_BASELINE`. Its other mentions, in the `_drift`
tests near the end of the file, are sample data, and stay.

Run: `pixi run --frozen -e geovista pytest tests/test_typing_ratchet.py`

Expected: PASS. Removing a name from both lists is the one move the ratchet allows.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 105 errors in 1 file (checked 86 source files)`, every one in
`src/geovista/bridge.py`, on 26 distinct lines. If the count differs, stop: the
measurement this task rests on has moved, and the steps below need re-deriving.

- [ ] **Step 3: Annotate the private helpers with what they receive**

Correction 2. In `Transform._as_contiguous_1d`, replace:

```text
        def _contiguous(bnds: ArrayLike, kind: str) -> np.ndarray:
            """Verify and construct a contiguous bounds array.

            Parameters
            ----------
            bnds : ArrayLike
```

with:

```text
        def _contiguous(bnds: np.ndarray, kind: str) -> np.ndarray:
            """Verify and construct a contiguous bounds array.

            Parameters
            ----------
            bnds : ndarray
```

In `Transform._verify_2d`, replace `def _verify_2d(xs: ArrayLike, ys: ArrayLike) -> None:`
with `def _verify_2d(xs: np.ndarray, ys: np.ndarray) -> None:`, and in its docstring
replace:

```text
        xs : ArrayLike
            A (M+1, N+1) or (M, N, 4) x-axis array.
        ys : ArrayLike
            A (M+1, N+1) or (M, N, 4) y-axis array.
```

with:

```text
        xs : ndarray
            A (M+1, N+1) or (M, N, 4) x-axis array.
        ys : ndarray
            A (M+1, N+1) or (M, N, 4) y-axis array.
```

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 20 errors in 1 file`, on 15 lines.

- [ ] **Step 4: Type `from_unstructured`'s masked connectivity**

The smallest index is a numpy integer, which `start_index : int | None` cannot hold, and
`int()` would turn a fully masked connectivity's `ValueError` into a `MaskError`, so it
gets a local of its own. Replace:

```python
if not ignore_start_index:
    if start_index is None:
        start_index = connectivity_array.min()

    if start_index not in [0, 1]:
        emsg = (
            "Require a 'start_index' in the closed interval [0, 1], got "
            f"'{start_index}'."
        )
        raise ValueError(emsg)

    if start_index:
        connectivity_array -= start_index
```

with:

```python
if not ignore_start_index:
    # the smallest index is a numpy integer, or masked if every index is
    base = connectivity_array.min() if start_index is None else start_index

    if base not in [0, 1]:
        emsg = f"Require a 'start_index' in the closed interval [0, 1], got '{base}'."
        raise ValueError(emsg)

    if base:
        connectivity_array -= base
```

`np.ma.is_masked` narrows nothing, and only a masked array can be masked, so the branch
tests the type as well; the connectivity is already 2D (correction 5). Replace:

```python
if np.ma.is_masked(connectivity_array):
    # create face connectivity from masked vertex indices, thus
    # supporting varied mesh face geometry e.g., triangular, quad,
    # pentagon (et al) cells within a single mesh.
    connectivity_array = np.atleast_2d(connectivity_array)
    if (ndim := connectivity_array.ndim) > 2:
        emsg = f"Masked connectivity must be at most 2D, got {ndim}D."
        raise ValueError(emsg)
    n_faces = connectivity_array.shape[0]
```

with:

```python
if isinstance(connectivity_array, np.ma.MaskedArray) and np.ma.is_masked(
    connectivity_array
):
    # create face connectivity from masked vertex indices, thus
    # supporting varied mesh face geometry e.g., triangular, quad,
    # pentagon (et al) cells within a single mesh.
    n_faces = connectivity_array.shape[0]
```

The stacked faces are masked and the serialized ones are not, so they take two names.
Replace:

```python
faces = np.ma.hstack([n_vertices.reshape(-1, 1), connectivity_array]).ravel()
faces = faces[~faces.mask].data
```

with:

```python
stacked = np.ma.hstack([n_vertices.reshape(-1, 1), connectivity_array]).ravel()
faces = stacked[~stacked.mask].data
```

Run: `pixi run --frozen -e geovista mypy`

Expected: `Found 16 errors in 1 file`, on 11 lines, every one in `from_tiff`.

- [ ] **Step 5: Check `from_tiff` against the stubs**

At the top of `src/geovista/bridge.py`, replace `from typing import TYPE_CHECKING` with
`from typing import TYPE_CHECKING, cast`, and replace:

```python
if TYPE_CHECKING:
    import numpy as np
```

with:

```python
if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy as np
```

In `Transform.from_tiff`, `masked` takes a `bool`, and the stubs type `read` as returning
a plain array whatever `masked` says, so the mask and data are taken with the
`numpy.ma` functions that hold for either. `np.dstack` takes a sequence of arrays, one per
band. Replace:

```python
data = src.read(masked=extract) if rgb else src.read(band, masked=extract)

if extract:
    # ignore the mask on the alpha channel, if present
    mask = data[0].mask & data[1].mask & data[2].mask if rgb else data.mask
    # ensure there is masked data prior to extracting unmasked points
    extract = np.sum(mask) > 0
    data = data.data

if rgb:
    data = np.dstack(data).reshape(-1, count)
```

with:

```python
masked = bool(extract)
data = src.read(masked=masked) if rgb else src.read(band, masked=masked)

if extract:
    # ignore the mask on the alpha channel, if present
    masks = np.ma.getmaskarray(data)
    mask = masks[0] & masks[1] & masks[2] if rgb else masks
    # ensure there is masked data prior to extracting unmasked points
    extract = bool(np.sum(mask) > 0)
    data = np.ma.getdata(data)

if rgb:
    data = np.dstack(list(data)).reshape(-1, count)
```

The stub defect of correction 3. Replace:

```python
# rasterio 1.4.0 (regression) expects 1D arrays, fixed in 1.4.1
# see https://github.com/rasterio/rasterio/issues/3191
xs, ys = rio.transform.xy(src.transform, rows.flatten(), cols.flatten())

# ensure we have arrays, rather than a list of arrays
xs, ys = np.asanyarray(xs), np.asanyarray(ys)
```

with:

```python
# rasterio 1.4.0 (regression) expects 1D arrays, fixed in 1.4.1
# see https://github.com/rasterio/rasterio/issues/3191, though the
# rasterio stubs accept sequences only (typing spec §8 item 7)
coords = rio.transform.xy(
    src.transform,
    cast("Sequence[int]", rows.flatten()),
    cast("Sequence[int]", cols.flatten()),
)

# ensure we have arrays, rather than a list of arrays
xs, ys = np.asanyarray(coords[0]), np.asanyarray(coords[1])
```

No comment line may open with `# type`, which the `python-use-type-annotations` hook
reads as a type comment, so the comment says "the rasterio stubs" rather than open a
line with `types-rasterio`.

`rasterio`'s CRS is not a `CRSLike`, but its WKT is, and `pyproj` reads it through
`to_wkt` either way. Replace:

```text
            # create the geotiff mesh
            mesh = cls.from_2d(
                xs,
                ys,
                data=data,
                name=name,
                crs=src.crs,
```

with:

```text
            # rasterio's crs is no CRSLike, but its wkt is, and the crs is None
            # for a geotiff without one, which the rasterio stubs leave out
            crs = src.crs.to_wkt() if src.crs else None

            # create the geotiff mesh
            mesh = cls.from_2d(
                xs,
                ys,
                data=data,
                name=name,
                crs=crs,
```

Two of the module's tests pin the old calls with mocks, so they follow. In
`tests/bridge/test_from_tiff.py`, in both `test_rgb_band` and `test_extract`, replace
`    crs = mocker.sentinel.crs` with:

```python
crs = mocker.MagicMock(to_wkt=mocker.MagicMock(return_value=mocker.sentinel.wkt))
```

and in both of their `expected_kwargs`, replace `        "crs": crs,` with
`        "crs": mocker.sentinel.wkt,`. In `test_rgb_band`, replace:

```python
data = mocker.sentinel.data
mocked_read = mocker.MagicMock(return_value=data)
```

with:

```python
data = mocker.sentinel.data
bands = [mocker.sentinel.band] * band
mocked_read = mocker.MagicMock(return_value=bands if rgb else data)
```

and replace `        mocked_dstack.assert_called_once_with(data)` with
`        mocked_dstack.assert_called_once_with(bands)`.

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`.

Run: `pixi run --frozen -e geovista pytest tests/bridge/test_from_tiff.py -v`

Expected: PASS, 23 tests.

- [ ] **Step 6: Let `mypy` see `pyproj`**

As change 2 did for `transform.py`, so that `from_points`' `pyproj.CRS.from_user_input` is
checked rather than `Any`. In the `TYPE_CHECKING` block, replace:

```python
from numpy.typing import ArrayLike
import pyvista as pv
```

with:

```python
from numpy.typing import ArrayLike
import pyproj
import pyvista as pv
```

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`.

- [ ] **Step 7: Verify the whole**

Run: `pixi run --frozen -e geovista pytest tests/bridge tests/test_typing_ratchet.py`

Expected: PASS; `tests/bridge` holds 64 tests, 19 more than on `main`.

Run: `pixi run --frozen -e geovista pytest -m "not image" --numprocesses auto --dist worksteal --deselect tests/docs/test_gallery_scenes.py::test_show`

Expected: exit 0, `2698 passed`: `main`'s 2679 and the 19 this plan adds. The figure
assumes a docs build in `docs/_build`, without which `tests/docs` skips more.

Run: `pixi run --frozen -e geovista pre-commit run --files src/geovista/bridge.py tests/bridge/*.py tests/test_typing_ratchet.py pyproject.toml`

Expected: every hook passes.

- [ ] **Step 8: Check that the gallery's meshes do not move**

The unstructured gallery is built from the pantry's meshes, through `from_unstructured`
and `from_2d`. Fingerprint all of them on `main` and on the branch:

```bash
git worktree add --detach /tmp/geovista-main main
cat > /tmp/fingerprint.py <<'EOF'
import hashlib, inspect, json, sys, warnings
import numpy as np
from geovista.pantry import meshes

warnings.simplefilter("ignore")
found = {}
for name, fn in sorted(inspect.getmembers(meshes, inspect.isfunction)):
    if fn.__module__ != meshes.__name__ or name.startswith("_"):
        continue
    mesh, digest = fn(), hashlib.sha256()
    digest.update(np.ascontiguousarray(mesh.points).tobytes())
    digest.update(np.ascontiguousarray(getattr(mesh, "faces", [])).tobytes())
    for key in sorted(mesh.array_names):
        array = np.asarray(mesh[key])
        text = "".join(array.ravel()) if array.dtype.kind == "U" else None
        digest.update(key.encode())
        digest.update(text.encode() if text is not None else array.tobytes())
    found[name] = digest.hexdigest()
json.dump(found, open(sys.argv[1], "w"), indent=1)
EOF
(cd /tmp && PYTHONPATH=/tmp/geovista-main/src pixi run --manifest-path "$OLDPWD" --frozen -e geovista python /tmp/fingerprint.py /tmp/main.json)
(cd /tmp && PYTHONPATH="$OLDPWD/src" pixi run --manifest-path "$OLDPWD" --frozen -e geovista python /tmp/fingerprint.py /tmp/branch.json)
python3 -c "import json; a, b = (json.load(open(f'/tmp/{n}.json')) for n in ('main', 'branch')); print(len(a), [k for k in a if a[k] != b[k]])"
git worktree remove --force /tmp/geovista-main
```

Expected: `21 []`, every pantry mesh identical, points, faces and arrays. CI's image
tests then confirm the rendering.

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml src/geovista/bridge.py tests/
pixi run --frozen -e geovista git commit -F <message>
```

Message, humanized: `fix: take bridge.py out of the typing ratchet`, with a body
summarising corrections 2, 3 and 5 and the cast, and naming the tests changed and why.

---

### Task 5: the spec, the issues and the changelog

The spec is corrected against the five measurements above, the cast gets the issue §8
needs, and the pull request's number enters the spec here.

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md`: §3.3, §4, §7,
  §8, §9
- Create: `changelog/{PR}.bugfix.rst`, `changelog/{PR}.dependency.rst`

**Interfaces:**
- Consumes: the measurements in "Five corrections this plan makes to the spec".
- Produces: row 3's `in progress` status, which task 6 lands; the issue §8 item 7 cites.

- [ ] **Step 1: Say where the §3.3 rule applies**

In typing spec §3.3, after the paragraph ending "`pantry/meshes.py` still load `numpy`
without one.", insert:

```markdown
The rule governs published signatures. Change 3 found the `ArrayLike` idiom left on 13
of `bridge.py`'s lines once change 2 had landed, and one conversion, at the top of
`Transform.from_points`, cleared two of them and a genuine `AttributeError`. The other
eleven were private helpers that only ever receive what a boundary has converted,
`_verify_2d` and the `_contiguous` nested in `_as_contiguous_1d`, so they are annotated
with the `ndarray` they receive. The API reference publishes no private members.
```

- [ ] **Step 2: Mark row 3 in progress**

In the typing spec §4 table, change row 3's Status from `not started` to
`` in progress ({pull}`PR`) ``, substituting the real pull request number.

- [ ] **Step 3: Record where `rasterio`'s imports went**

In typing spec §7, in the "untyped imports" bullet, replace the closing sentence,
"Change 2 cleared `lazy_loader`'s 19 early, with the override of {ref}`§8 <typing-spec-8>`
item 5, because the first module to leave the ratchet imports it; the rest is part of
change 6.", with the text below. Rewrap it into the bullet at the spec's width with its
two-space indent, keeping each code span and role on one line:

```markdown
Change 2 cleared `lazy_loader`'s 19 early, with the override of {ref}`§8 <typing-spec-8>`
item 5, because the first module to leave the ratchet imports it. Change 3 cleared
`rasterio`'s 2 with typeshed's `types-rasterio` instead of an override: `rasterio` ships
no `py.typed`, but typeshed has carried stubs for it since June 2026, and checked against
them `from_tiff` reported eleven lines of its own. conda-forge also carries
`types-shapely`, `pandas-stubs` and `types-click-default-group`, and has none for `geopy`
or `pooch`. The rest is part of change 6.
```

- [ ] **Step 4: Report the stub gaps upstream**

{user}`bjlittle` reviews this draft with the plan, and it is filed only on that approval.
Humanize it first, then write it to `/tmp/typeshed-issue.md`:

````markdown
> Researched and drafted by Claude (Anthropic's AI model, in Claude Code), which also ran
> the measurements below; reviewed by @bjlittle before posting.

Three places where the `rasterio` stubs are narrower than `rasterio` 1.5.2 at runtime,
found while type checking geovista against `types-rasterio` 1.5.2.20261005.

1. `rasterio.transform.xy` types `rows` and `cols` as `int | Sequence[int]`, and its
   result as `tuple[float, float] | tuple[list[float], list[float]]`. `rasterio` takes
   numpy arrays, and gives arrays back for them:

   ```python
   rows, cols = np.meshgrid(np.arange(2), np.arange(3), indexing="ij")
   xs, ys = xy(transform, rows.flatten(), cols.flatten())
   type(xs)  # <class 'numpy.ndarray'>
   ```

   An `ndarray` is not a `Sequence`, so a caller passing one needs a cast.
2. `DatasetBase.crs` returns `CRS`, but a GeoTIFF without a CRS gives `None`.
3. `DatasetReaderBase.read` returns `NDArray[Any]` whatever `masked` is, but with
   `masked=True` it returns a `numpy.ma.MaskedArray`, so its `mask` does not type check.

If any of these would be welcome as a pull request, Claude can prepare one the same way,
for @bjlittle to review before it is opened.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

Run: `gh issue create --repo python/typeshed --title "[rasterio] numpy arrays in transform.xy, a crs of None, and read(masked=True)" --body-file /tmp/typeshed-issue.md`

Expected: the issue's URL. Add no labels; there are no rights to.

- [ ] **Step 5: Raise the issue §8 item 7 cites**

Write to `/tmp/cast-issue.md`, substituting the typeshed issue's URL and humanizing:

```markdown
`Transform.from_tiff` passes `rasterio.transform.xy` its pixel rows and columns as numpy
arrays, which `rasterio` takes and which the `types-rasterio` stubs refuse, typing them as
`int | Sequence[int]`. Change 3 of the typing roadmap (#{PR}) bridges that with a
`typing.cast`, recorded as typing spec §8 item 7.

The cast comes out when the stubs accept arrays. Reported upstream as <typeshed URL>,
alongside two gaps the code already meets without a cast: a `crs` of `None` typed as
`CRS`, and `read(masked=True)` typed as a plain array.
```

Run: `gh issue create --repo bjlittle/geovista --title "typing: drop the rasterio.transform.xy cast in from_tiff once the stubs take arrays" --label agentic --label "type: tech-debt" --body-file /tmp/cast-issue.md`

Expected: the issue's URL; its number is `ISSUE` below.

- [ ] **Step 6: Record the cast**

Append to typing spec §8, substituting the number:

```markdown
7. **Open** ({issue}`ISSUE`) — **The cast in `from_tiff` waits on typeshed.**
   `types-rasterio` types the rows and columns of `rasterio.transform.xy` as
   `int | Sequence[int]`, though `rasterio` takes arrays, which is what
   `Transform.from_tiff` passes, so change 3 passes them through a `typing.cast`. It
   comes out when the stubs accept arrays, reported to typeshed with two other gaps that
   the code meets without one.
```

In typing spec §9, append:

```markdown
- `typeshed` pull request 15884, which added the `rasterio` stubs that change 3 checks
  `bridge.py` against: <https://github.com/python/typeshed/pull/15884>
- The `typeshed` issue reporting the three gaps in those stubs, cited by item 7 of
  {ref}`§8 <typing-spec-8>`: <typeshed URL>
```

- [ ] **Step 7: Write the changelog fragments**

Create `changelog/{PR}.bugfix.rst`, humanized:

```rst
``Transform.from_points`` now accepts lists for ``xs`` and ``ys`` with
``vectors`` in their own latitude-longitude CRS other than WGS84, as its
``ArrayLike`` annotation promises; it raised ``AttributeError``.
``Transform.from_unstructured`` drops points masked alike in ``xs`` and ``ys``
from their faces whatever their CRS, where it did so for WGS84 alone.
``geovista.bridge`` also leaves the typing ratchet, so ``mypy`` checks it in
full. (:user:`claude`)
```

Create `changelog/{PR}.dependency.rst`, humanized:

```rst
Added typeshed's ``types-rasterio`` stubs to the ``devs`` environment, so
``mypy`` checks ``geovista.bridge`` against ``rasterio``'s own interface.
(:user:`claude`)
```

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py {PR} "changelog/{PR}.bugfix.rst,changelog/{PR}.dependency.rst"`

Expected: `🆗 Your changelog contribution looks good to me.`

- [ ] **Step 8: Verify the spec and the docs**

Run: `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py`

Expected: PASS. Row 3's `in progress` carries its pull request, item 7 cites its issue,
and every new code span stays on one line.

Run, from `docs/`:

```bash
pixi run --frozen -e docs sphinx-build -b html -W --keep-going \
  -D plot_docstring=False -D plot_gallery=False \
  -D plot_inline=False -D plot_tutorial=False \
  -d _build/doctrees src _build/html
```

Expected: `build succeeded`, with no warnings.

- [ ] **Step 9: Commit and push**

```bash
git add docs/src/developer/specs/2026-10-06-type-coverage-design.md changelog/
pixi run --frozen -e geovista git commit -F <message>
git push
```

Message, humanized: `docs: correct the typing spec against change 3's measurements`.

---

### Task 6: land row 3

The pull request's last commit, made once the implementation and every review round are
done, so that approving and merging are one step. Date it the day it is committed; if
the approval or merge slips to another day, correct the date before it lands.

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md`: §4

- [ ] **Step 1: Mark the row landed**

In the typing spec §4 table, replace row 3's `` in progress ({pull}`PR`) `` with
`` ✅ landed (TODAY, {pull}`PR`) ``, where `TODAY` is that day as `YYYY-MM-DD`.

- [ ] **Step 2: Verify, commit and push**

Run: `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py`

Expected: PASS. A terminal status needs a date and a reference, and this one has both.

```bash
git add docs/src/developer/specs/2026-10-06-type-coverage-design.md
pixi run --frozen -e geovista git commit -m "docs: mark row 3 of the typing roadmap landed"
git push
```

---

## Done when

- `pixi run --frozen -e geovista mypy` exits 0 with `geovista.bridge` absent from both the
  ratchet and `RATCHET_BASELINE`, and `types-rasterio` locked in every `devs` environment.
- `test_crs__lists` and both cases of `test_masked_points_leave_their_faces` were seen
  failing as tasks 1 and 2 describe, and then passing.
- `tests-unit "not image"` passes under `pytest-xdist`, the pantry fingerprints match
  `main`, and CI is green, image tests included.
- Typing spec §3.3, §4, §7, §8 and §9 agree with the measurements, and row 3 reads landed
  as the pull request's last commit.
- The typeshed report is filed and linked from the issue §8 item 7 cites.
- The pull request carries `agentic` and `type: tech-debt`.
