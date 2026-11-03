# Ledger Row 6 and Items Row 5: The Globe Family Brought In Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 6 of ledger spec §8 and row 5 of items spec §8 together. The decisions
of the globe, scene and heights specifications join the ledger, and their open items and
the ledger specification's own item join the items grammar.

**Architecture:** No library change. One new test pins the name of `gvHeight`.
- **Decisions:** each gains its state and provenance in place. Globe §2 decision 4 is
  retired and replaced by a new decision 7, and each specification gains a Verification
  section.
- **Items:** each takes the grammar of items spec §3.2, with an issue and an owing row,
  and new roadmap rows are added where no unlanded row can owe an item.
- **Exemptions:** `UNLEDGERED` empties, and `UNITEMED` loses four specifications.

**Tech Stack:** MyST Markdown, pytest, the `check-spec-status`, `check-spec-renumbering`
and `verification-report` pixi tasks, and `gh` for issues and labels.

**Spec:** ledger spec, `docs/src/developer/specs/2026-10-30-decision-ledger-design.md`
(§3.2 to §3.5, §3.9), and items spec,
`docs/src/developer/specs/2026-11-02-open-items-design.md` (§3.2 to §3.6, §3.10).

## Global Constraints

- **Provenance** comes from the commit that first added each decision:
  - globe decisions 1 to 6: `2026-10-26, {user}`bjlittle`, {pull}`2732``;
  - scene decisions 1 to 9: `2026-10-27, {user}`bjlittle`, {pull}`2757``;
  - heights decisions 1 to 11: `2026-10-29, {user}`bjlittle`, {pull}`2771``. This is the commit date, as the crs bring-in used. Ledger spec §3.2's 2026-10-28 is only an example.
- **Globe decision 4 is retired** (bjlittle, 2026-11-03), because #2757 changed its meaning from "one exaggeration" to two factors, and scene spec §5 calls the old form rejected.
  - Its entry gets back its 2026-10-26 text, with state `🗄️ Retired (2026-10-27, {user}`bjlittle`, {pull}`2757`; agreed 2026-10-26, {pull}`2732`)` and a sentence: retired because the scene's vertical mapping became an exaggeration above and below sea level, replaced by §2 decision 7.
  - The text as it stands today becomes globe decision 7, `🤝 Agreed (2026-10-27, {user}`bjlittle`, {pull}`2757`)`.
- **Other rewordings since first written** are edits, not changes of meaning: globe decision 5 (#2757) and scene decision 4 (#2766).
- **Verification sections:** each specification gains `(<prefix>-spec-11)=` / `## 11. Verification` after its References, as earlier bring-ins did.
- **The rule for a span:** a decision whose text holds in full today is verified, and a later row adds evidence for its own entry points. A decision naming work of an unlanded row stays pending on that row.
- **Every verified row is mutation-checked** before its test is cited (docs/AGENTS.md). Cite with `Holds <prefix> spec §2 decision N.`, and date each row `<DATE>, {pull}`<PR>``. One exception: scene decision 5 is already cited from #2766, so its row is `✅ verified (2026-10-28, {pull}`2766`)`.
- **Items take the grammar of items spec §3.2.** 🔎 is found with `git log -S`. Each open item gets its own issue labelled `spec: open item`, and an agent may add the label.
- **No item settles.** Globe items 6 and 10 become ❓ Open, owed by new `candidate` rows whose trigger is "a user asks for it", admitted as unobservable (bjlittle, 2026-11-02).
- **Sign-offs:** an agent never adds `signed-off`. bjlittle signs off globe decisions 2, 3 and 6, and the retirement of globe decision 4.
- `<PR>` is this pull request and `<DATE>` its merge day.

## The Proposed Ledger

**Globe spec.** Rows 1 and 2 of §9 have landed.

| # | Proposed | Evidence |
|---|---|---|
| 1 | ⏳ pending | rows 3 to 5 of §9 |
| 2 | ✍️ signed off | "Checked in review that this specification designs heights in physical units and the replacement of `zlevel` as row 2 of crs spec §10, and leaves volumes, plumes and region solids to §7." |
| 3 | ✍️ signed off | "Checked in review that heights spec row 1 ({pull}`2777`) takes heights and depths only as lengths, through `height=`, `depth=` and the `zs` of `to_structured_grid`, and converts no model level." |
| 4 | 🗄️ retired (2026-10-27, {pull}`2757`) | replaced by §2 decision 7 |
| 5 | ⏳ pending | row 5 of §9 |
| 6 | ✍️ signed off | "Checked in review that §3.2, §3.5 and §3.6 record each measurement with its method, environment, commit and date." |
| 7 | ✅ verified | `tests/geoplotter/test_add_mesh.py`, `tests/geoplotter/test_GeoPlotterBase.py` (mutations: `_at_scene_globe` returning the mesh unchanged; a setter on `GeoPlotter.globe`) |

**Scene spec.** Rows 1 and 2 have landed, so every decision is verified.

| # | Evidence (mutation) |
|---|---|
| 1 | `tests/globe/test_no_radius.py` (`radius` added back to `geodesic.line`) |
| 2 | `tests/globe/test_no_radius.py` (the same) |
| 3 | `tests/globe/test_to_mesh.py` (float32 fields; a field renamed) |
| 4 | `tests/globe/test_from_mesh.py` (`from_mesh` raising on `gvRadius`, or on a sphere) |
| 5 | `tests/common/test_current_fields.py`, cited since #2766 (`common._current` a no-op) |
| 6 | `tests/common/test_sanitize_legacy.py`, `tests/common/test_sanitize.py` (no translation; `legacy=False` by default) |
| 7 | `tests/common/test_sanitize_legacy.py`, `tests/globe/test_no_radius.py` (`RETIRED_FIELDS = ()`) |
| 8 | `tests/globe/test_Globe.py` (`Globe.radius` returning a float) |
| 9 | `tests/accessor/test_GeoVistaAccessor.py` (`__eq__` ignoring the globe; the accessor renamed) |

**Heights spec.** Row 1 of §9 has landed; row 2 has not.

| # | Proposed | Evidence (mutation) |
|---|---|---|
| 1 | ✅ verified | `tests/bridge/test_heights.py`, `tests/core/test_carried_heights.py`, `tests/globe/test_vertical.py`, and a **new** test pinning the name `gvHeight` (`GV_POINT_HEIGHT = "height"` passes every test today) |
| 2 | ✅ verified | `tests/bridge/test_heights.py`, `tests/accessor/test_heights.py`, `tests/globe/test_heights.py` (`depth=` not negated) |
| 3 | ✅ verified | `tests/bridge/test_heights.py`, `tests/globe/test_vertical.py`, `tests/globe/test_heights.py` (NaN refused; NaN not at sea level; infinity accepted) |
| 4 | ⏳ pending | rows 1 to 2 of §9 |
| 5 | ⏳ pending | rows 1 to 2 of §9 |
| 6 | ✅ verified | `tests/bridge/test_heights.py`, `tests/core/test_resize.py`, `tests/transform/test_heights.py`, `tests/globe/test_heights.py` (`_refuse_zlevel` a no-op) |
| 7 | ⏳ pending | row 2 of §9 |
| 8 | ✅ verified | `tests/common/test_from_cartesian.py`, `tests/bridge/test_heights.py` (`from_cartesian` reporting `gvHeight`) |
| 9 | ✅ verified | `tests/bridge/test_heights.py`, `tests/globe/test_heights.py` (the cell-sized branch removed) |
| 10 | ✅ verified | `tests/bridge/test_heights.py`, `tests/globe/test_heights.py`, `tests/transform/test_heights.py` (never refused; always refused) |
| 11 | ✅ verified | `tests/bridge/test_heights.py`, `tests/bridge/test_to_structured_grid.py`, `tests/globe/test_heights.py` (`vertical_units` ignored) |

**Ledger spec §10 decision 12** becomes ✅ verified with `tests/test_spec_conventions.py`, since emptying `UNLEDGERED` delivers it.

## The Proposed Items

New roadmap rows, appended so no row is renumbered:

| Spec | Row | Scope | Status |
|---|---|---|---|
| globe | 7 | Heights given for each cell | candidate: a user asks for it, which no check can observe |
| globe | 8 | Heights against another vertical datum | candidate: a user asks for it, which no check can observe |
| globe | 9 | A vertical mapping in bands, or as a function of height | candidate: a user asks for it, which no check can observe |
| globe | 10 | The render radius at the Earth's radius: picking, clipping planes and interaction measured, with `remesh` at that radius (#2779) | not started |
| scene | 3 | The release after which a retired field is refused, once row 5 of globe spec §9 adds `gvZScale` and `gvZLevel` | not started |
| heights | 3 | A scene whose globe can be replaced, rebuilding every layer from its heights | not started |
| heights | 4 | Heights from a raster band in `Transform.from_tiff`, before row 5 of globe spec §9 | not started |
| heights | 5 | A surface below sea level seen past the base layer, landing with row 4 of globe spec §9 | not started |
| ledger | 7 | Emojis for a roadmap row's states | not started |

Owing rows, with 🔎 found by `git log -S` and every 🎫 labelled:

| Item | 🎯 | 🎫 |
|---|---|---|
| globe items 1, 2, 3, 5, 7, 9 | row 6, 4, 4, 4, 4, 5 of §9 | new issues |
| globe item 4 | row 10 of §9 | new issue |
| globe items 6, 8, 10 | rows 7, 9, 8 of §9 | #2728, new, #2782 |
| globe item 11 (new): `remesh` at the Earth's render radius, found in #2777 | row 10 of §9 | #2779 |
| scene item 1 | row 3 of §9 | #2758 |
| heights items 1, 2, 3 | rows 3, 4, 5 of §9 | #2769, #2770, new |
| heights item 4 (new): heights read back without their unit, against scene spec §2 decision 8 | row 2 of §9 | new |
| ledger item 1, narrowed to a roadmap row's states | row 7 of §8 | new |
| items spec §7 item 11 (new): an item owed by another specification's row | row 6 of §8 | new |

## Review Focus

1. **The retirement round-trip:** globe decision 4's restored text must be its 2026-10-26 wording exactly, and the suite's replacement rule (ledger spec §3.6 item 8) must accept decision 7 as in force (Task 1).
2. **Renumbering:** appending rows and items, and inserting decision 7 at the end, renumbers nothing. `check-spec-renumbering` must pass, and every existing citation of a globe decision must still name the same one (Task 1, Task 4).
3. **A decision verified on a span:** heights decisions 2, 6, 9 and 11 hold today, and row 2 must add evidence. The tests cited must fail under the mutation recorded, not merely touch the decision (Task 2).
4. **The ledger's completeness:** with row 6 landed, every ledger roadmap row but the new row 7 has landed, and ledger spec §3.5 must still hold for its §10 (Task 3, Task 5).
5. **The labels:** every 🎫, old or new, carries `spec: open item`, and the nightly drift finds every labelled issue cited (Task 4, Task 5).

---

### Task 1: The decisions, in place

**Files:** the globe, scene and heights specifications.

- [ ] **Step 1:** Give every decision its state and provenance per Global Constraints, and reflow §2 alone.
- [ ] **Step 2:** Retire globe decision 4. Restore its first text with `git show 7f11f403:<path>`, write its retired state and its sentence, and append decision 7 with today's wording.
- [ ] **Step 3:** Run the conventions suite and `check-spec-renumbering`, both of which must pass. Commit: `docs: give the globe family's decisions their state, and retire globe decision 4`.

### Task 2: The evidence

**Files:** the tests named in The Proposed Ledger, and a new test of the name `gvHeight`, in `tests/bridge/test_heights.py`.

- [ ] **Step 1:** Write the `gvHeight` name test, and watch it fail under `GV_POINT_HEIGHT = "height"`.
- [ ] **Step 2:** For each verified decision, re-run its mutation in a throwaway worktree, confirm the cited tests fail, then add `Holds <prefix> spec §2 decision N.` to one test in each file.
- [ ] **Step 3:** Run the cited modules on test-py313 and test-py314, which must pass. Commit: `tests: cite the globe family's decisions each test holds`.

### Task 3: The Verification sections

**Files:** the three specifications, the ledger spec §10, and `tests/test_spec_conventions.py`.

- [ ] **Step 1:** Append each §11 Verification table as The Proposed Ledger gives it. Set ledger spec §10 decision 12 to verified, and empty `UNLEDGERED`.
- [ ] **Step 2:** Run the conventions suite and the incremental strict docs build, both of which must pass. Commit: `docs: bring the globe family into the ledger`.

### Task 4: The items

**Files:** the three specifications, the ledger spec §7, the items spec §7, and `tests/test_spec_conventions.py`.

- [ ] **Step 1:** Raise the new issues, each `agentic`, `spec: open item` and `type: …`. Add `spec: open item` to #2728, #2782, #2758, #2769, #2770 and #2779.
- [ ] **Step 2:** Append the new roadmap rows. Convert every item to the grammar of §3.2. Append globe item 11, heights item 4 and items spec §7 item 11 (each with 🔎 `<DATE>, {pull}`<PR>``, except globe item 11, found in #2777). Narrow ledger item 1 with a sentence, and change items spec §8 row 6's scope to "§7 items 3 to 11".
- [ ] **Step 3:** Remove the globe, scene, heights and ledger specifications from `UNITEMED`.
- [ ] **Step 4:** Run the conventions suite, `check-spec-renumbering`, `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>` and `drift`. Everything must hold except the sign-offs. Commit: `docs: bring the globe family's open items in`.

### Task 5: Landing

- [ ] **Step 1:** Write `changelog/<PR>.contributor.rst`, crediting `:user:`claude``, and validate it.
- [ ] **Step 2:** Run the full suite with images on test-py313 and test-py314, mypy, the docs build and `verification-report`. Then the final review, on `opus`.
- [ ] **Step 3:** Ask bjlittle to add `signed-off` for globe decisions 2, 3 and 6 and the retirement of decision 4.
- [ ] **Step 4 (last commit):** ledger spec §8 row 6 and items spec §8 row 5 both become `✅ landed (<DATE>, {pull}`<PR>`)`.
