# geovista Heights as Data — Design Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. It states how a mesh carries the height of each of its points, where those
> heights enter `geovista`, where a point with a height is drawn, and which heights are
> refused. Where the two ever diverge it is the specification that gets corrected. Read it
> as current; the roadmap states what has actually landed.

- **Date:** 2026-10-28 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `heights spec §…`
- **Scope:** heights and depths as data on a mesh, the keywords that take them, positions
  built from them on the globe and on a map, heights that are missing, and what is refused
- **Parent spec:** the globe, heights and layers design
  ([`2026-10-26-globe-heights-layers-design.md`](2026-10-26-globe-heights-layers-design.md)).
  This extends globe spec §4.3 and globe spec §4.4, and is row 3 of globe spec §9. It
  inherits that specification's decisions (globe spec §2) and testing (globe spec §6),
  except that a missing height is no longer refused (§2 decision 3). It builds on the
  globe that a mesh records, of the globe on the scene design (scene spec §4.3), and
  amends scene spec §4.4 for a mesh with heights (§4.3)
- **Published:** in the specifications index

(heights-spec-1)=
## 1. Purpose

Row 3 of globe spec §9 makes heights data. A mesh carries the height of each point, in
metres above mean sea level, and the scene draws each point from its height through the
vertical mapping of its globe. A height is read back from the data, never from where its
point is drawn (globe spec §4.3, globe spec §4.4).

The parent fixes the formulas, the reference and most of the refusals. It left open how a
mesh stores its heights, which functions take them, how a height lives beside `zlevel`
until row 5 removes it, and what a scene does when its globe changes. {user}`bjlittle`
settled these while this was written, along with a case the parent did not consider: the
depths of an ocean model, which arrive masked over land.

(heights-spec-2)=
## 2. Decisions

These were decided with {user}`bjlittle` while the design was written.

1. **A mesh stores its heights in one point array, `gvHeight`.** It is float64, in metres
   above mean sea level. A mesh without it is at sea level. The prefix matches the fields
   of the globe (scene spec §2 decision 3), and leaves a user's own array named `height`
   alone.
2. **A depth is a negative height.** `depth=` is offered beside `height=`, positive
   downward, and negated once where it is given. `mesh.gv.depth` is offered beside
   `mesh.gv.height`, and negates the heights where they are read. No depth is stored, so a
   mesh has one array and one sign.
3. **A missing height is no height.** A masked or NaN height is stored as NaN, and its point
   is drawn at sea level, as a mesh given no height is. Only an infinite height is refused.
   This amends globe spec §4.3, which refused every height that is not finite, so that an
   ocean's depths, masked over land, load as its data does today, and `threshold` drops
   the land (§3.2).
4. **Heights enter where a mesh is built and where it is added to a scene.** The bridge's
   constructors, its `Transform` factory, `to_structured_grid`, `GeoPlotter.add_mesh` and
   `GeoPlotter.add_points` take them, as globe spec §4.3 names. `resize` and
   `transform_mesh` take none, and position a mesh from the heights it carries.
5. **Heights are given once.** A mesh that carries heights and is given more is refused,
   and so is `height=` given with `depth=`. `geovista` never picks one set of heights over
   another.
6. **A height and a z-level are never given together.** Until row 5 of globe spec §9
   removes `zlevel`, a mesh with heights and a z-level other than 0 is refused. A height is
   physics and a z-level is display, which globe spec §2 decision 1 keeps apart. Drawing a
   layer apart becomes the lift of row 4.
7. **A scene's globe is fixed when the scene is made.** Positions are built from heights
   when a mesh is added, and `GeoPlotter.globe` stays read-only (scene spec §6). A scene
   that replaces its globe and rebuilds every layer from its heights, as globe spec §4.1
   describes, is §8 item 1.
8. **`from_cartesian` reads positions, and nothing else.** Its third column stays the
   z-level, which is 0 for a mesh with heights. Heights are read from `gvHeight`, through
   `mesh.gv.height`.
9. **Heights given for each cell stay refused,** as globe spec §8 item 6 defers them
   ({issue}`2728`).
10. **A CRS whose vertical axis is an ellipsoidal height is refused only with heights.**
    Without heights, its horizontal axes are read, as they are today (§3.4).
11. **`vertical_units=` names the unit of heights given as plain numbers,** a CF unit string
    read by `geovista.units.to_metres`, for `height=`, `depth=` and the `zs` of
    `to_structured_grid` alike.

(heights-spec-3)=
## 3. What Exists Today

Each measurement below was taken on 2026-10-28, with `pyvista` 0.49.1, VTK 9.7.1, NumPy
2.5.4, `pyproj` 3.8.0 and PROJ 9.9.0.

(heights-spec-3-1)=
### 3.1 Heights by Other Means

Nothing in `geovista` takes a height. A z-level offsets a point by `zlevel * zscale` times
the render radius, which is a fraction of the sphere rather than a length. A point cloud
keeps its levels in the radius of each point and records the `zscale` that encoded them as
`gvZScale`, and on a map it carries them in the point array `gvZLevel`. The gallery warps
its orography by hand (globe spec §3.6), and so does the README.

`to_structured_grid` keeps only the number of its `zs`. Its levels are spaced by half the
mean arc of a cell in latitude, and offset by its `zlevel`. It was added after 0.5.3
({pull}`2185`), so neither its `zlevel` nor its `zscale` has been released.

A mesh records two exaggerations, above and below sea level (scene spec §2 decision 3),
and nothing reads either yet.

(heights-spec-3-2)=
### 3.2 Masked Data

The bridge fills masked data with NaN. Eleven of the gallery's examples then drop it with
`threshold()`, among them the OISST and ORCA2 examples, which mask the land.
`geovista.units.to_metres` also reads a masked element as NaN.

A 4 × 3 grid was built with `Transform.from_1d`, with its western column of cells masked
and a point array of heights that is NaN along its western edge. `threshold` on its data
kept 9 of its 12 cells and 16 of its 20 points, and none of the NaN heights. A point that a
sea cell shares with a land cell survives `threshold`, so whether it has a height depends on
how the data was masked.

(heights-spec-3-3)=
### 3.3 The Active Scalars

`threshold()` and `add_mesh` both read a mesh's active scalars by default. On a mesh from
`Transform.from_1d` with cell data, a point array assigned by item became the active
scalars when nothing had read them before, and did not once something had. On a mesh with
no data it always did. `point_data.set_array` never changed them. `_record_zlevels`
already sets `gvZLevel` with `set_array` for this reason.

(heights-spec-3-4)=
### 3.4 Vertical Axes in PROJ

`EPSG:4979`, WGS 84 in three dimensions, has the axes "Geodetic latitude", "Geodetic
longitude" and "Ellipsoidal height". `EPSG:9705`, "WGS 84 + MSL height", is a compound CRS
whose third axis is "Gravity-related height", and so is `EPSG:4326+3855`, WGS 84 with
EGM2008 heights. The bridge accepts all three today: `from_points` and `from_1d` read their
horizontal axes, and record WGS 84.

(heights-spec-3-5)=
### 3.5 The Unit of a Plain Number

`geovista.units.to_metres(value, units=None)` reads a plain value in metres, unless `units`
names a CF unit. It refuses a value that carries its units as an attribute, as an xarray
DataArray does, and asks for its values with their units as `units`. A height given as a
plain number in another unit therefore needs a keyword of its own.

(heights-spec-4)=
## 4. Design

(heights-spec-4-1)=
### 4.1 Heights on a Mesh

A mesh carries its heights in the point array `gvHeight`: float64, in metres above mean sea
level, one for each point. `geovista` sets it with `set_array`, so it never becomes the
active scalars (§3.3), and `threshold()` and `add_mesh` go on reading the data. A mesh
without `gvHeight` is at sea level. A NaN in it is a missing height (§4.3).

`mesh.gv.height` returns the heights, as a float64 array that cannot be written, or `None`
for a mesh without them. `mesh.gv.depth` returns their negation, or `None`: a point 4,000 m
below sea level has a depth of 4,000, a point on land a negative depth, and a missing
height a depth of NaN. Both are computed from `gvHeight` when read, and both are read-only,
down to the arrays they return. Heights say where the points are drawn, so changing the
numbers without moving the points would make the two disagree, as scene spec §4.6 says of
the globe. Heights are given where a mesh is built or added to a scene instead (§4.2).
Like the points themselves, they stay out of the equality of `mesh.gv`, which compares no
geometry (scene spec §4.6).

Every function that returns a mesh made from one it was given keeps its heights,
interpolated at any point a cut adds. `combine` keeps them whatever its `data`, and gives a
height of 0 to the points of a mesh that has none, since such a mesh is at sea level.

A cut through cells interpolates every floating point array at the points it adds, over the
triangle each one lies in. `vtkIntersectionPolyDataFilter` interpolates some of those points
from the wrong points, 3 of the 12 that a cut at 15° E adds to a 30° grid, and it adds points
inside a triangle wherever the cutting plane's own diagonal crosses one. A point on an edge
takes the heights at the two ends of that edge, so a missing height elsewhere on its
triangle never reaches it.

(heights-spec-4-2)=
### 4.2 Where Heights Enter

| function | takes |
|---|---|
| `Transform.from_1d`, `from_2d`, `from_points` and `from_unstructured` | `height=`, `depth=`, `vertical_units=` |
| `Transform(...)`, the factory | the same, when it is made, carried by every mesh it makes |
| `Transform.to_structured_grid` | its `zs` as heights, and `vertical_units=` |
| `GeoPlotter.add_mesh` and `GeoPlotter.add_points` | `height=`, `depth=`, `vertical_units=` |

A height is given in any form of globe spec §4.2: a plain number or array in metres, or in
the unit `vertical_units` names, or a `pint` quantity of length from any registry. A scalar
gives every point that height. An array gives one height for each point, in the order of
the points the function builds, as point data given to it is ordered. An array the size of
the cells is refused, naming {issue}`2728`. For the bridge, the cells are the faces given,
before any masked face is dropped. An array whose size matches both the points and the
cells is read as heights of the points, and an array of one value gives one height to the
whole mesh, as a scalar does. A `zscale` given with heights is ignored, since there is no
z-level for it to scale.

`depth=` takes the same forms, positive downward, and is negated once, on the way in. A
negative depth is a height above sea level.

`add_mesh(mesh, height=...)` writes the heights to the mesh it draws, which is a copy, and
never to the mesh it was given. `add_points` builds its point cloud with them.

`to_structured_grid` reads its `zs` as the heights of the bounds of its layers, in metres,
in the unit `vertical_units` names, or as a quantity. Uneven levels are kept as given. Each
must be finite, since a level is a coordinate rather than data that may be missing. A grid
of depths passes their negation. Its `zlevel` and `zscale` are removed, which breaks no
release (§3.1).

`Transform.from_tiff` takes no heights, since its points come from the file (§8 item 2).
Nor do `resize` and `transform_mesh`, which position a mesh from the heights it carries
(§4.3), nor the built-in layers, which lie at sea level.

(heights-spec-4-3)=
### 4.3 Positions

A point is drawn from its height `h` as globe spec §4.4 sets, with the globe's radius `R`,
its scale `s`, the render radius over `R`, and its vertical mapping `V`, which is
`exaggeration * h` at or above sea level and `exaggeration_below * h` below it:

- on the globe, at a radius of `s (R + V(h))`;
- on a map, at `z = V(h)`, in the length unit of the CRS's horizontal axes, or where those
  axes are angular, as the angle `V(h)` subtends at `R`, in their angular unit.

A missing height is drawn as a height of 0.

Every function that positions a mesh with heights builds its points this way, from their
longitudes, latitudes and heights: the bridge at the globe it is given, `resize` at the
globe it is given, and `transform_mesh` at its globe, on the sphere or on a map. A scene
adding a mesh that records another globe builds it at the scene's, in place of the scale by
the ratio of render radii (scene spec §4.2). A mesh without heights is built at a height of
0, so it is drawn as it was before. A mesh with heights that records no globe is drawn where
its points lie, as any mesh that records no globe is (scene spec §4.4). Given to `resize` or
`transform_mesh`, it is positioned at `Globe()`, as such a mesh is.

A mesh with heights is never read at the one radius its points lie at, under item 2 of
scene spec §4.4. Its points lie at their heights, so heights that are all equal would read
as a globe at the lifted radius, and the mesh would be lifted twice. `Globe.from_mesh`
reads such a mesh at its `gvRadius`, if it has one, and otherwise returns `None`.

A point cloud with heights carries no z-level, so its radius encodes no level, and the third
column `from_cartesian` reports for it is 0, as it is for a surface. It records no
`gvZScale`, and on a map it carries no `gvZLevel`.

At the default globe a depth of 4,000 m is drawn 6.3 × 10⁻⁴ of the render radius below the
surface, which is too small to see. A user draws depths apart by giving the scene a globe
with `exaggeration_below`, as globe spec §4.1 intends.

(heights-spec-4-4)=
### 4.4 Refusals

Each of these raises a `ValueError` that names what was given:

- `height=` with `depth=`;
- heights given to a mesh that carries them, whether to `add_mesh` or, as a cloud, to
  `add_points`;
- heights with a z-level other than 0, wherever either is given, including a point cloud
  whose points already carry levels other than 0, and `resize` or `transform_mesh` given a
  z-level for a mesh with heights;
- heights for each cell ({issue}`2728`);
- an infinite height;
- an array that has neither one height for each point nor one for the whole mesh;
- a height that is not a length, such as a pressure, which `to_metres` refuses, naming its
  unit;
- `vertical_units` with a quantity, which carries its own unit, or with no height;
- heights with a CRS that has an axis named "Ellipsoidal height" (§3.4), which asks for a
  CRS whose vertical axis is gravity-related, or for none.

(heights-spec-4-5)=
### 4.5 What Row 3 Leaves Alone

- **Picking** gains nothing. A picked point's index reads its height from `mesh.gv.height`,
  which is what globe spec §4.4 asks of a picked point.
- **Lines and the search tree.** A geodesic line or a bounding box placed on a surface with
  heights lies where it does today, and `KDTree` searches the positions it is given. Lines
  at their true heights are row 4's (globe spec §4.5).
- **The base layer** is opaque at sea level, so it hides a surface below it from outside the
  globe (§8 item 3).
- **Vectors** keep their components. How the vertical mapping bends an arrow is
  globe spec §8 item 9.
- **The gallery and the README** keep their z-levels and their hand-warped orography until
  row 5 of globe spec §9 migrates them. Row 3 changes two examples, `grid/reykjanes` and
  `grid/reykjanes_contour`, whose `zs` it reads as heights. Their levels are 250 m apart,
  and were drawn half a cell of latitude apart before they were heights. Each example gives
  its grid and its scene `Globe(exaggeration=22.34)`, which draws them that far apart, so
  their images stand. {user}`bjlittle` plans to redesign `to_structured_grid` once row 1
  lands ({issue}`2774`).

(heights-spec-5)=
## 5. Alternatives Considered

- **A height and a z-level that add.** Rejected, by §2 decision 6. It needs a combined
  behaviour on the globe, on a map and in point clouds, each to design and test, and row 5
  removes it.
- **A scene whose globe can be replaced in row 3.** Deferred, by §2 decision 7. The scene
  would keep each layer's mesh, texture, z-level and transform, and rebuild every actor from
  them, which is a larger piece of work than the heights themselves (§8 item 1).
- **New heights replacing a mesh's own on the copy drawn.** Rejected, by §2 decision 5.
  The scene would show heights that the mesh does not hold.
- **Storing a depth as given, as `gvDepth`.** Rejected, by §2 decision 2. Every reader would
  handle two arrays and their signs.
- **A plain array named `height`.** Rejected, by §2 decision 1. It would collide with a
  user's own data.
- **Heights given to `resize` and `transform_mesh`.** Rejected, by §2 decision 4. Two more
  ways to give heights, each needing the refusal of §2 decision 5, for nothing the bridge and
  the scene do not already offer.
- **`from_cartesian` reporting heights.** Rejected, by §2 decision 8. One column would carry
  two meanings until row 5.
- **Refusing a missing height, as the parent did.** Rejected, by §2 decision 3. Data
  masked over land, loaded as the gallery loads it, would be refused. Refusing it only when
  a mesh is drawn was also rejected: a point a sea cell shares with a land cell may keep a
  missing height after `threshold` (§3.2), and the refusal would come where the user least
  expects it.
- **Settling {issue}`2728` here.** Deferred, by §2 decision 9. Drawing each cell flat at its
  own height, or averaging heights onto the points, each needs its own argument.
- **Refusing a CRS with an ellipsoidal height whenever it is given.** Rejected, by §2
  decision 10. Callers who pass `EPSG:4979` for longitudes and latitudes would break.
- **Lowering the base layer below the deepest height in row 3.** Deferred to row 4, which
  owns the base layer's lowering (globe spec §4.5).
- **A gallery example of heights in row 3.** Deferred to row 5, which migrates the
  orography example to heights.
- **`height_units` and `depth_units`.** Rejected, by §2 decision 11. Two keywords on every
  builder, and a third for the `zs` of `to_structured_grid`.
- **Arrays from `mesh.gv.height` that can be written.** Rejected, by §4.1. Writing to one
  would change the heights a mesh reports without moving its points.

(heights-spec-6)=
## 6. Testing

Every result is checked against a reference independent of `geovista`, as globe spec §6
requires, which this adds to:

- **heights**: a height in feet, kilometres or metres, as a quantity from any registry or
  with `vertical_units`, reads back from `mesh.gv.height` the same height in metres, and its
  point is drawn at `s (R + V(h))` on the globe and at `V(h)` in the CRS's unit on a map, by
  the formula, for every function of §4.2 and for `resize` and `transform_mesh`;
- **depths**: `depth=d` gives the mesh that `height=-d` gives, `mesh.gv.depth` is the
  negation of `mesh.gv.height`, and a negative depth is a height above sea level;
- **the vertical mapping**: a height above sea level moves by the factor above, and a depth
  by the factor below, and a mesh resized or transformed to a globe with another mapping
  moves by the formula, with every height read back unchanged;
- **reading a globe**: a mesh with heights all equal, that records no globe, reads as no
  globe, and `resize` lifts it once;
- **missing heights**: a masked or NaN height reads back as NaN and is drawn at sea level; a
  grid masked over land in its data and its heights, built by the bridge and passed through
  `threshold()` on its data, keeps its sea cells at their depths, as §3.2 measured;
- **the array**: `gvHeight` is never the active scalars, whatever the mesh carried before;
  neither `mesh.gv.height` nor `mesh.gv.depth` can be set, nor their arrays written; and
  heights survive the seam cut, `cast`, the slicers and `combine`, with 0 for a mesh that
  has none;
- **the scene**: a mesh with heights added to a scene with another render radius, Earth
  radius or exaggeration is drawn by the formula at the scene's globe, and the mesh given
  is unchanged;
- **`to_structured_grid`**: uneven heights, in metres or in another unit, place each level
  at its height;
- **refusals**: each case of §4.4 raises, naming what was given, and a CRS with a
  gravity-related height, or a CRS with an ellipsoidal height given no heights, is accepted
  as it is today;
- **the radius**: each of the above holds at a render radius of 1 and at the Earth's
  radius.

(heights-spec-7)=
## 7. Scope

In scope: `gvHeight`, `height=`, `depth=` and `vertical_units=`, `mesh.gv.height` and
`mesh.gv.depth`, positions built from heights on the globe and on a map, missing heights,
`to_structured_grid` reading its `zs` as heights, and the refusals of §4.4.

Out of scope:

- heights given for each cell ({issue}`2728`);
- a scene whose globe can be replaced (§8 item 1);
- heights read from a raster band (§8 item 2);
- layering, the base layer's lowering and the lift, which are row 4 of globe spec §9;
- removing `zlevel` and `zscale`, and migrating the gallery and the README, which are row 5;
- a vertical mapping in bands, or as a function of height (globe spec §8 item 8);
- converting heights between vertical datums (globe spec §7).

(heights-spec-8)=
## 8. Open Items

Each carries the status grammar of docs spec §3.6.

1. **Open** — **A scene whose globe can be replaced.** Globe spec §4.1 has a scene rebuild
   every position from its layers' heights when its vertical mapping changes. Row 3 fixes a
   scene's globe when the scene is made (§2 decision 7), so a new exaggeration means a new
   plotter ({issue}`2769`).
2. **Open** — **Heights from a raster band.** `Transform.from_tiff` builds its points from
   the file, and `extract` may drop some of them, so an array of heights cannot be matched to
   them. A digital elevation model is a GeoTIFF, and one of its bands could be read as the
   heights of the points ({issue}`2770`).
3. **Open** — **A surface below sea level, under the base layer.** The base layer is opaque at
   sea level, so an ocean floor drawn at its depth cannot be seen from outside the globe.
   Until row 4, a user drops the base layer or gives it an opacity. Row 4 of globe spec §9
   owns it, with the base layer's lowering (globe spec §4.5).

(heights-spec-9)=
## 9. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | Heights on a mesh: `gvHeight`, `height=`, `depth=` and `vertical_units=` on the bridge, `to_structured_grid` reading its `zs` as heights, positions from heights on the globe and on a map through the bridge, `resize` and `transform_mesh`, `mesh.gv.height` and `mesh.gv.depth`, missing heights, heights through the filters and `combine`, and the refusals of §4.4 | ✅ landed (2026-10-29, {pull}`2777`) |
| 2 | Heights in the scene: `height=`, `depth=` and `vertical_units=` on `GeoPlotter.add_mesh` and `GeoPlotter.add_points`, and a mesh that records another globe drawn from its heights | not started |

Statuses follow docs spec §3.6. Row 2 is planned once row 1 has landed. Until it lands, a
scene scales a mesh with heights that records another globe by the ratio of render radii,
as row 2 of scene spec §9 left it. Neither row breaks a release, since the `zlevel` and
`zscale` that `to_structured_grid` loses have never been released, and neither changes an
example in the README. Row 3 of globe spec §9 lands with row 2, before 0.6 is released.

(heights-spec-10)=
## 10. References

- The globe, heights and layers design: globe spec §2, globe spec §4.1, globe spec §4.2,
  globe spec §4.3, globe spec §4.4, globe spec §6, globe spec §8 and globe spec §9.
- The globe on the scene design: scene spec §2 decision 3, scene spec §4.2,
  scene spec §4.3, scene spec §4.4 and scene spec §4.6.
- {issue}`2728`, heights given for each cell.
