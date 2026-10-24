# CRS Projection Coverage Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land roadmap row 1 of the CRS specification: a test that records which PROJ methods and `cartopy` classes project a global mesh cleanly today, and fails whenever that changes without the record changing too.

**Architecture:** One test module holds the ledger and measures each method as crs spec §3.1 does, through `transform_mesh`, one parametrised test per method and per class. It declares itself a repository check, so a failure links to its section on the checks page. The specification's counts are corrected to the measurement.

**Tech Stack:** PROJ 9.9 through `pyproj` 3.8, `cartopy` 0.26, pytest with `pytest-xdist`, `packaging.version`.

**Spec:** `docs/src/developer/specs/2026-10-23-globe-first-crs-design.md` (`crs spec §…`, merged in #2717), §3.1, §3.2 and §6. Rows 2 to 4 each get a child specification before they are planned, as `bjlittle/tephpy` does.

## Global Constraints

- Every geometric result is checked against a reference independent of `geovista` (§6). Here the reference is the measurement of §3.1, and the test records it.
- The coverage test makes coverage visible and stops it shrinking by accident, like the typing ratchet (§6).
- The test is a repository check: it declares `CHECK = "<name>"` and gets a section in `docs/src/developer/checks.rst` (`checks spec §3`).
- One roadmap row per pull request. This one marks row 1 ``✅ landed (YYYY-MM-DD, {pull}`N`)`` and runs `GH_TOKEN="$(gh auth token)" pixi run -e test check-spec-status <N>`.
- Warnings are errors under pytest.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``, and the pull request carries the `agentic` label.

## Review Focus

1. **The PROJ that `pyproj`'s wheels bundle**, 9.8.1, which lacks `dsea`, `hourglass`, `interrupted`, `ivea` and `tsea`. The PyPI jobs must pass by skipping exactly those, each with its reason, and no others. `test_methods_are_the_projections_proj_offers` and the version guard of `test_method_outcome` cover it.
2. **A warning from `transform_mesh`**, such as the area-of-use warning `LambertZoneII` raises, under warnings as errors. It must not turn a geometric outcome into `raises`. `test_cartopy_outcome[LambertZoneII]` covers it.
3. **PROJ with its network off**, as the wheels ship it. Every outcome was measured the same, and Step 4 runs the module under `PROJ_NETWORK=OFF`.
4. **A method a future PROJ adds.** The inventory test must fail by naming it, and say to measure it into `WORKS` or `FAILS`, rather than ignore it.
5. **A metric that stops firing**, after a change to `outcome`, which would let every failing method look like it works. `test_every_failure_kind_is_detected` holds one method to each failure kind.

---

Measured on 2026-10-24 at `7ca628c1` with PROJ 9.9.0: 162 PROJ methods carry a classification in `proj -lP`, of which 91 work, and 17 of `cartopy`'s 38 classes work. The specification counted 161 and 70 failing. The difference is that `interrupted` is new, `rouss` now works, and `august` fails without a class. `pyproj`'s wheels bundle PROJ 9.8.1, which lacks `dsea`, `hourglass`, `interrupted`, `ivea` and `tsea`. Every other outcome is the same there.

### Task 1: The Ledger and the Test

**Files:**
- Create: `tests/transform/test_projection_coverage.py`
- Modify: `docs/src/developer/checks.rst` (a "Projection Coverage" section)
- Modify: `docs/src/developer/specs/2026-10-23-globe-first-crs-design.md` (§1, §3.1, §3.2, §10 row 1)
- Modify: `docs/AGENTS.md` (ask whether a roadmap row is bounded before planning it)
- Create: `changelog/<PR>.internal.rst`

**Interfaces:**
- Produces, in the test module: `CHECK = "projection-coverage"`; `METHODS: frozenset[str]` (162); `WORKS: frozenset[str]` (91); `FAILS: dict[str, int | None]` (71, method to class, `None` unclassified); `CARTOPY_CLASSES: frozenset[str]` (38); `CARTOPY_WORKS: frozenset[str]` (17); `CARTOPY_FAILS: dict[str, int]` (21); `NOT_PROJECTIONS: frozenset[str]` (30); `SINCE: dict[str, str]`; `PARAMETERS: dict[str, str]`; `outcome(crs: pyproj.CRS | ccrs.Projection) -> tuple[str, str]`. Row 4 replaces `WORKS` with its registry.

Values, decided here:

- `WORKS`: `adams_ws1` `adams_ws2` `aea` `aitoff` `apian` `boggs` `bonne` `cea` `col_urban` `collg` `comill` `crast` `denoy` `eck1` to `eck6` `eqc` `eqdc` `eqearth` `euler` `fahey` `fouc` `fouc_s` `gall` `gins8` `gn_sinu` `goode` `hammer` `hatano` `hourglass` `kav5` `kav7` `lagrng` `larr` `lask` `lcca` `leac` `loxim` `mbt_fps` `mbt_s` `mbtfpp` `mbtfpq` `mbtfps` `mill` `moll` `murd1` `murd3` `natearth` `natearth2` `nell` `nell_h` `ortel` `patterson` `poly` `putp1` `putp2` `putp3` `putp3p` `putp4p` `putp5` `putp5p` `putp6` `putp6p` `qua_aut` `robin` `rouss` `rpoly` `sinu` `times` `tissot` `urm5` `urmfps` `vandg` `vandg2` `vandg3` `vandg4` `vitk1` `wag1` to `wag7` `weren` `wink1` `wink2` `wintri`.
- `FAILS`: the members of crs spec §3.2's six lists with their class, less `rouss`, plus `interrupted` in class 5 and `august` and `bacon` as `None`.
- `CARTOPY_WORKS`: `Aitoff` `AlbersEqualArea` `EckertI` to `EckertVI` `EqualEarth` `EquidistantConic` `Hammer` `LambertCylindrical` `Miller` `Mollweide` `PlateCarree` `Robinson` `Sinusoidal`. `CARTOPY_FAILS` is §3.2's 21 `cartopy` classes with their class. `UTM` is built as `UTM(zone=30)`, every other class with no arguments.
- `NOT_PROJECTIONS`: `affine` `axisswap` `cart` `defmodel` `deformation` `geoc` `geocent` `geogoffset` `gridshift` `helmert` `hgridshift` `horner` `latlon` `latlong` `longlat` `lonlat` `molobadekas` `molodensky` `noop` `pipeline` `pop` `push` `set` `tinshift` `tmerczoned` `topocentric` `unitconvert` `vertoffset` `vgridshift` `xyzgridshift`.
- `SINCE`: `{"dsea": "9.9.0", "hourglass": "9.9.0", "interrupted": "9.9.0", "ivea": "9.9.0", "tsea": "9.9.0"}`.
- `PARAMETERS`, the typical parameters a method needs before PROJ will build it: `lat_1=20 lat_2=60` for `aea` `eqdc` `euler` `imw_p` `lcc` `murd1` `murd2` `murd3` `pconic` `tissot` `vitk1`; `lat_1=45` for `bonne` `ccon`; `lat_0=35` for `lcca`; `chamb` `lat_1=10 lon_1=30 lon_2=40`; `geos` `h=35785831`; `nsper` `h=3000000`; `tpers` `h=5500000 tilt=30 azi=20`; `gn_sinu` `m=2 n=3`; `interrupted` `base=sinu`; `labrd` `lat_0=-18.9 lon_0=46.4372083 azi=18.9 k_0=0.9995`; `lsat` `lsat=2 path=2`; `misrsom` `path=1`; `ob_tran` `o_proj=moll o_lat_p=45 o_lon_p=-90`; `oea` `m=1 n=2`; `omerc` `lat_0=45 lonc=0 alpha=30`; `sch` `plat_0=30 plon_0=0 phdg_0=0`; `tpeqd` `lat_1=0 lon_1=0 lat_2=60 lon_2=60`; `urm5` `n=0.9 alpha=2 q=4`; `urmfps` `n=0.5`; `utm` `zone=30`. Each is written `+key=value` after `+proj=<method>`.

`outcome` measures as crs spec §3.1 does, and returns the first failure it finds, in this order:

1. The mesh is `geovista.Transform.from_1d(np.arange(-180, 181, 5.0), np.arange(-90, 91, 5.0))`, with each point's latitude from `from_cartesian` attached as the point array `gvCoverageLatitude`, which the cut interpolates.
2. `transform_mesh(mesh, crs)` inside `warnings.catch_warnings()` with warnings ignored, since the outcome is geometric. Any exception gives `("raises", <type name>)`.
3. Any non-finite x or y gives `"non-finite"`. Any |x| or |y| over `1e8` gives `"runaway"`.
4. Each cell's signed area in x and y, by the shoelace formula. Ignoring areas below `1e-9` times the median absolute area, cells of both signs give `("folded", <count of the minority sign>)`.
5. A cell whose x-extent exceeds half the mesh's x-extent, or y-extent half its y-extent, gives `("torn", "span")`. So does an edge longer than ten times the median of the edges joining the same two latitudes, read from `gvCoverageLatitude` rounded to six decimals: `("torn", "edge")`.
6. Otherwise `("works", "")`.

- [ ] **Step 1: Write the failing tests**

```python
def test_methods_are_the_projections_proj_offers():
    offered = set(pyproj.list.get_proj_operations_map())
    assert offered - METHODS - NOT_PROJECTIONS == set()
    missing = {m for m in METHODS - offered if PROJ < Version(SINCE.get(m, "0"))}
    assert METHODS - offered == missing


def test_ledger_partitions_every_method():
    assert WORKS.isdisjoint(FAILS) and WORKS | set(FAILS) == METHODS
    assert set(FAILS.values()) <= {1, 2, 3, 4, 5, 6, None}
    assert CARTOPY_WORKS.isdisjoint(CARTOPY_FAILS)
    assert CARTOPY_WORKS | set(CARTOPY_FAILS) == CARTOPY_CLASSES


@pytest.mark.parametrize("method", sorted(METHODS))
def test_method_outcome(method): ...  # works iff in WORKS


@pytest.mark.parametrize("name", sorted(CARTOPY_CLASSES))
def test_cartopy_outcome(name): ...  # works iff in CARTOPY_WORKS


@pytest.mark.parametrize(
    ("method", "kind"),
    [
        ("ortho", "raises"),
        ("merc", "runaway"),
        ("aeqd", "folded"),
        ("igh", "torn"),
        ("stere", "non-finite"),
    ],
)
def test_every_failure_kind_is_detected(method, kind):
    assert outcome(_crs(method))[0] == kind
```

`PROJ` is `Version(pyproj.proj_version_str)`, from `packaging.version`. A method in `SINCE` that the running PROJ predates is skipped by `test_method_outcome` with the reason `"<method> arrived in PROJ <version>"`, and by nothing else. A method PROJ offers that the ledger lacks fails the inventory test with `"PROJ offers <method>, which the ledger does not hold: measure it into WORKS or FAILS, or add it to NOT_PROJECTIONS"`. A mismatch of outcome fails with `"<method> now works: move it from FAILS to WORKS"` or `"<method> no longer works (<kind>: <detail>)"`, and the same with `CARTOPY_` for a class.

- [ ] **Step 2: Run the tests and see them fail**

Run: `pixi run --frozen -e geovista pytest tests/transform/test_projection_coverage.py -n 8 -q`
Expected: FAIL, as `outcome` and the ledger do not exist yet.

- [ ] **Step 3: Implement `outcome`, `_crs(method: str) -> pyproj.CRS`, and the ledger**, as above.

- [ ] **Step 4: Run the tests and see them pass**

Run the same command, then again under `pixi run --frozen -e geovista env PROJ_NETWORK=OFF pytest ...`.
Expected: 162 + 38 + 7 passed in each. A run on PROJ 9.8.1 skips the five methods of `SINCE`.

- [ ] **Step 5: Add the check's section to `checks.rst`**, labelled `gv-developer-checks-projection-coverage` and `tippy-gv-developer-checks-projection-coverage`, in the page's five parts:
  - **The rule:** which PROJ methods and `cartopy` classes project a global mesh cleanly is recorded, and changes only with the ledger.
  - **Why:** decision 12, and to make coverage visible.
  - **When it fails:** move a method that now works into `WORKS`, and treat one that stopped working as a regression.
  - **Declaring an exception:** none, though `PARAMETERS` gives a method the parameters it needs.
  - **More:** `crs spec §6`.

  `tests/test_repository_checks.py` then passes.

- [ ] **Step 6: Correct the specification to the measurement.**
  - §1 and §3.1: 162 methods.
  - §3.2: 71 failing; class 2 loses `rouss` (18); class 5 gains `interrupted` (9). `august` and `bacon` are named as failing without a class, in place of "One method, `bacon`, is unconfirmed".
  - §10: row 1 `✅ landed`.

  Then run `tests/test_spec_conventions.py`, `tests/docs/test_readingtime_coverage.py` and `check-spec-status`.

- [ ] **Step 7: Write the fragment, run the hooks and the full suite, and commit**

```bash
git add tests/transform/test_projection_coverage.py docs/src/developer/checks.rst \
  docs/src/developer/specs/2026-10-23-globe-first-crs-design.md docs/AGENTS.md \
  docs/src/developer/plans/2026-10-24-crs-projection-coverage.md changelog/
pixi run --frozen -e geovista git commit -m "tests: record which projections work today, as a repository check"
```
