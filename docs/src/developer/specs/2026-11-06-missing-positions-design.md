# Missing Positions Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. It states when a position given to `geovista` is missing, and what each public
> function that takes positions does with one. Read it as current; the roadmap states what
> has actually landed.

- **Date:** 2026-11-06 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `positions spec §…`
- **Scope:** positions given as longitudes and latitudes, or as x and y in a CRS, that are
  masked or NaN; what the queries, single positions, geodesic shapes, point clouds, meshes
  and conversions of the public API do with them; and the refusal of an infinite coordinate
- **Lineage:** **positions spec**
- **Children:** none
- **Published:** in the specifications index

(positions-spec-1)=
## 1. Purpose

Geospatial data marks a value that isn't there with a mask or with NaN. `geovista` already
reads missing data and missing heights that way: the bridge fills masked data with NaN, and
a masked or NaN height is missing (heights spec §2 decision 3). A missing position has had
no such rule, so each function that takes positions met a mask in its own way, and most
read the value under the mask as a real position (§3.1).

{issue}`2849` reported two of them, found while servicing the review of {pull}`2844`:
`KDTree.query` names a real cell for a masked point, and `geodesic.line` raises an
unrelated `TypeError`. A survey of the public API found the same defect in eleven more
functions. Fixed one at a time, each would choose its own meaning for a masked position.

This specification settles that meaning once (§2 decision 1), then says what each kind of
function does with a missing position.

(positions-spec-2)=
## 2. Decisions

1. **🤝 Agreed** (2026-11-06, {user}`bjlittle`, {pull}`2888`) — **A position is missing when
   either of its coordinates is masked or NaN.** A position needs both coordinates, so one
   masked or NaN coordinate leaves none. This extends the rule of
   heights spec §2 decision 3 from heights to positions. It widens the test of the
   bridge, which reads a point as missing only when `xs` and `ys` carry the same mask
   (§3.3). Chosen by {user}`bjlittle` on 2026-11-06, over reading only a masked coordinate
   as missing and over keeping the bridge's test and refusing a coordinate masked alone.
2. **🤝 Agreed** (2026-11-06, {user}`bjlittle`, {pull}`2888`) — **An infinite coordinate is
   refused.** No position lies at it, and it is not missing either. The `ValueError` names
   the argument, as heights spec §2 decision 3 refuses an infinite height.
3. **🤝 Agreed** (2026-11-06, {user}`bjlittle`, {pull}`2888`) — **A query answers that a
   missing point has no neighbour.** `KDTree.query` gives it a distance of `inf` and an
   index equal to the number of points in the tree. That is pykdtree's own answer for a
   point beyond `distance_upper_bound`, so a caller who handles that case handles this one,
   and the other points of the query are still answered. Chosen by {user}`bjlittle` on
   2026-11-06, over refusing the query.
4. **🤝 Agreed** (2026-11-06, {user}`bjlittle`, {pull}`2888`) — **A function that answers
   for one position refuses a missing one.** `find_nearest_cell` and
   `GeoPlotter.view_poi` are each given a single position and have nothing to answer
   for a missing one, so each raises a `ValueError` naming the argument. Chosen by
   {user}`bjlittle` on 2026-11-06 for `find_nearest_cell`, over answering with an empty
   list. `view_poi` was found by the same survey and follows the same reasoning.
5. **🤝 Agreed** (2026-11-06, {user}`bjlittle`, {pull}`2888`) — **A geodesic shape refuses a
   missing position.** `geodesic.line`, `BBox` and `wedge` raise a `ValueError` naming the
   argument. A line has no one right way across a gap, and a box needs every corner.
   Accepting a missing position later would break no caller, so refusing it now keeps the
   other readings open. Chosen by {user}`bjlittle` on 2026-11-06, over breaking the line at
   the gap and over joining the positions either side of it.
6. **🤝 Agreed** (2026-11-06, {user}`bjlittle`, {pull}`2888`) — **A point cloud drops a
   missing point, with a warning.** `Transform.from_points` and `GeoPlotter.add_points`
   leave the point out, and its entry in every array given for each point in the same call
   goes with it, as {pull}`2628` drops a face and its cell data. The warning counts the
   points dropped. Chosen by {user}`bjlittle` on 2026-11-06, over refusing the cloud and
   over keeping a NaN point in it.
7. **🤝 Agreed** (2026-11-06, {user}`bjlittle`, {pull}`2888`) — **A mesh treats every
   missing point as the bridge treats a masked one.** The rules of §3.3 apply to each
   point that §2 decision 1 reads as missing, where today they cover only a point that `xs`
   and `ys` mask alike.
   `Transform.from_1d` refuses a NaN bound as it refuses a masked one, and
   `Transform.to_structured_grid`, whose grid has a point at every node, refuses a missing
   position the same way. This follows from §2 decision 1.
8. **🤝 Agreed** (2026-11-06, {user}`bjlittle`, {pull}`2888`) — **A conversion carries a
   missing position through as NaN.** `transform_points` returns NaN for it, and
   `vectors_to_cartesian` returns NaN for a vector at it, as `to_cartesian` has since
   {pull}`2844` and as `transform_point`, `geodesic.npoints` and `npoints_by_idx` already
   do. A conversion is a step inside other work, and that work decides what a
   missing position means for it.

(positions-spec-3)=
## 3. What Exists Today

(positions-spec-3-1)=
### 3.1 The Survey

Each public function that takes positions was given a masked longitude on 2026-11-06, on
`main` after {pull}`2887`:

| Function | Given a masked longitude |
|---|---|
| `KDTree.query` | names a real cell, reading the value under the mask as the position |
| `find_nearest_cell` | names cell 0, VTK's answer for the NaN point that `to_cartesian` gives it |
| `GeoPlotter.view_poi` | points the camera at longitude 0 |
| `geodesic.line` | raises a `TypeError` from `np.isclose`, naming no argument |
| `geodesic.BBox`, `geodesic.wedge` | build a mesh with NaN points, and say nothing |
| `Transform.from_points`, `GeoPlotter.add_points` | make a real point at the value under the mask |
| `Transform.to_structured_grid` | makes a real point at the value under the mask |
| `transform_points` | transforms the value under the mask |
| `vectors_to_cartesian` | computes the vector at the value under the mask |
| `Transform`, `Transform.from_2d`, `Transform.from_unstructured` | use the value under the mask, unless `xs` and `ys` carry the same mask (§3.3) |
| `Transform.from_1d` | refuses a masked bound |
| `to_cartesian`, `transform_point`, `geodesic.npoints`, `geodesic.npoints_by_idx` | return NaN |
| `wrap` | keeps the mask |

A NaN coordinate fares no better. pykdtree answers a NaN point with a distance of
1.3e154 and an index of 4294967295, past the end of the tree, and answers an infinite one
the same way. `from_1d` and `from_2d` build faces with a NaN vertex.

(positions-spec-3-2)=
### 3.2 Missing Values Elsewhere

The bridge fills masked data with NaN (heights spec §3.2). A masked or NaN height is
missing and is drawn at sea level, and only an infinite height is refused
(heights spec §2 decision 3). `to_cartesian` reads a masked coordinate as NaN since
{pull}`2844`, which found that `np.vstack` drops a mask while still returning a masked
array.

(positions-spec-3-3)=
### 3.3 Masked Points in the Bridge

Five pull requests gave the bridge's meshes rules for a point that `xs` and `ys` mask
alike:

- {pull}`2599` keeps such a point out of the faces of a connectivity taken from a shape. A
  face keeps its other vertices, and stays while three remain.
- {pull}`2620` and {pull}`2626` keep it out of the transform, so a value under the mask
  outside a projection's domain raises no `ProjError`. The point stands on the first point
  that is not masked, where it cannot stretch the bounds of the mesh.
- {pull}`2628` drops a face of a connectivity array that uses it, with a warning counting
  the faces, and cuts data given for each face to the faces that remain. The point stays in
  the mesh, so data given for each point still fits. {user}`bjlittle` chose the drop on
  {issue}`2621`, over taking the point out of the face and over refusing the call.
- {pull}`2632` refuses a masked bound in `from_1d`, since a masked bound is a gap in its
  axis.

The masks are compared whole. When they differ anywhere, no point is masked, and each
value under a mask is read as a coordinate.

(positions-spec-4)=
## 4. Design

(positions-spec-4-1)=
### 4.1 A Missing Position

One private helper in `geovista.common` decides it for every function. It takes the two
coordinates as they arrive, after a `pint` quantity is read in its units and before any
transform, and returns a boolean array of their shape that is `True` wherever either is
masked or NaN. A masked array whose mask is `nomask` has no missing position.

The same helper refuses an infinite coordinate, before any position is built, with a
`ValueError` naming the argument as the function calls it: `lons` or `lats`, `xs` or `ys`,
`x` or `y`, or `lon1` or `lon2`. Conversions refuse it too, by §2 decision 2. An infinite
value under a mask counts as missing, since a value under a mask is never read.

The test reads positions as given, so a value under a mask is never transformed. A NaN that
a transform produces, for a position outside a CRS's domain, is not a missing position
(§4.8).

(positions-spec-4-2)=
### 4.2 Queries

`KDTree.query` leaves its missing points out of the query and gives each the answer pykdtree
gives a point beyond `distance_upper_bound`: a distance of `inf` and an index equal to the
number of points in the tree. With `k` above 1, every neighbour of a missing point has that
answer. The other points are queried as before, and their answers do not change.

(positions-spec-4-3)=
### 4.3 Single Positions

`find_nearest_cell` raises a `ValueError` naming `x` or `y` when its point-of-interest is
missing, and so does `GeoPlotter.view_poi`. Given one coordinate, `view_poi` sets the other
to 0, in the units of the one given, so that a refusal names only the coordinate the caller
gave. The default position of `view_poi`, the centre of the last mesh added, is not given
by the caller and is out of scope.

(positions-spec-4-4)=
### 4.4 Geodesic Shapes

`geodesic.line` and `BBox` raise a `ValueError` when any position given is missing, before
any geodesic is computed. The message names the argument, `lons` or `lats` for `line` and
`xs` or `ys` for `BBox`, and counts the missing positions. `wedge` raises the same way for
a missing `lon1` or `lon2`. `geodesic.panel` takes the name of a panel, not a position, and
`npoints` and `npoints_by_idx` are conversions (§4.7).

(positions-spec-4-5)=
### 4.5 Point Clouds

`Transform.from_points` drops each missing point before it transforms the rest, and warns
once, counting the points it dropped. Every array given for each point in the same call
loses the same entries: `data`, `vectors`, the heights of `height` or `depth`, and a
`zlevel` array. A value given once for every point is kept as it is. A cloud whose every
point is missing is built with no points, and the warning says so.

`GeoPlotter.add_points` passes `xs` and `ys` to `from_points`, and an array of `scalars` to
`add_mesh`, so it cuts `scalars` by the same points. Points given as a mesh or as
Cartesian `points` are positions already, and out of scope (§4.8).

(positions-spec-4-6)=
### 4.6 Meshes

`Transform.from_unstructured`, and `from_2d` and the `Transform` constructor through it,
read the test of §4.1 where they read a mask shared by `xs` and `ys` today, and apply the
rules of §3.3 to each missing point. A coordinate masked alone, masks that differ, and a
NaN coordinate each keep their point out of the faces and out of the transform. The
warning of {pull}`2628` names a missing point rather than a masked one.

`Transform.from_1d` refuses a NaN bound with the error it gives a masked one.
`Transform.to_structured_grid` refuses a missing position in `xs` or `ys` the same way,
since its grid has a point at every node and no face to drop.
`Transform.from_tiff` builds its positions from the file's transform, which leaves none
missing (§4.8).

(positions-spec-4-7)=
### 4.7 Conversions

`transform_points` returns NaN for a missing position and leaves its value out of the
transform, as §3.3 leaves a masked point out, so a value under a mask outside the domain of
the target CRS raises nothing. `vectors_to_cartesian` returns NaN for each component of a
vector at a missing position. `to_cartesian`, `transform_point`, `geodesic.npoints` and
`npoints_by_idx` already return NaN, and row 5 of §9 tests them for it.

(positions-spec-4-8)=
### 4.8 What This Design Leaves Alone

- Missing data values, which the bridge fills with NaN, and missing heights, which
  heights spec §2 decision 3 governs.
- Points given as a mesh or as Cartesian `xyz`, to `GeoPlotter.add_points` or as the mesh
  of a `KDTree`, which are positions already built.
- A NaN that a transform produces for a position outside a CRS's domain. The position was
  given, and §4.1 reads positions as given.
- The positions `Transform.from_tiff` builds from a file, and the masked data that its
  `extract` removes.
- `wrap`, which keeps the mask of the longitudes it is given, and so carries a missing
  longitude through already.
- The longitude of `GeoPlotter.add_meridian` and the latitude of `add_parallel`, and the
  values given to `create_meridian_labels` and `create_parallel_labels`, which place
  gridlines and labels rather than positions.
- A latitude beyond ±90°, or any other position given out of range. The prefix leaves room
  for a later rule about positions given in error.

(positions-spec-5)=
## 5. Alternatives Considered

- **Reading only a masked coordinate as missing, and NaN as today.** Rejected, by
  §2 decision 1. A NaN vertex would stay in its face, and pykdtree answers a NaN point with
  an index past the end of the tree (§3.1).
- **Keeping the bridge's test, and refusing a coordinate masked alone.** Rejected, by
  §2 decision 1. A dataset that masks only its longitudes would be refused rather than
  drawn.
- **Refusing a query with a missing point.** Rejected, by §2 decision 3. One missing point
  would fail the whole batch.
- **`find_nearest_cell` answering an empty list.** Rejected, by §2 decision 4. With
  `single=True` it returns one cell ID, so it would have to raise there anyway, and would
  give two answers to one question.
- **Breaking a line at a missing position**, as matplotlib draws a masked line. Rejected
  for now, by §2 decision 5. `close=True` and the two-position minimum would each need a
  rule of their own. Refusing first leaves this open.
- **Joining the positions either side of a missing one with one geodesic.** Rejected, by
  §2 decision 5. The shape would change without saying so.
- **Refusing a point cloud with a missing point.** Rejected, by §2 decision 6. A cloud of
  observations with gaps would be refused, where the bridge's meshes drop the faces at a
  gap and draw the rest.
- **Keeping a missing point in the cloud as NaN.** Rejected, by §2 decision 6. The count
  would be kept, so arrays added later would fit, but a point with no position would stay
  in the cloud for VTK and every projection to handle.
- **Placing this specification under the heights specification**, extending
  heights spec §2 decision 3. Rejected by {user}`bjlittle` on 2026-11-06. Positions are not
  that specification's subject, and this one would sit four generations deep.

(positions-spec-6)=
## 6. Testing

Each case is checked against a reference built without the missing positions: the same
call given only the positions that are present, or pykdtree's answer for a point beyond
`distance_upper_bound`.

- **the test of §4.1**: a longitude masked alone, a latitude masked alone, both, NaN in
  either, a `pint` quantity of a masked array, and a mask of `nomask`; and an infinite
  coordinate refused, naming its argument, in every function of this specification;
- **queries**: a missing point answers a distance of `inf` and the tree's count of points,
  for `k` of 1 and above, and every other point answers what it answers when queried alone;
- **single positions**: `find_nearest_cell` and `view_poi` refuse a masked or NaN
  coordinate, naming it;
- **geodesic shapes**: `line`, `BBox` and `wedge` refuse a missing position, naming the
  argument, before any geodesic is computed;
- **point clouds**: a cloud with missing points equals the cloud built from the others, with
  its `data`, `vectors`, heights, `zlevel` array and, through `add_points`, `scalars` cut
  alike, and one warning counting the points dropped; a cloud of only missing points has
  no points;
- **meshes**: a coordinate masked alone, masks that differ and a NaN coordinate each drop
  the faces that use their point, with the warning, as a point masked alike does in the
  tests of {pull}`2628`; `from_1d` refuses a NaN bound; and `to_structured_grid` refuses a
  missing position;
- **conversions**: `transform_points` gives NaN for a missing position, including one whose
  value under the mask lies outside the domain of the target CRS, `vectors_to_cartesian`
  gives NaN for a vector at one, and `to_cartesian`, `transform_point`, `npoints` and
  `npoints_by_idx` give NaN.

Each test is checked to fail when the behaviour it covers is removed.

(positions-spec-7)=
## 7. Scope

In scope: the test of §4.1, the refusal of an infinite coordinate, and the functions of
§3.1 as §4.2 to §4.7 describe them. In scope too: the width check of `geodesic.wedge`,
which §8 item 3 records.

Out of scope: everything §4.8 lists.

(positions-spec-8)=
## 8. Open Items

Each carries the grammar of items spec §3.2.

1. **🏁 Resolved** (2026-11-07, {pull}`2893` · 🔎 2026-11-06, {pull}`2889` · 🎫 {issue}`2890`) — **The
   final review of row 1 left four gaps.** Three behaviours of row 1 work, but no
   test holds them: `KDTree.query` broadcasting a missing point against a `zlevel` of another
   shape, `GeoPlotter.view_poi` given one coordinate alone as a missing `pint` quantity, and a
   NaN `zlevel` querying as it did before (§4.2). The fourth is the message refusing an
   infinite value, which gives a flat index for an array of more than one dimension, where an
   index for each dimension would be clearer. Owed by row 2 of §9, the next row to use the
   test of §4.1. Row 2 settled all four. In `tests/search/test_missing_positions.py`,
   `test_a_zlevel_that_broadcasts` holds the broadcast and `test_a_nan_zlevel_is_not_missing`
   the NaN `zlevel`, and the case `y-nan-quantity` of `test_one_coordinate_given_missing` in
   `tests/geoplotter/test_view_poi.py` holds `view_poi`. The refusal of an infinite
   coordinate, and that of an infinite height, now give the index in each dimension, such as
   `(1, 1)`, and keep `at index 1` for one dimension.

2. **❓ Open** (🔎 2026-11-07, {pull}`2893` · 🎯 row 3 of §9 · 🎫 {issue}`2895`) — **The
   final review of row 2 left four minor points.** `geodesic.wedge` given `None` for a
   longitude says it is masked or NaN, where it raised a `TypeError`, since the test of §4.1
   reads `None` as NaN. `units._angle` reads a masked quantity as NaN, with no NumPy warning,
   for every caller, so row 5 cannot count on that warning to flag a masked angle given to
   `npoints`. `_refuse_missing_positions` given two coordinates of one size but different
   shapes raises NumPy's broadcast message, which a grid of positions would meet. And the
   Raises sections of `line` and `BBox` leave out the refusal of a `pint` quantity given for
   one coordinate alone, and that of an angle for a projected CRS. Owed by row 3 of §9, the
   next row to use the test of §4.1.

3. **❓ Open** (🔎 2026-11-07, {pull}`2893` · 🎯 row 6 of §9 · 🎫 {issue}`2894`) — **`geodesic.wedge`
   builds a bounding-box for two equal longitudes.** It refuses a wedge 180 degrees or more
   wide, but not one of no width. Its check, `if 0 < delta >= 180`, reads as
   `0 < delta and delta >= 180`, so `wedge(10, 10)` builds a bounding-box of 132,098 points,
   though the message of the check asks for a width in the open interval (0, 180). The final
   review of row 2 found it. The check is older than this specification and has nothing to
   do with a missing position, and fixing it would refuse calls that build today. Owed by
   row 6 of §9, added for it, since no other row touches `wedge`.

(positions-spec-9)=
## 9. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | Queries: the test of §4.1 and the refusal of an infinite coordinate, `KDTree.query` answering that a missing point has no neighbour (§4.2), and `find_nearest_cell` and `GeoPlotter.view_poi` refusing a missing position (§4.3) | ✅ landed (2026-11-06, {pull}`2889`) |
| 2 | Geodesic shapes: `geodesic.line`, `BBox` and `wedge` refusing a missing position (§4.4) | ✅ landed (2026-11-07, {pull}`2893`) |
| 3 | Point clouds: `Transform.from_points` and `GeoPlotter.add_points` dropping a missing point, and its entries in every array given for each point, with a warning (§4.5) | 🚧 in progress ({pull}`2899`) |
| 4 | Meshes: `Transform.from_unstructured`, `from_2d` and the `Transform` constructor reading the test of §4.1, `from_1d` refusing a NaN bound, and `to_structured_grid` refusing a missing position (§4.6) | 📋 not started |
| 5 | Conversions: `transform_points` and `vectors_to_cartesian` returning NaN for a missing position (§4.7) | 📋 not started |
| 6 | Wedge width: `geodesic.wedge` refusing a wedge of no width, as the message of its check says (§8 item 3) | 📋 not started |

Statuses follow docs spec §3.6. Each row lands in a pull request of its own, as
{user}`bjlittle` chose on 2026-11-06. Row 1 brings the test of §4.1, which the others use,
so rows 2 to 5 each need row 1, and row 6 needs none. {issue}`2849` closes when rows 1 and 2 have landed.

Row 4 changes the mesh built from a NaN coordinate: the faces that use its point are
dropped, with a warning, where today they are built with a NaN vertex.

(positions-spec-10)=
## 10. References

- heights spec §2 decision 3 and heights spec §3.2, the rule for a missing height.
- {issue}`2849`, which reported `KDTree.query` and `geodesic.line`.
- {pull}`2844`, which made `to_cartesian` read a masked coordinate as NaN.
- {pull}`2599`, {pull}`2620`, {pull}`2626`, {pull}`2628` and {pull}`2632`, the bridge's
  rules for a masked point (§3.3), and {issue}`2621`, where the rule for a face was chosen.
- pykdtree, whose answer for a point beyond `distance_upper_bound` §2 decision 3 adopts:
  <https://github.com/storpipfugl/pykdtree>

(positions-spec-11)=
## 11. Verification

Each row follows ledger spec §3.4.

| Decision | Status | Evidence |
|---|---|---|
| §2 decision 1 | ⏳ pending | rows 1 to 5 of §9 |
| §2 decision 2 | ⏳ pending | rows 1 to 5 of §9 |
| §2 decision 3 | ✅ verified (2026-11-06, {pull}`2889`) | `tests/search/test_missing_positions.py` |
| §2 decision 4 | ✅ verified (2026-11-06, {pull}`2889`) | `tests/geoplotter/test_view_poi.py`, `tests/search/test_missing_positions.py` |
| §2 decision 5 | ✅ verified (2026-11-07, {pull}`2893`) | `tests/geodesic/test_missing_positions.py` |
| §2 decision 6 | ⏳ pending | row 3 of §9 |
| §2 decision 7 | ⏳ pending | row 4 of §9 |
| §2 decision 8 | ⏳ pending | row 5 of §9 |
