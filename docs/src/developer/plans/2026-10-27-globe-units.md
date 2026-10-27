# Globe Units Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 1 of globe spec §9: `geovista.units`, which reads a length or an angle in any of the three forms of globe spec §4.2 and converts it, once, to metres or to degrees, with `pint` and `pint-cf` as new core dependencies.

**Architecture:** One module, `src/geovista/units.py`, with two public functions, `to_metres` and `to_degrees`, over private helpers that turn a value into a quantity in one cached `pint-cf` registry. A plain number never imports `pint`. Nothing else in `geovista` calls the module yet: the globe's radius takes it in row 2, and heights in row 3.

**Tech Stack:** `pint` 0.26.2, `pint-cf` 0.2.1 (with its `lark` 1.3.1), NumPy, pytest.

**Spec:** `docs/src/developer/specs/2026-10-26-globe-heights-layers-design.md` (`globe spec §…`, #2732): §4.2, §6 and §9 row 1, with crs spec §2 decision 13 and crs spec §4.9 of `2026-10-23-globe-first-crs-design.md`. {user}`bjlittle` confirmed on 2026-10-27 that the row is bounded enough to plan without a child specification, with calls 1 to 5 below flagged.

## Global Constraints

- A length or an angle arrives in one of three forms (globe spec §4.2): a plain number, in metres or degrees; a `pint` quantity from any registry, read by its magnitude and the long form of its units, `str(quantity.units)`, never the short form; or a magnitude with a CF unit string, parsed by the registry of `pint-cf`.
- Each is converted once, at the boundary, to metres or degrees. Inside, the engine works on plain floats and NumPy arrays (crs spec §4.9).
- An angle must have angular units: a dimensionless quantity is refused as an angle, never read as radians. Anything that is not the dimension asked for is refused with its unit named (globe spec §4.2).
- `geovista` depends on `pint` and `pint-cf` as they stand, behind `geovista.units`, so replacing `pint-cf` touches one module (globe spec §4.2).
- A height given in feet, kilometres or metres, through any registry or a CF unit string, reads back the same height in metres, exactly (globe spec §6).
- New public API: `__all__ = ["to_degrees", "to_metres"]`, NumPy docstrings, `.. versionadded:: 0.6.0` under `Notes`.
- `mypy` runs strict over the whole package, and no override may be added: `pint`, `pint-cf` and `lark` all ship `py.typed`.
- Warnings are errors under pytest.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: enhancement`, `feature: crs` and `agentic`.
- One roadmap row per pull request. This one marks globe spec §9 row 1 landed and runs `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>`.
- Cite a specification section in plain text (`globe spec §4.2`), never with a `{ref}` role.

## Calls Made in This Plan

Calls 1 to 5 were put to {user}`bjlittle` before planning. Calls 6 to 10 are made here.

1. **The API** is `to_metres(value, units=None)` and `to_degrees(value, units=None)`. `value` is a number, an array or a `pint` quantity, and `units` is a CF unit string, for the third form.
2. **`pint` is imported only when a quantity or a CF string arrives**, since importing it takes 0.27 s. One registry is built and cached, since each costs 0.06 s.
3. **The angle rule:** a unit is an angle when its base units are exactly `radian`. `pint` otherwise converts `1`, `percent` and `m/m` to degrees without a word.
4. **The pins** are `pint >=0.25.2,<0.27` and `pint-cf >=0.2.1,<0.3`, the same in `requirements/pypi-core.txt` and `[tool.pixi.dependencies]`. 0.25.2 is `pint-cf`'s own floor. `pint-cf` imports private modules of `pint`, such as `pint.delegates.formatter._compound_unit_helpers`, so `pint` stays below its next minor release until that release is checked.
5. **Row 1 wires nothing in.** It delivers the module and its tests.
6. **A masked element becomes NaN**, never its fill value. `netCDF4`, a core dependency, returns masked arrays by default. Other values that are not finite pass through, so that heights can refuse them with their own message in row 3 (globe spec §4.3).
7. **`pint-cf`'s `DeprecationWarning` for its COARDS placeholders** (`level`, `layer`, `sigma_level` and their plurals) is silenced while a unit is parsed. Each is dimensionless, so `geovista` refuses it as a length or an angle anyway, with its own message.
8. **A unit `pint-cf` cannot read raises one `ValueError` that names it**, whichever of `pint`'s `PintError`, `lark`'s `LarkError` or a `ValueError` (for `"3 km"`) `pint-cf` raised.
9. **The registry stays private.** A user with no registry of their own passes a CF string.
10. **A scalar or 0-d input gives a Python `float`**, and anything else a float64 array.

## Review Focus

1. **A masked array from `netCDF4`.** A masked element must become NaN, never its fill value. `test_masked_values_become_nan` (Task 1).
2. **A unit only another registry defines**, as MetPy defines its own. It must be refused with a `ValueError` naming it, not an `AttributeError` or `pint`'s own error. `test_refuses_a_unit_only_another_registry_defines` (Task 1).
3. **A NumPy scalar or a 0-d array.** It must give a Python `float`. `test_numpy_scalar_gives_float` (Task 1).
4. **A deprecated CF placeholder under warnings as errors.** `"level"` must raise the `ValueError`, never a `DeprecationWarning`. `test_refuses_deprecated_cf_placeholder` (Task 1).
5. **A dimensionless quantity from another registry, given as an angle.** It must be refused. `test_refuses_a_dimensionless_quantity_as_an_angle` (Task 2).

---

Measured on 2026-10-27 at `1c052e22`, with Python 3.14.9 and `pint` 0.26.2, `pint-cf` 0.2.1 and `lark` 1.3.1 installed apart from the `pixi` environment:

- Importing `pint` took 0.27 s and `pint_cf` 0.008 s more. Each call of `cf_unitregistry()` took 0.06 s and returned a new registry.
- In `pint-cf`'s registry, `m`, `metre`, `km`, `ft`, `feet` and `nautical_mile` are lengths. `degree`, `degrees`, `degrees_north` and `degrees_east` are `arc_degree`, and `radian` and `arcsecond` are angles, all dimensionless. `1`, `""` and `percent` are dimensionless. `nmi` is a nano international mile. `level` raises a `DeprecationWarning`.
- From a plain `pint.UnitRegistry`, `str(units)` gives `nautical_mile` for `nmi`, `foot` for `foot` and `turn` for `turn`, which `pint-cf` reads as a circle.
- `Quantity(h, u).to("m").magnitude` equals `h * f` exactly for `ft` (0.3048), `km`, `m` and `nautical_mile` (1852), with `h = [0, 1, 1000, 8848.86, 29031.7, -10994, 1e-9 / 3]`.
- A float32 magnitude stays float32 through `pint`, and integers become float64.
- `1`, `percent` and `m/m` convert to degrees: `1` gives 57.29577951308232.
- The base units of `degree`, `degrees_north`, `arcsecond` and `turn` are `radian`, and of `1` and `percent`, `dimensionless`.
- `"not_a_unit"` raises `pint`'s `UndefinedUnitError`, `"m!!"` `lark`'s `UnexpectedCharacters`, and `"3 km"` a `ValueError`.
- Adding quantities from two registries raises a `ValueError`.

### Task 1: Lengths, and the Dependencies

**Files:**
- Modify: `requirements/pypi-core.txt` (two lines after `numpy`)
- Modify: `pyproject.toml` (`[tool.pixi.dependencies]`, two lines after `numpy`)
- Modify: `pixi.lock` (by `pixi lock`)
- Create: `src/geovista/units.py`
- Create: `tests/units/__init__.py` (the licence header and `"""Unit-tests for :mod:`geovista.units`."""`, as `tests/crs/__init__.py`)
- Create: `tests/units/test_to_metres.py`
- Create: `tests/units/test_import.py`

**Interfaces:**
- Produces, public: `to_metres(value: ArrayLike | pint.Quantity, units: str | None = None) -> float | NDArray[np.float64]`, with the overload `(value: float, units: str | None = None) -> float`.
- Produces, private, for Task 2:
  - `_registry() -> pint.UnitRegistry`, a `functools.cache` over `pint_cf.cf_unitregistry()`;
  - `_magnitude(value: object) -> NDArray[np.float64]`, as float64 with masked elements NaN, never importing `pint`;
  - `_quantity(value: object, units: str | None) -> tuple[pint.Quantity, str] | None`. It returns `None` for a plain value whose `units` is `None`, without importing `pint`; an empty string is a unit, parsed as dimensionless. Otherwise it returns the quantity in `_registry()` with a `_magnitude` magnitude, and the unit's label: `units` as given, or `str(value.units)` for a quantity. A value is a quantity when it has both `magnitude` and `units` attributes. It raises `ValueError` for a quantity given `units` as well, and for a unit it cannot read;
  - `_result(values: NDArray[np.float64]) -> float | NDArray[np.float64]`, a Python `float` for a 0-d array.

- [ ] **Step 1: Add the dependencies**

Add `pint >=0.25.2,<0.27` and `pint-cf >=0.2.1,<0.3` to `requirements/pypi-core.txt`, and `pint = ">=0.25.2,<0.27"` and `pint-cf = ">=0.2.1,<0.3"` to `[tool.pixi.dependencies]`, each after `numpy`. Then:

Run: `pixi lock && pixi list -e geovista '^(pint|pint-cf|lark)$'`
Expected: `pint` 0.26.2, `pint-cf` 0.2.1 and `lark` listed.

Run: `pixi run --frozen -e geovista pytest tests/test_dependency_ceilings.py -q`
Expected: PASS.

- [ ] **Step 2: Write the failing tests**

`tests/units/test_to_metres.py`:

```python
H = np.array([0.0, 1.0, 1000.0, 8848.86, 29031.7, -10994.0, 1e-9 / 3])


def test_plain_number_is_metres():
    result = to_metres(6378137.0)
    assert result == 6378137.0
    assert type(result) is float


def test_plain_array_is_metres():
    result = to_metres(H)
    assert np.array_equal(result, H)
    assert result.dtype == np.float64


def test_integers_become_float64():
    assert to_metres(np.array([1, 2])).dtype == np.float64


@pytest.mark.parametrize(
    ("units", "factor"),
    [("m", 1.0), ("km", 1000.0), ("ft", 0.3048), ("nautical_mile", 1852.0)],
)
def test_cf_string_is_exact(units, factor):
    assert np.array_equal(to_metres(H, units), H * factor)


@pytest.mark.parametrize(
    "registry",
    [pint.UnitRegistry(), pint_cf.cf_unitregistry()],
    ids=["pint", "pint-cf"],
)
@pytest.mark.parametrize(
    ("units", "factor"),
    [
        ("meter", 1.0),
        ("kilometer", 1000.0),
        ("foot", 0.3048),
        ("nautical_mile", 1852.0),
    ],
)
def test_quantity_from_any_registry_is_exact(registry, units, factor):
    assert np.array_equal(to_metres(registry.Quantity(H, units)), H * factor)


def test_short_form_is_never_read():
    assert to_metres(pint.UnitRegistry().Quantity(1.0, "nmi")) == 1852.0


def test_float32_magnitude_becomes_float64():
    assert to_metres(H.astype(np.float32), "km").dtype == np.float64


def test_numpy_scalar_gives_float():
    result = to_metres(np.float64(2.0), "km")
    assert result == 2000.0
    assert type(result) is float


@pytest.mark.parametrize(("units", "expected"), [(None, 1.0), ("km", 1000.0)])
def test_masked_values_become_nan(units, expected):
    result = to_metres(np.ma.masked_array([1.0, 2.0], mask=[False, True]), units)
    assert result[0] == expected
    assert np.isnan(result[1])


def test_non_finite_passes_through():
    assert np.isnan(to_metres(np.nan, "km"))
    assert to_metres(np.inf) == np.inf


@pytest.mark.parametrize("units", ["hPa", "degree", "1", "m2", ""])
def test_refuses_another_dimension(units):
    with pytest.raises(ValueError, match=re.escape(f"{units!r} is not a length")):
        to_metres(1.0, units)


def test_refuses_a_quantity_of_another_dimension():
    with pytest.raises(ValueError, match="'hectopascal' is not a length"):
        to_metres(pint.UnitRegistry().Quantity(1000.0, "hPa"))


@pytest.mark.parametrize("units", ["not_a_unit", "m!!", "3 km"])
def test_refuses_an_unreadable_unit(units):
    with pytest.raises(
        ValueError, match=re.escape(f"{units!r} is not a unit geovista can read")
    ):
        to_metres(1.0, units)


def test_refuses_a_unit_only_another_registry_defines():
    registry = pint.UnitRegistry()
    registry.define("gvhop = 1.7 * meter")
    with pytest.raises(ValueError, match="'gvhop' is not a unit geovista can read"):
        to_metres(registry.Quantity(1.0, "gvhop"))


def test_refuses_deprecated_cf_placeholder():
    with pytest.raises(ValueError, match="'level' is not a length"):
        to_metres(1.0, "level")


def test_refuses_units_given_twice():
    with pytest.raises(ValueError, match="not both"):
        to_metres(pint.UnitRegistry().Quantity(1.0, "m"), "km")
```

`tests/units/test_import.py`:

- `test_plain_numbers_never_import_pint`: run, with `subprocess.run([sys.executable, "-c", code], check=True)`, a `code` that imports `geovista.units`, calls `to_metres(1.0)` and `to_metres(np.ones(3))`, and asserts no name in `sys.modules` is `pint` or starts with `pint.`.
- `test_one_registry_serves_every_call`: `assert units._registry() is units._registry()`.
- `test_only_units_imports_pint`: parse every `.py` file under `Path(geovista.__file__).parent` with `ast`, and assert that the set of files with an `Import` or `ImportFrom` of a top-level `pint`, `pint_cf` or `lark` is exactly `{"units.py"}`.

- [ ] **Step 3: Run the tests to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/units -q`
Expected: FAIL, collecting with `ModuleNotFoundError: No module named 'geovista.units'`.

- [ ] **Step 4: Implement `src/geovista/units.py`**

The licence header, `from __future__ import annotations`, a module docstring with `.. versionadded:: 0.6.0`, `__all__`, and `pint`, `ArrayLike` and `NDArray` imported under `TYPE_CHECKING` only. Then the four helpers of the Interfaces block and `to_metres`:

- `_quantity` imports `pint.errors.PintError` and `lark.exceptions.LarkError` inside the function. It parses the label with `_registry().Unit(label)` inside `warnings.catch_warnings()` with `warnings.simplefilter("ignore", DeprecationWarning)` (call 7), and turns `PintError`, `LarkError` or `ValueError` into `ValueError(f"{label!r} is not a unit geovista can read")`, raised `from` the original. Given a quantity and `units` too, it raises `ValueError("give the units on the quantity or as units, not both")`.
- `_magnitude` is `np.ma.filled(np.ma.asarray(value, dtype=np.float64), np.nan)`.
- `to_metres` returns `_result(_magnitude(value))` when `_quantity` returns `None`. Otherwise, unless the unit's dimensionality equals that of `meter`, it raises `ValueError(f"{label!r} is not a length")`, and returns `_result` of the quantity's magnitude in `meter`.

Its docstring documents the three forms, the units for a plain number, and `Raises ValueError`, with `.. versionadded:: 0.6.0` under `Notes`.

- [ ] **Step 5: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/units -q`
Expected: PASS, every test.

- [ ] **Step 6: Run the hooks**

Run: `pixi run --frozen -e geovista pre-commit run --files requirements/pypi-core.txt pyproject.toml src/geovista/units.py tests/units/__init__.py tests/units/test_to_metres.py tests/units/test_import.py`
Expected: every hook Passed or Skipped, `mypy` and `numpydoc-validation` included.

- [ ] **Step 7: Commit**

```bash
git add requirements/pypi-core.txt pyproject.toml pixi.lock src/geovista/units.py tests/units docs/src/developer/plans/2026-10-27-globe-units.md
pixi run --frozen -e geovista git commit -m "feat: read a length in any form geovista accepts, as metres"
```

### Task 2: Angles

**Files:**
- Modify: `src/geovista/units.py`
- Create: `tests/units/test_to_degrees.py`
- Modify: `tests/units/test_import.py` (`to_degrees(1.0)` joins the subprocess)

**Interfaces:**
- Consumes: `_registry`, `_magnitude`, `_quantity` and `_result` from Task 1.
- Produces: `to_degrees(value: ArrayLike | pint.Quantity, units: str | None = None) -> float | NDArray[np.float64]`, with the overload `(value: float, units: str | None = None) -> float`.

- [ ] **Step 1: Write the failing tests**

```python
def test_plain_number_is_degrees():
    result = to_degrees(45.0)
    assert result == 45.0
    assert type(result) is float


@pytest.mark.parametrize(
    "units", ["degree", "degrees", "degrees_north", "degrees_east"]
)
def test_cf_degrees(units):
    assert to_degrees(45.0, units) == 45.0


def test_radians():
    assert to_degrees(np.pi, "radian") == 180.0


def test_arcseconds():
    assert to_degrees(3600.0, "arcsecond") == pytest.approx(1.0, rel=1e-12)


@pytest.mark.parametrize(
    "registry",
    [pint.UnitRegistry(), pint_cf.cf_unitregistry()],
    ids=["pint", "pint-cf"],
)
def test_quantity_from_any_registry(registry):
    result = to_degrees(registry.Quantity(np.array([0.0, np.pi / 2]), "radian"))
    assert result == pytest.approx([0.0, 90.0], rel=1e-12)


def test_turns_from_another_registry():
    assert to_degrees(pint.UnitRegistry().Quantity(0.5, "turn")) == pytest.approx(
        180.0, rel=1e-12
    )


@pytest.mark.parametrize("units", ["1", "percent", "", "m/m"])
def test_refuses_a_dimensionless_angle(units):
    with pytest.raises(ValueError, match=re.escape(f"{units!r} is dimensionless")):
        to_degrees(1.0, units)


def test_refuses_a_dimensionless_quantity_as_an_angle():
    with pytest.raises(ValueError, match="'dimensionless' is dimensionless"):
        to_degrees(pint.UnitRegistry().Quantity(1.0, "dimensionless"))


@pytest.mark.parametrize("units", ["m", "hPa"])
def test_refuses_another_dimension(units):
    with pytest.raises(ValueError, match=re.escape(f"{units!r} is not an angle")):
        to_degrees(1.0, units)
```

- [ ] **Step 2: Run the tests to watch them fail**

Run: `pixi run --frozen -e geovista pytest tests/units/test_to_degrees.py -q`
Expected: FAIL, with `ImportError: cannot import name 'to_degrees'`.

- [ ] **Step 3: Implement `to_degrees` in `src/geovista/units.py`**

With no units, it returns `_result(_magnitude(value))`. Otherwise, it takes `_, base = _registry().get_base_units(unit)`. When `base` is the registry's `radian`, it returns `_result` of the magnitude in `degree`. When the unit is dimensionless, it raises `ValueError(f"{label!r} is dimensionless, and an angle needs an angular unit, such as 'degree' or 'radian'")`. Anything else raises `ValueError(f"{label!r} is not an angle")`. Add `"to_degrees"` to `__all__`, and give it the docstring of `to_metres` for angles.

- [ ] **Step 4: Run the tests to watch them pass**

Run: `pixi run --frozen -e geovista pytest tests/units -q`
Expected: PASS, every test in the package.

- [ ] **Step 5: Run the hooks**

Run: `pixi run --frozen -e geovista pre-commit run --files src/geovista/units.py tests/units/test_to_degrees.py tests/units/test_import.py`
Expected: every hook Passed or Skipped.

- [ ] **Step 6: Commit**

```bash
git add src/geovista/units.py tests/units
pixi run --frozen -e geovista git commit -m "feat: read an angle in any form geovista accepts, as degrees"
```

### Task 3: Land the Row

**Files:**
- Create: `changelog/<PR>.feature.rst`
- Modify: `docs/src/developer/specs/2026-10-26-globe-heights-layers-design.md` (§9 row 1)

- [ ] **Step 1: Run the whole suite**

Run: `CI=true LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe pixi run --frozen -e geovista tests-unit`
Expected: PASS, with no new skips.

- [ ] **Step 2: Build the docs strictly**

Run the incremental `sphinx-build` of `AGENTS.md` with `-W --keep-going`, then `grep -rl to_metres docs/_build/html/reference/generated/api`.
Expected: the build succeeds, and the API reference has a page for `geovista.units`.

- [ ] **Step 3: Open the pull request**

Push `feat/globe-units` and open it with the labels of the Global Constraints, and a humanized body. The body notes that the conda-forge feedstock needs `pint` and `pint-cf` at the next release.

- [ ] **Step 4: Write the fragment, and mark the row**

`changelog/<PR>.feature.rst`:

```rst
Added ``geovista.units``, which reads a length or an angle given as a plain
number, as a ``pint`` quantity from any registry, or with a CF unit string, and
converts it to metres or degrees. ``pint`` and ``pint-cf`` are new
dependencies. (:user:`claude`)
```

Mark globe spec §9 row 1 ``✅ landed (YYYY-MM-DD, {pull}`<PR>`)``.

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py <PR> "changelog/<PR>.feature.rst"`, then `pixi run --frozen -e geovista pytest tests/test_spec_conventions.py tests/docs/test_readingtime_coverage.py tests/test_status_references.py -q`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>`.
Expected: the fragment passes, the tests pass, and every status reference holds.

- [ ] **Step 5: Commit and push**

```bash
git add changelog/<PR>.feature.rst docs/src/developer/specs/2026-10-26-globe-heights-layers-design.md
pixi run --frozen -e geovista git commit -m "docs: mark globe spec row 1 landed, and add the changelog fragment"
git push
```
