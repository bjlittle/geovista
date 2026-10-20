# geovista type coverage — design specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. From change 1 of {ref}`§4 <typing-spec-4>` onward, `.pre-commit-config.yaml`,
> `.github/workflows/ci-typing.yml` and the `[tool.mypy]` block of `pyproject.toml` cite it
> by section — `typing spec §3.2` and the like — so these sections carry the reasoning
> behind what those files do, and where the two ever diverge it is the specification that
> gets corrected. Read it as current; the roadmap states what has actually landed.

- **Date:** 2026-10-06 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `typing spec §…` — not `mypy spec`, which would read as covering the
  tool rather than the coverage it is bought to provide
- **Scope:** where `geovista` runs `mypy`, what it is allowed not to check yet, and the
  order in which that allowance is withdrawn; the strictness settings themselves stay as
  they are
- **Parent spec:** none, but not unconventioned. It was the first specification in this
  repository and so inherited nothing; the conventions it arrived at are now written down,
  and governed, by {ref}`docs spec §1 <docs-spec-1>`
- **Published:** in the specifications index, since change 1 of
  {ref}`docs spec §4 <docs-spec-4>` took off the `orphan: true` it carried while nothing
  listed it

(typing-spec-1)=
## 1. Purpose

`geovista` has run `mypy` in strict mode since the configuration was written, and that
check has never seen a third-party type. The `pre-commit` hook is `mirrors-mypy`, whose
isolated virtual environment installs `mypy` and nothing else, so every import from
`pyvista`, `numpy`, `pyproj` and the rest resolves to `Any`. A check against `Any`
succeeds against anything.

The size of what it misses was measured on 2026-10-06, by running the same configuration
inside the `geovista` pixi environment where the real types are present:

| | errors | distinct source lines |
|---|---|---|
| `src/geovista` excluding `examples/` | 492 | 186, across 22 of 25 modules |
| `src/geovista/examples/` | 150 | 142 |
| **total** | **642** | **328** |

The error count overstates the defect count. `mypy` reports an attribute access on a union
once per member, and `numpy.typing.ArrayLike` is a seven-member union, so one line can
raise seven errors. Counting distinct source lines instead, and setting aside the errors
suppressed by {ref}`§3.4 <typing-spec-3-4>`, the work is **206 lines**.

Three of the twenty-five library modules report nothing, and none of the three is much of
a check: `mypy` reads `__init__.pyi` in place of `__init__.py`, `_version.py` is generated
by `setuptools-scm`, and `__main__.py` is nineteen lines. The check that was supposed to be
guarding the other twenty-two has been reporting success throughout.

(typing-spec-2)=
## 2. Decisions

- **The authoritative check runs against the locked environment, never a second copy of
  it.** `additional_dependencies` on a `mirrors-mypy` hook would mean maintaining a list
  of `geovista`'s dependencies that `pixi` neither reads nor updates. That list demonstrably
  diverges: a probe carrying the eight typed core distributions saw 602 errors where the
  pixi environment saw 642, because the hook's virtual environment has none of the optional
  dependencies that `rasterio`, `h3`, `pandas` and `pyvistaqt` are imported from. The
  divergence is silent and no test can detect it. See {ref}`§3.1 <typing-spec-3-1>`.
- **The hook goes live before the errors are fixed, not after.** Twenty-two modules cannot
  be corrected in one reviewable change, and a check that stays blind until the last of
  them lands guards nothing in the meantime. A per-module ratchet makes the debt explicit
  and lets each module be retired on its own. See {ref}`§3.2 <typing-spec-3-2>`.
- **An annotation that over-promises is corrected by honouring it, not by narrowing it.**
  `to_cartesian(lons: ArrayLike, ...)` reaches straight for `lons.shape`, so a caller who
  reads the signature and the docstring and passes a list gets `AttributeError`. Converting
  at the boundary makes the published contract true and cannot break an existing caller.
  See {ref}`§3.3 <typing-spec-3-3>`.
- **A defect a gallery script cannot fix is suppressed in the configuration, never worked
  around in the script.** The gallery is rendered into the documentation and readers are
  invited to copy it, so a `type: ignore` comment in one is a directive published as
  example code. The suppression then has to name its real cause, or nobody will know when
  it can go. See {ref}`§3.4 <typing-spec-3-4>`.

(typing-spec-3)=
## 3. Architecture

(typing-spec-3-1)=
### 3.1 Where the check runs

The `mirrors-mypy` hook is replaced by a `local` hook that invokes the pixi environment's
own `mypy`:

```yaml
ci:
  skip: [mypy]

- repo: local
  hooks:
    - id: mypy
      name: mypy
      entry: pixi run --frozen -e geovista mypy
      language: system
      pass_filenames: false
      types: [python]
```

`--frozen` resolves strictly from `pixi.lock`, so the hook checks against exactly the
environment CI installs. Measured on 2026-10-06, this runs in 17 seconds against the 93
seconds the `mirrors-mypy` virtual environment took to build, and reports all 642 errors
rather than 602.

`pre-commit.ci` has no `pixi`, so the hook is listed under `ci.skip`. The coverage it would
have provided moves to `.github/workflows/ci-typing.yml`, which runs the identical command.
This follows `pyvista`, which runs `mypy` as a dedicated workflow and carries no `mypy`
hook at all; `geovista` keeps the hook as well, because this repository gates commits with
hooks rather than deferring to CI.

All three existing `[[tool.mypy.overrides]]` blocks are kept, and one of the three is
narrowed. Measured on 2026-10-06, removing all three raises the total from 642 to 648.
`disallow_untyped_decorators` stays on `geovista.cli` unchanged: `click` ships `py.typed`,
but `main.command` is an untyped decorator and three commands depend on it. The `union-attr`
suppression on `geovista.examples.grid.*` is unchanged too; it predates this spec.
`disallow_subclassing_any` is the one that narrows. It stays on `geovista.qt`, where
`pyvistaqt` is absent from the locked environment altogether, so its three base classes are
`Any`, but it is redundant for `geovista.geoplotter` and `geovista.report`, which report an
identical 36 and 5 errors either way, so those two names come off its `module` list.

(typing-spec-3-2)=
### 3.2 The ratchet

The twenty-two modules carrying errors are listed once with `ignore_errors`, alongside the
gallery. With the library ignored and the {ref}`§3.4 <typing-spec-3-4>` suppression
applied, `examples/` still reports 28 errors — 8 `import-untyped` and the 20 lines change 7
corrects — so `geovista.examples.*` joins the ratchet as a twenty-third entry and leaves
with change 7.

```toml
[[tool.mypy.overrides]]
# typing spec §3.2 -- the ratchet. This list only ever shrinks, and
# "tests/test_typing_ratchet.py" holds it to that. Delete the whole
# block, and that test, when the last entry goes.
ignore_errors = true
module = [
  "geovista.bridge",
  "geovista.common",
  # the remaining twenty
  "geovista.examples.*",
]
```

From that point the check is live for every module added afterwards, the three that report
nothing today having little in them to check. Each subsequent change deletes one entry and
fixes what it exposes.

A ratchet with nothing holding it becomes a dumping ground, so the list is mirrored in a
test that permits removals and refuses additions:

```python
RATCHET_BASELINE = frozenset({"geovista.bridge", "geovista.common", ...})


def test_ratchet_only_shrinks():
    added, retired = _drift(_ignored(), RATCHET_BASELINE)
    assert not added, f"added to the typing ratchet: {sorted(added)}"
    assert not retired, f"no longer ignored: {sorted(retired)} -- update the baseline"
```

The second assertion is what keeps the first one honest. A baseline that names are only
ever checked *against* is a high-water mark, and it keeps the name a retirement took out:
a later change can then put that module back under `ignore_errors` and the test still
passes, handing back the coverage the retiring change won with nothing in the diff to
catch it. Holding the two level costs a line per retirement, and makes re-entry an
addition to a list documented as only ever shrinking, in front of a reviewer watching it
grow.

The same reasoning governs how the test reads `ci-typing.yml`. The workflow matters only
because `pre-commit.ci` skips `mypy` on the understanding that it runs there instead, so
the test requires the hook's `entry` to be the last command of a step carrying neither
`if` nor `continue-on-error`. Searching the script for the command as a substring would
accept `echo`-ing it, commenting it out, or appending `|| true`. Requiring it *last*
covers the job's `bash -l {0}`, which drops the `-e` that GitHub's default shell carries,
so a command with anything after it can fail while the step succeeds.

This follows `tests/test_python_support.py`, which encodes a convention as a test rather
than trusting it to review, and reads `pyproject.toml` as text so that it needs neither a
built artefact nor a network.

(typing-spec-3-3)=
### 3.3 The ArrayLike contract

295 of the 492 library errors, spread over 61 lines, are one idiom. A parameter is annotated
`ArrayLike`, which is correct for a public boundary, and the body then treats it as an
`ndarray`:

```python
def to_cartesian(
    lons: ArrayLike,
    lats: ArrayLike,
    *,
    radius: float | None = None,
    # further keyword-only arguments elided
) -> np.ndarray:
    # 143 lines further on, with no conversion anywhere in between
    if lons.shape != lats.shape:
        msg = "'lons' and 'lats' do not have same shape."
        raise ValueError(msg)
```

`ArrayLike` admits `str`, `bytes`, `complex` and nested sequences, none of which carry
`.shape`. The annotation and the docstring both say `array_like`; the implementation
requires rather more, and a caller who believes them raises `AttributeError` at runtime
today. The signature is not wrong about what the function should accept — the body is wrong
about what it does accept.

The correction converts at the boundary:

```python
lons, lats = np.asanyarray(lons), np.asanyarray(lats)
```

Docstrings are unchanged, because they already promise `array_like`. Behaviour widens
only, so no existing caller can break, and `np.asanyarray` returns its argument unchanged
when handed an array, so the hot paths are unaffected.

Those 61 lines sit in eight modules, and two of them hold most of it — `transform.py` has
20 and `bridge.py` 19, which is roughly two-thirds of each module's errors. `geodesic.py`
has 7, `common.py` 6, `geoplotter.py` 4, and `pantry/meshes.py`, `search.py` and
`pantry/data.py` the remaining 5 between them. The roadmap of
{ref}`§4 <typing-spec-4>` is ordered to follow that concentration, so the idiom is
established in the first two changes and applied by rote afterwards. Change 2 found,
though, that only one of `transform.py`'s 20 lines needed the conversion.

The conversion narrows only where `mypy` can see `numpy`. A module that loads it lazily,
with `np = lazy.load("numpy")`, hands `mypy` an `Any`, and assigning an `Any` never
narrows an `ArrayLike` parameter, so the module must also import `numpy` under
`TYPE_CHECKING`, as `common.py` does. Change 2 measured this on `transform.py`, which
already converted with `np.atleast_1d` and still reported the idiom: importing `numpy` and
`pyproj` that way cleared 15 of its 20 lines on its own. Four of the other five came from
the return annotations of `transform_points` and `combine`, which promised `ArrayLike` for
an `ndarray`, and the fifth was `zlevel`. `core.py`, `crs.py`, `filters.py`,
`geoplotter.py`, `gridlines.py`, `raster.py`, `pantry/data.py` and `pantry/meshes.py`
still load `numpy` without one.

The rule governs published signatures. Once change 2 had landed, the `ArrayLike` idiom was
left on 13 of `bridge.py`'s lines. One conversion, at the top of `Transform.from_points`,
cleared two of them along with a genuine `AttributeError`. The other eleven sat in private
helpers that only ever receive what a boundary has converted, `_verify_2d` and the
`_contiguous` nested in `_as_contiguous_1d`, so change 3 annotates them with the `ndarray`
they receive. The API reference publishes no private members.

Change 4 found the idiom on eight of `common.py`'s lines, not the six counted above, all in
two public functions and both real bugs. `vectors_to_cartesian` read `.shape` from points
and vector components it never converted, so lists raised `AttributeError`, and `nan_mask`
handed a list back unchanged where it promises an array. Both now convert at the boundary.
`nan_mask` converts a list with `np.ma.asanyarray`, because `np.asanyarray` drops the mask
of any masked array the list holds, and any function that handles masked data needs the
same care.

Change 4 also met a pattern this rule does not cover: a runtime type check on an annotated
parameter. `mypy` reports the check's body unreachable, because the annotation says the
check can never fail. The parameter is annotated instead with the type the function
accepts before it validates, `pv.DataSet` for `cast_UnstructuredGrid_to_PolyData`, which
keeps the check reachable without a `type: ignore`. That check was broken as well, and
raised `AttributeError` where it meant `TypeError`.

The review of change 4 also found an annotation narrower than its docstring. `wrap`
documents any NumPy data-type for `dtype` but was annotated `np.dtype | None`, so `mypy`
refused `np.float32` and `"f4"`, and change 4 had altered the function's default to fit that
annotation. {pull}`2616` widened the annotation to `DTypeLike` instead, for the reason
{ref}`§5 <typing-spec-5>` gives against tightening a published contract to match an
implementation. {issue}`2614` tracked it.

Change 5 found the idiom where `mypy` could not see it. `geoplotter.py` loaded `numpy` and
`pyproj` with `lazy.load` and imported neither under `TYPE_CHECKING`, so both were `Any`
and the module reported 15 lines where it had 16. `_add_graticule_labels` indexed
`GraticuleGrid.lonlat` as an array, so a list raised `TypeError`, and multiplied its
`mask` by `REMESH_SEAM`, which is −1, so a list mask became empty and raised `ValueError`;
both now convert where they are used. `npoints_by_idx` converts its points too. `BBox`
called it 259 times with lists that grow to tens of thousands of points, though, and
converting them on every call made `BBox` ten times slower. `BBox` now indexes its own lists and calls `npoints` directly: a private
caller on a hot path can step past a converting boundary instead of paying for it.

Change 6b met change 4's runtime check twice more, in `core.py`. `combine` and
`slice_cells` check for the `pv.PolyData` they were annotated to receive, so both now take
a `pv.DataSet`. `combine` handed a single mesh back before its check, so
`combine(pv.ImageData(...))` returned an `ImageData` from a function annotated to return
`PolyData`. It now raises `TypeError`, as it does for any other mesh it can't combine.
`find_nearest_cell` documents `z` as optional and zero by default, and accepted `None`,
which VTK refused with `TypeError` on a projected mesh. `None` now means zero.

(typing-spec-3-4)=
### 3.4 Gallery suppressions

122 of the 150 errors in `examples/` are two defects, measured on 2026-10-06 against
`pyvista` 0.49.0 with the override below lifted. Their causes differ, and this section got
the second one wrong twice before it was measured; {ref}`§8 <typing-spec-8>` records both
corrections:

- 77 × `call-arg`, *Missing positional argument "self" in call to "__call__" of
  "_Wrapped"*, raised on no-argument calls such as `p.view_xy()`. `pyvista`'s `_Wrapped`
  decorator loses the descriptor protocol in its annotations. This one is upstream. It
  is `pyvista` issue 6589, open since 2024, and is fixed on `main` by `pyvista` pull
  request 9162, merged the day after 0.49.0 was released. Checked against a clone of
  that `main`, the count is 0. Tracked by {issue}`2568`.
- 45 × `attr-defined`, *pv.Plotter.camera? has no attribute "zoom"*, 44 of them on `zoom`
  and one on `roll`. This one is ours, and it is one line. `GeoPlotterBase.view_poi`
  declares `self.camera: pv.Plotter.camera`, naming a property where a type belongs.
  `mypy` cannot bind it, so the attribute keeps the unbound type it prints as
  `pv.Plotter.camera?`, and since `GeoPlotterBase` precedes `pv.Plotter` among
  `GeoPlotter`'s bases, that declaration shadows `pyvista`'s own `camera` and every access
  through it fails. `geoplotter.py` is in the ratchet, so the annotation is never reported
  where it is written, only where it does damage. Change 5 removed the declaration
  ({ref}`§3.5 <typing-spec-3-5>`). All 45 cleared, and 44 `no-untyped-call` took their
  place, because `Camera.zoom` has no annotations in 0.49.0. That residue is upstream, and
  `pyvista` `main` already annotates it. Tracked by {issue}`2569`.

Both are disabled for the gallery alone, which leaves its genuine errors visible, 35 of
them after change 5:

```toml
[[tool.mypy.overrides]]
# typing spec §3.4 -- two "pyvista" 0.49 defects, both fixed on its "main":
# "_Wrapped" loses the descriptor protocol, and "Camera.zoom" carries no
# annotations. Confined to the gallery, whose scripts are published as
# example code, so a "type: ignore" comment in one is a directive a reader
# is invited to copy. Withdraw when the "pyvista" floor carries both fixes.
disable_error_code = ["call-arg", "no-untyped-call"]
module = ["geovista.examples.*"]
```

The comment is quoted as it stands in `pyproject.toml`, because a specification that
quotes the code has to quote what the code says. Both codes now name upstream defects
fixed on `pyvista` `main`, so the override goes when the floor reaches the release that
carries them ({issue}`2568`). Change 5 also adds seven errors in `uber_h3.py`, which keeps
the plotter's actors in fields typed `str | PolyData`. They appeared once `add_mesh`
admitted it can return `None`, and change 7 corrects them with the rest of the gallery.

In the library, measured on 2026-10-11 with the whole ratchet lifted, `attr-defined` is
zero, `call-arg` is one, in `cli.py`, and `no-untyped-call` is four, in `raster.py` and
`themes.py`, all in modules change 6 retires, so the suppression stays confined to where
the plotting calls are. This extends a pattern already
in `pyproject.toml`, where `union-attr` is disabled for `geovista.examples.grid.*` on
account of `geopy` being untyped.

(typing-spec-3-5)=
### 3.5 Where geovista departs from pyvista

`GeoPlotterBase` is a mixin. `GeoPlotter` combines it with `pyvista`'s `Plotter`, and
`geovista.qt` with `pyvistaqt`'s `QtInteractor` and `BackgroundPlotter`, both plotters
too, and with its `MultiPlotter`, which is not ({issue}`2622`). `mypy` had no way to know
any of that. So the
mixin declared what it borrowed: `Callable[..., None]` for `add_text`, `add_point_labels`
and `reset_camera`, `Theme` for `theme`, and for `camera` an annotation that isn't a type
({ref}`§3.4 <typing-spec-3-4>`). Each one clashed with `pyvista`'s own definition. Change 5
gives the mixin `pv.BasePlotter` as its base under `TYPE_CHECKING`, and `object` at
runtime. The declarations go, and so do the three `type: ignore` comments they needed.

What remains is deliberate. `add_mesh` and `add_points` take the mesh or the points
positionally and everything else by keyword, where `pyvista` accepts a long run of
positional arguments, and `add_mesh` adds nothing for an empty mesh and returns `None`.
Matching `pyvista` would change `geovista`'s public API, so both `def` lines carry
`# type: ignore[override]`, citing this section. `add_mesh`, `add_points`,
`add_base_layer` and `add_coastlines`, which return what `add_mesh` returns, are annotated
`pv.Actor | None`. Change 5 removes three `type: ignore` comments from the library and adds
these two, leaving nine.

(typing-spec-4)=
## 4. Roadmap

| # | Scope | Lines | Status |
|---|---|---|---|
| 1 | The `local` hook, `ci-typing.yml`, the ratchet and its test | 0 | ✅ landed (2026-10-06, {pull}`2565`) |
| 2 | `transform.py` | 29 | ✅ landed (2026-10-08, {pull}`2580`) |
| 3 | `bridge.py` | 28 | ✅ landed (2026-10-09, {pull}`2599`) |
| 4 | `common.py` | 20 | ✅ landed (2026-10-10, {pull}`2612`) |
| 5 | `geoplotter.py`, `geodesic.py` | 38 | ✅ landed (2026-10-11, {pull}`2619`) |
| 6a | The untyped imports, and `cache`, `cli`, `config`, `geometry`, `qt` | 11 | ✅ landed (2026-10-11, {pull}`2631`) |
| 6b | `core`, `search`, `filters`, `gridlines`, `crs` | 38 | not started |
| 6c | `pantry` and its three modules, `raster`, `report`, `themes` | 19 | not started |
| 7 | `examples/`, its ratchet entry, and the ratchet retired | 20 | not started |

Row 6, the seventeen library modules left in the ratchet, was split into three pull
requests ({user}`bjlittle`, 2026-10-11). Its count of 51 does not reproduce. Lifted at the
census commit, the seventeen report 71 lines, and on `main` before 6a, 53. Ten of them load
`numpy` or `pyvista` lazily without importing it under `TYPE_CHECKING`
({ref}`§3.3 <typing-spec-3-3>`), and with those imports the 53 becomes 68. Each row counts
the lines its change clears from that 68, so 6a's 11 includes three untyped imports in
`pantry/data.py`.

Statuses follow {ref}`docs spec §3.6 <docs-spec-3-6>`: a landed row names the date and the
pull request that landed it. This is a living document, so a change that measures something
the design assumed edits the design in place, and the sentence that was there before
survives nowhere else. Change 1 rewrote the entry count of {ref}`§3.2 <typing-spec-3-2>`
and the override claim of {ref}`§3.1 <typing-spec-3-1>`; the row is what makes {pull}`2565`
reachable from the sections it corrected, so a reader who wants the measurement rather than
the conclusion has somewhere to go.

Each change carries a towncrier fragment and the `agentic` label. Changes 2 to 4 alter
published signatures and each adds tests exercising the widened input.

(typing-spec-5)=
## 5. Alternatives considered

- **`additional_dependencies` on the `mirrors-mypy` hook.** The route `tephpy` takes, and
  the one this work began with. Self-contained and runs unchanged on `pre-commit.ci`. It is
  rejected on the measurement in {ref}`§2 <typing-spec-2>`: the second dependency list is
  unlocked, hand-maintained, and already 40 errors adrift.
- **A CI job alone, with no hook.** `pyvista`'s arrangement exactly. Rejected because this
  repository's practice is that hooks gate commits, and a type error found only after
  pushing is found a cycle too late.
- **Narrowing the `ArrayLike` annotations instead of converting.** A smaller change with no
  runtime effect. Rejected because it tightens a published contract to match an
  implementation shortfall, and leaves the documented `array_like` promise to be reworded
  across every affected docstring.
- **One change for all 206 lines.** Atomic, with no interim configuration. Rejected as a
  25-file review spanning public signatures, internals and gallery scripts, where a problem
  in any one module blocks the rest.

(typing-spec-6)=
## 6. Testing

`tests/test_typing_ratchet.py` holds the ratchet to {ref}`§3.2 <typing-spec-3-2>`, failing
when a module is added to the ignore list and passing when one is removed. It is deleted
with the last entry.

Changes 2 to 4 of the roadmap each add tests passing lists where arrays were passed before,
so that the widened contract of {ref}`§3.3 <typing-spec-3-3>` is exercised rather than
merely annotated.

The check itself is verified by `ci-typing.yml`, which fails the pull request on any error
outside the ratchet.

(typing-spec-7)=
## 7. Scope

Out of scope:

- **The strictness settings.** `strict`, `warn_unreachable` and the three
  `enable_error_code` entries stay as they are. This work makes the existing settings
  effective; it does not add to them.
- **`tests/` and `docs/`.** `files` names `src/geovista` alone, and widening it is a
  separate decision with its own error budget.
- **Chasing the `pyvista` fix into a release.** The `call-arg` defect is already reported
  and already fixed on `main`, as are the missing `Camera.zoom` annotations, so what
  remains is a version floor, tracked by {issue}`2568`. It does not gate any of the
  roadmap.
- **The untyped imports.** 32 errors are imports rather than code: 29 `import-untyped` from
  distributions that ship no annotations — `lazy_loader` alone accounts for 19, then
  `geopy`, `rasterio` and `shapely` 2 each, and one each from `click_default_group`,
  `fastparquet`, `pandas` and `pooch` — plus 3 `import-not-found`. The gallery adds
  `cmocean`, `cartopy` and `h3` on top, which is why the figure here is smaller than a
  count taken over the whole tree. Two of the three not-found, `geovistaconfig` and
  `geovista.siteconfig`, are the optional site configuration and are *meant* to be absent,
  so they want a targeted `ignore_missing_imports` rather than a fix. The configuration
  carries none for them yet. Change 2 cleared `lazy_loader`'s 19 early, with the override
  of {ref}`§8 <typing-spec-8>` item 5, because the first module to leave the ratchet
  imports it. Change 3 cleared `rasterio`'s 2 with typeshed's `types-rasterio`, not an
  override: `rasterio` ships no `py.typed`, but typeshed has carried stubs for it since
  June 2026, and against them `from_tiff` reported eleven lines of its own. conda-forge
  also carries `types-shapely`, `pandas-stubs` and `types-click-default-group`, and nothing
  for `geopy` or `pooch`. Change 6a took the three stub packages into the `devs` feature,
  and they revealed two errors in `geometry.py`. `pooch`, `geopy` and `fastparquet` ship no
  annotations and have no stubs, so one override covers them until they do
  ({ref}`§8 <typing-spec-8>` item 9). The two site configurations share a second with
  `pyvistaqt`, which ships `py.typed` but is in no locked environment ({issue}`2630`).

(typing-spec-8)=
## 8. Open items

Each carries the status grammar of {ref}`docs spec §3.6 <docs-spec-3-6>`.

1. **Resolved** (2026-10-06, {issue}`2568` and {issue}`2569`) — **Are the
   {ref}`§3.4 <typing-spec-3-4>` defects reported upstream?** This item asserted that
   neither was, and raising the issues to track them showed both halves of that wrong.
   One defect was reported in 2024 and has been fixed on `pyvista` `main` since September
   2026. The other is not upstream at all. Each now has its own trigger and its own
   issue, below.
2. **Open** ({issue}`2568`) — **The `call-arg` suppression will outlive its cause.**
   `pyvista` pull request 9162 fixes it, and the pin in `pyproject.toml` is
   `>=0.48.0,<0.50.0`, so what matters is the floor rather than the ceiling. Withdraw
   that half of the override when the floor reaches the release carrying the fix.
3. **Resolved** (2026-10-11, {pull}`2619`) — **The
   `attr-defined` suppression hid a bug of ours.** It is labelled upstream in
   `pyproject.toml`, and the cause is one annotation in `geoplotter.py`, described in
   {ref}`§3.4 <typing-spec-3-4>`. Until it is corrected, 45 errors in the gallery sit
   under a comment that sends the next reader to the wrong repository. This item and
   {ref}`§3.4 <typing-spec-3-4>` first blamed `lazy.load`, on the theory that `mypy`
   could not see a base class loaded at runtime, and so did {issue}`2569` as first
   written. Checking that premise on 2026-10-07, before taking item 4 upstream,
   disproved it. `geoplotter.py` imports `pyvista` under `TYPE_CHECKING` as well, which
   is what `mypy` reads, and the 77 `call-arg` errors of item 2 are raised on methods
   `GeoPlotter` inherits, which could not happen if its base were unresolved. The
   unbound type in the message, `pv.Plotter.camera?`, is the annotation's own text. The
   same check found that {ref}`§3.4 <typing-spec-3-4>` had been showing a one-line
   paraphrase of the override's comment while saying it quoted it; it now quotes
   `pyproject.toml` verbatim. Change 5 removed the annotation and swapped `attr-defined`
   for `no-untyped-call` in the override, whose comment now names its real causes.
4. **Resolved** (2026-10-07,
   [`lazy-loader` issue 181](https://github.com/scientific-python/lazy-loader/issues/181))
   — **Whether to pursue `lazy_loader` upstream.** Yes, after measuring. It is 19 of the
   29 untyped imports, one for each of the 20 library modules that import it except
   `__init__.py`, which `mypy` reads through `__init__.pyi` instead. With a typed copy on
   `mypy_path` and the library checked under `--strict`, a bare `py.typed` marker turns
   those 19 into 42 `no-untyped-call`, one at every `lazy.load`, the way `Camera.zoom`
   behaves in {ref}`§3.4 <typing-spec-3-4>`. The marker together with annotations on
   `load` and `attach` and a return type on `attach_stub` clears all 19 and leaves every
   other error unchanged, line for line, so the request asks for both and offers a
   follow-up pull request. A maintainer's advice there, in its issue 165, is to keep
   using `lazy_loader` until Python 3.15 is the floor and then move to the `lazy import`
   of PEP 810. This item argued until 2026-10-07 that it was also the root of item 3; it
   is not, which left the import count as the whole case.
5. **Open** ({issue}`2570`) — **The `lazy_loader` override comes out when upstream
   allows.** The `ignore_missing_imports` override for `lazy_loader` clears all 19
   locally. It was meant for change 6, and change 2 brought it in, because `transform.py`
   imports `lazy_loader`, as most library modules do, and could not leave the ratchet
   without it. It comes out when the floor reaches a release carrying the marker, or when
   PEP 810 replaces `lazy_loader`, whichever is first.
6. **Open** ({issue}`2568`) — **The cast in `transform_mesh`, and a typed local in
   `core.py`, wait on the same `pyvista` release.** `pyvista` 0.49 annotates
   `pyvista_ndarray.__setitem__` with `key: int | NumpyArray[int]`, which refuses the
   tuple index of `mesh.points[:, 0]` that it accepts at runtime, so change 2 sets the
   points through a `typing.cast`. The annotation refuses a slice key in the same way, so
   change 6b types the ids that `_keep_roles` assigns through one as any array.
   `pyvista` pull request 9262 widens the key, merged on 2026-09-23 after 0.49.0, so the
   cast and the local come out with the floor that carries it, the trigger item 2 already
   waits on.
7. **Open** ({issue}`2601`) — **The cast in `from_tiff` waits on typeshed.**
   `types-rasterio` types the rows and columns of `rasterio.transform.xy` as
   `int | Sequence[int]`. `rasterio` takes arrays, which is what `Transform.from_tiff`
   passes, so change 3 passes them through a `typing.cast`. It comes out when the stubs
   accept arrays. The report to typeshed covers two other gaps as well, which the code
   handles without a cast.
8. **Open** ({issue}`2568`) — **Three typed locals wait on the same
   `pyvista` release.** `pyvista` 0.49 leaves `GPUInfo.__init__` unannotated, and its
   `_Wrapped` decorator, item 2's cause, breaks `self.reset_camera(render=False)`. So
   `_warn_opacity` and `view_poi` call each through a local annotated `Callable`.
   Change 6a added the third, for `p.add_axes()` in the `plot` command of `cli.py`.
   `pyvista` `main` fixes both defects, and the three locals come out with the floor
   that carries them, the trigger items 2 and 6 already wait on.
9. **Open** ({issue}`2629`) — **Three dependencies ship no annotations.** The latest
   releases of `pooch` (1.9.0), `geopy` (2.5.0) and `fastparquet` (2026.9.0; the lock has
   2026.5.0) carry no `py.typed` and have no stubs on conda-forge or in typeshed, so one
   `ignore_missing_imports` override makes each import `Any`. Only `pooch`'s entry is live
   so far: `geopy` and `fastparquet` are imported only by `pantry/data.py`, which leaves
   the ratchet in change 6c. Each name comes out when its distribution or a stub
   package types it. `pooch` has an open upstream issue asking for annotations.
10. **Open** ({issue}`2568`) — **Four typed locals wait on the same `pyvista` release.**
    `pyvista` 0.49 types its arrays with Python's `int`, `bool` and `float` as the dtype.
    `numpy.float64` subclasses `float`, so a float array passes into `pyvista`, but
    `numpy.intp` and `numpy.bool` subclass neither `int` nor `bool`, so `extract_cells`
    refuses every real mask or index array. For the same reason, numpy's own methods
    refuse arrays that `pyvista` hands back: `+=` on a mesh's faces, and `min` on a
    cell's points. Change 6b types the two masks in `filters.remesh`, the faces in
    `core.combine` and the points in `core.slice_cells` as any array. `pyvista` pull
    requests 9344 and 9351 replace the annotations. Both merged on 2026-09-29, after the
    0.49 release branch was cut on 2026-09-07, so 0.49.1 doesn't carry them, and the
    locals come out with the floor that does, the trigger items 2, 6 and 8 wait on.

(typing-spec-9)=
## 9. References

- `pyvista`'s `type-checking.yml` workflow, the precedent for {ref}`§3.1 <typing-spec-3-1>`:
  <https://github.com/pyvista/pyvista/blob/main/.github/workflows/type-checking.yml>
- `mypy`'s `python_version`, pinned to the support floor by {pull}`2563`, and the
  `tests/test_python_support.py` convention this specification's ratchet test follows
- `mypy` issue 13916, the reason the hook passes no filenames:
  <https://github.com/python/mypy/issues/13916>
- `pyvista` issue 6589 and pull request 9162, the report and the fix for the `call-arg`
  half of {ref}`§3.4 <typing-spec-3-4>`:
  <https://github.com/pyvista/pyvista/issues/6589> and
  <https://github.com/pyvista/pyvista/pull/9162>
- `pyvista` pull request 9262, which widens the index `pyvista_ndarray.__setitem__`
  accepts, cited by item 6 of {ref}`§8 <typing-spec-8>`:
  <https://github.com/pyvista/pyvista/pull/9262>
- `pyvista` pull requests 9344 and 9351, which replace the array aliases that item 10 of
  {ref}`§8 <typing-spec-8>` waits on:
  <https://github.com/pyvista/pyvista/pull/9344> and
  <https://github.com/pyvista/pyvista/pull/9351>
- `lazy_loader` issue 165, on its relation to PEP 810, cited by item 4 of
  {ref}`§8 <typing-spec-8>`: <https://github.com/scientific-python/lazy-loader/issues/165>
- `lazy_loader` issue 181, the request for a marker and annotations that resolves item 4
  of {ref}`§8 <typing-spec-8>`: <https://github.com/scientific-python/lazy-loader/issues/181>
- `typeshed` pull request 15884, which added the `rasterio` stubs that change 3 checks
  `bridge.py` against: <https://github.com/python/typeshed/pull/15884>
- `typeshed` issue 16504, reporting three gaps in those stubs, cited by item 7 of
  {ref}`§8 <typing-spec-8>`: <https://github.com/python/typeshed/issues/16504>
