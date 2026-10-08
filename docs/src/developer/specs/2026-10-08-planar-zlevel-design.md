# geovista planar z-levels — design specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. It states how `transform_mesh` turns a z-level into a height in a planar
> coordinate reference system (CRS), and where the two ever diverge it is the
> specification that gets corrected. Read it as current; the roadmap states what has
> actually landed.

- **Date:** 2026-10-08 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `zlevel spec §…`
- **Scope:** the height a z-level gives a mesh or point cloud in a planar CRS. The globe,
  where a level lives in the radius, is unchanged
- **Parent spec:** none; its conventions are those of {ref}`docs spec §1 <docs-spec-1>`
- **Published:** in the specifications index

(zlevel-spec-1)=
## 1. Purpose

A `zlevel` lifts a mesh or point cloud above the surface it is drawn on, or sinks it below,
by `zlevel * zscale` of some length. On the globe that length is the radius of the sphere,
so a level means the same thing for every mesh in a scene. In a planar CRS it has been a
quarter of each mesh's own x/y extent, floored:

```python
xmin, xmax, ymin, ymax, _, _ = mesh.bounds
xdelta, ydelta = abs(xmax - xmin), abs(ymax - ymin)
delta = max(xdelta, ydelta) // 4
```

The `TODO` beside that code already says the strategy "is slightly flawed in that there
isn't consistent scaling across all geometries added to the render scene". Every mesh
brings its own length, so the same level puts meshes of different sizes at different
heights. Measured on `main` at 3d4a5a88 with `+proj=eqc` and the default `zscale` of 1e-4,
a mesh at `zlevel=1` sits at:

| mesh | z |
|---|---|
| global, 360° × 180° | 1,001.9 |
| regional, 40° × 20° | 111.3 |
| regional, 10° × 5° | 27.8 |

A regional mesh at `zlevel=2` sits at 55.7, about eighteen times lower than the global mesh
at `zlevel=1`, so the layer meant to be on top is hidden underneath it. Two tiles of one
dataset at the same level step where they meet. In a planar CRS measured in degrees the
floor makes the length zero for a mesh less than 4° across, and a 3° mesh in NAD83 sits at
z = 0 whatever its level. {issue}`2588` holds these measurements.

Point clouds suffer most. An oceanographer working with a NEMO ORCA2 cloud extracts
features such as eddies and plots each as a cloud of its own, beside the whole dataset.
Every feature brings a smaller extent, so its depths are compressed. Measured on `main` at
fcbfe28d with the North Atlantic sample that `geovista` ships, a 10° × 10° box over the
Gulf Stream holds 12,836 of the cloud's 265,791 points, down to 4,833 m. Projected to
`eqc`, those points sit 14.4 times deeper in the whole cloud than in the feature. On the
globe the same points agree exactly, so the oceanographer renders on the globe instead.

`GeoPlotter.add_mesh` sends every mesh of a projected scene through the same code and
leans on it. On a planar CRS the coastlines and graticule default to `zlevel=3`, and the
base layer to `-1` with ten times the default `zscale`, so whether a dataset draws above or
below them has depended on its extent.

(zlevel-spec-2)=
## 2. Decisions

- **The length is the Earth's radius, measured in the CRS's own units.** It belongs to the
  CRS, so every mesh and cloud transformed into that CRS shares it, and a level is the same
  proportion of the Earth's radius as it is on the globe. Chosen on 2026-10-08 over the
  alternatives of {ref}`§5 <zlevel-spec-5>`.
- **`zscale` stays the only control.** It already scales every level, on the globe and in
  the plane, so the length needs no setting of its own.
- **`GeoPlotter` does not change.** Its layers all pass through `transform_mesh`, and they
  keep their order, since every one of them is scaled by the same length.
- **Nothing persisted needs migrating.** A planar z is computed afresh by every transform,
  from the levels a point cloud carries or from the `zlevel` a caller passes.

(zlevel-spec-3)=
## 3. Design

(zlevel-spec-3-1)=
### 3.1 The rule

In a planar CRS, a point at level `zlevel` sits at

```text
z = zlevel * zscale * R
```

where `R` is the radius of the Earth expressed in the units of the CRS's horizontal
coordinates:

- for a projected CRS, the semi-major axis of its ellipsoid divided by the metres in one
  unit of its first axis;
- for a geographic CRS, one radian expressed in its angular unit, so 57.2958 for degrees;
- for a compound or a bound CRS, the `R` of its horizontal component, which `pyproj`
  reports directly.

On the globe, `to_cartesian` lifts a point by `radius * zlevel * zscale`, so the rule gives
a level the same proportion of the Earth's radius in either. `pyproj` supplies both inputs,
as `CRS.ellipsoid.semi_major_metre` and the `unit_conversion_factor` of the first entry in
`CRS.axis_info`. Measured on 2026-10-08:

| CRS | unit | `R` |
|---|---|---|
| `+proj=eqc` | metre | 6,378,137 |
| `+proj=eqc +units=km` | kilometre | 6,378.137 |
| `+proj=robin +ellps=sphere` | metre | 6,370,997 |
| EPSG:2263, New York State Plane | US survey foot | 20,925,604 |
| EPSG:27700, British National Grid | metre | 6,377,563 |
| EPSG:4269, and `+proj=longlat` | degree | 57.2958 |
| EPSG:3857, and `+proj=lcc` | metre | 6,378,137 |

`R` does not depend on the domain of a projection, so Mercator and Lambert conformal conic,
which run to infinity towards a pole, need no special case.

(zlevel-spec-3-2)=
### 3.2 What changes in transform_mesh

`transform_mesh` computes `R` for its target CRS with a private helper, and uses it in place
of the extent. The bounds, the floor division and the `TODO` beside them go.

A point cloud's carried levels, the `GV_POINT_ZLEVEL` array of {pull}`2587`, are encoded
with `R` on the way into a planar CRS, so a feature extracted from a cloud lands at the z
it has inside the whole cloud. A cloud moved between planar CRSs is encoded again with the
target's `R`, so a move from metres to kilometres keeps its depths in proportion. A mesh's
z is computed from the `zlevel` passed in, as it is today.

Nothing changes for a WGS84 target, where the level stays in the radius. The `radius`
argument still applies only to the globe, since a planar offset is a proportion of the
Earth's radius in the units of the CRS, whatever radius the globe is drawn at. A level of
zero still leaves z at zero.

(zlevel-spec-3-3)=
### 3.3 Magnitudes

For a global mesh, every planar offset shrinks by the ratio of `R` to the old length: to
0.64 of what it was in `eqc`, which is exactly 2/π, to 0.75 in `robin` and to 0.71 in
`moll`. A regional mesh rises to meet it. In `eqc` the coastlines sit 1.9 km above the base
map rather than 3.0 km, and the base layer 6.4 km below it rather than 10.0 km. Every layer
shrinks by the same factor, so the plotter's layers keep their order: base layer, then
data, then coastlines and graticule. Beside a map 40,075 km across these offsets are small,
so the image tests should change only where offsets are large, and item 2 of
{ref}`§8 <zlevel-spec-8>` records what they actually show.

The ORCA2 cloud of the gallery's `eqc` example covers only the North Atlantic, so its own
length was 4,007,091 rather than a global mesh's. Under the rule its depths are 1.59 times
what they were, and its deepest point, at 5,275 m, moves from z = −211,365 to −336,433.

(zlevel-spec-3-4)=
### 3.4 Errors

A CRS that offers no ellipsoid, or no unit on its first axis, has no `R` to compute, and
`transform_mesh` then raises a `ValueError` naming the CRS rather than guessing a scale.
No CRS that `transform_mesh` can reach is affected, by item 1 of
{ref}`§8 <zlevel-spec-8>`, so the guard is tested on the helper directly.

Units come from the first horizontal axis. A projected CRS uses one unit on both axes, a
latitude-first geographic CRS such as EPSG:4269 uses degrees on both, and an unusual angular
unit converts the same way, so radians give 1 and grads 63.66.

(zlevel-spec-4)=
## 4. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | The rule in `transform_mesh`, its tests and docstring, and the image baselines it moves | in progress ({pull}`2591`) |

Statuses follow {ref}`docs spec §3.6 <docs-spec-3-6>`. The image baselines live in
`bjlittle/geovista-data`, so row 1 lands there first: the new images are released there,
and the pull request here raises `DATA_VERSION` and `registry.txt` together, as
`tests/AGENTS.md` describes. The change carries two towncrier fragments, `bugfix` for the
inconsistency and `breaking` for the size of every planar offset, which anyone who tuned
`zscale` for a projection will see shrink.

(zlevel-spec-5)=
## 5. Alternatives considered

- **The projected extent of the CRS's domain, divided by four.** It keeps today's z for a
  global mesh in `eqc`, `robin` and `moll` exactly. But it has to sample the domain, it needs
  a fallback for a domain that runs to infinity, which would be the rule above, and it makes
  the depth of a level vary from one projection to another: an orthographic view would get
  half the Earth's radius. It would not spare the ORCA2 image either.
- **A fixed `R` times π/2.** It keeps `eqc` as it is today and moves other projections by 11
  to 18 percent, but the π/2 is only what dividing the equator by four left behind.
- **One length per `GeoPlotter` scene.** A length shared across the meshes of a scene would
  fix the plotter but not a direct caller of `transform_mesh`, and it would depend on which
  mesh was added first. The rule depends on the CRS alone, so it needs no plotter to be
  consistent.

(zlevel-spec-6)=
## 6. Testing

Unit tests in `tests/transform/test_transform_mesh.py` pin the rule:

- a global mesh, a regional mesh and two tiles of one mesh at the same level all sit at
  exactly `zlevel * zscale * R`;
- a regional mesh at `zlevel=2` sits above a global mesh at `zlevel=1`;
- a 3° mesh in NAD83 at `zlevel=5` sits at 5 × 1e-4 × 57.2958, not at 0;
- a point cloud and a subset of it give every shared point the same z;
- a planar z divided by `R` equals the proportion by which the same level lifts a point on
  the globe;
- kilometres give a thousandth of the value in metres, and US feet and degrees their own
  `R`.

The tests already in that module compare against relationships that hold for any length,
so they should pass unchanged. The image tests run only in CI, so their failed images are
fetched from the run and reviewed before any new baseline is proposed.

(zlevel-spec-7)=
## 7. Scope

In scope are the planar offset in `transform_mesh`, its docstring, its tests, the image
baselines it moves and the changelog. Out of scope are the globe, which does not change; the
default levels of `GeoPlotter`, which keep their order; {issue}`2583`, the point data that
`slice_lines` drops; and making `R` public, which nothing outside `transform_mesh` needs
yet.

(zlevel-spec-8)=
## 8. Open items

Each carries the status grammar of {ref}`docs spec §3.6 <docs-spec-3-6>`.

1. **Resolved** (2026-10-08, {pull}`2591`) — **Can a CRS that `transform_mesh` reaches
   lack an ellipsoid or an axis unit?** No. A compound CRS and a bound one report the
   ellipsoid and first axis of their horizontal component, a rotated pole CRS is a
   derived geographic one in degrees, and a geocentric one is in metres. An engineering
   CRS is the one kind without an ellipsoid, and `pyproj` refuses to build a
   transformer to it, so `transform_mesh` fails before it needs `R`. The `ValueError`
   of {ref}`§3.4 <zlevel-spec-3-4>` is tested on the helper directly.
2. **Open** ({issue}`2588`) — **Which image baselines move?** The ORCA2 `eqc` gallery image
   will, by {ref}`§3.3 <zlevel-spec-3-3>`. The other offsets are small beside their maps,
   and CI decides.

(zlevel-spec-9)=
## 9. References

- {issue}`2588`, which reported the bug and holds the extent measurements of
  {ref}`§1 <zlevel-spec-1>`
- {pull}`2587`, which carries a point cloud's levels as `GV_POINT_ZLEVEL` and confined the
  planar offset to planar targets
- {pull}`1977`, which added the WGS84 branch to `transform_mesh`
- `pyproj`'s `CRS.ellipsoid` and `CRS.axis_info`:
  <https://pyproj4.github.io/pyproj/stable/api/crs/crs.html>
- `tests/AGENTS.md`, on landing image baselines in `bjlittle/geovista-data`
