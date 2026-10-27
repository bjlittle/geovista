# geovista Globe-First CRS Foundation — Design Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. It states how `geovista` takes a mesh from the globe into any coordinate
> reference system (CRS) it supports, and where the two ever diverge it is the
> specification that gets corrected. Read it as current; the roadmap states what has
> actually landed.

- **Date:** 2026-10-23 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `crs spec §…`
- **Scope:** the foundation every projected scene stands on: the globe model, units, the
  cutting engine on the sphere, the domain of each class of projection, datums, the CRS
  interface, and the reuse of all of it across a time series
- **Parent spec:** none; its conventions are those of docs spec §1
- **Published:** in the specifications index

(crs-spec-1)=
## 1. Purpose

`geovista` should support, at a minimum, every use case and capability that `cartopy`
offers, which is the de facto standard, and do better. The first step, and the one the
rest stand on, is solid support for coordinate reference systems. Regions for users, 3D
region solids, a rigorous vertical dimension and features without `cartopy` all follow,
each as a design of its own (§9).

Today `geovista` projects a mesh in one way. It rotates the mesh about the polar axis so
that the central meridian sits at zero, cuts a seam along the antimeridian, and projects
the vertices. That assumes a projection takes the whole globe in one piece, with a single
seam on a meridian. Measured on 2026-10-23 against a global 5° mesh
(§3.1), the assumption holds for 17 of `cartopy`'s 38 projection
classes and 91 of the 162 projection methods of PROJ 9.9. The rest raise, run off to
infinity, or tear, in six distinct ways (§3.2).

The design keeps data on the globe for as long as possible and projects it last. Every
cut, clip, seam and test of a domain happens on the sphere, where there are no
discontinuities, no wrapping at ±180° and no edges sitting exactly on a seam. The
geodesic `BBox` manifold was the first step in that direction, and this design
generalises it.

The bar is scientific confidence. A scientist must be able to trust and check every cut,
every boundary and every height, so the design is built around two rules it may never
break (§2, decision 1).

(crs-spec-2)=
## 2. Decisions

These were decided with {user}`bjlittle` while the design was written.

1. **Never quietly wrong, and never silently drop data.** These are the hard rules, in
   that order. A result that looks plausible but is subtly off is the worst outcome. A
   cell, point or line removed without a word is the next worst.
2. **Globe first.** Data stays on the sphere until the last step, and projection happens
   once, at the end.
3. **Rebuild from the ground up.** The seam and transform code (`MeridianSlice`, `remesh`,
   the central meridian rotation in `transform_mesh` and `GeoPlotterBase.add_mesh`) is
   redesigned around the engine of §4.2, not extended.
4. **Breaking changes are allowed.** `geovista` is 0.x with a small community, so this is
   the time to make them.
5. **cartopy is not a foundation.** Its approach clips in projected space with planar
   geometry, which this design rejects. `cartopy` becomes an optional dependency, and is
   dropped once the Natural Earth features no longer need it. `shapely` plays no part in
   geometry.
6. **Learn from cartopy, without repeating its journey.** Its lasting idea is that a
   projection carries knowledge of its own valid domain, and that idea is kept, applied on
   the globe. Its defaults are inherited where they are sound, and challenged where they
   smell (§5).
7. **Three ways in.** Scientists may name a projection with a `geovista` class that mirrors
   `cartopy`'s name and keywords, with a PROJ string or `pyproj.CRS`, or with a `cartopy`
   CRS object. Writing PROJ strings is for power users, and nobody is forced to.
8. **A safe default for data meshes.** A data mesh's cells are never refined by default.
   Refinement for display is an explicit opt-in, every sub-cell carries the id of its
   source cell, and the result records that it was refined
   (§4.6). Built-in lines and boundaries, such as coastlines, the
   graticule and a domain's edge, are always densified. A user's line mesh is data, and
   follows the rule for data meshes.
9. **Cut once, map many.** Most time series keep a fixed mesh and change only its values,
   so the geometry is worked once and every frame carries its values through a stored
   mapping (§4.5).
10. **Coverage commitment.** The architecture covers every class of projection. Delivery
    commits to `cartopy` parity (all 38 classes, interrupted Goode Homolosine and
    Spilhaus included), to every PROJ method in classes 1 to 4 except four, and to keeping
    the 91 methods that work today working. The four are the Space Oblique Mercator family
    (`som`, `lsat`, `misrsom`), which follows a satellite's ground track rather than a
    great circle, and `bipc`, which joins two oblique cones. They, and the other
    interrupted and polyhedral methods, come when a scientist asks. Anything not yet
    supported fails loudly (§4.3).
11. **Build on specialised packages.** `geovista` is the glue in its cartographic domain.
    PROJ does projection mathematics, VTK and `pyvista` do mesh processing, and
    `geovista` contributes upstream where a package needs shaping for its use, rather
    than reinventing what the package does. `pyvista` exposes the whole of VTK's filter
    set, so where `pyvista` lacks exactly what is needed and cannot be reshaped upstream,
    a custom VTK filter is an option.
12. **No release regresses a working use.** Until a class lands, the PROJ methods it holds
    keep today's path unchanged, so a regional mesh in Web Mercator, UTM, the British
    National Grid or a rotated pole keeps working. That path is deleted when the last
    class lands (§10).
13. **Units are first class, through `pint`.** Every physical quantity at the API boundary
    is either a plain number in its documented unit, or a `pint` quantity. A CF unit
    string, as an Iris cube or an xarray `units` attribute carries, is read with
    `pint-cf`'s CF-compliant registry. Inside, quantities are converted once to SI and the
    hot paths stay plain NumPy (§4.9). `cf-units` is not used,
    because it builds on the UDUNITS-2 C library, which pip cannot install; that is the
    view of {user}`bjlittle`, a core developer of `cf-units`.

(crs-spec-3)=
## 3. What Exists Today

(crs-spec-3-1)=
### 3.1 How It Was Measured

Each of the 162 PROJ projection methods that `proj -lP` lists with a classification, and
each of `cartopy` 0.26's 38 projection classes through its PROJ definition, took a global
5° mesh through `transform_mesh`, using PROJ 9.9.0 and `pyproj` 3.8.0 at
`6c27439f`. Methods that PROJ will only build with parameters were given typical ones
(`+lat_1=20 +lat_2=60` for a conic, `+h=35785831` for `geos`, and so on). A method
counted as working when it raised nothing and every point was finite, no coordinate
exceeded 10⁸ m, no cell was folded (its winding reversed), and no cell was torn. A cell
was torn if it spanned more than half the projection, or had an edge more than ten times
the median of the edges between the same two latitudes. The second test catches tears
across an interruption, and the comparison within a latitude band spares the expected
stretching of a cylindrical projection near a pole.

The coverage test of §6 repeats this measurement in every run of the
unit tests. The first measurement counted 161 methods and found `rouss` failing. The
test's first run, on 2026-10-24 at `7ca628c1`, counted 162 and found `rouss` working, and
§3.2 reports its outcomes.

On a sample of twelve working methods the whole plotter worked as well: mesh, coastlines,
graticule and textured base layer. The one exception was `vandg`, whose coastlines raise
`ProjError`.

(crs-spec-3-2)=
### 3.2 The Six Classes of Failure

The 71 failing PROJ methods and 21 failing `cartopy` classes fall into six classes, each
needing something different on the globe before it can be projected. Two methods,
`august` and `bacon`, fail without a class yet: each tears its cells at the south pole.

| # | Class | What goes wrong | PROJ | `cartopy` | Issue |
|---|---|---|---|---|---|
| 1 | Latitude limits | a pole goes to infinity | 9 | 3 | {issue}`140` |
| 2 | A cap around a centre | only a cap is valid, and the far side raises or runs away | 18 | 9 | {issue}`1402` |
| 3 | A band around a central line | singular 90° from the line | 21 | 6 | {issue}`2674` |
| 4 | Oblique aspect, one seam | the seam is not a meridian | 4 | 1 | {issue}`2519` |
| 5 | Interrupted | several partial seams | 9 | 1 | none |
| 6 | Polyhedral | seams along the edges of faces | 8 | 1 | none |

The members of each class, by PROJ method and `cartopy` class:

1. `merc`, `webmerc`, `tobmerc`, `cc`, `calcofi`, `lcc`, `ccon`, `pconic`, `murd2`;
   `Mercator`, `LambertConformal`, `LambertZoneII`.
2. `ortho`, `gnom`, `nsper`, `tpers`, `geos`, `stere`, `ups`, `sterea`, `laea`, `aeqd`,
   `airy`, `nicol`, `adams_hemi`, `alsk`, `gs48`, `gs50`, `lee_os`, `mil_os`;
   `Orthographic`, `Gnomonic`, `NearsidePerspective`, `Geostationary`, `Stereographic`,
   `NorthPolarStereo`, `SouthPolarStereo`, `LambertAzimuthalEqualArea`,
   `AzimuthalEquidistant`.
3. `tmerc`, `etmerc`, `utm`, `gstmerc`, `cass`, `tcc`, `tcea`, `omerc`, `somerc`, `labrd`,
   `ocea`, `oea`, `krovak`, `mod_krovak`, `nzmg`, `bipc`, `imw_p`, `sch`, `som`, `lsat`,
   `misrsom`; `TransverseMercator`, `UTM`, `OSGB`, `OSNI`, `EuroPP`, `ObliqueMercator`.
4. `ob_tran`, `bertin1953`, `tpeqd`, `chamb`; `RotatedPole`.
5. `igh`, `igh_o`, `imoll`, `imoll_o`, `peirce_q`, `guyou`, `healpix`, `rhealpix`,
   `interrupted`; `InterruptedGoodeHomolosine`.
6. `isea`, `ivea`, `dsea`, `tsea`, `airocean`, `spilhaus`, `s2`, `qsc`; `Spilhaus`.

The 91 methods that work today are every whole-world method with a single seam on the
antimeridian of its central meridian: 51 pseudocylindrical (`robin`, `moll`, `eqearth`,
`natearth`, `wag1` to `wag6`, `eck1` to `eck6`, and more), 10 cylindrical without a
singular pole (`eqc`, `cea`, `mill`, `gall`, `patterson`, and more), 12 conic (`aea`,
`eqdc`, `poly`, `bonne`, and more), 17 others (`wintri`, `aitoff`, `hammer`, `vandg`,
`lagrng`, and more), and one azimuthal, `rouss`. Several have no `cartopy` class, such as
Winkel Tripel, Natural Earth and Van der Grinten, which is one place `geovista` is
already ahead.

Projecting leniently, by turning PROJ's error checks off and dropping every cell that is
non-finite, folded or runaway, made 28 of the 70 methods of the first measurement render
cleanly but with jagged edges.
That fallback is rejected as a default (§7).

(crs-spec-3-3)=
### 3.3 The Globe and the Vertical

The radius of the globe defaults to 1 (`common.RADIUS`), and nothing records its units.
At an Earth radius of 6.371×10⁶ m the projection path holds, including a seam that
bisects cells, because its tolerances are already relative to the mesh. The scene does
not: coastlines, the graticule and the base layer are still drawn at radius 1, and vanish
inside an Earth-sized mesh. A `zlevel` is a fraction of a radius scaled by `zscale`, not
a height.

Only EPSG:4326 renders as a globe. By design of `crs.planar`, every other geographic CRS
renders flat, including `OGC:CRS84`, `+proj=longlat +datum=WGS84` and the WGS84 3D CRS
EPSG:4979. A geocentric CRS such as EPSG:4978 collapses to a plane, and a CRS of another
body, such as Mars, fails because PROJ will not transform between bodies.

(crs-spec-4)=
## 4. Design

(crs-spec-4-1)=
### 4.1 The Globe Model

> **Extended by a child specification.** The globe of a scene, heights and depths in
> physical units, the vertical exaggeration, and the layering that replaces `zlevel` and
> `zscale` are specified in [`2026-10-26-globe-heights-layers-design.md`](2026-10-26-globe-heights-layers-design.md), `globe spec §…`, which inherits this document's
> decisions (§2) and testing (§6) unchanged.

Each scene has one globe model, and every layer takes its geometry from it: data meshes,
coastlines, graticule, base layer, and later regions and region solids. Nothing assumes a
radius of 1.

The model carries:

- a physical radius, a length quantity, by default the WGS84 semi-major axis of
  6,378,137 m, which is the sphere `cartopy` uses for its spherical classes;
- the scale between physical units and the units the scene is rendered in, so a scene can
  be rendered at a normalised radius of 1 while every height and tolerance stays physical
  (§8, item 3);
- an explicit vertical exaggeration, applied once by the scene
  (globe spec §4.4).

Every tolerance in the engine is relative to the radius or expressed as an angle, so a
result is the same at radius 1 and at the Earth's radius. Heights in physical units, and
what replaces the `zlevel` and `zscale` of zlevel spec §3.1, were
first given to the design of region solids and the vertical, and came forward into
globe spec §4.

(crs-spec-4-2)=
### 4.2 The Cutting Engine

Almost every operation of this design is a cut by a plane on the sphere. A plane through
the centre meets the sphere in a great circle, and a plane off the centre meets it in a
small circle, such as a parallel or the rim of a cap. The engine offers four primitives:

1. **Rotate.** Turn a mesh with a 3D rotation, between the geographic frame and a
   projection's natural frame (§4.3). Today's rotation about the
   polar axis by the central meridian is the special case.
2. **Clip.** Keep the part of a mesh where a signed function is not negative, and cut
   every crossing cell exactly where the function crosses zero, interpolating the values
   at each new point along its edge. The distance from a plane is the common case. A
   limit that is not a plane on the sphere is clipped by its exact predicate, evaluated
   at each point: the horizon of a perspective projection on an ellipsoid, such as
   `cartopy`'s `Geostationary` on WGS84, lies between 81.30° and 81.33° from the
   sub-satellite point on `geovista`'s sphere, depending on azimuth, so no single cap
   fits it.
3. **Cut a seam.** Split a mesh along an arc of a great circle bounded by two half-planes,
   such as a meridian from pole to pole, or half a meridian for an interruption. Points on
   the seam are duplicated so that the connectivity breaks, and each copy belongs to the
   side its cells are on.
4. **Densify.** Subdivide a line or a boundary along its declared edge type (a great
   circle, a small circle, or straight in a named CRS) until it lies within a tolerance
   of the true curve. The tolerance is one physical quantity, the sag of a segment from
   the true curve on the sphere, in metres or as an angle, the same for every projection.
   Where a projection stretches strongly, near a domain's edge for example, a segment is
   also subdivided until its projected midpoint lies within the tolerance of the
   projected chord, converted to a distance on the ground by the local scale. That test
   uses the forward projection alone, so it works for the 25 PROJ methods without an
   inverse. `geodesic.GEODESIC_NPTS` and the graticule's `n_samples` fold into it.

Each primitive works on surfaces, lines and points. A point is kept or removed whole, and
a line is clipped or cut at its exact crossing. Each primitive also returns an account of
its work (§4.6).

The seam must land exactly where PROJ puts its discontinuity, to the last digit. The
review of {pull}`2689` found that a difference of 3.3×10⁻⁹° put both copies of a seam
on the same edge of a Robinson map. Today `transform_mesh` avoids the question by
rebasing the target CRS to a central meridian of zero, so that seam points sit exactly at
±180°. A general rotation cannot always rebase the CRS, so each copy of a seam point is
moved a small angle into its own side before projection. The angle must exceed PROJ's
tolerance for wrapping a longitude and stay far below any distance a scientist would
notice. It is verified per class (§6, and §8
item 6).

The exact cut of a crossing cell puts new points on the cell's straight edges, which are
chords inside the sphere. Today's seam cut moves each of them back out to the radius
interpolated for it ({pull}`2715`). That radial move keeps a point on a great-circle cut,
whose plane passes through the centre, but would lift a point on a small-circle cut off
its circle. So how the engine moves them is left to the builder, provided each point stays
on the circle it was cut on, at the radius interpolated for it.

VTK, through `pyvista`, does the clipping and cutting. `pyvista` 0.49 made clipping by a
plane, clipping by a surface, transforms and extraction faster, and `pyvista` 0.49 is the
floor (§8, item 9). Manifold, through `pyvista-manifold`, is not part
of the foundation: its booleans need closed solids, so it cannot cut an open data mesh.
It belongs to the region solids of project 4.

(crs-spec-4-3)=
### 4.3 Projection Domains

A projection's domain is its valid region on the globe, together with its seams. Most
failing projections are a normal-aspect projection seen through a rotation of the sphere:
transverse Mercator is Mercator turned on its side, and an azimuthal projection centred
anywhere is a polar one rotated. So a domain is described by three things:

1. a rotation into the projection's natural frame;
2. limits in that frame, which are small-circle clips;
3. seams in that frame, which are great-circle arcs.

| Class | Natural frame | Limits | Seams |
|---|---|---|---|
| 0, whole globe | central meridian at zero | none | the antimeridian |
| 1, latitude limits | central meridian at zero | a minimum and a maximum latitude | the antimeridian |
| 2, a cap | the centre turned to the north pole | a cap of a given angular radius | none, since a cap is a disc |
| 3, a band | the central line turned to the equator | a band of a given half-width, and a length along it | the antimeridian of the frame, where the band is a full ring |
| 4, oblique | the projection's pole turned to the north pole | none | the antimeridian of the frame |
| 5, interrupted | central meridian at zero | none | the antimeridian, and a half-meridian per interruption |
| 6, polyhedral | per method | none | the edges of the faces |

Class 0 is what works today. It must stay working, as a class like any other.

A cap needs no seam, because the sphere minus anything outside a cap is a disc, which
projects without tearing. That holds for the near-whole-globe caps of `laea` and `aeqd`,
whose domain removes a small cap around the antipode, and for the hemispheres of `ortho`.

Some methods are polynomials fitted to one region, and far from it they do not fail but
are quietly wrong: `nzmg` maps a point 3,000 km from New Zealand without complaint. They
are `nzmg` and PROJ's modified stereographics, `alsk`, `gs48`, `gs50`, `lee_os` and
`mil_os`. Their domain is their published region, as a lat/lon box or a cap. A lat/lon
box is still four planes: two parallels and two meridian half-planes.

A national grid, such as the British National Grid, is a transverse Mercator or a conic
with a published area of use, and its domain is that area of use, as a lat/lon box
(§4.8).

Each PROJ method maps to one class and to the parameters that set its domain, read from
the CRS: `lat_0` and `lon_0` for a cap, `lon_0`, `lat_0` and `alpha` or `lonc` for a band,
`o_lat_p` and `o_lon_p` for an oblique frame, `h` for a perspective horizon. The registry
of methods is `geovista`'s own knowledge, written once per class and parameterised per
method. The interruptions of `igh` and `igh_o`, and the faces of `spilhaus`, are tables
taken from PROJ's implementation of each.

A method that the registry does not hold raises an error that names the method and says
its domain is not yet supported, rather than rendering something torn. Until its class
lands, though, a method of classes 1 to 6 keeps today's path, as decision 12 of
§2 requires. The 91 methods of
§3.2 enter the registry as class 0, each verified by the coverage
test of §6.

Each domain has defaults and overrides (§5). A domain's limits are
angles on the globe, never distances in projected units.

(crs-spec-4-4)=
### 4.4 The CRS Interface

There are three ways in, and one engine underneath.

1. **`geovista` CRS classes**, in `geovista.crs`, mirror `cartopy`'s class names and
   keywords where `cartopy` has the class, so a scientist moves across by changing an
   import: `NorthPolarStereo(central_longitude=0)`,
   `Mercator(min_latitude=-80, max_latitude=84)`, `LambertConformal(cutoff=-30)`.
   Projections that `cartopy` lacks get classes named in the same style, such as
   `WinkelTripel` and `NaturalEarth`. A class is thin: a PROJ definition, which stays the
   single source of projection mathematics, together with its domain and the overrides
   that domain takes.
2. **A PROJ string or a `pyproj.CRS`**, for power users, as today. Domain options that
   PROJ cannot express, such as the cap of a stereographic view, are given alongside the
   CRS. Otherwise the registry's defaults apply.
3. **A `cartopy` CRS object**, accepted as it is today. Its domain settings that have a
   meaning on the globe are read without importing `cartopy`. `LambertConformal` keeps
   its `cutoff` as an attribute. `Mercator` keeps only its limits in projected metres, so
   its `min_latitude` and `max_latitude` are recovered by inverting its y-limits through
   PROJ, which is exact: `Mercator(min_latitude=-60, max_latitude=70)` gives back −60°
   and 70°. That is the one translation from projected units. Other limits in projected
   units are not translated.

The names of the domain options and of the classes for projections that `cartopy` lacks
are left to the builder, provided each class's options match `cartopy`'s where `cartopy`
has them.

(crs-spec-4-5)=
### 4.5 Cut Once, Map Many

The geometry of a projected scene depends on the mesh's geometry, the CRS, the datum
operation, the domain and the globe model, and not on the mesh's values. So the work is
done once and recorded as a mapping:

- for each output cell and point, the index of its source;
- for each new point that an exact cut makes, its source points and interpolation
  weights;
- for each point of a vector field, the local linear map, the Jacobian of the
  projection, that takes a vector from the geographic frame to the projected one. A
  rotation would be right only for a conformal projection, and would quietly misdirect
  the vectors of Robinson or Mollweide. Projecting vector fields is parity work
  (§9); the mapping has room for it.

The mapping is cached against a key made of everything the geometry depends on, so a
change to any of them recomputes it and nothing goes stale. Each frame of a time series
then carries its values through the mapping with NumPy indexing, weights and linear
maps, and no VTK geometry work, and `GeoPlotter` updates the arrays of the mesh it already
renders, in place. When a mesh's geometry does change between frames, the cache misses
and the full path runs, which is correct but slower.

The mapping is also the record of what was kept, cut and removed, which
§4.6 relies on.

(crs-spec-4-6)=
### 4.6 Accounting for Every Cell

Every operation reports what it did, and nothing is removed in silence:

- a result records the CRS, datum operation and domain it was projected with, and whether
  it was refined for display. A domain always cuts exactly. The edge modes of the regions
  design (§9) join the record, and the key of
  §4.5, when it lands;
- anything removed is counted, and the removed part can be recovered from the mapping;
- a removal that the chosen CRS implies, such as the far hemisphere of an orthographic
  view or the poles of a Mercator one, is recorded but not warned about, since a warning
  on every such plot would be noise;
- every other removal is warned about, such as a point that the datum operation cannot
  take (§4.8), or a result that is not finite;
- a caller may turn a warning into an error, or acknowledge it, but only explicitly.

The form of the record, as field data on the mesh, a Python object beside it, or both, is
left to the builder.

A data mesh is never refined by default, so every vertex of a projected mesh is a source
vertex, apart from the points an exact cut adds on its cut edges. Display refinement is
an explicit opt-in. It subdivides a mesh's cells so that coarse cells follow the curves
of a strongly curved projection. Each sub-cell carries its source cell's id, cell data is
copied, point data is interpolated only when that is asked for too, and the result records
both. Area weights for statistics never need refinement, since they can be computed
exactly from each cell's spherical polygon.

(crs-spec-4-7)=
### 4.7 Lines, Points and the Built-In Layers

Coastlines, the graticule, the base layer and every other built-in layer go through the
same engine and take the scene's globe model. Lines are clipped to the domain and cut at
its seams at their exact crossings, and densified as §4.2
describes. Points are kept or removed, with the same account as cells. The base layer's
texture coordinates come from each vertex's longitude and latitude in the natural frame,
so that `raster.wrap_texture` no longer depends on a scalar central meridian. The
graticule is generated on the sphere and clipped to the domain, and its labels sit inside
it. Placing labels along a domain's edge, as `cartopy` can, is part of the parity work of
§9.

(crs-spec-4-8)=
### 4.8 Datums

The engine works on the sphere in the geographic frame of the target CRS's own datum. A
mesh's vertices go from their source CRS to the target's base geographic CRS by a single
datum operation for the whole scene, chosen by the policy below. The domain and its seams
are then cut in that frame, and the map projection alone is applied last, so a seam lands
where the projection puts its discontinuity, to the last digit. The operation is recorded
with the result (§4.6) and is part of the cache key
(§4.5).

On the sphere a longitude is always east of Greenwich, and every angle is in the engine's
canonical angular unit (§4.9), whatever the base geographic CRS
measures in. Not every one measures in degrees from Greenwich. NTF (Paris), the base of
Lambert zone II, EPSG:27572, measures in grads east of Paris, so its coordinates are
converted as they reach the sphere, and converted back for the projection. Measured on
2026-10-24, reading them as degrees from Greenwich put a mesh projected to EPSG:27572
17.8 km out ({pull}`2718`).

PROJ is never left to choose an operation point by point. Measured on 2026-10-23, WGS84 to
the British National Grid, EPSG:27700, at 52°N moves a point 129 m east of where the
projection alone would put it up to 2.0°E, and not at all from 2.125°E. There the best
operation's area of use ends and PROJ falls back to a ballpark operation with no shift.
That is a quiet 129 m step inside the domain of a UK model. `geovista` had it too
({issue}`2714`), until {pull}`2718` applied items 2 and 3 of the policy below to each call
of `transform_points`, over the points of that call, as there is no scene or domain to
take an extent from yet. A point the chosen operation cannot take is counted and
reported, never given a different operation.

The operation is chosen by one policy:

1. **The extent is the data's.** It is the extent of the scene's data meshes, after the
   domain has clipped them. The built-in layers, such as coastlines, do not widen it.
2. **The most accurate available operation that covers it.** Of the operations whose
   area of use covers the extent, the most accurate available one is chosen, and applied
   to every point. An operation that needs a grid is available only where the grid is
   installed. One that is not available is passed over without a warning, as PROJ passes
   it over, and the record says so (item 5).
3. **Coverage before accuracy, and never a mix.** Where no operation's area of use covers
   the extent, the most accurate operation that can transform every point of it is
   chosen instead, with a warning that the extent exceeds its area of use. PROJ's
   ballpark operation, which applies no datum shift, is chosen only when no other
   operation exists.
4. **A national grid's domain is its area of use.** The domain of a national grid is the
   area of use of its EPSG definition (§4.3). Anything outside it is
   a removal the CRS implies (§4.6), and what remains is covered by
   the grid's own operations.
5. **The record explains the choice.** It names the operation, its accuracy and any grid
   it used, and any more accurate operation it passed over for a missing grid. PROJ may
   fetch grids over the network on demand, while `pyproj`'s wheels ship none and leave
   the network off, so the same code can choose differently on two machines, and the
   record is what explains the difference. `geovista` leaves PROJ's network setting to
   the user.

Measured for EPSG:27700 on 2026-10-23, PROJ offers nine operations from WGS84. The most
accurate, at 1 m, is grid-based, and its area of use is exactly the area of use of
EPSG:27700, from 9.01°W to 2.01°E and from 49.75°N to 61.01°N. It raises beyond its grid,
at 2.125°E for instance. Seven parametric operations, accurate to between 2 m and 35 m,
transform any point, though each one's area of use lies within the UK. The ninth is the
ballpark operation, which PROJ's choice point by point falls back to east of 2°E. Under
the policy, a scene on the British National Grid is clipped to the area of use, and every
point that remains takes the 1 m operation. Where its grid is not installed, as with
`pyproj`'s wheels, the most accurate available operation is accurate to 2 m. Its area of
use ends at 1.92°E and 60.94°N, inside that of EPSG:27700, so a scene that reaches past
it takes the 2 m operation with the warning of item 3.

(crs-spec-4-9)=
### 4.9 Units

> **Extended by a child specification.** [`2026-10-26-globe-heights-layers-design.md`](2026-10-26-globe-heights-layers-design.md) settles how `geovista.units` reads each
> form (globe spec §4.2), and adds heights and depths to the
> quantities with a unit.

Every physical quantity that crosses the API boundary has a unit. In the foundation these
are the globe's radius (§4.1), the densification tolerance, a
length or an angle (§4.2), and the angles of domain options, such
as a cap's radius or a band's half-width (§4.3). Heights and
depths join them in project 4 (§9).

A function takes each such quantity in one of three forms:

1. a plain number, in the unit its docstring documents, such as degrees for an angle and
   metres for a length;
2. a `pint` quantity, from any registry, read by its magnitude and unit, so that a
   quantity from MetPy's or `pint-xarray`'s registry is accepted as readily as one from
   `geovista`'s own;
3. where a function reads units from data, a CF unit string, parsed by `pint-cf`.

Each is converted once, at the boundary, to SI for lengths and to one canonical unit for
angles. Inside, the engine works on plain floats and NumPy arrays, so units add nothing
to the per-frame cost of §4.5. A physical length that a result or
record reports, such as the radius it was projected at, carries its unit.

Units for data values, such as a temperature or a concentration, stay with the data.
`geovista` reads them only to label a scalar bar.

(crs-spec-5)=
## 5. Defaults, and Where cartopy Departs From PROJ

Defaults follow `cartopy`, so existing plots look the same, except where a default smells.
Each departure below was measured on 2026-10-23 against `cartopy` 0.26 and PROJ 9.9, and
carries a verdict.

| Departure | Measured | Verdict |
|---|---|---|
| A forced sphere of radius 6,378,137 m for 14 classes, including `Orthographic`, `Miller`, `Gnomonic` and `NearsidePerspective` | no difference for sphere-only methods such as `robin`; `Orthographic` moves 7.6 km east and 22.7 km north at 90°E 45°N against PROJ's ellipsoidal `ortho`, and `Miller` 11.2 km and 6.0 km | **Open** (§8, item 1): it dates from PROJ's spherical-only `ortho` before 7.2 |
| Domains as rectangles or ellipses in projected metres | `NorthPolarStereo`'s ±5×10⁷ m reaches 61.4°S; `Gnomonic`'s reaches 82.7° from its centre; `TransverseMercator`'s ±2×10⁷ m by ±1×10⁷ m includes the near-singular regions; `ObliqueMercator` reuses `Mercator`'s latitude-limit extents | **Challenged**: limits are angles on the globe, with defaults per class (§8, item 2) |
| Regional defaults: `Mercator` from −80° to 84°, and `LambertConformal` centred on the contiguous United States (−96°, 39°, parallels 33° and 45°) with a cutoff at −30° | as stated | **Inherited**, for familiarity, with the reason for each documented on its class |
| Degree-like units, `to_meter=111319.49`, for `LambertCylindrical` and `RotatedPole` | as stated | **Inherited** for `RotatedPole`, whose users think in rotated degrees; **challenged** for `LambertCylindrical`, which takes PROJ's metres |
| Hand-written national grids: `OSNI` mixes the WGS84 ellipsoid with modified Airy axes and carries no datum, where `OSGB` carries its datum | as stated | **Challenged**: national grids are built from their EPSG definitions |
| A densification threshold in each projection's own units, from 0.5° for `PlateCarree` to 100 km for the polar stereographics | as stated | **Replaced** by densification on the sphere (§4.2) |

`cartopy`'s globe default is the WGS84 ellipsoid, where PROJ's is GRS80. The two differ by
a fraction of a millimetre in the semi-minor axis, and the verdict is to inherit WGS84.

(crs-spec-6)=
## 6. Testing

Every geometric result is checked against a reference that is independent of
`geovista`, never against its own earlier output:

- **PROJ itself**, for the projected coordinates of every vertex that a domain keeps;
- **exact formulae**, where they exist, such as the area of a cap, 2πR²(1 − cos θ), the
  latitude of a clipped boundary, and the angular radius of a perspective horizon;
- **the seam**, tested per class: no cell spans more than half the projection, and no edge
  is more than ten times the median of the edges between the same two latitudes, which
  are the metrics of §3.1. A seam that bisects cells leaves polar
  triangles up to 0.31 of the projection wide, for a Greenwich CRS too, so half is the
  threshold;
- **the radius**, by running each class at a radius of 1 and at the Earth's radius, and
  comparing;
- **limits that are not planes**, such as an ellipsoidal horizon, against the exact
  predicate, so that no kept vertex raises in PROJ and no vertex PROJ can project is
  removed;
- **the datum**, by checking that a mesh crossing the edge of an operation's area of use,
  such as a UK model across 2°E on the British National Grid, has no step: either one
  operation takes every point it keeps, or the domain removes, and records, what that
  operation cannot take.

A **coverage test** records the outcome of every PROJ method and every `cartopy` class on
a global mesh, measured as §3.1 describes, and only lets the set
that works grow. A method claimed as supported must work, and one that is not supported
must raise the error of §4.3. Like the typing ratchet of
typing spec §4, it makes coverage visible and stops it shrinking
by accident.

**Image tests**, one or more per class, cover the scenes scientists asked for: Arctic sea
ice in a polar stereographic cap, a UK model on the British National Grid with coastlines,
an orthographic globe, a rotated pole regional model, interrupted Goode Homolosine and
Spilhaus.

**Early adopters** at the Met Office, from the disciplines that asked for each feature,
sign it off against data they already understand. That is the human half of never being
quietly wrong.

(crs-spec-7)=
## 7. Alternatives Considered

- **Build on `cartopy`.** Rejected. Its domains are boundaries in projected space, applied
  with planar geometry through `shapely`, and that is the approach this design replaces.
  It also cannot take an arbitrary PROJ string, where `geovista` already can.
- **Clip in projected space.** Rejected, for the discontinuities, wrapping and seam
  coincidences that globe first avoids.
- **A lenient fallback by default**, projecting with PROJ's checks off and dropping what
  fails. Rejected, because it drops data silently and leaves jagged edges. It made 28 of
  the 70 methods failing in the first measurement render (§3.2), and
  might return later as an explicit, loud opt-in.
- **PROJ strings only.** Rejected, because `cartopy`'s classes are scientists' muscle
  memory, and forcing PROJ strings on them would be alien.
- **Commit to every PROJ method.** Rejected, because verification is the real cost, and
  each interrupted or polyhedral layout needs its own seam table and verification.
- **Refine data meshes by default.** Rejected, because it invents vertices, interpolates
  values nobody measured, and breaks the one-to-one mapping between output and model
  cells.
- **Extend `MeridianSlice` and `remesh`.** Rejected, because they are meridian-specific
  throughout: they cut with a vertical plane rotated about the polar axis, and tell east
  from west by longitude.
- **Manifold for the domain cuts.** Rejected for the foundation, because its booleans need
  closed solids. It is kept for the region solids of project 4.
- **`cf-units` for units.** Rejected, because it builds on the UDUNITS-2 C library, which
  pip cannot install. `pint-cf` reads the same CF unit strings with `pint`.
- **Plain numbers in documented units, as today.** Rejected, because the defects this
  design starts from cluster around implicit units: a radius of 1 with no unit, a
  `zlevel` scaled by `zscale` in place of a height, feet converted by hand, and the
  grad-based prime meridians of {issue}`2518`.

(crs-spec-8)=
## 8. Open Items

Each carries the status grammar of docs spec §3.6.

1. **Open** — **Inherit or challenge `cartopy`'s forced sphere?** Following PROJ's
   ellipsoidal `ortho` is more faithful, but moves an orthographic view by up to tens of
   kilometres against `cartopy`. The same question applies to the other 13 classes,
   though for sphere-only methods it changes nothing.
2. **Open** — **The default domain of each class.** Settled so far: `Mercator`'s −80° and
   84°, and `LambertConformal`'s cutoff at −30°. Still to settle are the default cap of a
   polar stereographic and a gnomonic view, and the default band of a transverse
   Mercator. A transverse Mercator band is a full ring around the globe, so its default
   presumably takes only the half of the ring on the central meridian's side, from pole to
   pole, and its half-width is open. A national grid takes the area of use of its EPSG
   definition (§4.8).
3. **Open** — **Physical or normalised render units.** Rendering at the Earth's radius in
   metres makes every coordinate physical, but VTK's precision and cameras at that scale
   need checking against rendering at a normalised radius of 1.
4. **Open** — **The form and names of the domain options and of the record**
   (§4.4 and §4.6), to be settled with an
   early adopter's code in hand.
5. **Open** — **An escape hatch for unsupported methods, once today's path is gone.**
   Whether a power user may then project to a method the registry does not hold, at their
   own risk and with a loud warning, or whether the error is final.
6. **Open** — **The angle a seam point moves into its own side.** It must exceed PROJ's
   tolerance for wrapping a longitude, and needs measuring per class.
7. **Open** — **Upstream.** Whether to ask PROJ to expose each method's valid domain, which
   would let `geovista`'s registry check itself against PROJ.
8. **Open** — **Spilhaus's faces**, which must be derived from PROJ's implementation, and
   verified against it.
9. **Open** — **The `pyvista` floor of 0.49**, which needs confirming against the clipping
   paths the engine uses, and the pins of `requirements/`.
10. **Open** — **The fate of `geodesic.BBox` and `GeoPlotter(manifold=...)`.** The regions
    design of project 3 replaces them. Until it lands, they keep working on top of the
    engine.
11. **Resolved** (2026-10-26, {pull}`2732`) — **`pint-cf`'s maturity.** It is at 0.2.1.
    Whether `geovista` depends on it as it stands, contributes to it, or keeps the CF
    strings it needs behind a small adapter of its own until it matures. It depends on
    `pint-cf` as it stands, on PyPI and conda-forge, behind `geovista.units`, so replacing
    it would touch one module (globe spec §4.2).

(crs-spec-9)=
## 9. Scope

In scope is the foundation: the globe model and units, the cutting engine, the domains of
all six classes with the coverage of §2 decision 10, datums, the CRS
interface, cut once map many, the accounting of every cell, and the built-in layers on
top of them.

Out of scope, each as a design of its own, in this order:

1. **Regions for users.** Caps, latitude and meridian bands, lat/lon boxes, polygons and
   shapefiles, with an edge type (great circle, small circle, or straight in a named CRS)
   and an edge mode: cut exactly, whole cells inside, centre inside, or touching. Region
   sets, including one region per cell of a cubed-sphere panel ({issue}`1532`), and area
   weights for statistics ({issue}`59`). It builds on the clip, seam and densify
   primitives and on the accounting.
2. **Region solids and the vertical.** A floor and a ceiling, volume meshes, and plumes,
   with Manifold through `pyvista-manifold`, and with gmsh through `scikit-gmsh` for
   tessellation and layered volumes as an optional extra, since both are GPLv3 where
   `geovista` is BSD-3. Vertical datums other than mean sea level, and the work of
   {issue}`15`, {pull}`2294`, {issue}`1029` and `bjlittle/geovista-jav-2026`. Heights in
   physical units, and the replacement of `zlevel`, came forward into
   globe spec §4. It builds on the globe model.
3. **Features without `cartopy`.** A Natural Earth reader for coastlines, borders, rivers,
   land and ocean, after which `cartopy` is dropped. It builds on densification.
4. **The rest of `cartopy` parity**: gridline labels along a domain's edge, web map tiles,
   streamlines ({issue}`675`), point labels ({issue}`1189`), the day and night terminator,
   and geodesic circles and annotation.

Also out of scope, and recorded here so they are not forgotten: a "globe" CRS other than
EPSG:4326, so that `OGC:CRS84` or another body renders as a globe; a geocentric target
such as EPSG:4978; and the true shape of the ellipsoid.

The CRS work of this design closes {issue}`140`, {issue}`1402`, {issue}`2674` and
{issue}`2519`.

(crs-spec-10)=
## 10. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | The coverage test of §6, recording today's outcomes | ✅ landed (2026-10-26, {pull}`2721`) |
| 2 | The globe model, units, heights and layers, by rows 1 to 5 of globe spec §9 | not started |
| 3 | The cutting engine: rotate, clip, cut a seam, densify, with the account of each | not started |
| 4 | The domain registry, and class 0 on the engine, replacing today's seam and transform path with no change to the 91 methods that work | not started |
| 5 | The CRS interface: `geovista` classes, domain options, and `cartopy` objects read without importing it | not started |
| 6 | Class 1, latitude limits | not started ({issue}`140`) |
| 7 | Class 2, caps | not started ({issue}`1402`) |
| 8 | Class 3, bands | not started ({issue}`2674`) |
| 9 | Class 4, oblique aspects | not started ({issue}`2519`) |
| 10 | Class 5, interrupted Goode Homolosine, both emphases | not started |
| 11 | Class 6, Spilhaus | not started |
| 12 | Cut once, map many | not started |
| 13 | Display refinement, as an explicit opt-in | not started |

Statuses follow docs spec §3.6. Rows 1 to 4 come first and in
order, since everything else stands on them. From row 4, a method whose class has not
landed keeps today's path, and the last class row deletes that path. Rows 5 to 13 may
then proceed in any order that suits the early adopters, and each lands with its tests,
its image baselines and a towncrier fragment. Each breaking change carries a `breaking`
fragment.

(crs-spec-11)=
## 11. References

- {issue}`140`, {issue}`1402`, {issue}`2674` and {issue}`2519`, the four CRS issues this
  design closes
- {issue}`2714`, the datum step that the review of this design found, and {pull}`2718`,
  whose review found the missing grids of `pyproj`'s wheels and the grads of NTF (Paris)
- {issue}`15`, {issue}`59`, {issue}`229`, {issue}`377`, {issue}`843`, {issue}`1029`,
  {issue}`1532`, {issue}`1869` and {issue}`1986`, which shaped it
- {pull}`2294`, the draft that maps depth onto the radius, and {pull}`2689`, whose review
  found the cost of a seam a few digits out
- PROJ's projection list, from `proj -lP`, and its operations:
  <https://proj.org/en/stable/operations/projections/index.html>
- `cartopy` 0.26's `crs.py`, for its defaults, its forced spheres and its domains:
  <https://github.com/SciTools/cartopy/blob/main/lib/cartopy/crs.py>
- `pyvista` 0.49's release notes, for its faster mesh processing:
  <https://github.com/pyvista/pyvista/releases/tag/v0.49.0>
- `pyvista-manifold`, which wraps Manifold's booleans on closed solids:
  <https://github.com/pyvista/pyvista-manifold>
- `scikit-gmsh`, which wraps gmsh, both GPLv3: <https://github.com/pyvista/scikit-gmsh>
- `pint`: <https://github.com/hgrecco/pint>, and `pint-cf`, its CF-compliant registry:
  <https://github.com/pgamez/pint-cf>
