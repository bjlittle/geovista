# Decision Ledger, Row 4: The Typing, Zlevel and Checks Specifications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 4 of ledger spec §8: the typing, zlevel and checks specifications
join the ledger, each decision numbered with its provenance, and each ending with a
Verification table whose every row is verified or signed off.

**Architecture:** No code changes. Each specification's bulleted Decisions become numbered
`🤝 Agreed` entries, a §10 Verification table follows its References, the tests that
already exercise a decision gain a citation of it, and the three leave `UNLEDGERED` in the
conventions test, which then holds them to the ledger rules.

**Tech Stack:** MyST Markdown, pytest, the `check-spec-status` and `verification-report`
pixi tasks.

**Spec:** `docs/src/developer/specs/2026-10-30-decision-ledger-design.md` (ledger spec),
§3.9 above all, with §3.2 and §3.4 for the forms.

## Global Constraints

- Decisions are numbered in their present order (ledger spec §3.9 step 1), and keep their titles and text verbatim; only indentation changes.
- Provenance (ledger spec §3.9 step 2), from `git log -S` on each title, with one ruling below:
  - typing spec decisions 1 to 4: `2026-10-06, {user}`bjlittle`, {pull}`2564``;
  - zlevel spec decisions 1 to 4: `2026-10-08, {user}`bjlittle`, {pull}`2589``;
  - checks spec decisions 1 to 8: `2026-10-23, {user}`bjlittle`, {pull}`2705``.
- **Ruling, for review:** typing spec decision 4 is dated by {pull}`2564`, not {pull}`2567`. `git log -S` on its present title finds #2567, which reworded it from "An upstream defect is suppressed where it lands, never worked around in the source". The reasoning (a `type: ignore` in a gallery script is published as example code) is unchanged, so the rewording is an edit under §3.9 step 2, not a new decision. If review judges the meaning changed, the entry cites {pull}`2567` on 2026-10-07 instead.
- Each specification gains `(<prefix>-spec-10)=` / `## 10. Verification` after its §9 References, opening "Each row follows ledger spec §3.4.", as the docs and citation specifications do.
- A verified row cites `<DATE>, {pull}`<PR>``, since this pull request is where a test first cites the decision. A signed-off row cites `<DATE>, {user}`bjlittle`, {pull}`<PR>``. `<PR>` is this pull request and `<DATE>` the day it merges; redate everything if the merge slips past midnight UTC.
- A citation in a test is a docstring sentence, `Holds <prefix> spec §2 decision N.`, on the test named below, or a `#:` comment where the evidence is a constant.
- An agent never adds the `signed-off` label; {user}`bjlittle` adds it to this pull request, and `status references` fails until he does.
- No decision is retired (§3.9 step 4): planar z-levels are retired only by globe spec §9 row 5, which has not started, and nothing else has overtaken any of the sixteen. No decision is undelivered (§3.9 step 5), so no open item or issue is raised.

## The Proposed Ledger

Each row is {user}`bjlittle`'s judgement in review (§3.9 step 4: "not mechanical").

**typing spec** — every row of its §4 roadmap has landed.

| # | Decision | Proposed | Evidence |
|---|---|---|---|
| 1 | The authoritative check runs against the locked environment | ✅ verified | `tests/test_ci_typing.py`: `test_ci_typing_runs_the_hook_command` (the CI step ends with the hook's `pixi run --frozen` entry, installed `frozen` from the lock) |
| 2 | The hook goes live before the errors are fixed | ✍️ signed off | "Checked in review that the hook and its ratchet went live in row 1 of §4 ({pull}`2565`) before any module was corrected, and that row 7 retired the ratchet ({pull}`2681`)." |
| 3 | An annotation that over-promises is corrected by honouring it | ✅ verified | `tests/bridge/test_lists.py`: lists build the mesh arrays do, across every factory |
| 4 | A gallery defect is suppressed in the configuration | ✅ verified | `tests/test_ci_typing.py`: `test_only_the_known_overrides_relax_strict` (`RELAXED` pins the `geovista.examples.*` override, whose reason cites typing spec §3.4) |

**zlevel spec** — row 1 of its §4 landed in {pull}`2591`.

| # | Decision | Proposed | Evidence |
|---|---|---|---|
| 1 | The length is the Earth's radius, in the CRS's own units | ✅ verified | `tests/transform/test_transform_mesh.py`: `test_transform_mesh__zlevel_in_the_units_of_the_crs` |
| 2 | `zscale` stays the only control | ✅ verified | `tests/transform/test_transform_mesh.py`: `test_transform_mesh__cloud_carries_the_zscale_given_in_a_planar_crs` (`zscale` scales the levels in the plane) |
| 3 | `GeoPlotter` does not change | ✅ verified | `tests/transform/test_transform_mesh.py`: `test_transform_mesh__data_above_the_coastlines_whatever_its_extent` (the plotter's base, coastline and data layers keep their order) |
| 4 | Nothing persisted needs migrating | ✍️ signed off | "Checked in review that no planar z is stored: every transform computes it afresh, from the levels a cloud carries or the `zlevel` given." |

**checks spec** — row 1 of its §4 landed in {pull}`2707`; row 2 is a `candidate`.

| # | Decision | Proposed | Evidence |
|---|---|---|---|
| 1 | One page, for a reader who has just failed a check | ✅ verified | `tests/test_repository_checks.py`: `test_the_page_and_the_checks_agree` |
| 2 | Only `geovista`'s own checks, for now | ✍️ signed off | "Checked in review that the page documents only `geovista`'s own checks, and that row 2 of §4 keeps the third-party tools as a candidate." |
| 3 | A check with no exception still gets a section | ✅ verified | `tests/test_repository_checks.py`: `test_a_check_without_a_section_fails` |
| 4 | The breadcrumb points at `latest` | ✅ verified | `tests/test_repository_checks.py`: `test_breadcrumb_names_the_section` |
| 5 | The page is written by hand, and a gate keeps it honest | ✅ verified | `tests/test_repository_checks.py`: `test_the_page_and_the_checks_agree` |
| 6 | The gate is a check too | ✅ verified | `tests/test_repository_checks.py`: its own `CHECK = "repository-checks"`, which the gate holds to a section like any other |
| 7 | Existing write-ups stay where they are | ✍️ signed off | "Checked in review that the page links to the image marker, reading-time and changelog sections of the developer guide, which stay where they were." |
| 8 | The page carries no reading-time banner | ✅ verified | `tests/docs/test_readingtime_coverage.py`: the `developer/checks.rst` entry of `EXEMPT` |

Twelve verified, four signed off: `✅ 12 · ✍️ 4 · ⏳ 0 · 🗄️ 0` across the three.

## Review Focus

1. **A carried prefix across a comma** (`typing spec §3.3, §2 decision 3`): the citations here are sentences of their own, so none relies on a prefix carrying; the verification report, run in Task 4, shows each counted against the right specification.
2. **A decision whose text runs over several lines**: numbering adds a one-space indent to every continuation line, so the entry's paragraphs stay inside it. The conventions suite reads each entry's title (Task 1).
3. **The renumbering guard on a list numbered for the first time**: `check-spec-renumbering` must pass, as it did for the docs and citation specifications in row 1 (Task 1).
4. **A bare `§` in a Python docstring**, which names no document: every test citation carries its prefix (Task 2).
5. **The sign-off gate on this pull request**: four rows fail `status references` until {user}`bjlittle` labels it, which is the gate working, not a fault (Task 4).

---

### Task 1: Number the decisions

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-type-coverage-design.md`, `2026-10-08-planar-zlevel-design.md`, `2026-10-23-repository-checks-design.md`

- [ ] **Step 1:** Turn each `- **Title.**` item of §2 into `N. **🤝 Agreed** (<provenance>) — **Title.**`, with the provenance of Global Constraints, re-indenting continuation lines by one space, and reflow to 92 columns without splitting a citation.
- [ ] **Step 2:** Run `pixi run --frozen -e test-py313 python -m pytest tests/test_spec_conventions.py -q -n 8` → PASS, the three still in `UNLEDGERED`.
- [ ] **Step 3:** `pixi run --frozen -e test check-spec-renumbering` → PASS.
- [ ] **Step 4:** Commit — `docs: number the typing, zlevel and checks decisions`.

### Task 2: The tests cite what they hold

**Files:**
- Modify: `tests/test_ci_typing.py`, `tests/bridge/test_lists.py`, `tests/transform/test_transform_mesh.py`, `tests/test_repository_checks.py`, `tests/docs/test_readingtime_coverage.py`

- [ ] **Step 1:** Add each citation of The Proposed Ledger's Evidence column, as Global Constraints say.
- [ ] **Step 2:** Run the five modules and the conventions suite → PASS; `ruff` clean.
- [ ] **Step 3:** Commit — `tests: cite the typing, zlevel and checks decisions each test holds`.

### Task 3: The Verification sections

**Files:**
- Modify: the three specifications; `tests/test_spec_conventions.py` (`UNLEDGERED` loses the three)

- [ ] **Step 1:** Append each §10 Verification table, its rows as The Proposed Ledger gives them.
- [ ] **Step 2:** Conventions suite → PASS; the incremental docs build with `-W --keep-going` → `build succeeded`, each summary line rendered.
- [ ] **Step 3:** Commit — `docs: bring the typing, zlevel and checks specifications into the ledger`.

### Task 4: Landing

- [ ] **Step 1:** `pixi run --frozen -e test verification-report typing` (and `zlevel`, `checks`) → no findings.
- [ ] **Step 2:** `changelog/<PR>.contributor.rst`, crediting `:user:`claude``, validated with `.github/scripts/changelog.py`; humanize it.
- [ ] **Step 3:** Full suite with images, mypy, the docs build, and `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>` → everything holds but the four sign-offs, until {user}`bjlittle` adds `signed-off`; then all hold. Final review.
- [ ] **Step 4 (last commit):** ledger spec §8 row 4 → `✅ landed (<DATE>, {pull}`<PR>`)`, and ledger spec §10 left as it is: decision 12 stays pending until rows 5 and 6.
