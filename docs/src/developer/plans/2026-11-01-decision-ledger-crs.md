# Decision Ledger, Row 5: The CRS Specification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 5 of ledger spec §8: the crs specification joins the ledger, its 14
decisions gaining state and provenance, and a §12 Verification table recording each as
verified, signed off or pending.

**Architecture:** No library change. The decisions are numbered already, so each gains
its `🤝 Agreed` state and provenance in place. The tests that already hold a decision
gain a citation of it, once a mutation has shown that they fail when it regresses. The
specification then leaves `UNLEDGERED`.

**Tech Stack:** MyST Markdown, pytest, the `check-spec-status` and `verification-report`
pixi tasks.

**Spec:** `docs/src/developer/specs/2026-10-30-decision-ledger-design.md` (ledger spec),
§3.9 above all, with §3.2 and §3.4 for the forms.

## Global Constraints

- Provenance (ledger spec §3.9 step 2), from `git log -S` on each title: decisions 1 to 13 are `2026-10-24, {user}`bjlittle`, {pull}`2717``, and decision 14 is `2026-10-27, {user}`bjlittle`, {pull}`2752``, as ledger spec §3.9 already records.
- Titles and text stay verbatim; the opening sentence of §2, "These were decided with {user}`bjlittle` while the design was written.", stays.
- The specification gains `(crs-spec-12)=` / `## 12. Verification` after its §11 References, opening "Each row follows ledger spec §3.4.".
- A verified row cites `<DATE>, {pull}`<PR>``, and a signed-off row `<DATE>, {user}`bjlittle`, {pull}`<PR>``; `<PR>` is this pull request and `<DATE>` the day it merges, redated if the merge slips past midnight UTC.
- A pending row's Evidence names the rows of §10 that deliver it, as `row N of §10` or `rows N to M of §10`, so the verification report and a reader see what is owed.
- **Every verified row's test is shown to fail under a mutation of what the decision holds** before it is cited (the lesson of row 4, where two cited tests passed with their decision broken). Each mutation is reverted, and recorded in the ledger of this plan's workspace.
- A citation in a test is a docstring sentence, `Holds crs spec §2 decision N.`
- An agent never adds the `signed-off` label; {user}`bjlittle` adds it to this pull request.
- No decision is retired: §10 rows 2 to 13 have not landed, and nothing has overtaken any of the 14. No decision is undelivered: row 1, the only row landed, delivered the coverage test decision 12 needs.

## The Proposed Ledger

Each row is {user}`bjlittle`'s judgement in review (ledger spec §3.9 step 4). Only row 1
of §10 has landed (the coverage test, {pull}`2721`), so most decisions stay pending.

| # | Decision | Proposed | Evidence |
|---|---|---|---|
| 1 | Never quietly wrong, and never silently drop data | ⏳ pending | rows 3 to 13 of §10 |
| 2 | Globe first | ⏳ pending | rows 3 to 4 of §10 |
| 3 | Rebuild from the ground up | ⏳ pending | rows 3 to 4 of §10 |
| 4 | Breaking changes are allowed | ✍️ signed off | "Checked in review that {pull}`2766` used it, removing `radius=` with no alias as scene spec §2 decision 2 says it may, and recorded the break in a `breaking` fragment." |
| 5 | cartopy is not a foundation | ⏳ pending | rows 3 to 5 of §10 |
| 6 | Learn from cartopy, without repeating its journey | ⏳ pending | row 4 of §10 |
| 7 | Three ways in | ⏳ pending | row 5 of §10 |
| 8 | A safe default for data meshes | ⏳ pending | rows 3 to 13 of §10 |
| 9 | Cut once, map many | ⏳ pending | row 12 of §10 |
| 10 | Coverage commitment | ⏳ pending | rows 4 to 11 of §10 |
| 11 | Build on specialised packages | ✍️ signed off | "Checked in review that the units are `pint`'s and `pint-cf`'s ({pull}`2754`), projection is PROJ's through `pyproj`, and mesh processing is `pyvista`'s and VTK's." |
| 12 | No release regresses a working use | ✅ verified | `tests/transform/test_projection_coverage.py`: `test_method_outcome` and `test_cartopy_outcome` fail when a working method's outcome changes |
| 13 | Units are first class, through `pint` | ✅ verified | `tests/units/test_to_metres.py`, `tests/units/test_to_degrees.py`: a CF string read through `pint-cf`; replacing its registry with plain `pint` fails seven of their tests (measured on 2026-11-01). `tests/units/test_import.py`: only `geovista.units` imports `pint`, and plain numbers never do |
| 14 | A mesh describes itself, in any file VTK writes | ⏳ pending | row 2 of §10, row 13 of §10 |

Two verified, two signed off, ten pending: `✅ 2 · ✍️ 2 · ⏳ 10 · 🗄️ 0`.

**For judgement:**

- **Decision 13 is verified ahead of its roadmap row.** Units arrived with globe spec §9 row 1 ({pull}`2754`), but crs spec §10 row 2, which gathers rows 1 to 5 of globe spec §9, has not landed. The decision is delivered whole, so it is verified rather than left waiting on heights and layers.
- **Decision 14 stays pending although half of it holds.** `tests/globe/test_round_trip.py` shows a mesh's CRS and globe surviving `.vtk`, `.vtp`, `.vtu` and `.vtkhdf`. No test saves its heights, and the record of §4.6 does not exist until row 13. Verifying it now would claim more than the tests show.
- **Decisions 4 and 11 are principles, not deliverables**, so a sign-off records that they have been followed so far. Leaving them pending would leave them pending for ever, since no row of §10 delivers them; ledger spec §3.5 would then refuse the last row.

## Review Focus

1. **A numbered decision that gains its state in place**: the list keeps its numbers, so `check-spec-renumbering` must pass, and every citation of a crs decision in the scene and heights specifications must still resolve (Task 1).
2. **A pending row whose Evidence names roadmap rows**: the conventions test reads `row N of` for a candidate. Rows 3 to 13 here are `not started`, so naming them must not trip item 7 of ledger spec §3.6 while the roadmap is unfinished (Task 3).
3. **A mutation that the cited test does not catch**: the test is not cited, and the row becomes a sign-off or stays pending, with the change ledgered as a ruling (Task 2).
4. **A citation wrapped across lines** (`crs spec §2\n   decision 14`) in the heights specification: it must resolve as one citation once the decisions carry anchors (Task 1).
5. **The sign-off gate**: two rows fail `status references` until {user}`bjlittle` labels this pull request (Task 4).

---

### Task 1: State and provenance

**Files:**
- Modify: `docs/src/developer/specs/2026-10-23-globe-first-crs-design.md`

- [ ] **Step 1:** Turn each `N. **Title.**` of §2 into `N. **🤝 Agreed** (<provenance>) — **Title.**`, with the provenance of Global Constraints, and reflow §2 alone to 92 columns without splitting a citation.
- [ ] **Step 2:** `pixi run --frozen -e test-py313 python -m pytest tests/test_spec_conventions.py -q -n 8` → PASS; `pixi run --frozen -e test check-spec-renumbering` → PASS.
- [ ] **Step 3:** Commit — `docs: give the crs decisions their state and provenance`.

### Task 2: The tests cite what they hold

**Files:**
- Modify: `tests/transform/test_projection_coverage.py`, `tests/units/test_to_metres.py`, `tests/units/test_to_degrees.py`, `tests/units/test_import.py`

- [ ] **Step 1:** For decision 12, mutate `transform_mesh` so one method of `WORKS` (say `robin`) projects wrongly, and confirm `test_method_outcome[robin]` fails; revert. For decision 13, confirm the registry mutation above and that `test_only_units_imports_pint` fails if `geovista.common` imports `pint`; revert.
- [ ] **Step 2:** Add each citation of The Proposed Ledger's verified rows.
- [ ] **Step 3:** Run the four modules and the conventions suite → PASS; `ruff` clean.
- [ ] **Step 4:** Commit — `tests: cite the crs decisions each test holds`.

### Task 3: The Verification section

**Files:**
- Modify: the crs specification; `tests/test_spec_conventions.py` (`UNLEDGERED` loses it)

- [ ] **Step 1:** Append §12 Verification, its rows as The Proposed Ledger gives them.
- [ ] **Step 2:** Conventions suite → PASS; the incremental docs build with `-W --keep-going` → `build succeeded`, the summary line reading `✅ 2 · ✍️ 2 · ⏳ 10 · 🗄️ 0: 2 of 14 decisions in force verified`.
- [ ] **Step 3:** Commit — `docs: bring the crs specification into the ledger`.

### Task 4: Landing

- [ ] **Step 1:** `pixi run --frozen -e test verification-report crs`: findings only for the two signed-off decisions, if nothing cites them, and none for a verified row.
- [ ] **Step 2:** In `docs/AGENTS.md`, extend the spec-status line: a verified row's test must fail when its decision regresses, so check it by mutation (#2796). Keep the file under 200 lines.
- [ ] **Step 3:** `changelog/<PR>.contributor.rst`, crediting `:user:`claude``, validated with `.github/scripts/changelog.py`; humanize it.
- [ ] **Step 4:** Full suite with images, mypy, the docs build, and `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>` → everything holds but the two sign-offs, until {user}`bjlittle` adds `signed-off`. Final review on `opus`.
- [ ] **Step 5 (last commit):** ledger spec §8 row 5 → `✅ landed (<DATE>, {pull}`<PR>`)`.
