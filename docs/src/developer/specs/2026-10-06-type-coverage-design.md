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
- **Parent spec:** none. This is the first specification in this repository, so it inherits
  nothing, and the conventions it follows are not yet written down anywhere else
- **Published:** not yet. `conf.py` maps only `.rst` and `.ipynb` in `source_suffix`, so
  `sphinx` does not read this file and no toctree holds it. The reading-time gate in
  `tests/docs/test_readingtime_coverage.py` globs `*.md` and governs it already, which it
  passes. Publishing the specs tree is separate work, out of scope here

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
raise seven errors. Counting distinct source lines instead, and setting aside the upstream
false positives of {ref}`§3.4 <typing-spec-3-4>`, the work is **206 lines**.

Three of the twenty-five library modules are clean. The check that was supposed to be
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
- **An upstream defect is suppressed where it lands, never worked around in the source.**
  The gallery scripts are rendered into the documentation and readers are invited to copy
  them, so a `type: ignore` comment in one is a directive published as example code. See
  {ref}`§3.4 <typing-spec-3-4>`.

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

Two of the three existing `[[tool.mypy.overrides]]` blocks become redundant and are deleted
with the same change. `disallow_subclassing_any = false` and
`disallow_untyped_decorators = false` exist because `pv.Plotter` and `click`'s decorators
were `Any`; with the real types installed both produce zero errors.

(typing-spec-3-2)=
### 3.2 The ratchet

The twenty-two modules carrying errors are listed once, with `ignore_errors`:

```toml
[[tool.mypy.overrides]]
# typing spec §3.2 -- the ratchet. This list only ever shrinks, and
# "tests/test_typing_ratchet.py" holds it to that. Delete the whole
# block, and that test, when the last entry goes.
ignore_errors = true
module = ["geovista.bridge", "geovista.common", ...]
```

From that point the check is live for the three clean modules and for every module added
afterwards. Each subsequent change deletes one entry and fixes what it exposes.

A ratchet with nothing holding it becomes a dumping ground, so the list is frozen in a test
that permits removals and refuses additions:

```python
RATCHET_BASELINE = frozenset({"geovista.bridge", "geovista.common", ...})


def test_typing_ratchet_only_shrinks():
    current = _mypy_ignored_modules()
    assert current <= RATCHET_BASELINE
```

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
established in the first two changes and applied by rote afterwards.

(typing-spec-3-4)=
### 3.4 Upstream suppressions

121 of the 150 errors in `examples/` are two defects in `pyvista`'s own annotations, both
verified against the runtime on 2026-10-06 with `pyvista` 0.49.0:

- 77 × `call-arg`, *Missing positional argument "self" in call to "__call__" of
  "_Wrapped"*, raised on no-argument calls such as `p.view_xy()`. `pyvista`'s `_Wrapped`
  decorator loses the descriptor protocol in its annotations.
- 44 × `attr-defined`, *pv.Plotter.camera? has no attribute "zoom"*. The trailing `?`
  is `mypy` reporting a type it could only partially resolve; `Camera.zoom` is present and
  callable at runtime.

Both are disabled for the gallery alone, leaving the 20 genuine errors visible:

```toml
[[tool.mypy.overrides]]
# typing spec §3.4 -- both verified against the runtime, both upstream.
disable_error_code = ["attr-defined", "call-arg"]
module = ["geovista.examples.*"]
```

Neither code appears in the library, where `attr-defined` is zero and `call-arg` is one, so
the suppression is confined to where the plotting calls are. This extends a pattern already
in `pyproject.toml`, where `union-attr` is disabled for `geovista.examples.grid.*` on
account of `geopy` being untyped.

(typing-spec-4)=
## 4. Roadmap

| # | Scope | Lines | Status |
|---|---|---|---|
| 1 | The `local` hook, `ci-typing.yml`, the ratchet and its test | 0 | not started |
| 2 | `transform.py` | 29 | not started |
| 3 | `bridge.py` | 28 | not started |
| 4 | `common.py` | 20 | not started |
| 5 | `geoplotter.py`, `geodesic.py` | 38 | not started |
| 6 | `core.py`, `search.py` and the remaining fourteen modules | 51 | not started |
| 7 | `examples/`, and the ratchet retired | 20 | not started |

Each carries a towncrier fragment and the `agentic` label. Changes 2 to 4 alter published
signatures and each adds tests exercising the widened input.

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
- **Reporting the `pyvista` defects upstream.** Worth doing and recorded in
  {ref}`§8 <typing-spec-8>`, but it does not gate any of the roadmap.
- **The untyped imports.** 32 errors are imports rather than code: 29 `import-untyped`
  from distributions that ship no annotations — `lazy_loader` alone accounts for 19, then
  `cmocean` 5, `cartopy`, `geopy` and `rasterio` 2 each, and one each from `pooch`, `h3`
  and `fastparquet` — plus 3 `import-not-found`. Two of those three, `geovistaconfig` and
  `geovista.siteconfig`, are the optional site configuration and are *meant* to be absent,
  so they want a targeted `ignore_missing_imports` rather than a fix. The configuration
  carries no such entry today. Handling all of this is part of change 6.

(typing-spec-8)=
## 8. Open items

- The `pyvista` `_Wrapped` and `Plotter.camera` defects of
  {ref}`§3.4 <typing-spec-3-4>` have not been reported upstream. When they are fixed the
  suppression should be withdrawn, and a long-lived suppression is a smell in the same way
  a long-still pin is.
- `lazy_loader` is 19 of the 29 untyped imports and `geovista` imports it in every module,
  so a single upstream `py.typed` marker would clear most of that category. Whether to
  pursue it upstream or absorb it locally is settled in change 6.

(typing-spec-9)=
## 9. References

- `pyvista`'s `type-checking.yml` workflow, the precedent for {ref}`§3.1 <typing-spec-3-1>`:
  <https://github.com/pyvista/pyvista/blob/main/.github/workflows/type-checking.yml>
- `mypy`'s `python_version`, pinned to the support floor by {pull}`2563`, and the
  `tests/test_python_support.py` convention this specification's ratchet test follows
- `mypy` issue 13916, the reason the hook passes no filenames:
  <https://github.com/python/mypy/issues/13916>
