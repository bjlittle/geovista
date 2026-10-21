---
orphan: true
---

# type coverage change 6c — the last library modules

```{readingtime}
```

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** take the last seven library modules, `geovista.pantry` with `pantry.data`,
`pantry.meshes` and `pantry.textures`, `geovista.raster`, `geovista.report` and
`geovista.themes`, out of the typing ratchet, which then holds only the gallery, and fix the
theme bug and the five `type: ignore` comments their 19 lines sit beside.

**Architecture:** row 6c of typing spec §4, the last of the three pull requests row 6 was
split into ({pull}`2659`). Each module that loads `numpy` or `pyvista` lazily gains the
import under `TYPE_CHECKING` (typing spec §3.3), and leaves the ratchet in the commit that
makes it pass. Most of the 19 lines are narrowing an `Optional` the code knows is set, or
`pyvista` 0.49 calls it leaves unannotated, met with typed locals under §8 item 8 as change 5
did. `ThemeMixin` gets `Theme` as its base under `TYPE_CHECKING`, as change 5 gave
`GeoPlotterBase` `pv.BasePlotter`, which retires `themes.py`'s five `type: ignore`
comments; its missing `__slots__` is a bug on `main`, with a failing test first.

**Tech Stack:** `mypy` 2.x in strict mode, `pytest` with `pytest-mock`, `pyvista` 0.49.1,
`scooby` 0.12.

**Spec:** `docs/src/developer/specs/2026-10-06-type-coverage-design.md`, cited throughout
as `typing spec §…`. This plan implements row 6c of §4.

**Branch:** `debt/typing-library`. The plan is committed first and the pull request held in
draft until the implementation lands on it. `{PR}` below is that pull request's number.

## Global Constraints

- **Copyright header** and `from __future__ import annotations` on every Python file,
  `__init__.py` of a new test package included (root `AGENTS.md`). **Line length 88.**
- **The strictness settings stay as they are** (typing spec §7).
- **No new `type: ignore`, no `typing.cast`, and no new `noqa`.** An upstream defect is met
  with a typed local, a comment naming the defect beside it, and a typing spec §8 item.
- **A runtime type check on an annotated parameter** widens the parameter to the type the
  function accepts before it validates (typing spec §3.3, change 4's rule).
- **The ratchet only shrinks, in step:** `pyproject.toml` and `RATCHET_BASELINE` in the
  same commit as the fixes that make the module pass. Every commit passes the `mypy` hook.
- **Run the full non-image suite before each commit**, and the image tests locally before
  pushing: `CI=true GALLIUM_DRIVER=llvmpipe xvfb-run -a pixi run --frozen -e geovista pytest -n auto -m image tests`.
  `themes.py` styles every scene, and `raster.py` re-centres every texture.
- **Tests follow `tests/AGENTS.md`:** one file per function or class, in a package per
  module, and a test that renders carries `@pytest.mark.image` (none here does).
- **A probe of a scratch tree never runs `python -I`**, which ignores `PYTHONPATH`.
- **Changelog.** One fragment, `{PR}.bugfix.rst`, signed ``:user:`claude` ``; the
  `agentic` label on the pull request.
- **Every deferred item gets an `agentic` issue**, linked from the Follow-ups below and
  from the pull request's description.
- **Prose for other readers is humanized:** the spec's new text, the code comments, commit
  messages, the fragment and the pull request body. This plan is not.

## What the dry run measured

Measured on 2026-10-21 against `main` at `f91aae01`, with the seven entries lifted, the
`TYPE_CHECKING` imports added, and every fix below applied to a scratch tree, which `mypy`
then passed (85 source files there, 86 in the repository's checkout), with the non-image
suite and all 92 image tests green.

1. **Row 6c's count reproduces:** 23 errors on 19 lines. `report` 6 on 5, `meshes` 7 on 4,
   `themes` 4, `raster` 2, `pantry/data` 2, `pantry/__init__` 1, `textures` 1. Five modules
   need the import: `numpy` for `pantry/data`, `pantry/meshes` and `raster`, `pyvista` for
   `report` and `themes`, which have no `TYPE_CHECKING` block yet.
2. **Six lines are pyvista's unannotated calls**, the four typing spec §3.4 counts in
   `raster.py` and `themes.py` and two more in `report.py`: `GPUInfo.__init__`,
   `GPUInfo.get_info`, `Texture.to_image`, `Texture.__init__` and `Theme.__init__`. Checked
   against a clone of `pyvista` `main` (`fbc11b53`) with `pyvista-validation` 0.5.4, all
   six are annotated there. One `meshes.py` error goes as well. `main` types `to_image` as
   returning `ImageData | None`, so the typed local allows `None` now, and survives the floor
   rising until it comes out.
3. **A bug in `themes.py`.** `ThemeMixin` defines no `__slots__`, and `pyvista`'s
   `_all__slots__` reads `__slots__` from every class in a theme's MRO, so `==`,
   `to_dict()` and `save()` raise `AttributeError` on `GeoVistaTheme` and
   `GeoVistaDocumentTheme`. `deepcopy`, `pickle` and `set_plot_theme` are unaffected.
4. **`themes.py`'s five `type: ignore` comments can go.** `mixin_state` assigns theme
   properties on `self`, so `mypy` declares them on the mixin, where they clash with
   `Theme`'s (`misc` on both classes), and cannot see `self.font` (`attr-defined`, three).
   With `Theme` as the mixin's base under `TYPE_CHECKING` they all clear. Each theme must
   then list the mixin first: in the old order `mypy` reports an inconsistent MRO and a
   metaclass conflict. At runtime the mixin derives from `object` and adds only
   `mixin_state`, and both themes compare, convert, copy, pickle and set as before (measured
   with `__slots__` added). Not counted in the 19.
5. **`set_plot_theme`'s runtime check** on `Theme | str` is unreachable to `mypy`; change 4's
   rule widens it to `object`. `test_bad_theme_type` already passes an `int`.
6. **`scooby` is annotated narrower than it behaves.** `Report.__init__` takes `additional`
   as one package or a list; `scooby.Report` wraps a single one at runtime but is annotated
   for a list only, so `Report` wraps it itself. `core` and `optional` pass as
   `list[PackageLike]`, `list` being invariant, and `sort` as `bool`.
7. **The rest:** `pv.read` returns `DataSet | MultiBlock` where the coastlines and LFRic
   files are single `PolyData` meshes; the samples' `name` and payload are `Optional` where
   the code knows they are set; `SampleVectorsXYUVW.w` is annotated `ArrayLike` with a
   default of `None`; `name_reykjanes` and `_fetch_texture` rebind a name to another type;
   `nemo_orca2_cloud` negates an `ArrayLike`.
8. **One test changes.** `test_lfric.py::test_resolution_warning` mocks `pyvista.read` with
   a sentinel, which the new `isinstance` check refuses; it mocks a `PolyData` instead.
9. **Nothing tests `Report`, `wrap_texture` or `_fetch_texture`.** The plan adds pins for
   each before changing them.
10. **Three errors outside 6c appear only against `pyvista` `main`:** `search.py:160` and
    `geoplotter.py` 1076 and 1304. They belong to the floor rise {issue}`2568` tracks.
11. **`geopy` and `fastparquet` go live** in §8 item 9's override: without their entries,
    `pantry/data.py` reports both imports.

## Review Focus

1. **The geovista themes compare, convert and save,** and still style a scene as before.
   → task 4, `test_equal` and `test_to_dict`, which fail on `main`; the image suite.
2. **The bases' new order changes nothing a theme does.** `GeoVistaTheme.__mro__` now has
   `ThemeMixin` before `Theme`. → task 4 runs the theme tests and the image suite; the
   reviewer should look for any code that relies on the order.
3. **`Report` reports a single package, a list, a module, and the GPU or its failure.** →
   task 3, `test_additional`, `test_gpu`, `test_gpu_fail`, `test_no_gpu`.
4. **`wrap_texture` re-centres a texture by whole pixels**, and returns a texture centred
   on the prime meridian untouched. → task 2, `test_wrap`, `test_no_wrap`.
5. **A pantry mesh whose sample lacks a name or payload** now fails an `assert` where it
   failed in `pyvista` before. Every sample the pantry ships sets both where the code reads
   them: `cloud_amount` for every preference but the mesh, and `fvcom_tamar` its name, node
   and face (measured). `tests/pantry/meshes` and the gallery draw them.

---

### Task 1: retire the `pantry` package

**Files:**
- Modify: `src/geovista/pantry/__init__.py` (`fetch_coastlines`),
  `src/geovista/pantry/data.py` (`TYPE_CHECKING` block, `SampleVectorsXYUVW`,
  `name_reykjanes`), `src/geovista/pantry/meshes.py` (`TYPE_CHECKING` block,
  `cloud_amount`, `fvcom_tamar`, `lfric`, `nemo_orca2_cloud`),
  `src/geovista/pantry/textures.py` (`_fetch_texture`)
- Modify: `pyproject.toml`, `tests/test_typing_ratchet.py`,
  `tests/pantry/meshes/test_lfric.py`
- Create: `tests/pantry/textures/__init__.py`, `tests/pantry/textures/test__fetch_texture.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `SampleVectorsXYUVW.w: ArrayLike | None`; no signature changes.

- [ ] **Step 1: Pin `_fetch_texture`**

Create the package `tests/pantry/textures`, its `__init__.py` docstring
`"""Unit-tests for :mod:`geovista.pantry.textures`."""`, and `test__fetch_texture.py`:

```python
def test_location():
    """Test the location of the texture in the cache is returned."""
    result = checkerboard(location=True)
    assert isinstance(result, str)
    assert Path(result).name == "uv-checker-map-4k.png"
    assert Path(result).exists()


def test_texture():
    """Test the texture is returned."""
    assert isinstance(checkerboard(), pv.Texture)
```

Run: `pixi run --frozen -e geovista pytest tests/pantry/textures`

Expected: both pass on `main`; they pin what task 1 rewrites.

- [ ] **Step 2: Lift the four modules, and watch them fail**

Delete `  "geovista.pantry",`, `  "geovista.pantry.data",`, `  "geovista.pantry.meshes",` and
`  "geovista.pantry.textures",` from the ratchet and `RATCHET_BASELINE`. Add
`import numpy as np` to the `if TYPE_CHECKING:` blocks of `pantry/data.py` and
`pantry/meshes.py`.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 11 errors in 4 files`: `__init__.py` 67, `data.py` 153 and 820,
`meshes.py` 153 (three), 268 (two), 485 and 614, `textures.py` 68.

- [ ] **Step 3: The two reads**

In `fetch_coastlines` and `lfric`, bind `mesh = pv.read(resource)`, narrow it with
`assert isinstance(mesh, pv.PolyData)` under a one-line comment (humanized) saying the
resource is a single mesh of lines, or of cells, and return `mesh`.

- [ ] **Step 4: The samples**

- `SampleVectorsXYUVW.w: ArrayLike | None = field(default=None)`.
- `name_reykjanes`: bind the netCDF variable as `variable`, read `long_name` and `units`
  from it, and keep `data` for the array.
- `cloud_amount`: inside `if preference != ...MESH:`, under the comment "every preference
  but the mesh carries a named payload", assert `sample.name is not None` and
  `sample.data is not None`, and assign `np.asanyarray(sample.data)`.
- `fvcom_tamar`: inside `if warp:`, assert `name is not None` under "the sample names its
  payload, which the warp needs", and assign `np.asanyarray(sample.node)`.
- `nemo_orca2_cloud`: `zlevel=-np.asanyarray(sample.zlevel)`.

- [ ] **Step 5: `_fetch_texture`**

```python
    resource: str = CACHE.fetch(f"pantry/textures/{fname}")
    return resource if location else pv.read_texture(resource)
```

- [ ] **Step 6: The LFRic test's mock**

In `test_resolution_warning`, `mesh = mocker.MagicMock(spec=PolyData)`, importing
`PolyData` from `pyvista` at module level; the test's other assertions are unchanged.

- [ ] **Step 7: Verify, and commit**

Run: `pixi run --frozen -e geovista mypy`

Expected: `Success: no issues found in 86 source files`.

Run the full non-image suite. Expected: exit 0, 2926 passed with a docs build present (two
new tests, four fewer ratchet cases).

Run pre-commit on the changed files. Expected: every hook passes.

Message, humanized: `fix: type check the pantry in full`.

---

### Task 2: retire `geovista.raster`

**Files:**
- Modify: `src/geovista/raster.py`, `pyproject.toml`, `tests/test_typing_ratchet.py`
- Create: `tests/raster/__init__.py`, `tests/raster/test_wrap_texture.py`

**Interfaces:**
- Consumes: nothing.
- Produces: no signature changes.

- [ ] **Step 1: Pin `wrap_texture`**

Create the package `tests/raster` (`"""Unit-tests for :mod:`geovista.raster`."""`) and
`test_wrap_texture.py`, with a fixture `image` returning
`np.arange(2 * 4 * 3, dtype=np.uint8).reshape(2, 4, 3)`:

```python
@pytest.mark.parametrize("meridian", [None, 0, 360])
def test_no_wrap(image, meridian):
    """Test a texture centred on the prime meridian is returned as it is."""
    texture = pv.Texture(image)
    assert wrap_texture(texture, central_meridian=meridian) is texture


@pytest.mark.parametrize(("meridian", "shift"), [(90, -1), (180, 2), (-90, 1)])
def test_wrap(image, meridian, shift):
    """Test a texture is re-centred on the meridian."""
    result = wrap_texture(pv.Texture(image), central_meridian=meridian)
    np.testing.assert_array_equal(result.to_array(), np.roll(image, shift, axis=1))
```

Run: `pixi run --frozen -e geovista pytest tests/raster`

Expected: all six pass on `main` (the shifts are measured).

- [ ] **Step 2: Lift the module, and watch it fail**

Delete `  "geovista.raster",` from the ratchet and `RATCHET_BASELINE`. Make the `typing`
import `TYPE_CHECKING, Any`, and the `TYPE_CHECKING` block
`from collections.abc import Callable`, `import numpy as np`,
`from numpy.typing import NDArray`, `import pyvista as pv`.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 2 errors in 1 file`, both `no-untyped-call`: the
`texture.to_image()` and `pv.Texture(image)` lines.

- [ ] **Step 3: The typed locals**

Replace `grid = texture.to_image()` with, humanized:

```python
        # get the texture as a pyvista.ImageData. typing spec §8 -- pyvista 0.49
        # leaves Texture.to_image and Texture.__init__ unannotated
        to_image: Callable[[], pv.ImageData | None] = texture.to_image
        grid = to_image()
        # a texture always converts to an image
        assert grid is not None
```

bind `scalars = grid.active_scalars`, assert it is not `None` ("the pixels of a texture's
image are its active scalars") and reshape `scalars`; and build the result through
`as_texture: Callable[[NDArray[Any]], pv.Texture] = pv.Texture`.

- [ ] **Step 4: Verify, and commit**

Run `mypy`. Expected: `Success: no issues found in 86 source files`.

Run the full non-image suite. Expected: exit 0, 2931 passed.

Run pre-commit on the changed files. Expected: every hook passes.

Message, humanized: `fix: type check raster.py in full`.

---

### Task 3: retire `geovista.report`

**Files:**
- Modify: `src/geovista/report.py`, `pyproject.toml`, `tests/test_typing_ratchet.py`
- Create: `tests/report/__init__.py`, `tests/report/test_Report.py`

**Interfaces:**
- Consumes: nothing.
- Produces: no signature changes; `Report(additional=...)` behaves as before.

- [ ] **Step 1: Pin `Report`**

Create the package `tests/report` (`"""Unit-tests for :mod:`geovista.report`."""`) and
`test_Report.py`:

```python
@pytest.mark.parametrize(
    "additional",
    ["scooby", scooby, ["scooby"], [scooby]],
    ids=["name", "module", "names", "modules"],
)
def test_additional(additional):
    """Test a single package or a list of them is reported."""
    report = Report(additional=additional, gpu=False)
    assert "scooby" in report.packages


def test_gpu(mocker):
    """Test the GPU details are reported."""
    gpu_info = mocker.patch("pyvista.GPUInfo")
    gpu_info.return_value.get_info.return_value = [("GPU Vendor", "geovista")]
    report = Report()
    assert "GPU Vendor" in str(report)
    assert "geovista" in str(report)


def test_gpu_fail(mocker):
    """Test a GPU fault is reported, not raised."""
    mocker.patch("pyvista.GPUInfo", side_effect=RuntimeError)
    report = Report()
    assert "GPU Details : Error" in " ".join(str(report).split())


def test_no_gpu():
    """Test the GPU details are skipped when not wanted."""
    report = Report(gpu=False)
    assert "GPU Details : None" in " ".join(str(report).split())
```

Run: `pixi run --frozen -e geovista pytest tests/report`

Expected: all seven pass on `main`.

- [ ] **Step 2: Lift the module, and watch it fail**

Delete `  "geovista.report",` from the ratchet and `RATCHET_BASELINE`. Import
`TYPE_CHECKING` from `typing`, and add
`if TYPE_CHECKING:` with `from collections.abc import Callable` and `import pyvista as pv`
after the third-party imports.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 6 errors in 1 file`: two on the `GPUInfo` line, and
`additional`, `core`, `optional` and `sort` at the `super().__init__` call.

- [ ] **Step 3: Fix `Report.__init__`**

- Before the packages, under "scooby takes a single package too, though it is annotated
  for a list", wrap `additional` in a list when it is neither `None` nor a list.
- `core: list[PackageLike] = list(PACKAGES_CORE)`, likewise `optional`.
- The GPU details through two typed locals, under
  `# typing spec §8 -- pyvista 0.49 leaves GPUInfo unannotated`:
  `gpu_info: Callable[[], pv.GPUInfo] = pv.GPUInfo` and
  `get_info: Callable[[], list[tuple[str, str]]] = gpu_info().get_info`, then
  `extra_meta = get_info()`, inside the existing `try`.
- `sort=bool(sort)`.

- [ ] **Step 4: Verify, and commit**

Run `mypy`. Expected: `Success: no issues found in 86 source files`.

Run the full non-image suite. Expected: exit 0, 2937 passed.

Run pre-commit on the changed files. Expected: every hook passes.

Message, humanized: `fix: type check report.py in full`.

---

### Task 4: retire `geovista.themes`, and let the themes compare

**Files:**
- Modify: `src/geovista/themes.py`, `pyproject.toml`, `tests/test_typing_ratchet.py`
- Test: `tests/themes/test_themes.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `set_plot_theme(theme: object, /, *, bootstrap=...) -> bool`;
  `GeoVistaTheme(ThemeMixin, Theme)` and `GeoVistaDocumentTheme(ThemeMixin, DocumentTheme)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/themes/test_themes.py`, over its existing `themes` list:

```python
@pytest.mark.parametrize("theme", themes)
def test_equal(theme):
    """Test a theme compares equal to another instance of itself."""
    assert theme() == theme()


@pytest.mark.parametrize("theme", themes)
def test_to_dict(theme):
    """Test a theme converts to the dictionary it is saved as."""
    instance = theme()
    result = instance.to_dict()
    assert result["name"] == instance.name
    assert result["title"] == "GeoVista"
```

(`save` is `to_dict` written out; loading a saved theme back warns about a read-only
`pyvista` flag for any theme, which `filterwarnings = error` would fail.)

Run: `pixi run --frozen -e geovista pytest tests/themes/test_themes.py -k "equal or to_dict"`

Expected: all four FAIL, `AttributeError: type object 'ThemeMixin' has no attribute
'__slots__'`.

- [ ] **Step 2: Give the mixin its slots**

In `ThemeMixin`, before `mixin_state`, under the comment "pyvista gathers the slots of every
class a theme derives from, so the mixin declares that it has none", `__slots__ = ()`.

Run the step 1 tests. Expected: all four pass.

- [ ] **Step 3: Lift the module, and watch it fail**

Delete `  "geovista.themes",` from the ratchet and `RATCHET_BASELINE`. Import
`TYPE_CHECKING` beside `ClassVar`, and add an `if TYPE_CHECKING:` block with
`from collections.abc import Callable` and `import pyvista as pv` after
`import geovista.config as gvc`.

Run: `pixi run --frozen -e geovista mypy`

Expected: exits 1, `Found 4 errors in 1 file`: the two `super().__init__()` calls, the
assignment in `resolve_theme_name`, and the unreachable `raise` in `set_plot_theme`.

- [ ] **Step 4: Fix the four**

- In each theme's `__init__`, under
  `# typing spec §8 -- pyvista 0.49 leaves Theme.__init__ unannotated`, call the base through
  `init: Callable[[], None] = super().__init__`, then `init()`.
- `resolve_theme_name`: declare `theme: Theme | None` before the `if`.
- `set_plot_theme(theme: object, ...)`; its docstring keeps naming `Theme` or `str`.

Run `mypy`. Expected: `Success: no issues found in 86 source files`.

- [ ] **Step 5: Retire the five `type: ignore` comments**

After `_cached_themes`, add, humanized:

```python
if TYPE_CHECKING:
    # mypy needs to know the mixin is combined with a theme, which is true of
    # every class that uses it
    _ThemeBase = Theme
else:
    _ThemeBase = object
```

`class ThemeMixin(_ThemeBase):`; drop the three `# type: ignore[attr-defined]` from
`mixin_state`; and list the mixin first, without the `# type: ignore[misc]`:
`class GeoVistaTheme(ThemeMixin, Theme):` and
`class GeoVistaDocumentTheme(ThemeMixin, DocumentTheme):`.

Run `mypy`. Expected: `Success`, and the `warn_unused_ignores` of strict mode would have
reported any ignore left behind.

- [ ] **Step 6: Verify, and commit**

Run the full non-image suite. Expected: exit 0, 2940 passed.

Run the image suite under `xvfb-run`. Expected: 92 passed.

Run pre-commit on the changed files. Expected: every hook passes.

Message, humanized: `fix: type check themes.py in full, and let the geovista themes
compare`.

---

### Task 5: the spec and the changelog

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md`: §3.3, §3.4, §3.5,
  §8
- Create: `changelog/{PR}.bugfix.rst`

- [ ] **Step 1: §3.3**

After change 6b's paragraph, humanized:

```text
Change 6c applied the rule a third time: `set_plot_theme` checks for a `Theme` or a `str`
at runtime, so it takes an `object`. It also met an annotation narrower than its
behaviour, outside `geovista`: `scooby.Report` wraps a single package in a list at
runtime, but is annotated for a list only, so `geovista.Report`, which promises either,
wraps it itself.
```

- [ ] **Step 2: §3.4, the library's untyped calls**

After "so the suppression stays confined to where the plotting calls are.", add, humanized:
"Change 6c met those four, and two more that `report.py`'s `pyvista` import revealed, with
typed locals ({ref}`§8 <typing-spec-8>` item 8)."

- [ ] **Step 3: §3.5, the theme mixin**

After the paragraph ending "leaving nine.", add, humanized:

```text
Change 6c does the same for `ThemeMixin`, which the two `geovista` themes combine with
`pyvista`'s `Theme` and `DocumentTheme`. It sets theme properties on `self`, so `mypy`
declared them on the mixin, where they clashed with the theme's, and couldn't see
`self.font` at all. With `Theme` as its base under `TYPE_CHECKING`, each theme has to list
the mixin first, or its bases have no consistent order. That changes their MRO but nothing
they do, since the mixin adds only `mixin_state`. Five `type: ignore` comments go, leaving
four in the library. The mixin also lacked `__slots__`, and `pyvista` gathers the slots of
every class in a theme's MRO to compare, convert or save it, so `==`, `to_dict` and `save`
raised `AttributeError` on both themes. It now declares that it has none.
```

- [ ] **Step 4: §8, items 8 and 9**

Replace item 8 with, humanized:

```text
8. **Open** ({issue}`2568`) — **Nine typed locals wait on the same `pyvista` release.**
   `pyvista` 0.49 leaves `GPUInfo.__init__`, `GPUInfo.get_info`, `Texture.__init__`,
   `Texture.to_image` and `Theme.__init__` unannotated, and its `_Wrapped` decorator, item
   2's cause, breaks `self.reset_camera(render=False)`. So `_warn_opacity` and `view_poi`
   call `GPUInfo` and `reset_camera` through locals annotated `Callable`. Change 6a added
   a third, for `p.add_axes()` in the `plot` command of `cli.py`, and change 6c six more:
   two in `Report`, two in `wrap_texture` and one in each theme's `__init__`. `pyvista`
   `main` fixes every defect, and the locals come out with the floor that carries them,
   the trigger items 2 and 6 already wait on. `main` types `to_image` as returning
   `ImageData | None`, so the local in `wrap_texture` already allows `None`.
```

In item 9, replace "Only `pooch`'s entry is live so far: `geopy` and `fastparquet` are
imported only by `pantry/data.py`, which leaves the ratchet in change 6c." with "All three
entries have been live since change 6c took `pantry/data.py`, which imports `geopy` and
`fastparquet`, out of the ratchet."

- [ ] **Step 5: The changelog, and verify**

Create `changelog/{PR}.bugfix.rst`, humanized:

```rst
:class:`geovista.themes.GeoVistaTheme` and
:class:`geovista.themes.GeoVistaDocumentTheme` compare with ``==`` and convert
with ``to_dict()`` and ``save()``, where each raised ``AttributeError``.
``geovista.pantry`` and its modules, ``geovista.raster``, ``geovista.report`` and
``geovista.themes`` also leave the typing ratchet, so ``mypy`` checks the whole
library in full, and ``geovista.themes`` loses its five ``type: ignore``
comments. (:user:`claude`)
```

Run the changelog script, `tests/test_spec_conventions.py tests/test_status_references.py`,
`check-spec-status {PR}`, and the `-W` documentation build, as change 6b did. Expected: all
pass; autoapi drops the private `_ThemeBase` from `ThemeMixin`'s bases, as change 5's hook
does for `_PlotterBase`.

Message, humanized: `docs: record what typing change 6c found`.

---

### Task 6: land row 6c

After the final review, its fixes, CI and any Codex round, as the pull request's last
commit: row 6c's Status becomes `` ✅ landed (YYYY-MM-DD, {pull}`{PR}`) `` with
`date -u +%F`, and `check-spec-status {PR}` runs again. If the merge slips a day, correct the
date first.

Message, humanized: `docs: land typing roadmap row 6c`.

---

## Done when

- `pixi run --frozen -e geovista mypy` exits 0, and the ratchet and `RATCHET_BASELINE` hold
  only `geovista.examples.*`.
- `themes.py` carries no `type: ignore`, and the library four.
- The suite passes, image tests included, locally and in CI, and the documentation builds
  with `-W`.
- Typing spec §3.3, §3.4, §3.5 and §8 record what the change found, and row 6c reads landed.
- Every deferred item has an `agentic` issue, linked below and from the pull request.

## During execution

Tasks 1 to 5 ran natively in one session, and each step's output matched its `Expected:`
line, with two exceptions. `taplo-format` collapses the ratchet's `module` list onto one
line once it is short enough, so tasks 3 and 4 edited it as a list. And task 4's step 3
reported 11 errors, not 4: with `__slots__ = ()` in place and no `Theme` base yet, `mypy`
read `mixin_state`'s seven assignments against the empty slots. The dry run had added both
together. All eleven cleared in step 5. Typing spec §3.2 also gained a sentence saying the
ratchet now holds the gallery alone. The non-image suite reached 2940 passed and the image
suite 92, both locally.

## After the final review

The whole-branch review on Opus 5.5 found nothing critical, two important findings and five
minors. It reproduced the theme tests failing on `f91aae01`, the MRO swap reaching nothing
but `_all__slots__`, every typed local's pyvista 0.49 defect and its annotation on
`pyvista` `main`, and the spec's counts.

Both important findings were real. `Report` wrapped any `additional` that was not a list,
so a tuple or set, which `scooby` accepts, became one bogus package and raised `TypeError`;
it now wraps only a single `str` or module, as `scooby` does. And `test_additional` could
not fail, since `scooby` is a core package; it now reports `pytest`, which is neither core
nor optional, with tuple and set cases, beside `test_no_additional`.

Three minors were statements this change makes that were not true, so they were fixed too:
the themes now refuse an unknown attribute, which §3.5's "nothing they do" and the fragment
left out; "a texture always converts to an image" is false of an empty one; and
`tests/AGENTS.md` did not list `raster/` and `report/`. The other two were test gaps, closed
with `tests/themes/test_ThemeMixin.py`, which pins the runtime base, the MRO order and the
refused attribute as change 5's `test_GeoPlotterBase.py` does, and a `save` test. The suite
reached 2950 passed.

## Follow-ups

- {issue}`2568`: comment with the three errors `pyvista` `main` raises outside 6c
  (`search.py:160`, `geoplotter.py` 1076 and 1304), which the floor rise will meet, and
  the six new typed locals of §8 item 8.
- Change 7, the gallery: `wind_arrows_uvw.py` multiplies `sample.w`, which is now
  `ArrayLike | None`. `mypy` reports it when change 7 lifts the gallery's entry, so it
  needs no issue of its own.
