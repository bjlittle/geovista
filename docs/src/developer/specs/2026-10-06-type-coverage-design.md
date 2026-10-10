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
  where it is written, only where it does damage. Corrected to `pv.Camera` on a copy of
  the tree, all 45 clear and 44 `no-untyped-call` take their place, because `Camera.zoom`
  has no annotations in 0.49.0. That residue is upstream, and `pyvista` `main` already
  annotates it. Tracked by {issue}`2569`.

Both are disabled for the gallery alone, leaving the 28 genuine errors visible:

```toml
[[tool.mypy.overrides]]
# typing spec §3.4 -- two "pyvista" stub defects, both verified against the
# runtime on 2026-10-06 with pyvista 0.49.0: "_Wrapped" loses the descriptor
# protocol, and "Plotter.camera" resolves only partially so ".zoom" is
# unreachable. Confined to the gallery, whose scripts are published as
# example code, so a "type: ignore" comment in one is a directive a reader
# is invited to copy. Withdraw when upstream fixes them.
disable_error_code = ["attr-defined", "call-arg"]
module = ["geovista.examples.*"]
```

The comment is quoted as it stands in `pyproject.toml` rather than as it should read,
because a specification that quotes the code has to quote what the code says;
{issue}`2569` corrects it. The two
halves retire on different triggers. `attr-defined` goes with the one-line correction,
which falls to change 5 since `geoplotter.py` is in it, and the override then carries
`no-untyped-call` in its place for the 44 `zoom` calls. `call-arg` goes when the
`pyvista` floor reaches the release carrying the fix, and the `zoom` annotations are on
the same `main`, so from that release the gallery override has nothing left to hold.

Neither code appears in the library, where `attr-defined` is zero and `call-arg` is one, so
the suppression is confined to where the plotting calls are. This extends a pattern already
in `pyproject.toml`, where `union-attr` is disabled for `geovista.examples.grid.*` on
account of `geopy` being untyped.

(typing-spec-4)=
## 4. Roadmap

| # | Scope | Lines | Status |
|---|---|---|---|
| 1 | The `local` hook, `ci-typing.yml`, the ratchet and its test | 0 | ✅ landed (2026-10-06, {pull}`2565`) |
| 2 | `transform.py` | 29 | ✅ landed (2026-10-08, {pull}`2580`) |
| 3 | `bridge.py` | 28 | ✅ landed (2026-10-09, {pull}`2599`) |
| 4 | `common.py` | 20 | ✅ landed (2026-10-10, {pull}`2612`) |
| 5 | `geoplotter.py`, `geodesic.py` | 38 | not started |
| 6 | `core.py`, `search.py` and the remaining fourteen modules | 51 | not started |
| 7 | `examples/`, its ratchet entry, and the ratchet retired | 20 | not started |

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
  for `geopy` or `pooch`. The rest is part of change 6.

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
3. **Open** ({issue}`2569`, owned by change 5 of {ref}`§4 <typing-spec-4>`) — **The
   `attr-defined` suppression hides a bug of ours.** It is labelled upstream in
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
   `pyproject.toml` verbatim.
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
6. **Open** ({issue}`2568`) — **The cast in `transform_mesh` waits on the same `pyvista`
   release.** `pyvista` 0.49 annotates `pyvista_ndarray.__setitem__` with
   `key: int | NumpyArray[int]`, which refuses the tuple index of `mesh.points[:, 0]`
   that it accepts at runtime, so change 2 sets the points through a `typing.cast`.
   `pyvista` pull request 9262 widens the key, merged on 2026-09-23 after 0.49.0, so the
   cast comes out with the floor that carries it, the trigger item 2 already waits on.
7. **Open** ({issue}`2601`) — **The cast in `from_tiff` waits on typeshed.**
   `types-rasterio` types the rows and columns of `rasterio.transform.xy` as
   `int | Sequence[int]`. `rasterio` takes arrays, which is what `Transform.from_tiff`
   passes, so change 3 passes them through a `typing.cast`. It comes out when the stubs
   accept arrays. The report to typeshed covers two other gaps as well, which the code
   handles without a cast.

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
- `lazy_loader` issue 165, on its relation to PEP 810, cited by item 4 of
  {ref}`§8 <typing-spec-8>`: <https://github.com/scientific-python/lazy-loader/issues/165>
- `lazy_loader` issue 181, the request for a marker and annotations that resolves item 4
  of {ref}`§8 <typing-spec-8>`: <https://github.com/scientific-python/lazy-loader/issues/181>
- `typeshed` pull request 15884, which added the `rasterio` stubs that change 3 checks
  `bridge.py` against: <https://github.com/python/typeshed/pull/15884>
- `typeshed` issue 16504, reporting three gaps in those stubs, cited by item 7 of
  {ref}`§8 <typing-spec-8>`: <https://github.com/python/typeshed/issues/16504>
