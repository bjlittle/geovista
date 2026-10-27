# geovista Globe, Heights and Layers — Design Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. It states how `geovista` places data at a height, and how it keeps one layer
> of a scene from hiding another, and where the two ever diverge it is the specification
> that gets corrected. Read it as current; the roadmap states what has actually landed.

- **Date:** 2026-10-26 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `globe spec §…`
- **Scope:** the globe model of a scene, units, heights and depths in physical units, the
  vertical mapping, and the layering of surfaces and lines, which together replace
  `zlevel` and `zscale`
- **Parent spec:** the globe-first CRS design
  ([`2026-10-23-globe-first-crs-design.md`](2026-10-23-globe-first-crs-design.md)). This
  extends crs spec §4.1 and crs spec §4.9,
  and brings forward from crs spec §9 the heights in physical units
  and the replacement of `zlevel` that it gave to the design of region solids and the
  vertical. It inherits that specification's decisions (crs spec §2)
  and testing (crs spec §6) unchanged
- **Sibling spec:** the planar z-levels design
  ([`2026-10-08-planar-zlevel-design.md`](2026-10-08-planar-zlevel-design.md)), whose rule
  this specification replaces when row 5 of §9 lands
- **Prior art:** the vertical coordinates of the CF conventions, and the vertical CRSs of
  EPSG and PROJ; VTK's resolution of coincident topology, which is OpenGL's polygon offset
- **Published:** in the specifications index

(globe-spec-1)=
## 1. Purpose

A `zlevel` does two jobs that pull against each other. It lifts a surface off the textured
base layer so the two do not fight on screen, and it lifts coastlines so they are not buried
in the surface. It is also the only way to give anything a height, so a plume, a cloud
layer or an ocean depth goes through the same number, scaled by a `zscale` that has no unit.
{user}`bjlittle` introduced both to get layered surfaces to render, and calls the result a
hack at best.

That was a fair first step, and this is the time to replace it. Scientists using
`geovista` now look at volumes with real vertical extent, such as the volcanic ash and
sulphur dioxide plumes of `bjlittle/geovista-jav-2026`. They need to warp a surface by its
terrain, place a cloud or a plume at its true height above that terrain, exaggerate the
vertical so the structure can be seen, and show the viewer a vertical scale that tells the
truth about that exaggeration. None of that can be done rigorously while a height is a
fraction of whatever radius a mesh happens to have.

This specification separates the two jobs. A height becomes data in metres. Layering
becomes a matter of display, owned by the scene, and never moves data.

(globe-spec-2)=
## 2. Decisions

These were decided with {user}`bjlittle` while the design was written.

1. **Height and layering are separate concerns, and never mixed.** A height is physics. A
   layer's order is display. Nothing done to stop two layers fighting may move data, or
   reach a projected coordinate.
2. **This work comes forward.** The parent specification gave heights in physical units,
   and what replaces `zlevel`, to the later design of region solids and the vertical. They
   are core, and are designed here, as row 2 of the parent's roadmap. Volumes, plumes as
   solids, and a floor and ceiling stay with that later design.
3. **Heights and depths arrive computed.** Turning model levels into heights, as from the
   hybrid height of the Unified Model and LFRic and the orography beneath it, is done
   upstream, by Iris or `xarray`. `geovista` owns the reference, the units and the
   rendering. It may offer the conversion later, once this design has matured.
4. **One globe per scene.** A scene has one Earth radius, one render scale and one vertical
   mapping, at first an exaggeration above sea level and another below it (§4.1), and every
   layer takes its geometry from them, as
   crs spec §4.1 requires.
5. **`zlevel` and `zscale` are removed.** It is a breaking change, which
   crs spec §2 decision 4 allows. Physical stacking becomes heights, display
   stacking becomes the order of layers, and a layer that must be seen apart is lifted
   (§4.5).
6. **The evidence travels with the design.** The measurements that shaped it, the layering
   spike above all, are recorded here with their method, environment and date, so that a
   later reader can see why the design took the form it did, and repeat the measurement.

(globe-spec-3)=
## 3. What Exists Today

(globe-spec-3-1)=
### 3.1 Three Jobs in One Number

Across the package, `zlevel` and `zscale` and the constants behind them appear in some 500
lines, and in 11 of the gallery's examples, which use them in three different ways:

- **Stacking order.** The cloud examples place layer `i` at `(i + 1) * ZLEVEL_FACTOR`, and
  the H3 example stacks its layers at levels 60, 10, 5 and 1. These are not heights.
- **Keeping layers apart.** On the globe the base layer sits at `zlevel=-1` with
  `BASE_ZLEVEL_SCALE` of 10⁻³, a data surface at 0, and coastlines at 1 with `ZLEVEL_SCALE`
  of 10⁻⁴. Several examples say so, as "force zlevel alignment of coastlines and base
  layer".
- **A real depth squeezed in.** The ORCA2 point cloud example passes its depths in metres
  as a negative `zlevel`, with a `zscale` of its own.

(globe-spec-3-2)=
### 3.2 One Level, Two Heights

Measured on 2026-10-26 at `7ca628c1`, a mesh of radius 6,371,000 with `zlevel=10`, on the
globe and in Robinson:

| | data mesh | coastlines | the same mesh at `zlevel=10` |
|---|---|---|---|
| globe | radius 6,371,000 | radius 1.0001, inside the mesh | 6,371 m above it |
| Robinson | z = 0 | z = 1,913 m | z = 6,378 m |

On the globe a level is a fraction of the mesh's own radius; in a projection it is a
fraction of the WGS84 semi-major axis (zlevel spec §3.1). So the
same level is two different heights, and the coastlines' display offset becomes a rise of
1.9 km on the map, while on the globe they stay at radius 1, hidden inside an Earth-sized
mesh.

(globe-spec-3-3)=
### 3.3 Physics Rebuilt by Hand

The two applications of `bjlittle/geovista-jav-2026` each rebuild the vertical for
themselves:

- **Reykjanes** divides each altitude by its own Earth radius of 6,371,000 m, where
  `geovista` projects with 6,378,137 m, and derives a `zscale` from the ratio of its
  horizontal and vertical cell sizes. It then prints "Vertical Scale Factor: x…" on the
  screen as text.
- **Raikoke** does the same in feet, with an Earth radius in feet and its own unit
  conversions. Its flight levels are pressure altitudes in hundreds of feet, which it treats
  as geometric heights. To report the height of a picked cell it counts the cell's index in
  the grid, because the geometry no longer carries the height.

(globe-spec-3-4)=
### 3.4 Vertical Coordinates in the Wild

The samples that `geovista.pantry` serves, and those of `bjlittle/geovista-jav-2026`:

| source | vertical coordinate | what it is |
|---|---|---|
| NAME, Reykjanes | `altitude`, m, `positive: up` | above mean sea level |
| NEMO, ORCA2 | `deptht`, m, `positive: down`, labelled `model_level_number` | model levels at known depths below the sea surface |
| LFRic orography | `surface_altitude`, m | the terrain itself |
| LFRic winds | `full_levels` and `half_levels`, bare | model levels, with no heights in the file |
| QVA, Raikoke | `flight_level` | pressure altitude in hundreds of feet |

Earth science measures height from several zeros. The usual one for model output is mean
sea level, which is strictly the geoid: CF's `altitude`, and EPSG's gravity-related
heights such as EGM96 height (EPSG:5773) and Ordnance Datum Newlyn (EPSG:5701). Satellite
and GNSS data measure from the ellipsoid instead, as EPSG:4979 does, and the two differ by
the geoid's undulation, from about −106 m to +85 m. Height above the ground, depth below
the surface, and pressure are zeros of their own. A CRS can carry its vertical datum,
through a vertical, compound or 3D geographic CRS, and CF names it through standard names.

PROJ converts an ellipsoidal height to an EGM96 height with the grid
`us_nga_egm96_15.tif`, to 1 m. Without the grid it falls back to a ballpark operation that
applies no correction, the same quiet trap that {issue}`2714` found for horizontal datums.

The Unified Model and LFRic, whose output `geovista` mostly shows, take sea level as the
surface of their own spherical Earth, of radius 6,371,229 m, as `geovista` takes the surface
of its sphere.

(globe-spec-3-5)=
### 3.5 Measured: Layers on the Globe and on the Map

A throwaway spike measured, pixel by pixel, how each way of layering keeps a data surface
above the base layer, and coastlines above both.

**Method.** Measured on 2026-10-26 at `92142211`, with VTK 9.7.0, `pyvista` 0.49.1 and
Mesa 26.2.5, on two renderers: an NVIDIA GeForce RTX 4060 Laptop GPU through D3D12 in WSLg,
and llvmpipe (LLVM 23.1.3). The base layer was the C96 cubed sphere that `add_base_layer`
builds, in flat red; the data surface flat blue, as the C48 LFRic sample, a 1° grid and a
5° grid; the 10m coastlines flat green, two pixels wide. Lighting was off, at 800 × 800.
Bleed is the share of the surface's pixels where red shows. Coastline visibility counts
the green pixels within two of an ideal, where the lines are hidden only by a sphere 0.1%
smaller, and leak counts green outside it. The globe was seen whole, from 20 radii, close
over the United Kingdom, at a grazing angle to the limb, and from twelve points of an
orbit; the Robinson map flat, zoomed and tilted. Every case ran at radius 1 and at
6,378,137.

**Why the globe differs from the map.** On the map every layer lies in one plane, so the
layers truly coincide. On the globe they do not: each mesh is flat between its vertices,
so the middle of each cell sits below the sphere its vertices lie on. That sag grows with
the square of a cell's size:

| mesh | sag of a cell's centre, as a fraction of the radius | at 6,378,137 m |
|---|---|---|
| C96 | 6.7 × 10⁻⁵ | 427 m |
| 1° grid | 7.6 × 10⁻⁵ | 486 m |
| C48 | 2.7 × 10⁻⁴ | 1,707 m |
| 5° grid | 1.9 × 10⁻³ | 12,124 m |
| 10m coastlines, per segment | 9.3 × 10⁻⁶ | 60 m |

A finer base layer is closer to the sphere, so it pokes up through the middle of each cell
of a coarser surface laid over it, as {user}`bjlittle` had seen in practice. Today's offset
of 10⁻³ covers C48, and fails for anything coarser. C48 is about the coarsest LFRic mesh
seen in practice, but rectilinear grids and meshes users build can be coarser still.

**Results**, as the worst case over every view, bleed and coastline visibility, on the GPU,
with llvmpipe within a few points throughout:

| layering | C48 | 1° grid | 5° grid | Robinson, all three |
|---|---|---|---|---|
| today's offsets | 0% / 76% | 0% / 63% | 65% / 75% | ≤ 0.3% / 88% |
| none, every layer at one radius | 100% / 45% | 80% / 44% | 100% / 36% | ≤ 52% / 82% |
| depth bias, 1024 units | 0.08% / 82% | 0% / 83% | 0.77% / 69% | ≤ 0.3% / 100% |
| the hybrid | 0.003% / 84% | not run | 0% / 74% | not run |

- **Today's offsets** fail the 5° grid in every view, with the base layer showing through 29
  to 65% of it.
- **Depth bias**, VTK's polygon offset in its constant form, clears every close and orbiting
  view. On the map, at 64 units or more, it shows every coastline, and its bleed of 0.3% for
  C48 is that of every layering, today's included, so is not the layers fighting. On the
  globe it leaves a sliver at the grazing limb for a coarse mesh, which a stronger bias does
  not remove.
- **Its slope-scaled form** does not move that sliver, and buries the coastlines, which fall
  to between 5% and 40% visible.
- **VTK's z-buffer shift** is no better than no layering at all.
- **The hybrid** lowers the base layer by 1.1 times the measured sag of the coarsest
  surface above it, in render units, and gives the lines a depth bias of 4 units. It shows
  no bleed in any view, the limb included, on both renderers. A bias of 256 on the lines
  alone, with the surface no longer pulled forward too, leaked up to 11,000 pixels of the
  far side's coastlines over the horizon; 0 to 4 units leaked at most 2.
- **The radius makes no difference.** Every case measured the same at radius 1 and at
  6,378,137, which is evidence for crs spec §8 item 3.

Coastline visibility reached 100% in the close and orbiting views for both depth bias and
the hybrid. The shortfall in the table is at the limb, where the ideal over-counts: its
smaller occluding sphere uncovers lines just beyond the true horizon.

**Two things to know about the measurement.** Its first run modelled today's base layer
at 10⁻⁴ below the data rather than 10⁻³, and so showed today failing C48 as well. The
error was caught against `GeoPlotter` itself before any conclusion was drawn, and every
figure above is from the corrected run. And WSL's D3D12 driver aborts after some 300
plotters in one process, so each block of the measurement ran in a process of its own.

(globe-spec-3-6)=
### 3.6 The Gallery's Vertical

Measured on 2026-10-27 at `a0f95dbe`. Of the gallery's 48 examples, 30 have no vertical at
all. Each of the rest meets it in a way of its own, at the Earth's radius of 6,378,137 m:

| example | today | in this design |
|---|---|---|
| `warp/from_unstructured__lfric_orog` | warps along point normals by 2 × 10⁻⁵ per metre, an exaggeration of 127.6, chosen by hand | heights, with an exaggeration it states |
| `warp/from_unstructured__lfric_orog_eqc` | warps a Plate Carrée map by 200 per metre, an exaggeration of 200 | the same heights and exaggeration as on the globe |
| `warp/from_unstructured__fvcom` | warps by "Sea Floor Depth Below Geoid", positive downward, from −6.6 to 80.3 m, and is right only because its cells are wound so that its normals point inward | `depth=` and the factor below sea level, whatever the winding |
| `scalar_data/from_tiff__dem` | warps Mount Fuji by 2 × 10⁻⁷ per metre, an exaggeration of 1.28 | heights |
| `point_cloud/from_points__orca_cloud`, and its `_eqc` | places ocean depths of 0.5 to 5,275 m at negative levels scaled by 10⁻⁵, an exaggeration of 63.8 | `depth=` and the factor below sea level |
| `grid/reykjanes`, and its `_contour` | `to_structured_grid` keeps only the number of its 41 levels, which run from 0 to 10,000 m, and spaces them half a grid cell apart, an unstated exaggeration of 22.3; uneven levels would be drawn evenly | heights, honoured as given |
| `clouds_stratify` | stacks low, medium, high and very high cloud evenly, 47.8 km apart | a height for each band, or a lift |
| `domain/clouds`, and its `_robin` | floats one cloud layer 47.8 km up | a height, or a lift |
| `spatial_index/uber_h3` | floats H3 resolutions 0 to 3 at levels 60, 10, 5 and 1, from 38.3 km down to 0.6 km, an exploded view of a hierarchy with no altitude | a lift for each layer |
| `vector_data/wind_arrows_uvw` | lifts its arrows with `radius=1.1`, 638 km, and stretches their vertical component by 1,500 by hand | a lift, and the slope of the vertical mapping (§8 item 9) |
| `contour/banded_contour`, and the base layers set to a level of 0 | lifts lines over a surface by one level | the order, and the line bias of §4.5 |
| `curvilinear/from_2d__orca_moll` | extrudes a slab 1,000 km deep on a Mollweide map | a solid, left to the design of region solids (crs spec §9) |
| `README.md`, its seventh example | the same FVCOM warp, where a user looks first; nothing runs the README's 8 examples, and {issue}`782` found one broken in 2024 | `depth=`, run by the test of {issue}`2756` |

`to_structured_grid` carries {user}`bjlittle`'s TODO to "add richer vertical support", and
{user}`bjlittle` calls it a very poor proof of concept, and an example of why this design
work is being done. Every exaggeration in the gallery was chosen by hand, or by the code,
and none is recorded where a reader could find it.

(globe-spec-4)=
## 4. Design

(globe-spec-4-1)=
### 4.1 The Globe

> **Extended by a child specification.** [`2026-10-27-globe-scene-design.md`](2026-10-27-globe-scene-design.md), `scene spec §…`,
> specifies the `Globe` in place of every `radius`, the globe a mesh records, meshes that
> record none, and the retirement of fields `geovista` no longer writes. It inherits this
> document's decisions (§2) and testing (§6) unchanged.

A scene's globe holds three quantities, and nothing else in the scene holds them:

- **the radius**, the physical radius of the Earth, a length, by default the WGS84
  semi-major axis of 6,378,137 m, as crs spec §4.1 sets;
- **the render radius**, the radius the globe is drawn at, by default 1, so that a scene
  renders as it does today. The scale between the two is the render radius over the
  radius;
- **the vertical mapping**, which turns a height into how far above or below the surface
  it is drawn. In its first form it is two exaggerations, one for heights above sea level
  and one for depths below it, each by default 1, the true scale, since the vertical
  structure of an ocean and of an atmosphere above it differ by an order of magnitude. Any
  form of it always increases, so that anything higher is drawn higher, whatever its
  layer; is zero at sea level, so that the surface, the coastlines and the base layer never
  move; and is finite. Bands, and functions of height, are later forms (§8 item 8). The
  split is by height, not by what lies there: land below sea level, such as the Dead Sea
  at −430 m, takes the factor below, so with the two factors apart it is stretched as the
  ocean is. Order still holds, the two scales of §8 item 1 show it, and the
  documentation of the globe says so.

`GeoPlotter` takes a globe, and every layer it adds takes its radius from it, the base
layer, coastlines and graticule included. A globe is immutable. Changing the vertical
mapping of a scene replaces its globe, and the scene rebuilds every position from the heights its
layers carry (§4.4).

The render radius stays 1 by default. §3.5 found layering to behave
the same at the Earth's radius, which bears on crs spec §8 item 3, but
picking, the camera's clipping planes and interaction at that scale are not yet measured.

(globe-spec-4-2)=
### 4.2 Units

A length or an angle crosses the API boundary in one of three forms, as
crs spec §4.9 sets, and `geovista.units` converts each, once, to
metres or to degrees:

1. a plain number, in metres for a length and degrees for an angle;
2. a `pint` quantity, from any registry, read by its magnitude and the plain long form of
   its units, `format(quantity.units, "D")`. Measured with `pint-cf` 0.2.1, the short form
   of a nautical mile, `nmi`, reads as a nano international mile, so the short form is
   never used. Nor is `str(quantity.units)`, which follows the display format of the
   quantity's registry: a short format such as `"~"` gives `nmi`, and LaTeX gives markup
   that no registry reads ({pull}`2754`);
3. a magnitude with a CF unit string, such as `"km"` or `"degrees_north"`, parsed by the
   registry of `pint-cf`.

An angle must have angular units. `pint` counts an angle as dimensionless, so a
dimensionless quantity is refused as an angle rather than read as radians. Anything that is
not the dimension asked for, such as a pressure given as a height, is refused with its unit
named.

`geovista` depends on `pint` and on `pint-cf` as it stands, both on PyPI and conda-forge,
behind `geovista.units`, so that replacing `pint-cf` would touch one module. That answers
crs spec §8 item 11.

(globe-spec-4-3)=
### 4.3 Heights Are Data

A mesh carries the height of each point, in metres above mean sea level, as a point array.
A depth is a negative height, and may be given as a depth, positive downward, which is
negated once at the boundary. A mesh given no height is at sea level.

Heights are given where a mesh is built and where it is added to a scene: to the bridge's
`Transform` constructors and to `GeoPlotter.add_mesh` and `add_points`, as an array, a
scalar, or a length quantity, in any of the forms of §4.2.
A height belongs to a point. A height given for each cell is refused, rather than averaged
onto the points, since the average is not a value the data holds. {issue}`2728` records the
options, among them drawing each cell flat at its own height, and why refusing is the
default for now.

Mean sea level is the one reference. On `geovista`'s sphere it is the surface of the
sphere, which is how the models whose output it shows treat it too
(§3.4). A height declared against another zero is refused, never
mixed: a CRS whose vertical axis is an ellipsoidal height, as a 3D geographic CRS has, or a
compound CRS whose vertical datum is not gravity-related. PROJ names the vertical axis of
the one "Ellipsoidal height" and of the other "Gravity-related height". Converting such
heights through PROJ, with the geoid grid it needs, is a later step
(§7).

Heights that are not finite are refused.

`to_structured_grid` reads its `zs` as heights, in any form of §4.2, and honours them as
given, uneven levels included. Today it keeps only their number (§3.6).

(globe-spec-4-4)=
### 4.4 Positions Come From Heights

> **Extended by a child specification.** [`2026-10-27-globe-scene-design.md`](2026-10-27-globe-scene-design.md) settles which functions take a
> globe (scene spec §4.2), how a mesh stores the globe it records (scene spec §4.3), and the
> globe of a mesh that records none (scene spec §4.4).

The scene turns heights into positions, with its globe's radius `R`, scale `s` and
vertical mapping `V`. In its first form, `V(h)` is `E_above h` for a height at or above sea
level, and `E_below h` for one below:

- on the globe, a point at height `h` is drawn at radius `s (R + V(h))`;
- in a projection, at `z = V(h)`, converted to the length unit of the CRS's horizontal axes.
  Where those axes are angular, as in a geographic CRS drawn flat, a height becomes the
  angle it subtends at the radius `R`, in the CRS's angular unit, as
  zlevel spec §3.1 already does for a level.

A mesh is always positioned for some globe. The bridge's constructors and `transform_mesh`
take a globe, `Globe()` by default, in place of today's `radius`, and the mesh records the
globe it was positioned for. The globe and the heights are data on the mesh, so both
survive a file (crs spec §2 decision 14). A scene whose globe differs repositions the mesh
from its heights when it is added.

Because the heights stay as data, a point's height is read back from the data, not from
its position: a picked point reports the height it was given, and changing `V` rebuilds the
positions from the same heights. The scene can report `R`, `s` and `V`, so a vertical scale
shown to the viewer can be exact (§9, row 6). Everything that turns a height into a
position goes through `V`, and nothing assumes it is a straight line, so a later form of
it changes nothing else.

A coarse cell is still flat between its vertices, so its middle is drawn below the height
its vertices carry, by its sag (§3.5): 1.7 km at the centre of a C48
cell at true scale. That is a property of the mesh, not of its heights. Refining a mesh for
display reduces it, and stays an explicit opt-in
(crs spec §2, decision 8).

(globe-spec-4-5)=
### 4.5 Layers

Each layer of a scene has a place in an order: the base layer at the bottom, then data
surfaces in the order they are added unless given a place of their own, then lines such as
coastlines and the graticule, then labels. The order says which layer shows where two
coincide. It never changes a height.

Layers may share a place. Surfaces that do not overlap, such as regional meshes side by
side, have nothing to settle between them, so a user can give them one place and no bias
separates them. A surface added without a place still takes the next one, because the scene
does not check whether two surfaces overlap, and a surface that overlaps another needs a
place of its own.

**On the globe**, the hybrid of §3.5:

- the base layer is drawn lowered, in render units only, by 1.1 times the largest sag of
  the surfaces above it, so their cells' middles stay above it. A cell's sag is how far the
  mean of its vertices falls short of their mean radius, as a fraction of that radius, as
  §3.5 measured it;
- lines are drawn at their true heights, with a depth bias of 4 units towards the viewer,
  which covers their own sag of 9.3 × 10⁻⁶ without pulling the far side over the horizon.

Data surfaces are never moved. Two data surfaces at the same height on different meshes
fall back on their places and a depth bias, each place 256 units nearer the viewer than the
one below it, and surfaces that share a place share its bias. That can leave the sliver at
the limb that §3.5 measured for depth bias alone. Whether a
surface's bias also pulls its far side over the horizon, as a bias of 256 did for lines, is
not yet measured (§8, item 7).

**On a projected map**, where every layer at one height lies in one plane, layers are kept
apart by depth bias alone, each place 256 units nearer the viewer than the one below it,
well above the 64 that cleared every view measured. Nothing is offset in `z`.

VTK switches its polygon offset on for the whole process, and keeps the offsets themselves
on each mapper. `geovista` switches it on, so a plain `pyvista` plot in the same process
renders with VTK's default offsets, which pull its lines 4 units towards the viewer, and its
surfaces none.

The base layer's lowering is a display offset, so it is recorded with the scene, and never
reaches a coordinate a user reads back.

**A lift, for an exploded view.** A layer that has no altitude, or whose heights would
leave it hidden, may need drawing apart from the others, as the resolutions of an H3
hierarchy are, each floated above the next (§3.6). Neither a height, which is physics, nor
the order, which settles only which layer shows where two coincide, can do that. A lift
can. It is a display offset for one layer, given when the layer is added, as a fraction
`ℓ` of the radius: on the globe the layer is drawn at `s (R (1 + ℓ) + V(h))`, `ℓ` times the
render radius further out, and on a map at `z = V(h) + ℓ R`, in the CRS's length unit. A
lift is not a height:

- it is never exaggerated, and never written to a mesh, but recorded with the scene, as
  the base layer's lowering is;
- a picked point reports the height its data holds, not where its lift put it;
- the vertical scale marks a lifted layer as lifted, and reads no height from its
  position (§8 item 1);
- it is finite, may be negative to draw a layer beneath the surface, and is 0 by default.

Every method of `GeoPlotter` that adds a layer takes `lift`, except the base layer's.
Heights, the order and the lift keep apart the jobs that `zlevel` did in one number
(§3.1): where a thing is, which layer shows, and what is drawn apart for the eye.

(globe-spec-4-6)=
### 4.6 What Goes

When row 5 of §9 lands:

| today | becomes |
|---|---|
| `zlevel` on `add_mesh`, `add_points`, the bridge and the built-in layers | `height` or `depth` for a physical height, a layer's order for which layer shows, or a lift to draw it apart (§4.5) |
| `zscale` | the globe's vertical mapping |
| `ZLEVEL_SCALE`, `BASE_ZLEVEL_SCALE`, `ZTRANSFORM_FACTOR` | removed |
| `GV_POINT_ZLEVEL`, `GV_FIELD_ZSCALE` | a point array of heights in metres |
| `resize(..., zlevel=..., zscale=...)` | a height, or a globe's render radius |

The gallery's examples that use a level, or warp by hand, move to heights, an order or a
lift, each as its purpose in §3.1 and §3.6 says. The README's examples move with them, in
the pull request that changes what they use, and the test of {issue}`2756` runs them. The planar z-levels specification is then
retired, with a note at its head that this specification replaced it, and why.

(globe-spec-5)=
## 5. Alternatives Considered

- **Keep `zlevel`, scaled consistently.** Rejected. It mends the inconsistency of
  §3.2, but leaves height and display in one number, and leaves a
  plume's height a fraction of a radius.
- **A fixed geometric offset, as today.** Rejected. No fixed offset clears every resolution,
  and today's fails a 5° grid (§3.5).
- **Depth bias alone, on the globe.** Rejected. It leaves a sliver at the limb for a coarse
  mesh, and a stronger bias does not remove it.
- **Depth bias scaled by slope.** Rejected. It does not remove the sliver, and buries the
  coastlines.
- **VTK's z-buffer shift.** Rejected, as no better than no layering at all.
- **A renderer of its own for each layer, with depth buffers apart.** Not measured, and
  rejected: it orders whole layers, so a volume such as a plume could not pass behind the
  globe's far side, nor in front of part of a surface and behind the rest.
- **Lowering every surface, data included, by the sag above it.** Rejected, because it moves
  data that may be visible, and a data surface's height is physics.
- **Heights in the geometry, with the globe recorded beside them.** Rejected. Changing the
  exaggeration would mean recovering heights from positions, which is the reconstruction
  that Raikoke's picking has to do today (§3.3).
- **Averaging a height given for each cell onto the vertices**, as `pyvista`'s usual
  workaround does. Rejected as a default, because a corner then holds a height no cell has:
  a cell at 4,000 m among cells at 500 m is drawn about 2.6 km too low ({issue}`2728`).
- **Converting model levels to heights in `geovista` now.** Deferred, by decision 3.
- **Converting ellipsoidal heights to mean sea level now.** Deferred. It needs a geoid grid,
  and without one PROJ falls back silently (§3.4), so refusing is the
  rigorous step until the conversion is designed.

(globe-spec-6)=
## 6. Testing

Every result is checked against a reference independent of `geovista`, as
crs spec §6 requires:

- **heights**: a point given a height in feet, kilometres or metres, through any registry
  or a CF unit string, reads back the same height in metres, exactly; and is drawn at
  `s (R + V(h))` on the globe and `V(h)` in the CRS's unit on a map, by the formula;
- **the vertical mapping**: a height above sea level moves by the factor above, and a
  depth by the factor below; changing either moves every point by the formula, and leaves
  every height read back unchanged;
- **refusal**: an ellipsoidal height, a pressure given as a height, a height for each cell,
  a dimensionless angle and a height that is not finite each raise, naming the problem;
- **layering**: the measures of §3.5 become tests, on whichever
  renderer CI provides: no bleed, and every coastline of the close and orbiting views
  visible, for C48 and a 5° grid on the globe, and for C48 on Robinson;
- **places**: surfaces that share a place are drawn with one bias, and where two surfaces
  coincide, the one a place higher shows, on the globe and on a map;
- **the lift**: a layer lifted by `ℓ` is drawn `ℓ` times the render radius further out on the
  globe and `ℓ R` higher on a map, a picked point on it reports its data's height, and
  nothing is written to its mesh;
- **the radius**: each of the above holds at radius 1 and at the Earth's radius.

The layering tests render, so they carry the `image` marker, though they compare pixel
classes rather than a baseline image.

(globe-spec-7)=
## 7. Scope

In scope: the globe model on the scene, units, heights and depths above or below mean sea
level, the vertical mapping, layering on the globe and on a map, and the removal of
`zlevel` and `zscale`.

Out of scope, recorded so they are not forgotten:

- turning model levels into heights, by decision 3;
- pressure, flight levels and other vertical coordinates that are not lengths;
- ellipsoidal heights and other vertical datums, converted through PROJ with a geoid grid;
- height above the ground as a reference, which upstream turns into height above sea level;
- volumes, plumes as solids, and a floor and a ceiling, which stay with the design of region
  solids and the vertical (crs spec §9), along with {issue}`15`;
- the true shape of the ellipsoid (crs spec §9).

(globe-spec-8)=
## 8. Open Items

Each carries the status grammar of docs spec §3.6.

1. **Open** — **The vertical scale shown to the viewer.** Its form, a ruler beside the globe
   or a scale bar on the map, and how it marks the vertical mapping: two scales for two
   factors, and ticks that follow the mapping where it is not a straight line. Row 6 of
   §9 owns it.
2. **Open** — **A warped base layer.** The base layer is lowered by the sag of the surfaces
   above it. When it is terrain, warped by its own heights, that lowering moves terrain
   that may be visible where no surface covers it. Whether to lower it only beneath the
   surfaces, or accept the offset and record it, needs measuring with the LFRic orography.
3. **Open** — **Data surfaces at one height on different meshes.** They fall back on order
   and depth bias, which leaves a sliver at the limb for a coarse mesh. Whether that is ever
   seen in practice, and what to do if it is.
4. **Open** — **The physical render radius.** §3.5 found layering the
   same at the Earth's radius. Picking, clipping planes and interaction at that scale are
   not yet measured, before the default could change.
5. **Open** — **The ideal of the coastline measure.** It over-counts at the limb, so the
   limb's visibility is understated. A tighter ideal would let the limb be tested too.
6. **Deferred** (until users ask for it, {issue}`2728`) — **Heights given for each cell.**
   They are refused (§4.3). Averaging them onto the vertices lowers
   every peak and raises every valley without a word. Drawing each cell flat at its own
   height is honest but stepped. Users will want cell-centred heights to work as they are,
   and the issue holds the options for that conversation.
7. **Open** — **A biased surface at the limb.** A surface a place above another is drawn
   256 units nearer the viewer. A bias of 256 on lines pulled the far side's coastlines
   over the horizon (§3.5), and no surface was measured with one.
   Whether a surface's far side shows past the horizon, and if it does, whether to shrink
   the bias or apply it only where surfaces overlap, needs measuring before row 4 is
   planned.
8. **Open** — **Bands, and functions of height.** A vertical mapping in bands, such as a
   stratosphere compressed further than the troposphere beneath it, or one that follows a
   function of height. Either is recorded as a table of heights and the offsets they are
   drawn at, since a mesh records its globe losslessly (crs spec §2 decision 14) and a
   Python function cannot be saved in a file: a function is sampled into the table when
   the globe is made. A mesh records the table as a second form, beside the two factors,
   which are not retired. Any form keeps the three rules of §4.1. A mapping that is not a
   straight line distorts how thick a layer and how steep a slope look, so the vertical
   scale's ticks must follow it (item 1).
9. **Open** — **Vectors under the vertical mapping.** An arrow is drawn against a
   stretched vertical, so to stay tangent to an exaggerated surface its vertical component
   scales by the slope of the mapping at its height: in the first form, the factor above or
   below sea level. The 3-D winds of §3.6 stretch theirs by 1,500 by hand. Whether
   `geovista` applies the slope, and how a user asks for more to make a weak vertical wind
   legible, belongs with the vector work of crs spec §4.5.

(globe-spec-9)=
## 9. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | Units: `geovista.units`, with `pint` and `pint-cf` | ✅ landed (2026-10-27, {pull}`2754`) |
| 2 | The globe on the scene: the globe model, `GeoPlotter(globe=...)`, every built-in layer at its radius, and the round trip of crs spec §6, by rows 1 and 2 of scene spec §9 | not started |
| 3 | Heights as data: `height` and `depth`, the vertical mapping, positions on the globe and on a map, refusals, and `to_structured_grid` reading its levels as heights | not started |
| 4 | Layers: the order, the base layer's lowering, the lines' depth bias, depth bias on a map, the lift, and the measures of §3.5 as tests | not started |
| 5 | Removing `zlevel` and `zscale`, migrating the gallery and tests, and retiring the planar z-levels specification | not started |
| 6 | A vertical scale for the viewer | candidate: a scene with heights that a scientist shows |

Statuses follow docs spec §3.6. Each row that changes the public API updates the README's
examples in the same pull request ({issue}`2756`). Rows 1 to 5 come in order, and each
is planned once the rows before it have landed. Row 4 needs a renderer in CI, which the
image tests already have. Row 5 is breaking, and carries a `breaking` fragment beside its
own. Row 2 of the parent's roadmap lands with row 5 here.

(globe-spec-10)=
## 10. References

- {issue}`15`, {pull}`2294` and {issue}`1029`, earlier work on a vertical dimension
- {issue}`2588`, the planar z-level inconsistency, and {pull}`2591`, which fixed it
- `bjlittle/geovista-jav-2026`, the Reykjanes and Raikoke applications
- the CF standard names for vertical coordinates, `altitude`, `height`, `depth`,
  `height_above_mean_sea_level` and `height_above_reference_ellipsoid`:
  <https://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html>
- VTK's coincident topology, `vtkMapper.SetResolveCoincidentTopologyToPolygonOffset` and the
  relative offset parameters of each mapper:
  <https://vtk.org/doc/nightly/html/classvtkMapper.html>
- `pint`: <https://github.com/hgrecco/pint>, and `pint-cf`: <https://github.com/pgamez/pint-cf>
