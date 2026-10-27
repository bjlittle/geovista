# geovista Globe on the Scene — Design Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. It states how a scene's globe takes the place of every radius in `geovista`,
> how a mesh records the globe it was built for, and how `geovista` retires a field it no
> longer writes. Where the two ever diverge it is the specification that gets corrected.
> Read it as current; the roadmap states what has actually landed.

- **Date:** 2026-10-27 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `scene spec §…`
- **Scope:** the `Globe` in place of every `radius`, the globe a mesh records, meshes that
  record no globe, and the retirement of fields that `geovista` no longer writes
- **Parent spec:** the globe, heights and layers design
  ([`2026-10-26-globe-heights-layers-design.md`](2026-10-26-globe-heights-layers-design.md)).
  This extends globe spec §4.1 and globe spec §4.4, and is row 2 of globe spec §9. It
  inherits that specification's decisions (globe spec §2) and testing (globe spec §6)
  unchanged. It settles crs spec §8 item 12 of the globe-first CRS design, and adds to
  crs spec §4.9 how the public API reports a value with a unit
- **Published:** in the specifications index

(scene-spec-1)=
## 1. Purpose

Row 2 of globe spec §9 puts the globe on the scene. A scene's globe holds the Earth's
radius, the radius the scene is drawn at, and one vertical mapping, and every layer
takes its geometry from it (globe spec §4.1). The bridge and `transform_mesh` take a globe
in place of today's `radius`, and a mesh records the globe it was positioned for
(globe spec §4.4).

That left four questions, which {user}`bjlittle` settled while this was written: how far
the change reaches, what becomes of `radius=`, how a mesh stores its globe, and what
`geovista` does with a mesh saved before the globe existed. The answers raised a fifth:
how `geovista` stops writing a field, and in time stops reading it.

(scene-spec-2)=
## 2. Decisions

These were decided with {user}`bjlittle` while the design was written.

1. **The globe takes the place of every radius.** Wherever `geovista` sets the size of a
   sphere, it takes a globe. A partial change would leave a mesh built at one radius in a
   scene at another, with nothing to say which, and would put off design questions that
   are better faced now.
2. **`radius=` is removed, with no alias.** Today's `radius` is the radius a mesh is drawn
   at, which the globe calls its render radius. A user who passes 6,371,000 reads it as the
   Earth's radius, which the globe calls its radius. An alias would keep that ambiguity.
   crs spec §2 decision 4 allows the break, and a caller still passing `radius=` gets
   Python's error for an unexpected keyword.
3. **A mesh records its globe in four fields:** `gvGlobeRadius`, in metres,
   `gvGlobeRenderRadius`, `gvGlobeExaggerationAbove` and `gvGlobeExaggerationBelow`, each a
   float64 field array of one value. The two exaggerations are the first form of the
   vertical mapping of globe spec §4.1, above and below sea level. Each is named for a reader who opens the file in ParaView, and none depends on
   its place in an array.
4. **A mesh that records no globe is read, never refused.** It is placed on the default
   globe, at its `gvRadius` where it has one, and otherwise at the one radius its points
   lie at, if they lie at one. No position changes: today's `gvRadius` is exactly the render
   radius, and the Earth's radius was never recorded. A mesh whose globe cannot be read
   this way, such as one warped by its heights outside `geovista`, has no globe, and is
   drawn where its points are. This settles crs spec §8 item 12.
5. **Every mesh `geovista` produces carries only current fields.** A retired field found
   on a mesh is translated into what replaced it, and removed, in the mesh `geovista`
   returns or draws, so that saving that mesh does not carry the field forward. A mesh
   given to `geovista` only to read is never changed, unless the caller asked for the
   change in place.
6. **A public function cleans a mesh.** `geovista.common.sanitize_legacy` translates and
   removes every retired field in place, beside `sanitize` and `sanitize_vtk`, which purge
   index arrays. It serves a user cleaning saved files, and the refresh of the pantry's
   assets ({issue}`2753`).
7. **One table holds every retired field.** `gvRadius` is the first. `gvZScale` and
   `gvZLevel` join it when row 5 of globe spec §9 removes `zlevel`. When `geovista` stops
   reading them is decided once they are all in it (§8 item 1).
8. **A public value with a unit is a quantity.** Inside, `geovista` passes plain floats in
   SI, as crs spec §4.9 says. A public attribute or result that reports a physical value,
   such as a globe's radius, returns a `pint` quantity, so that the public API describes
   itself.
9. **geovista's view of a mesh lives in one namespace, `mesh.gv`.** It holds the mesh's
   `globe` and `crs`, both read-only, and is open to more. `mesh1.gv == mesh2.gv` when
   `geovista` describes the two meshes the same way, and
   `mesh1.gv.globe == mesh2.gv.globe` when their globes are equal.

(scene-spec-3)=
## 3. What Exists Today

(scene-spec-3-1)=
### 3.1 Thirty-Three Radii

Measured at `a0f95dbe`, 33 functions in 9 modules take a `radius`, and each is the radius
of a sphere, by default `common.RADIUS`, which is 1:

| module | functions |
|---|---|
| `bridge` | `Transform.__init__`, `from_1d`, `from_2d`, `from_points`, `from_tiff`, `from_unstructured` and `to_structured_grid` |
| `common` | `to_cartesian`, `vectors_to_cartesian`, `to_lonlat` and `to_lonlats` |
| `core` | `resize` |
| `geodesic` | `line`, and `BBox.boundary` and the private `BBox._generate_bbox_mesh` |
| `geometry` | `coastlines` and `load_coastlines` |
| `geoplotter` | `add_base_layer`, `add_coastlines`, `add_graticule`, `add_mesh`, `add_meridian`, `add_meridians`, `add_parallel`, `add_parallels` and `add_points`, and the private `_lfric_mesh` and `_add_graticule_labels` |
| `gridlines` | `create_meridians` and `create_parallels` |
| `search` | `KDTree.query` |
| `transform` | `transform_mesh`, and the private `_record_zlevels` |

One gallery example passes `radius=`, as do 13 calls in 8 test modules, and 3 pages of the
documentation.

(scene-spec-3-2)=
### 3.2 The Radius on a Mesh

The bridge, `geometry.coastlines`, `core.resize`, `transform_mesh` and `geodesic` write
the radius a mesh was built at as the field `gvRadius`. When `geovista` needs a mesh's
radius, `common.distance` measures the mean distance of its points from the origin, and
snaps the result to `gvRadius` where the two agree. A mesh with no `gvRadius` therefore
works today, as the pantry's LFRic meshes do, which carry only `gvCRS`. The pantry's
coastlines carry a `gvRadius` of 1 (crs spec §3.4).

(scene-spec-3-3)=
### 3.3 Field Data Through pyvista

Measured on 2026-10-27 at `a0f95dbe`, with `pyvista` 0.49.1 and VTK 9.7.1:

- `import geovista` already imports `pyvista` and VTK, in 1.17 s, so registering an accessor
  with `pyvista` when `geovista` is imported costs nothing more.
  `pyvista.register_dataset_accessor` arrived in `pyvista` 0.48.0, which is `geovista`'s
  floor.
- A field array survives `copy`, `clip`, `clip_box`, `threshold`, `extract_cells`, `slice`,
  `triangulate`, `decimate`, `extract_surface`, `cast_to_unstructured_grid`, `merge`,
  `connectivity`, `smooth`, `subdivide`, `cell_data_to_point_data` and `warp_by_scalar`, so
  a globe recorded on a mesh survives them too.
- `merge` keeps the field data of the first mesh alone, and so does `core.combine`, which
  compares neither the CRSs nor the radii of the meshes it combines. Combining meshes in
  different CRSs, or at different radii, records the first one's for all of them.
- Quantities from two `pint` registries cannot be added: `pint` raises "Cannot operate with
  Quantity and Quantity of different registries". Two from `pint`'s application registry
  can.

(scene-spec-3-4)=
### 3.4 A Mesh Warped Outside geovista

The gallery's LFRic orography example warps its mesh with `pyvista`: it computes point
normals, then calls `warp_by_scalar` with a factor of 2 × 10⁻⁵ on the altitudes. Measured on
2026-10-27 at `a0f95dbe`:

- `lfric_orog()` carries `gvCRS`, `gvRadius` of 1 and `gvName`, and its points lie at a
  radius of 1 exactly. The warp keeps the field data (§3.3), so the warped mesh still says
  it was drawn at a render radius of 1, which is true of its sea level.
- The altitudes run from −114.9 m to 5,176.4 m, with a mean of 224.4 m. A factor of
  2 × 10⁻⁵ at a render radius of 1 is an exaggeration of 127.6 at the Earth's radius,
  chosen by hand and recorded nowhere.
- The point normals depart from the radial direction by a median of 0.01° and at most
  0.43°, so the warp moves a point sideways by at most 1.6 km at the Earth's radius.
- The warped mesh's mean radius is 1.00449. Read as its render radius and drawn at 1, the
  mesh would shrink by 0.45%, and its sea level would sink about 28 km beneath the
  surface, below the base layer.

(scene-spec-4)=
## 4. Design

(scene-spec-4-1)=
### 4.1 The Globe

`geovista.Globe` is immutable, and takes four keyword arguments:

- `radius`, the Earth's radius, by default the WGS84 semi-major axis of 6,378,137 m, in
  any form `geovista.units.to_metres` reads (globe spec §4.2);
- `render_radius`, the radius the globe is drawn at, by default `common.RADIUS`, a plain
  number in the units of the scene;
- `exaggeration`, by default 1, a plain number, the factor for heights above sea level, and
  for depths below it too unless `exaggeration_below` is given;
- `exaggeration_below`, by default the `exaggeration`, a plain number, the factor for
  depths below sea level.

Each must be finite and positive. A factor of 0 would draw a range of heights at one
radius, and break the rule of globe spec §4.1 that the vertical mapping always increases.
Anything else raises a `ValueError` naming the value. `Globe(exaggeration=20)` stretches
the atmosphere and the ocean alike, and `Globe(exaggeration=20, exaggeration_below=100)`
stretches the ocean five times more. Land below sea level takes the factor below too
(globe spec §4.1), and the documentation of `Globe` says so.

A globe's `radius` returns a `pint` quantity in metres, in `pint`'s application registry,
the one `pint` provides for sharing quantities between packages, so that a user can add
it to quantities of their own (§2 decision 8). Its `render_radius`, `exaggeration` and
`exaggeration_below` return plain floats, since one is in the units of the scene and the
others are ratios.
Inside, `geovista` reads the radius as a float in metres, so drawing a scene never imports
`pint`; the first read of `radius` does. A globe also reports its scale, the render radius
over the radius.

Two globes are equal when their four values are, exactly, and a globe is hashable, so it
can key a cache such as the mapping of crs spec §4.5.

The class lives in `geovista.globe`, and is exported at the top level of `geovista`.

(scene-spec-4-2)=
### 4.2 Every Radius Becomes a Globe

Each function of §3.1 takes `globe: Globe | None = None` in place of `radius`, except the
methods of `GeoPlotter`:

- `GeoPlotter` takes `globe=` when it is made, `Globe()` by default, and every layer it
  adds takes its geometry from that globe, the base layer, coastlines and graticule
  included. Its methods take no globe of their own, since a scene has one
  (globe spec §2 decision 4). `GeoPlotter.globe` reports it, read-only, so a vertical
  scale can be exact (globe spec §4.4).
- A function that builds a mesh, such as a `Transform` constructor or `geodesic.line`,
  uses `Globe()` when given none, and records the globe it used on the mesh.
- A function given a mesh to work on, such as `transform_mesh`, uses the globe that mesh
  records (§4.4) when given none. `KDTree.query` uses the globe of the mesh its tree was
  built from.
- `resize` takes the globe to resize a mesh to, and records it.

A mesh added to a scene whose globe differs from the one it records is drawn at the
scene's globe, and the mesh drawn records the scene's globe. Every height is 0 until row 3
of globe spec §9, so on the globe this is a scale by the ratio of the two render radii,
and on a projected map it changes nothing. Row 3 makes it a rebuild from heights
(globe spec §4.4).

`zlevel` and `zscale` stay until row 5 of globe spec §9, and offset a point from the render
radius as they offset it from the radius today.

(scene-spec-4-3)=
### 4.3 The Globe on a Mesh

Every function that builds or positions a mesh writes the four fields of §2 decision 3,
named by four constants in `geovista.common`, and writes no `gvRadius`. `Globe.from_mesh`
reads a mesh's globe without changing the mesh, and `Globe.to_mesh` writes the four
fields to a mesh in place and removes `gvRadius` from it.

The round trip of crs spec §6 lands with row 1 of §9: a mesh carrying a CRS and a globe,
saved to binary legacy `.vtk`, `.vtp`, `.vtu` and `.vtkhdf` and read back, has the same CRS,
the same globe, and the same points, bit for bit.

(scene-spec-4-4)=
### 4.4 A Mesh That Records No Globe

`Globe.from_mesh`, given a mesh without the four fields, returns:

1. `Globe(render_radius=r)` for a mesh with a `gvRadius` of `r`;
2. otherwise, for a mesh that `crs.projected` does not call projected, and whose points
   all lie at one radius `r`, to within a relative spread of 10⁻⁶, `Globe(render_radius=r)`;
3. otherwise `None`: the mesh's globe cannot be read.

The spread of item 2 tells a mesh on a sphere from one whose heights were baked into its
positions. A warped mesh's mean radius is its sea level raised by its heights, and taking
it for the render radius would sink that sea level (§3.4). 10⁻⁶ admits a sphere stored in
float32, whose radius varies by some 6 × 10⁻⁸, and refuses heights of more than about 6 m
at the Earth's radius.

A mesh with no globe is drawn where its points are, never repositioned, and records no
globe on the mesh drawn. A function given such a mesh uses `Globe()` wherever it needs a
globe. Its heights, if it has any, are baked into its positions, so `geovista` cannot
report them, exaggerate them with the scene, or include them in a vertical scale. The
remedy is to pass the mesh unwarped, with its heights as data (globe spec §4.3).

A mesh with some of the four fields but not all is refused, naming what is missing,
since `geovista` never writes part of a globe.

(scene-spec-4-5)=
### 4.5 Retiring a Field

One table in `geovista.common` lists every field that `geovista` reads but no longer
writes. Each entry names the field, whether it is field, point or cell data, what replaced
it, the last release that wrote it, and how to translate it. Its name and form are left to the builder. `gvRadius` is the first
entry: field data, replaced by the globe of §4.3, last written by 0.5.3, or by any later
0.5 release, and translated as §4.4 item 1 says. 0.6 is the first release to write the
globe instead.

`sanitize_legacy(*meshes)` translates and removes every retired field of each mesh, in
place, with the same signature as `sanitize_vtk`. `sanitize` gains `legacy: bool = True`,
as it has `vtk`, so a call of it cleans retired fields too.

A function that returns or draws a mesh it made from one it was given applies the same
translation to the mesh it returns or draws. With `inplace=True`, the caller's mesh is
that mesh. Reading a retired field raises no warning, since every pantry asset would warn
until {issue}`2753` refreshes them, and a warning is an error under the test suite.

(scene-spec-4-6)=
### 4.6 The `gv` Namespace

`geovista` registers an accessor named `gv` on `pyvista.DataSet` when it is imported, with
`pyvista.register_dataset_accessor`, so every `pyvista` mesh has `mesh.gv`:

- `mesh.gv.globe` returns the `Globe` the mesh records, read by `Globe.from_mesh` (§4.4),
  or `None` when its globe cannot be read;
- `mesh.gv.crs` returns the mesh's CRS, read from its WKT as `crs.from_wkt` reads it, or
  `None`.

Each is read from the mesh's field data at every access, so it never goes stale, and
reading never changes the mesh. Neither can be set. A globe describes where a mesh's points
are, so setting one without moving them would make the two disagree. Assigning to
`mesh.gv.globe` raises an `AttributeError` that names `resize(mesh, globe=...)`, which moves
the points and records the globe together.

`mesh1.gv == mesh2.gv` when `geovista` describes the two meshes the same way: equal CRSs
and equal globes. It compares no geometry, which is what `pyvista`'s own comparison of
meshes is for. A member added to the namespace later says whether it joins this
comparison, and the specification that adds it records the choice.

(scene-spec-4-7)=
### 4.7 Combining Meshes

`core.combine` refuses meshes that `geovista` describes differently, by
`mesh1.gv == mesh2.gv`, and names what differs, the CRS or the globe. A caller resizes or
transforms the meshes to one globe and one CRS first. `pyvista`'s own `merge` keeps the
first mesh's field data (§3.3), and is outside `geovista`'s control. The documentation of
`combine` says so.

(scene-spec-4-8)=
### 4.8 What Goes

| today | becomes |
|---|---|
| `radius=` on the 33 functions of §3.1 | `globe=`, or the scene's globe for a `GeoPlotter` method |
| `gvRadius`, written | `gvGlobeRadius`, `gvGlobeRenderRadius`, `gvGlobeExaggerationAbove` and `gvGlobeExaggerationBelow`; `gvRadius` is read, and cleaned (§4.5) |
| a radius given to each layer of a scene | `GeoPlotter(globe=...)` |

The gallery example, the tests and the pages of §3.1 move to `globe=`.

(scene-spec-5)=
## 5. Alternatives Considered

- **Change only `GeoPlotter` and its built-in layers.** Rejected, by §2 decision 1.
- **Keep `radius=` as an alias of the render radius.** Rejected, by §2 decision 2.
- **One field array of four values, `gvGlobe`.** Rejected. A reader in ParaView would see
  four numbers with no names, and every reader would depend on their order.
- **The globe as text, such as JSON, in one string field.** Rejected. ParaView would show
  it as a string, and the numbers would go through text formatting.
- **Writing `gvRadius` beside the new fields, for older releases.** Rejected. A release
  before a breaking change is not supported across it, and in the new vocabulary a
  radius is the Earth's.
- **Measuring every mesh that records no globe,** as first designed. Rejected. A warped
  mesh would be read at its mean radius, and drawn 0.45% too small (§3.4).
- **Refusing a mesh with `gvRadius` and no globe.** Rejected, by §2 decision 4. A plain
  mesh with no record at all must be read anyway, so a mesh with more information can be
  read too.
- **Translating retired fields in place whenever a mesh is read.** Rejected, by §2
  decision 5: `geovista` would change a caller's mesh it was only asked to read.
- **A warning whenever a retired field is read.** Not now (§4.5). The cut-off of §8 item 1
  may add one.
- **A globe's radius as a float in metres.** Rejected, by §2 decision 8. A public value
  with a unit describes itself.
- **Quantities in `geovista`'s own `pint-cf` registry.** Rejected. A user could not add them
  to quantities of their own (§3.3).
- **A top-level accessor, `mesh.globe`.** Rejected. An accessor is an object `pyvista`
  builds around the mesh, so `mesh.globe` could only imitate a `Globe`, where
  `mesh.gv.globe` returns one. One namespace also claims one name on every `pyvista` mesh,
  however much `geovista` puts in it.
- **A settable `mesh.gv.globe`.** Rejected (§4.6). It would change the record without the
  points.
- **One exaggeration for the whole scene,** as globe spec §2 decision 4 first had it.
  Rejected. The ocean beneath a scene and the atmosphere above it need factors an order of
  magnitude apart.
- **An exaggeration for each layer.** Rejected. A cloud stretched more than the mountain
  beneath it could be drawn below the mountain, and the scene would have no one vertical
  scale.
- **The vertical mapping as a table from the start.** Not now. Two named factors read
  plainly in ParaView, and a table joins them later as a second form
  (globe spec §8 item 8), so neither is ever retired.
- **`combine` keeping the first mesh's record, as it does today.** Rejected, as quietly
  wrong when the meshes differ.

(scene-spec-6)=
## 6. Testing

Every result is checked against a reference independent of `geovista`, as
globe spec §6 and crs spec §6 require:

- **the globe**: a radius in each form of globe spec §4.2 reads as metres; a value that is
  not finite, a radius that is not positive and an exaggeration that is not positive are
  each refused; `exaggeration` alone sets both factors, and `exaggeration_below` sets the
  factor below sea level alone;
  equal values make equal globes;
- **the record**: every function of §3.1 that builds or positions a mesh writes the four
  fields, the globe it was given or its default, and no `gvRadius`;
- **the round trip** of §4.3;
- **reading**: each case of §4.4 gives the globe it names, a partial record is refused, and
  the mesh read is unchanged; a sphere in float32 reads at its radius, and the example's
  mesh warped as it is today, with its `gvRadius` removed, has no globe and is drawn
  unscaled;
- **cleaning**: `sanitize_legacy` translates and removes `gvRadius`; `sanitize` does so
  unless given `legacy=False`; no mesh that the bridge, `transform_mesh`, `resize` or
  `GeoPlotter` returns or draws carries a retired field; the table lists every field
  that `geovista` reads but does not write;
- **the scene**: a mesh built at a render radius of 1, added to a scene at 2, is drawn at
  2, and so are the pantry's coastlines; `GeoPlotter.globe` reports the scene's globe and
  cannot be set;
- **the quantity**: a globe's `radius` is a quantity in metres in `pint`'s application
  registry, which adds to another from it, and drawing a scene imports no `pint`;
- **the namespace**: `mesh.gv.globe` and `mesh.gv.crs` read what the mesh records, follow
  a change to its field data, and cannot be set; `mesh.gv` is equal for meshes with equal
  CRSs and globes, whatever their points, and unequal when either differs; equal globes
  hash equally;
- **combining**: `combine` refuses meshes with different CRSs, or different globes, and
  names which;
- **the radius**: each of the above holds at a render radius of 1 and at the Earth's
  radius.

(scene-spec-7)=
## 7. Scope

In scope: the `Globe`, the globe in place of every radius, the globe a mesh records, meshes
that record none, the table of retired fields and the cleaning of them, the `mesh.gv`
namespace, `combine` refusing meshes described differently, and the round trip of
crs spec §6.

Out of scope:

- heights, and the effect of the vertical mapping, which are row 3 of globe spec §9;
- a vertical mapping in bands, or as a function of height (globe spec §8 item 8);
- layering, row 4, and the removal of `zlevel` and `zscale`, row 5;
- when `geovista` stops reading retired fields (§8 item 1);
- the refresh of the pantry's assets ({issue}`2753`), which `sanitize_legacy` serves;
- a physical render radius by default (globe spec §8 item 4).

(scene-spec-8)=
## 8. Open Items

Each carries the status grammar of docs spec §3.6.

1. **Open** — **When retired fields stop being read.** The release after which
   `geovista` refuses a retired field rather than translating it, and what refusing it
   looks like, to settle once row 5 of globe spec §9 has added `gvZScale` and `gvZLevel` to
   the table of §4.5.

(scene-spec-9)=
## 9. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | The globe and its record: `geovista.Globe` with its radius as a quantity, the four fields, `Globe.from_mesh` and `Globe.to_mesh`, meshes that record no globe, the `mesh.gv` namespace with `globe`, `crs` and its equality, the table of retired fields, `sanitize_legacy` and `sanitize(legacy=...)`, and the round trip of crs spec §6 | not started |
| 2 | Every radius becomes a globe: `globe=` in place of `radius=` on the 33 functions, `GeoPlotter(globe=...)` and `GeoPlotter.globe`, `combine` refusing meshes described differently, only current fields in every mesh returned or drawn, and the gallery, tests and documentation moved to `globe=` | not started |

Statuses follow docs spec §3.6. Row 1 adds to the API and breaks nothing. Row 2 is
breaking, and carries a `breaking` fragment beside its own. Row 2 is planned once row 1
has landed, and row 2 of globe spec §9 lands with it. Both rows land before 0.6 is
released, since 0.6 is the first release that writes the globe and no retired field.

(scene-spec-10)=
## 10. References

- The globe, heights and layers design: globe spec §2, globe spec §4.1, globe spec §4.2,
  globe spec §4.4 and globe spec §9.
- The globe-first CRS design: crs spec §2 decisions 4 and 14, crs spec §3.4,
  crs spec §6 and crs spec §8 item 12.
- {issue}`2753`, the refresh of the pantry's assets.
