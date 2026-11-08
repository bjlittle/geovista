# Missing Positions in the Meshes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 4 of positions spec §9. `Transform.from_unstructured`, and `from_2d` and the `Transform` constructor through it, read the test of §4.1 where they read a mask shared by `xs` and `ys` today, and apply the rules of §3.3 to each missing point; `Transform.from_1d` refuses a NaN bound as it refuses a masked one, and `Transform.to_structured_grid` refuses a missing position the same way.

**Architecture:** In `from_unstructured`, row 1's `_missing_positions` replaces the comparison of whole masks, so a coordinate masked alone, masks that differ and a NaN coordinate each keep their point out of the faces and out of the transform, as a point masked alike is kept today. The constructor attaches `data` after the mesh is built, so it keeps which faces were dropped and cuts data given for each face, as `from_unstructured` does. A new `Transform._refuse_missing_bounds` refuses a missing bound for both `from_1d` and `to_structured_grid`.

**Tech Stack:** NumPy masked arrays, `pyproj`, `pyvista` 0.49.2, `pint` through `geovista.units`, pytest.

**Spec:** `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (`positions spec §…`): §2 decisions 1, 2 and 7, §3.3, §4.1, §4.6, §6, §9 row 4 and §11.

## Global Constraints

- A position is missing when either of its coordinates is masked or NaN (positions spec §2 decision 1). A masked array whose mask is `nomask` has no missing position, and a `None` is missing (§4.1).
- An infinite coordinate is refused with a `ValueError` naming the argument, `xs` or `ys` (§2 decision 2).
- A mesh treats every missing point as the bridge treats a masked one (§2 decision 7): the rules of §3.3 apply to each, a face of a shape keeping its other vertices while three remain ({pull}`2599`), the point left out of the transform and stood on the first point present ({pull}`2620`, {pull}`2626`), a face of a connectivity array that uses it dropped, with a warning counting the faces, and data given for each face cut to the faces that remain ({pull}`2628`).
- `from_1d` refuses a NaN bound with the error it gives a masked one, and `to_structured_grid` refuses a missing position in `xs` or `ys` the same way (§4.6).
- The test reads coordinates after a `pint` quantity is read in its units and before any point is transformed (§4.1).
- No new public name. `mypy` runs strict over the whole package, with no new override, and `ruff` allows 91 statements in a function. Warnings are errors under pytest. Docstrings are NumPy style, and `.. versionchanged::` is not used.
- Commit through `pixi run --frozen -e geovista git commit ...` after `pixi run --frozen -e geovista pre-commit run --files <paths>`. The fragment credits ``(:user:`claude`)``. The pull request carries `type: bug` and `agentic`, and closes no issue: {issue}`2849` closed when rows 1 and 2 landed. No issue follows a closing keyword in the body or any commit message.
- A test named as evidence in §11 cites its decision in its docstring, as "Holds positions spec §2 decision 7." (ledger spec §3.4), on the line the build links to (ledger spec row 9, {pull}`2902`).
- Cite a specification section in plain text (`positions spec §4.6`), never with a `{ref}` role.

## Calls Made in This Plan

{user}`bjlittle` confirmed on 2026-11-06 that the specification fixes how rows 1 to 5 behave (workflow rule 2.7). The calls are mine.

1. **The test is read on the points as given.** `from_unstructured` calls `_missing_positions(xs, ys, x_name="xs", y_name="ys")` before it flattens them, and keeps today's `mask` of `None` when no point is missing. So an infinite coordinate is named at its index as given: `"'xs' cannot be infinite, got inf at index (2, 2)."` for a grid, `"... at index 8."` for points in 1D.
2. **The warning names a missing point.** `"geovista connectivity defines 1 face that uses a missing point, which is dropped."`, and `"... 2 faces that use a missing point, which are dropped."`. Only the word changes. The tests of {pull}`2628` in `tests/bridge/test_from_2d.py` and `tests/bridge/test_from_unstructured.py` match the new word.
3. **The helpers say what they do.** `_drop_masked_faces` becomes `_drop_missing_faces` and `_transform_unmasked` becomes `_transform_present`, each with its docstring on a missing point. Nothing outside `bridge.py` names them.
4. **The constructor cuts data given for each face.** `Transform(xs, ys)` builds its mesh, and `__call__` attaches `data` to it later, refusing data given for each face once a face is dropped: `Transform(<a point masked alike>)(data=<4 values>)` raises "Require mesh data with either '9' points or '3' cells, got '4' values." today, where `from_2d` cuts the same data. Row 4 makes a coordinate masked alone or NaN drop faces too, so without this a call that builds today would be refused. The body of `from_unstructured` moves to a private `Transform._unstructured(...) -> tuple[pv.PolyData, np.ndarray]`, which returns the mesh and which faces given it kept, and `from_unstructured` returns its mesh. `from_2d`'s connectivity moves to `Transform._connectivity_2d(xs, ys) -> np.ndarray`. The constructor builds through them, keeps `self._kept`, and `__call__` passes it to `_as_compatible_data` as `kept`. This widens {pull}`2628` to a point masked alike through the constructor too (workflow rule 1.2).
5. **The warnings name the same line.** With `_unstructured` between them, `_drop_missing_faces` warns with `stacklevel=4` and the warning of masked connectivity with fewer than three vertices with `stacklevel=3`, so each still names the line that called `from_unstructured`, or `from_2d`'s line inside `bridge.py`, as today.
6. **One refusal of a missing bound.** `Transform._refuse_missing_bounds(xs, ys, /) -> None` reads each axis with row 1's `_missing`, which refuses an infinite value naming `xs` or `ys`, and raises `"Require an x-axis array with no masked or NaN bounds, got '1'."`, or `y-axis`, counting the entries missing as today's message counts the masked ones. `_as_contiguous_1d` calls it in place of its two counts of masked bounds, and `to_structured_grid` calls it after it reads its quantities.
7. **Everything else stays.** A missing point stays in the mesh, at the first point present, so data given for each point still fits; heights given for each point still fit; a point no face uses raises nothing; and a mesh whose every point is missing builds with no faces, as one masked alike does today.
8. **Evidence.** A new `tests/bridge/test_missing_mesh_positions.py` holds the tests of §2 decision 7. Decisions 1 and 2 stay pending until row 5 lands.
9. **One fragment, `2908.bugfix.rst`.** The branch is `fix/missing-positions-meshes`, and the plan is the first commit of draft pull request {pull}`2908` (workflow rule 2.3), which marks row 4 in progress (workflow rule 2.4).

## Review Focus

1. **A missing point in a shape.** Given `connectivity=(2, 4)`, the face keeps its other vertices, as a triangle, with no warning. `test_keeps_the_other_vertices_of_a_shape_face` (Task 1).
2. **Every point missing.** The mesh builds with no faces, and the warning counts all four. `test_builds_no_faces_when_every_point_is_missing` (Task 1).
3. **Heights and colours.** Heights given for each point still fit, and colours given for each face with `rgb=True` keep those of the faces that remain. `test_keeps_heights_for_each_point`, `test_cuts_colours_for_each_face` (Task 1).
4. **A hidden value beyond a bounded projection.** A point masked alone, or NaN, whose other value lies outside the domain of the CRS, never reaches the transform. `test_leaves_a_missing_point_out_of_the_transform` (Task 1).
5. **Data of another count through the constructor.** Data neither for each point, each face given nor each face kept is refused, as today. `test_constructor_refuses_data_of_another_count` (Task 2).

---

Measured on 2026-11-08 at `d1e19a46` (`main` after {pull}`2905`), with Python 3.14.10, NumPy 2.5.4, `pyvista` 0.49.2 and `pint` 0.26.2, in the `geovista` environment, on a grid of 3 by 3 points and 4 quads:

- `from_2d` with a longitude masked alone, or masks that differ, builds all 4 faces, at the values under the masks, without a warning; with a NaN longitude or latitude, all 4 faces, with a NaN point; with an infinite longitude, all 4 faces with a NaN point, and NumPy's "invalid value encountered in remainder". With the point masked alike it drops the faces that use it, warning "defines 4 faces that use a masked point, which are dropped." for the centre.
- `from_unstructured` with a connectivity array and a NaN longitude builds all its faces with a NaN point; given `connectivity=(2, 4)` and a point masked alike, the face keeps three vertices, without a warning.
- `Transform(<point masked alike>)(data=<4 values>)` raises "Require mesh data with either '9' points or '3' cells, got '4' values."; `from_2d` given the same data cuts it to 3.
- `from_1d` refuses a masked bound, "Require an x-axis array with no masked bounds, got '1'."; given a NaN or infinite bound it builds 4 faces with 3 NaN points.
- `to_structured_grid` builds 18 points at the value under a masked `xs`, 6 NaN points for a NaN one, and 6 NaN points with NumPy's warnings for an infinite `ys`.
- No sample of `geovista.pantry.data` has a coordinate masked, NaN or infinite, so no example's mesh changes.

### Task 1: Meshes Read the Test of §4.1

**Files:**
- Create: `tests/bridge/test_missing_mesh_positions.py`
- Modify: `src/geovista/bridge.py` (`from_unstructured`, `_drop_masked_faces`, `_transform_unmasked`, and the docstrings of `from_2d` and `from_unstructured`)
- Modify: `tests/bridge/test_from_2d.py`, `tests/bridge/test_from_unstructured.py` (the warning's word)

**Interfaces:**
- Consumes: `geovista.common._missing_positions(xs, ys, *, x_name, y_name) -> NDArray[np.bool_]`, from row 1.
- Produces: `Transform._drop_missing_faces(connectivity, mask, /)` and `Transform._transform_present(xs, ys, crs, mask, /)`, with today's signatures.

- [ ] **Step 1: Write the tests**

Module constants: `LONS = np.tile([0.0, 10.0, 20.0], (3, 1))`, `LATS = np.repeat([0.0, 10.0, 20.0], 3).reshape(3, 3)`, and `CORNER = (2, 2)`, a point only the fourth face uses. Helpers: `masked(values, *indices)` and `nan(values, *indices)`, as in `tests/bridge/test_missing_positions.py`; `alike(*indices)`, the pair masked alike at those points, which builds the reference; and `assert_same_mesh(result, expected)`, comparing `faces` exactly and `points` with `np.testing.assert_allclose`. Each test of a dropped face is checked against the reference built inside `pytest.warns`, and each named as evidence says "Holds positions spec §2 decision 7.".

- `test_drops_the_faces_of_a_missing_point(xs, ys, missing)` through `from_2d`, with ids `lon-masked` `(masked(LONS, CORNER), LATS)`, `lat-masked`, `lon-nan`, `lat-nan`, `quantity` `(UREG.Quantity(masked(LONS, CORNER), "degree"), LATS)` and `masks-differ` `(masked(LONS, CORNER), masked(LATS, (0, 0)))`, with `missing` the points the reference masks alike: warns "defines 1 face that uses a missing point, which is dropped" (`masks-differ`: "defines 2 faces that use a missing point, which are dropped"), and `assert_same_mesh` against `from_2d(*alike(*missing))`.
- `test_drops_through_every_entry_point(build)`, with ids `from_unstructured` (a connectivity array of the 4 quads, on the points raveled) and `constructor` (`Transform(xs, ys)()`), each given `nan(LONS, CORNER)`: the same warning and mesh as its reference.
- `test_keeps_the_other_vertices_of_a_shape_face()`: 8 points, `connectivity=(2, 4)`, point 2 NaN: no warning, face sizes `[3, 4]`, the same mesh as the reference.
- `test_builds_no_faces_when_every_point_is_missing()`: `LONS` all NaN: warns "defines 4 faces that use a missing point, which are dropped"; `n_cells == 0`, `n_points == 9`.
- `test_keeps_heights_for_each_point()`: `height=np.arange(9.0)` with `nan(LONS, CORNER)`: builds 3 faces.
- `test_cuts_colours_for_each_face()`: `rgb=True`, `data` of 4 colours, `nan(LONS, CORNER)`: the cell data is the first 3 colours.
- `test_leaves_a_missing_point_out_of_the_transform(mocker, xs)`: in a bounded projected CRS, a point whose x is masked alone, or NaN, and whose y lies outside the CRS's domain, as the {pull}`2620` test in `tests/bridge/test_from_unstructured.py` sets up: no error, and `mocker.spy(bridge, "transform_points")` shows the transform given 8 points.
- `test_refuses_infinite(xs, ys, name)` with ids `xs`, `ys`, an infinite value at `CORNER` of that coordinate: `from_2d` raises `ValueError` matching `"'{name}' cannot be infinite, got inf at index (2, 2)."`.
- `test_keeps_present_points(xs)` with ids `list` and `nomask`: no warning, 4 faces.

In `tests/bridge/test_from_2d.py` and `tests/bridge/test_from_unstructured.py`, each match on "a masked point" reads "a missing point".

- [ ] **Step 2: Run them to see them fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/bridge/test_missing_mesh_positions.py tests/bridge/test_from_2d.py tests/bridge/test_from_unstructured.py`
Expected: FAIL — the cases of a point not masked alike build every face unwarned, the infinite cases do not raise, and the tests of {pull}`2628` do not find "a missing point"; `test_keeps_the_other_vertices_of_a_shape_face` fails on face sizes `[4, 4]`; `test_keeps_present_points` PASSES.

- [ ] **Step 3: Read the test in `from_unstructured`, and rename the helpers**

Replace the comparison of whole masks with call 1, flattening the result with the points. Rename the helpers and reword the warning by calls 2 and 3. `from_2d`'s docstring says a quad-face with a missing vertex, one whose x or y value is masked or NaN, is dropped, with a warning; `from_unstructured`'s says the same of a face of a connectivity array; both say an infinite value is refused.

- [ ] **Step 4: Run them to see them pass**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/bridge`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/bridge/test_missing_mesh_positions.py tests/bridge/test_from_2d.py tests/bridge/test_from_unstructured.py src/geovista/bridge.py
pixi run --frozen -e geovista git commit -m "fix: drop the faces of a missing point from a mesh"
```

### Task 2: The Constructor Cuts Data Given for Each Face

**Files:**
- Modify: `src/geovista/bridge.py` (`from_unstructured`, `from_2d`, `__init__`, `__call__`)
- Test: `tests/bridge/test_missing_mesh_positions.py`

**Interfaces:**
- Consumes: Task 1's `from_unstructured`.
- Produces: `Transform._unstructured(xs, ys, /, *, <from_unstructured's keywords>) -> tuple[pv.PolyData, np.ndarray]` and `Transform._connectivity_2d(xs, ys) -> np.ndarray`.

- [ ] **Step 1: Write the tests**

- `test_constructor_cuts_data_for_each_face(xs, ys)`, with ids `nan` `(nan(LONS, CORNER), LATS)` and `alike` `alike(CORNER)`: under the warning, `Transform(xs, ys)(data=[1.0, 2.0, 3.0, 4.0])` has cell data `[1.0, 2.0, 3.0]`.
- `test_constructor_keeps_data_for_each_point()`: `data=np.arange(9.0)` fits the 9 points.
- `test_constructor_refuses_data_of_another_count()`: `data` of 5 values raises "Require mesh data with either '9' points or '3' cells, got '5' values.".

- [ ] **Step 2: Run them to see the cut fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/bridge/test_missing_mesh_positions.py -k constructor`
Expected: both cases of `test_constructor_cuts_data_for_each_face` FAIL with "got '4' values"; the other two PASS.

- [ ] **Step 3: Build the constructor through `_unstructured`**

By calls 4 and 5. A mesh built through `from_1d` drops no face, so its `_kept` is `None`.

- [ ] **Step 4: Run them to see them pass**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/bridge`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/bridge/test_missing_mesh_positions.py src/geovista/bridge.py
pixi run --frozen -e geovista git commit -m "fix: cut the data given for each face when the constructor drops one"
```

### Task 3: A Missing Bound Is Refused

**Files:**
- Modify: `src/geovista/bridge.py` (`_as_contiguous_1d`, `to_structured_grid`, and the docstrings of `from_1d` and `to_structured_grid`)
- Modify: `tests/bridge/test_from_1d.py` (the refusal's words)
- Test: `tests/bridge/test_missing_mesh_positions.py`

**Interfaces:**
- Consumes: `geovista.common._missing(values, *, name) -> NDArray[np.bool_]`, from row 1.
- Produces: `Transform._refuse_missing_bounds(xs, ys, /) -> None`.

- [ ] **Step 1: Write the tests**

- `test_from_1d_refuses_a_missing_bound(xs, ys, axis)`, with ids `x-nan` `([0.0, np.nan, 20.0], [0.0, 10.0, 20.0], "x")`, `y-nan` and `x-masked`: raises `ValueError` matching `"Require an {axis}-axis array with no masked or NaN bounds, got '1'."`.
- `test_from_1d_refuses_an_infinite_bound()`: `[0.0, np.inf, 20.0]` raises matching `"'xs' cannot be infinite, got inf at index 1."`.
- `test_to_structured_grid_refuses_a_missing_position(xs, ys, axis)`, with ids `x-masked`, `x-nan` and `y-nan`, `zs` of `[0.0, 1000.0]`: the same message.
- `test_to_structured_grid_refuses_infinite()`: an infinite `ys` raises matching `"'ys' cannot be infinite, got inf at index 1."`.

In `tests/bridge/test_from_1d.py`, the match "no masked bounds" reads "no masked or NaN bounds".

- [ ] **Step 2: Run them to see them fail**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/bridge/test_missing_mesh_positions.py tests/bridge/test_from_1d.py -k "bound or structured"`
Expected: FAIL — `from_1d` and `to_structured_grid` build with NaN points, and the masked bound's message lacks "or NaN".

- [ ] **Step 3: Add `_refuse_missing_bounds`, and call it**

By call 6. `from_1d`'s docstring says a masked or NaN bound is a gap in its axis and is refused, as is an infinite one; `to_structured_grid`'s Raises section lists a masked, NaN or infinite value in `xs` or `ys`.

- [ ] **Step 4: Run them to see them pass**

Run: `pixi run --frozen -e geovista pytest -q -p no:randomly tests/bridge`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/bridge/test_missing_mesh_positions.py tests/bridge/test_from_1d.py src/geovista/bridge.py
pixi run --frozen -e geovista git commit -m "fix: refuse a missing bound in from_1d and to_structured_grid"
```

### Task 4: Landing the Row

**Files:**
- Modify: `docs/src/developer/specs/2026-11-06-missing-positions-design.md` (§9 row 4, §11)
- Modify: this plan's Follow-ups, before merge
- Create: `changelog/2908.bugfix.rst`

- [ ] **Step 1: Watch each clause fail when it regresses**

Mutate one at a time, run the named test, see it fail, and revert:
- `from_unstructured` compares whole masks again: `test_drops_the_faces_of_a_missing_point`;
- it reads only the masks, not NaN: its `lon-nan` and `lat-nan` cases;
- it transforms every point: `test_leaves_a_missing_point_out_of_the_transform`;
- `__call__` passes no `kept`: `test_constructor_cuts_data_for_each_face`;
- `_refuse_missing_bounds` counts only the masked: `test_from_1d_refuses_a_missing_bound[x-nan]`;
- `to_structured_grid` no longer calls it: `test_to_structured_grid_refuses_a_missing_position`.

- [ ] **Step 2: Write the fragment, and mark the decision and the row**

`changelog/2908.bugfix.rst`, humanized, citing `geovista.bridge.Transform` and its `from_unstructured`, `from_2d`, `from_1d` and `to_structured_grid` by their documented paths, and naming the row as `row 4 of positions spec §9`. It says that a coordinate masked alone, masks that differ, or a NaN coordinate built faces at the value under a mask or with a NaN vertex; that such a point now drops its faces, with a warning, as a point masked alike does; that the constructor now cuts data given for each face; and that `from_1d` and `to_structured_grid` refuse a NaN position.

In §11, §2 decision 7 becomes ``✅ verified (<DATE>, {pull}`2908`)`` with evidence `tests/bridge/test_missing_mesh_positions.py`. Last, row 4 of §9 becomes ``✅ landed (<DATE>, {pull}`2908`)``. `<DATE>` is the day of this commit, corrected if the merge slips to another day (workflow rule 2.4).

List any issue this pull request raises under Follow-ups below, and in the pull request's description (workflow rule 4.5); each one deferred from this row is an open item of the spec, in this pull request (workflow rule 2.8).

Run: `pixi run --frozen -e docs python .github/scripts/changelog.py 2908 "changelog/2908.bugfix.rst"`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/test_spec_conventions.py tests/test_status_references.py tests/test_renumbering.py tests/test_verification_report.py`, then `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status 2908`.
Expected: the fragment passes, the tests pass, and every status reference holds.

- [ ] **Step 3: Commit, then run the whole suite and the docs build on that commit**

```bash
git add changelog/2908.bugfix.rst
pixi run --frozen -e geovista git commit -am "docs: mark positions spec row 4 landed, verify §2 decision 7, and add the fragment"
```

Run: the strict `sphinx-build` of `AGENTS.md` with `-E`, `--fail-on-warning` and `--keep-going`, then `pixi run --frozen -e geovista pytest -q -p no:randomly tests/docs/test_geovista_ledger.py`, then `CI=true GALLIUM_DRIVER=llvmpipe pixi run --frozen -e test-py313 tests-unit` and the same with `-e test-py314`.
Expected: the build succeeds, the evidence links to its citing line, and the suites PASS with no new skips and no image baseline regenerated.

- [ ] **Step 4: Push, and mark the pull request ready**

Push, confirm it with `git ls-remote` (workflow rule 4.6), check `gh pr view 2908 --json closingIssuesReferences` lists none, and mark the pull request ready once the final review's fixes have landed.

## Follow-ups

None. The final review left four minor points: the docstring of `from_unstructured` is corrected, and the other three stand, as the pull request's description says.
