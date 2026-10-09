---
orphan: true
---

# planar z-levels — the Earth's radius in the units of the CRS

```{readingtime}
```

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** make a `zlevel` in a planar CRS lift every mesh and point cloud by the same
length, the Earth's radius in the units of that CRS, so that equal levels sit at equal
heights in a projected scene whatever the extent of each mesh.

**Architecture:** `transform_mesh` offsets a planar z by `level * zscale * delta`, where
`delta` is a quarter of the mesh's own x/y extent, floored. A private helper,
`_earth_radius`, computes `R` from the target CRS with `pyproj`, and the offset becomes
`level * zscale * R`. Nothing else in the transform changes: the globe keeps its level in
the radius, point clouds keep carrying theirs as `GV_POINT_ZLEVEL`, and `GeoPlotter` is
untouched because every projected layer already passes through `transform_mesh`.

**Tech Stack:** `pyproj` (`CRS.ellipsoid`, `CRS.axis_info`), `numpy`, `pyvista` 0.49,
`pytest` with `pytest-xdist`, `pixi` (conda-forge); the image baselines live in
`bjlittle/geovista-data`.

**Spec:** `docs/src/developer/specs/2026-10-08-planar-zlevel-design.md`, cited throughout
as `zlevel spec §…`. This plan implements row 1 of zlevel spec §4.

**Branch:** `fix/planar-zlevel`. The plan is committed first and the pull request held in
draft until the implementation lands on it.

## Global Constraints

- **Copyright header.** Every Python file opens with the four-line BSD header of the root
  `AGENTS.md`, then `from __future__ import annotations`. Both are ruff-enforced.
- **Line length 88.** `[tool.ruff]` in `pyproject.toml`.
- **Docstrings.** NumPy style, validated by `numpydoc-validation`. A new private helper
  carries `.. versionadded:: 0.6.0` under `Notes`, as `_carried_zlevels` does.
- **No `type: ignore`, and every commit passes the `mypy` hook.** `pyproj` types are thin,
  so bind an annotated local before returning a value derived from them (root
  `AGENTS.md`).
- **The rule is zlevel spec §3.1:** `z = zlevel * zscale * R`, where `R` is the semi-major
  axis of the ellipsoid divided by the metres in one unit of the first axis for a
  projected CRS, and one radian in the angular unit for a geographic one.
- **The globe does not change, and `radius` still applies only to it** (zlevel spec §3.2).
- **`GeoPlotter` does not change** (zlevel spec §2).
- **Warnings are errors.** `filterwarnings = error` in `pyproject.toml`, so a test meeting
  the rotated pole central meridian warning must expect it.
- **Tests run in parallel.** `tests-unit` runs under `pytest-xdist`, plain `pytest`
  serially; every test this plan adds is a pure computation, safe either way.
- **Image tests run only in CI.** They segfault without a display, so a local run proves
  nothing about them.
- **Changelog.** Two towncrier fragments, `2591.bugfix.rst` and `2591.breaking.rst`
  (zlevel spec §4), each signed ``:user:`claude` ``. Pass `agentic` and `type: bug` to
  `gh pr create`.
- **Names.** Repository text names the reviewer as {user}`bjlittle`.
- **Landing.** Row 1 is committed `✅ landed` as the pull request's last commit, dated the
  day {user}`bjlittle` approves it; if the merge slips a day, the date is corrected
  before it lands.

## What the dry run settled

Measured on 2026-10-08 against `main` at `8beb68cb`, in a scratch worktree carrying the
code below.

1. **Open item 1 of zlevel spec §8 resolves.** No CRS that `transform_mesh` reaches lacks
   an ellipsoid or an axis unit. A compound CRS (EPSG:7405) and a bound one (a `tmerc`
   string with `+towgs84`) both report the Airy ellipsoid and a metre first axis, a
   rotated pole CRS is a derived geographic one in degrees, and EPSG:4978 is geocentric
   in metres. An engineering CRS and a vertical one have no ellipsoid, and `pyproj`
   refuses to build a transformer to either, so `transform_mesh` fails before it needs `R`.
   The guard stays, and is tested on the helper directly.
2. **The compound bullet of zlevel spec §3.1 needs no special case.** `pyproj` already
   reports the ellipsoid and first axis of the horizontal component of a compound CRS,
   and of the source of a bound one.
3. **A rotated pole CRS warns.** `geovista` cannot find its central meridian and assumes
   0, as `tests/crs/test_get_central_meridian.py::test_central_meridian__rotated_pole_warns`
   pins, so the rotated pole test expects the warning.
4. **The floor also truncated the scale in coarse units.** In kilometres, a cloud moved
   from metres kept 556.0 where 556.597 was due, which
   `test_transform_mesh__cloud_between_units` pins.
5. **No existing test asserts an absolute planar z.** The full non-image suite passed
   against the dry run, as did the spec gates with the new citation in `transform.py`.

## Review Focus

Five inputs the spec implies but does not pin, most likely to bite first. Each gets a test
in Task 1.

1. **Data a caller raises above the coastlines.** On a planar CRS the plotter adds its
   coastlines at `zlevel=3` and its base layer at `-1` with a `zscale` of 1e-3, over the
   whole globe. A small dataset at `zlevel=4` must draw above them; today it draws
   beneath. `test_transform_mesh__data_above_the_coastlines_whatever_its_extent`.
2. **A target with a central meridian.** `transform_mesh` rebases such a CRS to 0 before
   slicing, and the rebased CRS must give the same `R`.
   `test_transform_mesh__zlevel_with_a_shifted_meridian`.
3. **A compound target.** EPSG:7405 must give the Airy semi-major axis. The `compound`
   case of `test_transform_mesh__zlevel_in_the_units_of_the_crs`.
4. **A rotated pole target.** It is geographic, so `R` is one radian in degrees.
   `test_transform_mesh__zlevel_in_a_rotated_pole_crs`.
5. **A cloud moved between planar CRSs of different units.** Its depths must scale with
   the unit. `test_transform_mesh__cloud_between_units`.

---

### Task 1: the Earth's radius in transform_mesh

The behavioural change, its tests and its docstring.

**Files:**
- Modify: `src/geovista/transform.py`: the `zlevel` docstring of `transform_mesh`, the
  planar offset, and a new private helper at the end of the module
- Modify: `tests/transform/test_transform_mesh.py`
- Create: `tests/transform/test__earth_radius.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `_earth_radius(crs: pyproj.CRS) -> float` in `geovista.transform`, private,
  which raises `ValueError` when the CRS has no ellipsoid or its first axis no unit.

- [ ] **Step 1: Write the failing tests**

In `tests/transform/test_transform_mesh.py`, after the `ROBIN` constant add:

```python
#: The semi-major axis of the WGS84 and GRS80 ellipsoids, in metres.
SEMI_MAJOR: float = 6378137.0

#: The semi-major axis of the Airy 1830 ellipsoid, in metres.
AIRY: float = 6377563.396
```

Before `_cell_widths` add:

```python
def _quad(lon_min, lon_max, lat_min, lat_max) -> pv.PolyData:
    """Create a small quad mesh over the given extent, in degrees."""
    lons = np.linspace(lon_min, lon_max, 5)
    lats = np.linspace(lat_min, lat_max, 5)
    return gv.Transform.from_1d(lons, lats)
```

Append to the end of the file:

```python
@pytest.mark.parametrize(
    "extent",
    [(-180, 180, -90, 90), (0, 40, 30, 50), (0, 10, 40, 45), (40, 50, 30, 50)],
    ids=["global", "regional", "small", "tile"],
)
def test_transform_mesh__zlevel_ignores_the_extent(extent):
    """A level sits at one height in a planar CRS, whatever the extent of the mesh.

    Issue 2588: the offset scaled with a quarter of the mesh's own extent, so meshes
    of different sizes at the same level sat at different heights.

    """
    result = transform_mesh(_quad(*extent), PLANAR, zlevel=1)

    expected = ZLEVEL_SCALE * SEMI_MAJOR
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-12)


def test_transform_mesh__zlevel_orders_layers_across_extents():
    """A small mesh at a higher level sits above a global mesh at a lower one."""
    upper = transform_mesh(_quad(0, 10, 40, 45), PLANAR, zlevel=2)
    lower = transform_mesh(_quad(-180, 180, -90, 90), PLANAR, zlevel=1)

    assert upper.points[:, 2].min() > lower.points[:, 2].max()


def test_transform_mesh__zlevel_in_degrees_survives_a_small_extent():
    """A small mesh in a CRS measured in degrees is lifted, not left at zero."""
    result = transform_mesh(_quad(0, 3, 40, 42), "EPSG:4269", zlevel=5)

    expected = 5 * ZLEVEL_SCALE * np.degrees(1.0)
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-12)


def test_transform_mesh__cloud_feature_keeps_the_depths_of_the_whole():
    """A feature taken from a cloud sits at the depths it has in the whole cloud.

    Issue 2588: an oceanographer plotting eddies extracted from an ORCA2 cloud saw
    each feature's depths compressed, since a smaller cloud brought a smaller scale.

    """
    lons, lats = np.linspace(-60.0, 20.0, 9), np.linspace(10.0, 70.0, 9)
    depths = -np.linspace(0.0, 5000.0, 9)
    whole = gv.Transform.from_points(lons, lats, zlevel=depths, zscale=1e-5)
    part = slice(3, 5)
    feature = gv.Transform.from_points(
        lons[part], lats[part], zlevel=depths[part], zscale=1e-5
    )
    expected = transform_mesh(whole, PLANAR).points[part, 2]

    result = transform_mesh(feature, PLANAR)

    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-9)


def test_transform_mesh__zlevel_is_the_proportion_the_globe_gives(lifted_cloud):
    """A planar z is the proportion of the Earth's radius the sphere lifts it by."""
    lifts = np.linalg.norm(lifted_cloud.points, axis=1) - 1

    result = transform_mesh(lifted_cloud, PLANAR)

    np.testing.assert_allclose(result.points[:, 2] / SEMI_MAJOR, lifts, rtol=1e-9)


@pytest.mark.parametrize(
    ("crs", "extent", "radius"),
    [
        ("+proj=eqc +units=km", (-75, -73, 40, 41), SEMI_MAJOR / 1000),
        ("EPSG:2263", (-75, -73, 40, 41), SEMI_MAJOR / 0.3048006096012192),
        ("EPSG:4269", (-75, -73, 40, 41), np.degrees(1.0)),
        ("EPSG:7405", (-3, -1, 52, 53), AIRY),
    ],
    ids=["kilometre", "us-survey-foot", "degree", "compound"],
)
def test_transform_mesh__zlevel_in_the_units_of_the_crs(crs, extent, radius):
    """The offset is the radius of the Earth, measured in the units of the CRS."""
    result = transform_mesh(_quad(*extent), crs, zlevel=1)

    np.testing.assert_allclose(result.points[:, 2], ZLEVEL_SCALE * radius, rtol=1e-9)


def test_transform_mesh__zlevel_in_a_rotated_pole_crs():
    """A rotated pole CRS is geographic, so the offset is one radian in degrees.

    geovista cannot find the central meridian of a rotated pole CRS, and warns
    that it assumes 0, as ``test_central_meridian__rotated_pole_warns`` pins.

    """
    crs = ccrs.RotatedPole(pole_longitude=MERIDIAN, pole_latitude=45)

    with pytest.warns(UserWarning, match="central meridian"):
        result = transform_mesh(_quad(-75, -73, 40, 41), crs, zlevel=1)

    expected = ZLEVEL_SCALE * np.degrees(1.0)
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-9)


def test_transform_mesh__zlevel_with_a_shifted_meridian():
    """A target CRS rebased for its central meridian keeps the radius of its own."""
    crs = f"{PLANAR} +lon_0={REGIONAL_MERIDIAN}"

    result = transform_mesh(_quad(0, 10, 40, 45), crs, zlevel=1)

    expected = ZLEVEL_SCALE * SEMI_MAJOR
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-12)


def test_transform_mesh__data_above_the_coastlines_whatever_its_extent():
    """Data raised above the default level of the coastlines draws above them.

    On a planar CRS the plotter adds its base layer at zlevel -1 with a zscale of
    1e-3, and its coastlines at zlevel 3, both over the whole globe. Issue 2588: a
    small dataset at zlevel 4 still drew beneath them.

    """
    world = _quad(-180, 180, -90, 90)
    base = transform_mesh(world.copy(), PLANAR, zlevel=-1, zscale=1e-3)
    coastlines = transform_mesh(world.copy(), PLANAR, zlevel=3)

    data = transform_mesh(_quad(0, 10, 40, 45), PLANAR, zlevel=4)

    assert base.points[:, 2].max() < coastlines.points[:, 2].min()
    assert coastlines.points[:, 2].max() < data.points[:, 2].min()


def test_transform_mesh__cloud_between_units(lifted_cloud):
    """A cloud moved from metres to kilometres keeps its depths in proportion."""
    metres = transform_mesh(lifted_cloud.copy(), PLANAR)

    result = transform_mesh(metres, "+proj=eqc +units=km")

    expected = metres.points[:, 2] / 1000
    np.testing.assert_allclose(result.points[:, 2], expected, rtol=1e-9)
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `pixi run --frozen -e geovista pytest tests/transform/test_transform_mesh.py -k "ignores_the_extent or orders_layers or degrees_survives or feature_keeps or proportion_the_globe or units_of_the_crs or rotated_pole_crs or shifted_meridian or above_the_coastlines or between_units"`

Expected: **16 failed.**

- The four `zlevel_ignores_the_extent` cases sit at 1001.8754, 111.3194, 27.8298 and
  55.5183, where 637.8137 is due.
- `zlevel_orders_layers_across_extents`: `assert 55.6596 > 1001.8754`.
- `zlevel_in_degrees_survives_a_small_extent`: 0.0, where 0.028648 is due.
- `cloud_feature_keeps_the_depths_of_the_whole`: −5218.0875, where −41744.7937 is due.
- `zlevel_is_the_proportion_the_globe_gives`: 0.087266, where 1.0 is due.
- `zlevel_in_the_units_of_the_crs`: 0.0055 for `kilometre` (0.6378137 due), 14.0093 for
  `us-survey-foot` (2092.5604 due), 0.0 for `degree` (0.0057296 due) and 3.4325 for
  `compound` (637.7563 due).
- `zlevel_in_a_rotated_pole_crs` and `zlevel_with_a_shifted_meridian`: 0.0 and 27.8298.
- `data_above_the_coastlines_whatever_its_extent`: `assert 3005.6262 < 111.3192`.
- `cloud_between_units`: 556.0, where 556.597 is due.

- [ ] **Step 3: Write the helper's failing test**

Create `tests/transform/test__earth_radius.py`:

```python
# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.transform._earth_radius`."""

from __future__ import annotations

from pyproj import CRS
import pytest

from geovista.transform import _earth_radius

#: A local engineering CRS, which has no ellipsoid.
ENGINEERING = (
    'ENGCRS["local",EDATUM["site"],CS[Cartesian,2],'
    'AXIS["x",east,LENGTHUNIT["metre",1]],AXIS["y",north,LENGTHUNIT["metre",1]]]'
)


def test_needs_an_ellipsoid():
    """A CRS without an ellipsoid has no radius to scale a level by.

    No CRS that ``transform_mesh`` can reach lacks one, since ``pyproj`` refuses to
    transform to an engineering CRS, so the guard is tested here directly.

    """
    with pytest.raises(ValueError, match="Cannot determine the radius of the Earth"):
        _ = _earth_radius(CRS.from_wkt(ENGINEERING))
```

- [ ] **Step 4: Run it to see it fail**

Run: `pixi run --frozen -e geovista pytest tests/transform/test__earth_radius.py`

Expected: an error at collection, `ImportError: cannot import name '_earth_radius' from
'geovista.transform'`. Run it apart from Step 2, since the error stops the whole session.

- [ ] **Step 5: Use the Earth's radius in transform_mesh**

In `transform_mesh`, replace the planar offset, at the function's own indentation:

```text
        # a planar target offsets z by the level, whereas on the sphere the level
        # is already in the radius that to_cartesian applied
        if tgt_crs != WGS84 and (np.any(level) or cloud):
            xmin, xmax, ymin, ymax, _, _ = mesh.bounds
            xdelta, ydelta = abs(xmax - xmin), abs(ymax - ymin)
            # TODO @bjlittle: Make this scale factor configurable at the API/module
            #                 level, as current strategy is slightly flawed in that
            #                 there isn't consistent scaling across all geometries
            #                 added to the render scene.
            delta = max(xdelta, ydelta) // 4
            zs = level * zscale * delta
```

with:

```text
        # zlevel spec §3.1 -- a planar target offsets z by the level times the
        # radius of the Earth in its own units, whereas on the sphere the level
        # is already in the radius that to_cartesian applied
        if tgt_crs != WGS84 and (np.any(level) or cloud):
            zs = level * zscale * _earth_radius(tgt_crs)
```

The comment cites the spec, and `tests/test_spec_conventions.py` reads it: a citation of
a section that does not exist fails there with the file and line.

Append to the end of the module:

```python
def _earth_radius(crs: pyproj.CRS) -> float:
    """Determine the radius of the Earth, in the units of a CRS.

    A planar CRS offsets a z-level by this length, so that a level is the same
    proportion of the Earth's radius as it is on the sphere. For a geographic CRS
    the radius is one radian, expressed in its angular unit.

    Parameters
    ----------
    crs : :class:`~pyproj.crs.CRS`
        The planar CRS.

    Returns
    -------
    float
        The radius of the Earth, in the unit of the first axis of the CRS.

    Raises
    ------
    ValueError
        If the CRS has no ellipsoid, or its first axis has no unit.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    ellipsoid = crs.ellipsoid
    factor = crs.axis_info[0].unit_conversion_factor if crs.axis_info else None

    if ellipsoid is None or not factor:
        emsg = (
            f"Cannot determine the radius of the Earth in the units of {crs.name!r}, "
            "which has no ellipsoid or no axis unit."
        )
        raise ValueError(emsg)

    radius: float = (
        1.0 / factor if crs.is_geographic else ellipsoid.semi_major_metre / factor
    )
    return radius
```

In the docstring of `transform_mesh`, after the line ending ``e.g., ``radius * zlevel *
zscale``.`` under `zlevel`, insert, at the docstring's indentation:

```text
        In a planar CRS the offset is ``zlevel * zscale`` times the radius of the
        Earth in the units of that CRS, the same proportion as on the sphere.
```

- [ ] **Step 6: Run the new tests to see them pass**

Run: `pixi run --frozen -e geovista pytest tests/transform/test_transform_mesh.py tests/transform/test__earth_radius.py -k "ignores_the_extent or orders_layers or degrees_survives or feature_keeps or proportion_the_globe or units_of_the_crs or rotated_pole_crs or shifted_meridian or above_the_coastlines or between_units or needs_an_ellipsoid"`

Expected: **17 passed.**

- [ ] **Step 7: Run the suites around it**

Run: `pixi run --frozen -e geovista tests-unit "not image"`

Expected: PASS, none failed.

Run: `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py`

Expected: PASS, the citation in `transform.py` resolving.

- [ ] **Step 8: Run mypy and the hooks**

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`

Run: `pixi run --frozen -e geovista pre-commit run --files src/geovista/transform.py tests/transform/test_transform_mesh.py tests/transform/test__earth_radius.py`

Expected: every hook passes.

- [ ] **Step 9: Commit**

```bash
git add src/geovista/transform.py tests/transform/test_transform_mesh.py tests/transform/test__earth_radius.py
pixi run --frozen -e geovista git commit -m "fix: lift a planar z-level by the Earth's radius in the units of the CRS"
```

---

### Task 2: the spec and the changelog

The spec records what the dry run settled, and the change gains its fragments.

**Files:**
- Modify: `docs/src/developer/specs/2026-10-08-planar-zlevel-design.md`: §3.1, §3.4, §4,
  §8
- Create: `changelog/2591.bugfix.rst`, `changelog/2591.breaking.rst`

**Interfaces:**
- Consumes: the measurements in "What the dry run settled".
- Produces: row 1's `in progress`, which Task 4 lands.

- [ ] **Step 1: Mark row 1 in progress**

In zlevel spec §4, change row 1's status from `` not started ({issue}`2588`) `` to
`` in progress ({pull}`2591`) ``, substituting the real pull request number.

- [ ] **Step 2: Say that pyproj resolves compound and bound CRSs**

In zlevel spec §3.1, replace the bullet:

```markdown
- for a compound CRS, the `R` of its horizontal component.
```

with:

```markdown
- for a compound or a bound CRS, the `R` of its horizontal component, which `pyproj`
  reports directly.
```

- [ ] **Step 3: Resolve open item 1**

In zlevel spec §3.4, replace:

```markdown
Whether any CRS that `transform_mesh` can reach is affected is item 1 of
{ref}`§8 <zlevel-spec-8>`.
```

with:

```markdown
No CRS that `transform_mesh` can reach is affected, by item 1 of
{ref}`§8 <zlevel-spec-8>`, so the guard is tested on the helper directly.
```

In zlevel spec §8, replace item 1 in full with, substituting the date and number:

```markdown
1. **Resolved** (2026-10-08, {pull}`2591`) — **Can a CRS that `transform_mesh` reaches
   lack an ellipsoid or an axis unit?** No. A compound CRS and a bound one report the
   ellipsoid and first axis of their horizontal component, a rotated pole CRS is a
   derived geographic one in degrees, and a geocentric one is in metres. An engineering
   CRS is the one kind without an ellipsoid, and `pyproj` refuses to build a
   transformer to it, so `transform_mesh` fails before it needs `R`. The `ValueError`
   of {ref}`§3.4 <zlevel-spec-3-4>` is tested on the helper directly.
```

- [ ] **Step 4: Write the changelog fragments**

Create `changelog/2591.bugfix.rst`, substituting the real number:

```rst
In a planar CRS, ``transform_mesh`` now lifts a mesh by ``zlevel * zscale``
times the radius of the Earth in the units of that CRS, the proportion a level
already has on the globe. Every mesh and point cloud in a projected scene shares
that length, so meshes of different extents at one level sit at one height, a
layer at a higher level draws above one at a lower level, and a feature taken
from a point cloud sits at the depths it has in the whole cloud. Before, the
length was a quarter of each mesh's own extent. Closes :issue:`2588`.
(:user:`claude`)
```

Create `changelog/2591.breaking.rst`:

```rst
Planar ``zlevel`` offsets change size. For a mesh spanning the globe they become
0.64 of what they were in ``eqc``, 0.75 in ``robin`` and 0.71 in ``moll``, and
smaller meshes rise to match. Layers keep their order, but anyone who tuned
``zscale`` for a projection will see a different depth, and can raise ``zscale``
to restore it. (:user:`claude`)
```

- [ ] **Step 5: Verify**

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py 2591 "changelog/2591.bugfix.rst,changelog/2591.breaking.rst"`

Expected: `🆗 Your changelog contribution looks good to me.`

Run: `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py`

Expected: PASS.

Run, from `docs/`:

```bash
pixi run --frozen -e docs sphinx-build -b html -W --keep-going \
  -D plot_docstring=False -D plot_gallery=False \
  -D plot_inline=False -D plot_tutorial=False \
  -d _build/doctrees src _build/html
```

Expected: `build succeeded`, with the new sentence under `zlevel` in the API reference.

- [ ] **Step 6: Commit and push**

```bash
git add docs/src/developer/specs/2026-10-08-planar-zlevel-design.md changelog/
pixi run --frozen -e geovista git commit -m "docs: record the dry run's findings in the planar z-level spec"
git push
```

---

### Task 3: the image baselines

Only CI renders the image tests, so this task follows what it reports. Zlevel spec §3.3
expects the ORCA2 `eqc` gallery image to move, its depths 1.59 times deeper.

**Files:**
- Modify: `src/geovista/cache/__init__.py`: `DATA_VERSION`
- Modify: `src/geovista/cache/registry.txt`: one line per image that moved, in place
- Modify: `docs/src/developer/specs/2026-10-08-planar-zlevel-design.md`: §8 item 2
- In `bjlittle/geovista-data`: `assets/tests/unit/<name>.png` for each image that moved

**Interfaces:**
- Consumes: Task 1's change, pushed.
- Produces: baselines that match it, and the version that serves them.

- [ ] **Step 1: Let CI render the change**

Run: `gh pr checks 2591 --repo bjlittle/geovista --watch`

Expected: the image jobs fail on
`examples.test__point_cloud.from_points__orca_cloud_eqc`, and every other job passes.
Any other failing image is examined in Step 3 before it is accepted. If no image job
fails, go to Step 7 and record that no baseline moved.

- [ ] **Step 2: Fetch the renders**

Run: `gh run download <run-id> --repo bjlittle/geovista --pattern "ci-tests-failed-images-*" --dir /tmp/2591-images`

Expected: one PNG per failing image test. Fetch the baseline each replaces with
`pixi run --frozen -e geovista python -c "from geovista.cache import CACHE; print(CACHE.fetch('tests/unit/<name>.png'))"`.

- [ ] **Step 3: Review them with bjlittle**

Compare each render with its baseline, and confirm the change is the one zlevel spec §3.3
predicts: the same scene, its elevated layers at the new heights. Show both to
{user}`bjlittle`, and go on only with their approval of the new appearance.

- [ ] **Step 4: Land the renders in geovista-data**

Clone `bjlittle/geovista-data`, copy each approved render over
`assets/tests/unit/<name>.png`, and open a pull request there with the `agentic` label.
Never edit `version.txt` or tag by hand: its `ci-release.yml` sets both on merge
(`tests/AGENTS.md`). With `version.txt` at `2026.10.1`, a merge in October releases
`2026.10.2`.

- [ ] **Step 5: Serve them**

Once {user}`bjlittle` has merged it and the release exists, set `DATA_VERSION` in
`src/geovista/cache/__init__.py` to the new tag, and in `src/geovista/cache/registry.txt`
replace the hash on each moved image's line with `sha256sum` of its new PNG. Edit the
lines in place; never re-sort the file.

- [ ] **Step 6: Verify and push**

Run: `pixi run --frozen -e geovista python -c "from geovista.cache import CACHE; CACHE.fetch('tests/unit/examples.test__point_cloud.from_points__orca_cloud_eqc.png')"`

Expected: the new PNG downloads and its hash verifies, with no error.

```bash
git add src/geovista/cache/__init__.py src/geovista/cache/registry.txt
pixi run --frozen -e geovista git commit -m "test: refresh the image baselines the planar z-level rule moves"
git push
```

Expected: CI passes, image jobs included.

- [ ] **Step 7: Resolve open item 2**

In zlevel spec §8, replace item 2 in full with a **Resolved** item, dated, citing this
pull request, and naming each baseline that moved, or recording that none did. Run
`pixi run --frozen -e geovista pytest tests/test_spec_conventions.py`, expecting PASS,
then commit it as `docs: record which image baselines the planar z-level rule moved` and
push.

---

### Task 4: land row 1

The trial convention of committing the landed row before the merge.

**Files:**
- Modify: `docs/src/developer/specs/2026-10-08-planar-zlevel-design.md`: §4

- [ ] **Step 1: Mark row 1 landed, on the day of approval**

Once every review round is done and {user}`bjlittle` approves, change row 1's status to
`` ✅ landed (YYYY-MM-DD, {pull}`2591`) ``, dated that day.

- [ ] **Step 2: Verify, commit and push**

Run: `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py`

Expected: PASS.

```bash
git add docs/src/developer/specs/2026-10-08-planar-zlevel-design.md
pixi run --frozen -e geovista git commit -m "docs: mark row 1 of the planar z-level roadmap landed"
git push
```

This is the pull request's last commit. If the merge slips past that day, correct the date
first.

---

## Definition of done

- The 17 new tests were seen failing as Task 1 describes, and then passing.
- `tests-unit "not image"` passes under `pytest-xdist`, and CI is green, image tests
  included, against baselines {user}`bjlittle` approved.
- Zlevel spec §4 row 1 reads landed, and §8 items 1 and 2 are resolved.
- `changelog/2591.bugfix.rst` and `changelog/2591.breaking.rst` exist, and the pull
  request carries `agentic` and `type: bug`.

## After the final review

The whole-branch review ran on Opus 5.5 against `8beb68cb..9ef1d0da`, while CI rendered
Task 3's images, and returned "with fixes": no critical findings, two important and two
minor. It agreed that the code matches this plan word for word, and that its 16 tests fail
on the old rule.

| finding | outcome | commit |
|---|---|---|
| the breaking fragment told everyone to raise `zscale`, though only a global mesh's offset drops: a smaller one rises, about twice over the North Atlantic and 23 times for 10° across | the fragment and zlevel spec §3.3 give both directions, and the inverse ratio that restores the old depth | `c56be66d` |
| a vertical CRS was said to reach the `ValueError` guard | not reproduced: in the locked environment `pyproj` refuses EPSG:5703 before `R` is needed, so item 1 keeps its answer, but neither it nor the helper's test calls an engineering CRS the one kind without an ellipsoid any more | `c56be66d` |
| a geographic CRS declared in radians took `R = 1`, though `pyproj` returns its coordinates in degrees (minor) | fixed at {user}`bjlittle`'s request: one radian in degrees, 57.2958 | `e7e94167` |
| the shifted-meridian test could not see a rebuild that lost the ellipsoid or the unit (minor) | fixed at {user}`bjlittle`'s request: Airy in kilometres, which a mutant rebuilding a bare `+proj=eqc` now fails | `11b90b4a` |

Of the behaviours the review set aside, two predate this change and are raised for later:
{issue}`2594`, graticule labels ignoring `zscale` on a planar CRS, and {issue}`2595`,
targets whose WKT holds non-ASCII text, Web Mercator among them. The rest stand as outside
the spec, each with its ruling in the ledger. Task 2's quoted text for item 1 is left as it
was executed; the dry-run note above is corrected in place.

Task 3 met two images rather than one. Besides the ORCA2 gallery image, the UK LAM scene of
`test_view_poi` in `eqc` crossed its warning threshold, and both `test pypi` jobs failed on
the same two because they run the image suite too. Each moved by a fraction of a pixel, as
the camera frames the new scene bounds. {user}`bjlittle` approved both,
`bjlittle/geovista-data#136` released them as 2026.10.2, and `6c34fe92` serves them.
