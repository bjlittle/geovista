# Layers of a Scene Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. It states how a scene keeps its layers apart where they meet, and how a user
> says which one shows: on the globe and on a map, on the desktop and on the web. Where the
> two ever diverge it is the specification that gets corrected. Read it as current; the
> roadmap states what has actually landed.

- **Date:** 2026-11-12 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `layers spec §…`
- **Scope:** named tiers and the order of layers, the base layer's lowering, depth bias,
  the horizon clip, the lift, and how each behaves on the globe, on a map, below the
  surface and on the web
- **Lineage:** [crs spec](2026-10-23-globe-first-crs-design.md) › [globe spec](2026-10-26-globe-heights-layers-design.md) › **layers spec**
- **Children:** none
- **Extends:** globe spec §4.5, as row 4 of globe spec §9. It inherits that specification's
  decisions (globe spec §2) and testing (globe spec §6), except that a layer's place
  becomes a named tier (§2 decision 3), and every layer is clipped at its horizon
  (§2 decision 5). crs spec §2 decision 8 stands unchanged (§2 decision 2)
- **Prior art:** the `zorder` of matplotlib and cartopy; the panes of Leaflet, and
  Mapbox's `beforeId`; VTK's resolution of coincident topology; the horizon clip of
  discussion {issue}`2440`
- **Published:** in the specifications index

(layers-spec-1)=
## 1. Purpose

Globe spec §4.5 designed how a scene keeps one layer from hiding another, from a spike that
looked at the globe from outside, with every layer at sea level. Row 4 of globe spec §9
builds it. Before it was planned, two more spikes measured the design against what users
meet: ocean data below sea level, layers above it, coarse surfaces under fine ones, a camera
inside the Earth, and the documentation's interactive scenes, which run in a web browser.
They also tried two ways for a user to say which layer shows.

{user}`bjlittle` settled the decisions of §2 from those measurements, which §3 records with
their figures. Most of globe spec §4.5 stands. What changed is how the order is given, a
clip that stops depth bias pulling the far side of the globe into view, and what happens
below the surface and on the web.

(layers-spec-2)=
## 2. Decisions

These were decided with {user}`bjlittle` while the design was written.

1. **🤝 Agreed** (2026-11-14, {user}`bjlittle`, {pull}`2954`) — **Layering is designed for a
   camera outside the globe, and keeps a camera inside working.** The default camera is
   outside, looking at the globe, or above a map, looking down. A camera beneath the surface
   or inside the Earth, as an oceanographer looking at the ocean may want, must still work:
   below the surface the scene switches off the lowering, the bias and the clip, and depth
   alone decides (§4.4). Designing that view is §8 item 5.
2. **🤝 Agreed** (2026-11-14, {user}`bjlittle`, {pull}`2954`) — **No refinement by default.**
   crs spec §2 decision 8 stands: a data mesh's cells are never refined by default. On the
   globe the default is the hybrid of globe spec §4.5 with the horizon clip of §2 decision 5.
   Refinement for display, the opt-in of row 13 of crs spec §10, is what fixes the scenes the
   default handles less well (§4.7).
3. **🤝 Agreed** (2026-11-14, {user}`bjlittle`, {pull}`2954`) — **The order is given by named
   tiers, not by a number.** A `zorder` would be familiar to matplotlib and cartopy users,
   but on the globe it cannot mean what it means there: depth still decides, so a mountain in
   front hides a layer of any order. A tier's name says what it is for. The built-in tiers,
   bottom to top, are `"subsurface"`, `"base"`, `"data"`, `"lines"` and `"labels"`. A layer
   names its tier with `tier=`, and within a tier layers keep the order they were added,
   unless `above=` or `below=` places one next to another of that tier.
4. **🤝 Agreed** (2026-11-14, {user}`bjlittle`, {pull}`2954`) — **A user can add and alias
   tiers.** `add_tier(name, above=..., below=...)` inserts a tier next to another, and
   `GeoPlotter(tiers=[...])` gives the whole order at once. `alias_tier(alias, tier)` gives a
   tier a second name. A name that is neither a tier nor an alias is refused, and the scene
   always reports a tier by its own name, never by an alias.
5. **🤝 Agreed** (2026-11-14, {user}`bjlittle`, {pull}`2954`) — **Every layer is clipped at
   its own horizon.** Depth bias pulls a layer towards the viewer, and with it any part of
   the layer behind the globe. Clipping each layer at the horizon it can be seen over removes
   that part, so no bias can pull it into view. The plane follows the camera, and is worked
   out from the layer's highest point, so a layer above sea level keeps what peeks over the
   horizon. It applies while an opaque base layer hides the far side, and a scene without one
   is not clipped (§4.3).
6. **🤝 Agreed** (2026-11-14, {user}`bjlittle`, {pull}`2954`) — **Layers below sea level have
   a tier below the base layer.** Lowering the base layer draws the sea surface beneath any
   shallow ocean data, which then shows through it. A layer in a tier below `"base"` is
   pushed away from the viewer instead, and a layer given depths joins `"subsurface"` by
   default.
7. **🤝 Agreed** (2026-11-14, {user}`bjlittle`, {pull}`2954`) — **On the web, the bias is
   restored and the clip is left out for now.** The interactive scenes of the documentation,
   and trame's client-side rendering in a notebook, lose the bias in export, which is a gap
   in trame's serializer that vtk.js does not share. The bias is written back, upstream and
   in geovista's documentation build until upstream lands (§4.8). A clip that follows the
   camera needs code in the browser, and is §8 item 2.

(layers-spec-3)=
## 3. What Was Measured

**Method.** Measured on 2026-11-11 and 2026-11-12 at `0b2a59ee`, with VTK 9.7.2, `pyvista`
0.49.2 and NumPy 2.5.4, on llvmpipe (LLVM 20.1.2) from Mesa 25.2.8, under `xvfb-run`, and in
headless chromium through trame's static vtk.js viewer, trame 4.0.0. Each scene was drawn at
800 × 800 in flat, unlit colours with anti-aliasing off, so that every pixel belongs to one
layer, and at a render radius of 1 and of 6,378,137. Depth bias is VTK's polygon offset in
its constant form, in units of the depth buffer. The scripts were throwaway, and are attached
to {pull}`2954` so that each measurement can be repeated.

The radius made no difference anywhere, as globe spec §3.5 found, except where two layers
coincide exactly, which the lowering exists to prevent.

(layers-spec-3-1)=
### 3.1 Sag, and Why Layers Fight

A cell is flat between its vertices, so its middle sits below the sphere they lie on, and a
finer mesh beneath pokes through it. Globe spec §3.5 called this sag, and tabled it: 6.7 ×
10⁻⁵ of the radius for C96, 2.7 × 10⁻⁴ for C48 and 1.9 × 10⁻³ for a 5° grid.

```{figure} figures/2026-11-12-layers-design/sag.png
:alt: A slice through the globe: a flat 20-degree cell is a chord whose middle dips below the sphere, while a finer mesh of 2.5-degree cells hugs it.
:width: 80%

Sag, in a slice through the globe with heights stretched four times.
```

```{figure} figures/2026-11-12-layers-design/bleed-without-layering.png
:alt: A close view of a 5-degree data surface in blue over the C96 base layer in red, with no layering. Red covers nearly everything; only specks of blue survive at the cells' corners.
:width: 50%

A 5° surface over the C96 base layer, with no layering at all.
```

(layers-spec-3-2)=
### 3.2 Bias Pulls the Far Side Over the Horizon

A global surface at sea level, with a regional one (40° square, on another mesh) a place
above it, so drawn nearer by a bias. Each cell of the regional surface was coloured by
whether it lay wholly in front of the horizon, wholly behind it, or across it, so any pixel
of the colour behind is that surface's far side pulled into view. Swept over 30 views, from
20, 3 and 1.2 radii and grazing the surface, with the regional surface across the horizon:

| Regional over global | Smallest bias with no bleed | Far side shown at that bias | At 256 | At 1024 |
|---|---|---|---|---|
| 1° grid over C48 | 16 | none | 1,724 px | 40,480 px |
| C48 over 1° grid | 128 | 291 px | 1,480 px | 36,819 px |
| 5° grid over C48 | 256 | 1,427 px | 1,427 px | 29,624 px |

No one bias suits every pair: the bias that stops a surface bleeding grows with its sag, and
the far side it shows grows with the bias.

```{figure} figures/2026-11-12-layers-design/far-side-crescent.png
:alt: The globe in red, with a magenta crescent along its left limb: a regional surface's far side, behind the globe, drawn in front of it.
:width: 50%

The far side of a 5° regional surface, biased 256, drawn over the limb from 1.2 radii.
```

Clipping every layer at the horizon, at the plane `C·v = R²` where `C` is the camera,
removes that far side, as discussion {issue}`2440` showed for coastlines and point clouds.
With it the far side showed in no view, at any bias up to 1,024, and every pair above showed
no bleed at 256.

```{figure} figures/2026-11-12-layers-design/horizon-clip.png
:alt: A diagram of a camera beside the globe. Tangent lines touch the globe at the horizon; the near side is green, the far side purple, and an orange clip plane passes through the two horizon points.
:width: 70%

The horizon clip.
```

(layers-spec-3-3)=
### 3.3 The Earlier Spike, Repeated With the Clip

The scene of globe spec §3.5: the C96 base layer, a global data surface (C48, a 1° grid or a
5° grid) and the 10m coastlines, in its views. Bleed is the share of the globe where the base layer
shows, worst over every view:

| Data surface | Hybrid | Hybrid and clip | Clip and bias 256, nothing lowered |
|---|---|---|---|
| C48 | 0.17% | 0.17% | 0.16% |
| 1° grid | 0.25% | 0.25% | 0.01% |
| 5° grid | 0% | 0% | 1.63% |

The hybrid also drew far-side coastlines along the skyline, 23 pixels for the 5° grid, which
the clip removes. The clip alone, with nothing lowered, leaves a sliver along the skyline: a
coarse surface's edge against the sky sags lower than the base layer's, so the base layer's
outline shows above it, and no bias can move an outline. Lowering the base layer keeps its
outline inside. Refining the 5° surface three times for display brings its sag below the
base layer's own, and then clip and bias with nothing lowered left 0.0008%.

```{figure} figures/2026-11-12-layers-design/skyline-three-layerings.png
:alt: Three views grazing the globe's edge. Left, the hybrid, with no red. Middle, clip and bias with nothing lowered, with a red line along the skyline. Right, the same with the surface refined, with a smooth skyline and no red.
:width: 100%

The skyline, grazing the surface: the hybrid; clip and bias alone; clip and bias with the 5°
surface refined for display.
```

Against the ideal of globe spec §3.5, every clipped layering showed 90.2% of the coastlines in the grazing
view. The ideal counts lines hidden only by a sphere 0.1% smaller, so it also counts 744
pixels of coastline just past the true horizon. Against an ideal clipped at the true horizon
the clipped layerings showed 100%.

(layers-spec-3-4)=
### 3.4 A Warped Base Layer

The base layer was the LFRic C48 orography, warped at an exaggeration of 1, 10 and 50, under
either the C48 SST, on its own mesh, or a 5° surface over the North Atlantic. Lowering it by
1.1 times the sag above, 1,877 m and 12,372 m, was compared with lowering it only beneath the
surface, and with not lowering it. Bleed is terrain inside the surface's footprint; moved is
terrain drawn elsewhere than unlowered:

| Base layer | Bleed, SST / 5° | Terrain moved, SST / 5° |
|---|---|---|
| lowered everywhere | 0.15% / 0.75% | 1,790 / 10,976 px |
| lowered beneath the surface | 0.44%, 6.24% at the Earth's radius / 1.9% | 962 / 158 px |
| not lowered | 1.4%, 32% at the Earth's radius / 99% | none |

Lowering everywhere moves terrain that no surface covers. Refined first, the 5° surface asks
for 174 m, and moves at most 167 pixels of terrain at any exaggeration.

```{figure} figures/2026-11-12-layers-design/terrain-sinks.png
:alt: Three views of Norway's terrain against the sky. Its skyline is a few pixels lower in the middle view, where the base layer is lowered by 12 km.
:width: 100%

Norway's skyline sinks when the base layer is lowered for a 5° surface out of view.
```

(layers-spec-3-5)=
### 3.5 Below Sea Level

An opaque C96 base layer, lowered 1,877 m for a C48 surface over Africa, and a 1° ocean layer
under the North Atlantic, where only the base layer covers it. Seen from outside, any of the
ocean layer that shows has come through the sea surface:

| Ocean layer, drawn this far down | Not lowered | Lowered | Lowered, in a tier below the base |
|---|---|---|---|
| 50 m | 169,950 px | 623,074 px | 1,645 px |
| 500 m | 1,116 px | 623,002 px | 1,243 px |
| 2 km | 0 | 69,400 px | 13 px |
| 50 m, exaggerated 50 times | 0 | 289 px | 0 |

The lowering puts the sea surface beneath the top 1.9 km of ocean. Even unlowered, the base
layer's own sag, 427 m at its cells' middles, lets the top few hundred metres through. Pushed
away in a tier below the base, the ocean layer stays hidden but for its edge at the limb, in
the grazing view, where the lowered base layer's outline is smaller than the ocean layer's.
Pushing it from 256 to 16,384 changed nothing there.

```{figure} figures/2026-11-12-layers-design/subsurface-under-the-base.png
:alt: Three views of the grey sea surface from 1.3 radii. Left, not lowered, all grey. Middle, lowered, almost all magenta: the ocean layer shows through. Right, lowered with the ocean layer in a tier below the base, all grey.
:width: 100%

An ocean layer 500 m down, under the base layer.
```

From inside the Earth, the bias and the clip work against the viewer. Left on, the clip drew
nothing, and the tier bias put the data at sea level in front of an ocean layer between it
and the camera. With all three off, the ocean layer showed.

(layers-spec-3-6)=
### 3.6 Above Sea Level

A regional layer at a height above the base layer, across the horizon, in the views of §3.2,
with a bias of 256. Lost is what depth testing alone shows and the clipped scene does not;
leaked is the reverse:

| Layer height | No clip | Clipped at sea level's horizon | Clipped at the layer's own horizon |
|---|---|---|---|
| 10 km | 737 px leaked | 8,732 px lost | 8 lost, 86 leaked |
| 100 km | 194 leaked | 60,904 lost | 116 lost, 6 leaked |
| 500 km | none | 136,952 lost | 160 lost |

```{figure} figures/2026-11-12-layers-design/clip-above-sea-level.png
:alt: Three views of a layer 100 km up showing as a magenta crescent past the grey globe's limb. The middle view, clipped at sea level's horizon, has a thinner crescent.
:width: 100%

A layer 100 km up, peeking over the horizon: the truth; clipped at sea level's horizon;
clipped at its own.
```

(layers-spec-3-7)=
### 3.7 Tiers, and Stacked Bias

`zorder` and named tiers were each prototyped over one engine and written for three scenes: a
regional surface over a global one, the reverse, and the graticule beneath a translucent
surface with the coastlines above it. Both expressed every scene, and drew them pixel for
pixel alike. Tiers interleave by placing a layer above or below another.

```{figure} figures/2026-11-12-layers-design/tiers-interleaving.png
:alt: Europe on the globe under a translucent blue surface, with the graticule dimmed beneath it and the coastlines crisp in green above it, beside the code that draws it in both styles.
:width: 100%

The graticule beneath a translucent surface, and the code for it in both styles.
```

Each place a layer sits above another adds 256 to its bias. A surface at sea level over the
Amazon, behind the Andes warped 50 times, was drawn at ranks 1 to 50, up to 12,800 units:
from rank 1 on, nothing more changed, and no rank pulled it in front of the mountains.

(layers-spec-3-8)=
### 3.8 On the Web

trame's serializer, which `pyvista` uses to export a scene to `.vtksz` for the documentation's
interactive tab and to render on the client in a notebook, writes a mapper's
`resolveCoincidentTopology` but not its relative polygon and line offsets, which carry the
bias, and has no serializer for clipping planes. An actor's scale and user matrix survive.
vtk.js in trame's viewer supports both the offsets and clipping planes.

A regional 5° surface a place above a global C48 surface, seen close: desktop VTK drew the
regional surface in 601,274 pixels. The browser, from the `.vtksz` as exported, drew it in
3,181, the corners of its cells, the rest lost under the finer surface. With the four calls a
serializer would write patched into the scene file, the browser drew it in 635,938, as the
desktop does. The hybrid's lowering, an actor scale, survived export; the clip did not.

```{figure} figures/2026-11-12-layers-design/bias-lost-on-the-web.png
:alt: Three views of a regional surface in orange over a global one in blue. Left, desktop, orange throughout. Middle, the browser as exported, blue with small orange diamonds at the cell corners. Right, the browser with the bias written back, orange throughout.
:width: 100%

A regional surface on the desktop, in the browser as exported today, and in the browser with
its bias written into the scene.
```

(layers-spec-4)=
## 4. Design

(layers-spec-4-1)=
### 4.1 Tiers

A tier settles which layer shows where two layers meet at one height. It never changes a
height, and it cannot make a layer show through another that lies in front of it. The
built-in tiers, bottom to top:

| Tier | Holds, by default | Kept apart by |
|---|---|---|
| `"subsurface"` | layers given depths, or heights all below sea level | bias, pushed away from the viewer |
| `"base"` | the base layer | lowering (§4.2) |
| `"data"` | `add_mesh` and `add_points` | bias, pulled towards the viewer |
| `"lines"` | coastlines, the graticule, meridians, parallels, geodesic lines and boxes, and any mesh of lines | bias, pulled nearer still |
| `"labels"` | graticule labels and point labels | bias, nearest |

Every method of `GeoPlotter` that adds a layer takes `tier=`, and the base layer's takes none;
the methods it inherits from `pyvista`, such as `add_point_labels`, do not. A method that
draws several actors, as the graticule draws its lines and labels, puts them all in the
tiers it names. Within a tier, layers keep the order they were added. `above=` or `below=`
takes the actor a method returned, of the same tier, and places the layer next to it; an
actor of another tier is refused, since `tier=` names the tier.

`add_tier(name, above=..., below=...)` inserts a tier next to one that exists, and
`GeoPlotter(tiers=[...])` gives the order at once, which must hold `"base"`.
`alias_tier(alias, tier)` gives a tier a second name: an alias of an alias names the same tier, and an alias may
not take the name of a tier. A name that is neither is refused with a `ValueError` naming the
tiers. `GeoPlotter.tiers` returns the order, bottom to top, as a tuple, and
`GeoPlotter.tier_aliases` a read-only mapping of each alias to its tier. A layer's tier is
always reported by its own name.

Each layer has a rank of its own: its place in the order, counting from the base layer,
positive above it and negative below, so two layers never share one. Its bias is its rank
times 256 units, and a layer of `"lines"` takes 4 more, as globe spec §4.5 has it. Layers no
longer share a place, as globe spec §4.5 let them: §3.7 found no harm in many ranks on the
desktop, where the clip removes the far side. On the web, where it cannot, see §4.8.

(layers-spec-4-2)=
### 4.2 On the Globe

The base layer is drawn lowered by 1.1 times the largest sag of the layers in the tiers above
it, as globe spec §4.5 has it, by the scale of its actor. The scale is worked out again when a
layer is added, and the scene renders again. It is a display offset: no coordinate a user
reads back changes. Layers of the tiers below the base never drive it.

Layers above the base are drawn nearer by their bias, and layers below it further away.

(layers-spec-4-3)=
### 4.3 The Horizon Clip

Every layer is clipped at a plane square to the line from the centre of the globe to the
camera, at a distance `x` along that line from the centre. For a layer whose highest point is
at a radius `r`, seen from a distance `d` past a sphere of radius `R`:

```text
x = (R² − √((d² − R²)(r² − R²))) / d
```

Everything beyond the plane lies behind the sphere, in its shadow from the camera, at any
radius up to `r`, so nothing the camera could see is cut. For a layer at sea level, `r = R`
and `x = R²/d`, discussion {issue}`2440`'s plane, and a layer whose highest point is below sea
level takes that plane too. `R` is the globe's render radius. The planes move with the
camera, before each render.

The clip undoes what an opaque globe hides, so it applies only while the scene has an opaque
base layer. A scene with no base layer, or one given an opacity, shows the far side as it
does today, and no layer is clipped.

(layers-spec-4-4)=
### 4.4 Below the Surface

When the camera is closer to the centre than the render radius, the scene draws its layers
with no lowering, no bias and no clip, and depth alone decides. They return when the camera
comes back out. Two layers that meet at one height then fight, which is accepted until
§8 item 5 designs this view.

(layers-spec-4-5)=
### 4.5 On a Map

On a projected map every layer at one height lies in one plane. Layers are kept apart by bias
alone, by rank, pulled nearer above the base and pushed away below it, as globe spec §4.5 has
it. Nothing is lowered and nothing clipped.

(layers-spec-4-6)=
### 4.6 The Lift

The lift is globe spec §4.5's, a display offset for one layer: on the globe a point is drawn
at `s (R (1 + ℓ) + V(h))`, and on a map at `z = V(h) + ℓR`. It is applied to the points of the
copy the scene draws. Scaling the layer's actor would draw it at `s (R + V(h))(1 + ℓ)`,
off by `ℓV(h)`: 2.5 km for a lift of 0.01 over terrain exaggerated 50 times.

(layers-spec-4-7)=
### 4.7 What the Default Handles Less Well

Without refinement, §3 measured these:

- a coarse surface forming the skyline lets the base layer's outline show above it, when
  nothing is lowered;
- a coarse surface over a finer one in the data tier lets the finer one show inside the
  coarse one's footprint at a grazing view, 4,762 pixels for a 5° surface over C48;
- a warped base layer under a coarse surface sinks where nothing covers it, by 12 km for a 5°
  surface;
- a layer in `"subsurface"` shows its edge past the lowered base layer's outline at the limb,
  up to 1,645 pixels;
- the base layer's own sag lets the top few hundred metres of an ocean layer show, unless its
  depths are exaggerated.

Each comes from sag. Refinement for display, the opt-in of row 13 of crs spec §10, shrinks
it: refined, the 5° surface left 12 pixels where it left 4,762, and asked for 174 m of
lowering where it asked for 12,372.

(layers-spec-4-8)=
### 4.8 On the Web

geovista asks trame to write each mapper's relative polygon and line offsets into an exported
scene, by an issue and a pull request of its own upstream. Until that lands, geovista's
documentation build writes them into each `.vtksz` it makes, as §3.8 did, so the interactive
tab draws the tiers as the desktop does. A notebook rendering on the client waits on upstream.

No clip follows the camera on the web, so a layer pulled nearer shows its far side at the
limb in close and grazing views, as §3.2 measured without the clip, and coastlines show past
the skyline, as the hybrid did. Since every layer has a rank of its own, the more layers a
scene has the further the top ones are pulled, and the more they show: 1,427 pixels at 256,
29,624 at 1,024, for a 5° surface. §8 item 2 is the remedy. trame's server-side rendering draws with desktop VTK, and
keeps the clip.

(layers-spec-4-9)=
### 4.9 What This Design Leaves Alone

- **Labels** take the top tier; how they meet depth and the clip is §8 item 1.
- **The view from below the surface** is §8 item 5.
- **A surface below sea level seen past the base layer** is heights spec §8 item 3, owed by
  row 5 of heights spec §9, which lands with row 2 here. Under an opaque base layer the
  subsurface tier keeps such a surface hidden (§3.5). Given an opacity, or left out, the base
  layer lets it be seen: nothing is clipped (§4.3), and its tier keeps it beneath the sea
  surface.
- **Data at sea level over warped terrain** lies beneath the terrain where the terrain rises,
  and a bias of 256 draws it over low ground anyway. Draping is §8 item 3.
- **Picking, clipping planes and interaction at the Earth's render radius** are
  row 10 of globe spec §9.

(layers-spec-5)=
## 5. Alternatives Considered

- **`zorder`.** Rejected, by §2 decision 3. It is familiar, but on the globe a higher order
  cannot override depth, and a matplotlib user would expect it to.
- **Refining every coarse surface by default.** Rejected, by §2 decision 2. It was the best
  measured, 0.0008% bleed with nothing lowered, but invents vertices and interpolates values
  nobody measured, as crs spec §2 decision 8 says.
- **The clip and bias, with nothing lowered.** Rejected, without refinement: a coarse
  surface's skyline lets the base layer show (§3.3).
- **Refinement and a small lowering, with no bias.** Rejected: the gap it leaves is below the
  depth buffer's precision from three radii, and bled 1.3% to 1.7%.
- **One bias for every pair, or one sized by sag, with no clip.** Rejected: the bias a coarse
  surface needs shows its far side (§3.2).
- **Lowering the lower surface by the upper one's sag.** Rejected: a lowered
  layer's smaller outline lets other layers' far sides show past it, 682 pixels for a 5°
  surface.
- **Clipping every layer at sea level's horizon.** Rejected: it cuts what a raised layer shows
  over the horizon (§3.6).
- **Lowering the subsurface tier with the base layer.** Not chosen: it would draw every depth
  1.9 km deeper for a C48 surface above. Refinement fixes the edge it would fix.
- **A lift by the actor's scale.** Rejected, as off by `ℓV(h)` (§4.6).
- **A viewer of geovista's own with a clip that follows the camera, now.** Deferred to
  §8 item 2, by §2 decision 7.

(layers-spec-6)=
## 6. Testing

Globe spec §6 applies. Its layering tests become these, each rendered, carrying the `image`
marker, and comparing classes of pixels, with no baseline image, at a render radius of 1
and of the Earth's radius:

- **bleed**: §3.3's scene, with no bleed over 0.3% in any view for C48, a 1° grid and a 5°
  grid, and none at all for a 5° grid over C48 on Robinson;
- **the far side**: the regional surfaces of §3.2, clipped, show no pixel behind the horizon
  at a bias of 1,024;
- **coastlines**: every coastline pixel of an ideal clipped at the true horizon shows, within
  two pixels;
- **above sea level**: a layer 100 km up loses no more than 200 pixels to the clip, against
  depth testing alone;
- **below sea level**: an ocean layer in `"subsurface"` 500 m down does not show through an
  opaque base layer from outside, except at the limb;
- **below the surface**: with the camera inside the Earth, the lowering, the bias and the clip
  are off, and come back when it leaves;
- **tiers**: the order, `above=` and `below=`, `add_tier`, `GeoPlotter(tiers=...)`, aliases,
  the refusals of §4.1, `GeoPlotter.tiers` and `GeoPlotter.tier_aliases`, and the defaults of
  each method, depths included;
- **the lift**: a lifted point lies at `s (R (1 + ℓ) + V(h))` on the globe and at `V(h) + ℓR`
  on a map, by the formula;
- **the web**: an exported `.vtksz` carries each mapper's offsets, read from its JSON.

The thresholds come from §3's measurements on llvmpipe, and are set once CI's renderer has
drawn each scene.

(layers-spec-7)=
## 7. Scope

In scope: named tiers and their API, the base layer's lowering by its actor, bias by rank,
the horizon clip, the camera below the surface, the map, the lift, and the bias on the web.

Out of scope:

- refinement for display, row 13 of crs spec §10;
- the view from below the surface (§8 item 5);
- a clip on the web (§8 item 2);
- draping data over terrain (§8 item 3);
- removing `zlevel` and `zscale`, row 5 of globe spec §9.

(layers-spec-8)=
## 8. Open Items

Each carries the status grammar of docs spec §3.6.

1. **❓ Open** (🔎 2026-11-14, {pull}`2954` · 🎯 row 2 of §9 · 🎫 {issue}`2949`) — **Labels.**
   Labels take the top tier. Whether a label is clipped with its point, drawn at its point's
   depth, or always shown, was not measured.
2. **❓ Open** (🔎 2026-11-14, {pull}`2954` · 🎯 row 5 of §9 · 🎫 {issue}`2950`) — **A clip on
   the web.** No clip follows the camera in a browser (§4.8). Either geovista's documentation
   ships a viewer with a few lines of vtk.js that move each layer's plane, or trame's viewer
   gains a hook for it upstream.
3. **❓ Open** (🔎 2026-11-14, {pull}`2954` · 🎯 row 6 of §9 · 🎫 {issue}`2951`) — **Data
   draped over terrain.** Data at sea level over a warped base layer lies beneath the terrain
   where it rises, and the bias of its tier draws it over low ground anyway. Draping it, at
   the terrain's heights, is a design of its own.
4. **❓ Open** (🔎 2026-11-14, {pull}`2954` · 🎯 row 7 of §9 · 🎫 {issue}`2952`) — **trame
   drops the bias.** trame's serializer does not write a mapper's relative offsets (§3.8).
   Until upstream does, geovista's documentation build writes them (§4.8), and that interim
   code goes once it does.
5. **❓ Open** (🔎 2026-11-14, {pull}`2954` · 🎯 row 8 of §9 · 🎫 {issue}`2953`) — **The view
   from below the surface.** Below the surface the scene switches its layering off
   (§4.4), so layers that meet at one height fight. An oceanographer inside the ocean,
   looking up or out, needs a layering of its own, with the base layer, the tiers and the
   clip read from inside, which discussion {issue}`2440` first raised.

(layers-spec-9)=
## 9. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | Tiers: the built-in tiers, `tier=`, `above=` and `below=`, `add_tier`, `alias_tier`, `GeoPlotter(tiers=...)`, `GeoPlotter.tiers` and `GeoPlotter.tier_aliases`, the defaults of each method, the refusals, and the bias by rank on a map | 📋 not started |
| 2 | The globe: the bias by rank, the base layer lowered by its actor, the horizon clip of each layer following the camera, the camera below the surface, labels (§8 item 1), and §3's measures as tests | 📋 not started |
| 3 | The lift, on the globe and on a map | 📋 not started |
| 4 | The web: the bias written into each `.vtksz` of the documentation build, and the issue and pull request upstream | 📋 not started |
| 5 | A clip on the web | 💡 candidate: trame's viewer offers a hook, or geovista ships a viewer |
| 6 | Data draped over terrain | 💡 candidate: a user asks for it, which no check can observe |
| 7 | The interim bias of row 4 removed | 💡 candidate: trame writes the bias |
| 8 | The view from below the surface | 💡 candidate: a scientist shows a scene from below the surface |

Statuses follow docs spec §3.6. Rows 1 to 4 come in order, each planned once the rows before it
have landed, and together they are row 4 of globe spec §9, which lands with row 4 here. Row 1
brings the bias to the map alone: on the globe it arrives in row 2 with the clip, so that no
release pulls the far side into view. Row 5 of heights spec §9 lands with row 2. Row 2 needs
a renderer in CI, which the image tests already have.

Each row sets to 0 the built-in offset that its own mechanism replaces: row 1 the coastlines'
lift on a map, and row 2 the base layer's and the lines' z-levels on the globe, so that no
layer is offset twice. A `zlevel` that a user gives keeps its meaning until
row 5 of globe spec §9 removes it, and the lift of row 3 refuses one other than 0.

(layers-spec-10)=
## 10. References

- The globe, heights and layers design: globe spec §3.5, globe spec §4.5, globe spec §6 and
  row 4 of globe spec §9.
- crs spec §2 decision 8, and row 13 of crs spec §10.
- Heights spec §8 item 3, and row 5 of heights spec §9, which lands with row 2 here.
- Discussion {issue}`2440`, the horizon clip.
- trame's serializer, `trame_vtk/modules/vtk/serializers/mappers.py`, and vtk.js's mapper.

(layers-spec-11)=
## 11. Verification

Each row follows ledger spec §3.4.

| Decision | Status | Evidence |
|---|---|---|
| §2 decision 1 | ⏳ pending | row 2 of §9 |
| §2 decision 2 | ⏳ pending | row 2 of §9 |
| §2 decision 3 | ⏳ pending | row 1 of §9 |
| §2 decision 4 | ⏳ pending | row 1 of §9 |
| §2 decision 5 | ⏳ pending | row 2 of §9 |
| §2 decision 6 | ⏳ pending | rows 1 to 2 of §9 |
| §2 decision 7 | ⏳ pending | row 4 of §9 |
