# Decision Ledger, Row 3: The Verification Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 3 of ledger spec §8: `pixi run -e test verification-report [prefix]`
prints, for every specification or one, each decision with its state and every place in
the repository that cites it, grouped, and flags what does not agree. It is a view on
demand, never a gate.

**Architecture:** A script, `.github/scripts/verification_report.py`, reads the
specifications with the conventions test's parsers (loaded by path, as
`check_status_references.py` does) and the corpus with the citation grammar, plus the
plans, which the corpus prunes. The ledger summary line moves from the Sphinx extension
into the grammar, so the report, which runs in the `test` environment without Sphinx,
writes the same line the build does.

**Tech Stack:** Python 3.13+, pytest, pixi tasks.

**Spec:** `docs/src/developer/specs/2026-10-30-decision-ledger-design.md` (ledger spec),
§2 decision 11 and §3.8.

## Global Constraints

- The task is `verification-report` in the pixi `test` feature, taking an optional prefix as `check-spec-renumbering` takes its option: `pixi run -e test verification-report` and `pixi run -e test verification-report heights`.
- Output is Markdown on standard output, and is appended to `$GITHUB_STEP_SUMMARY` when that is set.
- Exit 0 whatever the report finds; exit 2 only when it cannot read a specification, or the prefix names none (ledger spec §3.8: a gap is a finding, not a failure).
- Groups, in this order: source (`src/`, `.github/`), tests (`tests/`), documentation (anything else outside the two below), specifications (`docs/src/developer/specs/`), plans (`docs/src/developer/plans/`).
- Flags (ledger spec §3.8): a verified row whose evidence no longer cites its decision; a decision in force (`🤝 Agreed`) that nothing outside its own entry cites.
- The summary line reads exactly as the build writes it; it lives in `geovista_citations` as `summary(statuses)`, and `geovista_ledger.summary` delegates to it.
- A specification not yet in the ledger is reported too, its decisions without states, since rows 4 to 6 will want its citations.
- Python under `tests/` and `docs/src/_ext/` builds emoji and section signs by name.

## Review Focus

1. **A plan citing a decision bare** (`§2 decision 3`), which owns no sections: not counted against any specification, and no crash. Test in Task 2.
2. **A specification citing its own decision** elsewhere in its text: counted under specifications; the entry itself is not a citation of itself. Test in Task 2.
3. **An unknown prefix** (`verification-report nosuch`): exit 2 with a message naming the prefixes known. Test in Task 2.
4. **A specification whose Decisions are bullets** (the five not yet numbered before rows 4 to 6): reported with no decisions, never a crash. Test in Task 2.
5. **`$GITHUB_STEP_SUMMARY` set**: the same Markdown is appended, not overwritten. Test in Task 2.

---

### Task 1: The summary line moves into the grammar

**Files:**
- Modify: `docs/src/_ext/geovista_citations.py`, `docs/src/_ext/geovista_ledger.py`
- Test: `tests/docs/test_geovista_citations.py`

**Interfaces:**
- Produces: `geovista_citations.summary(statuses: Iterable[str]) -> str`; `geovista_ledger.summary` is that function.

- [ ] **Step 1:** Write `test_summary_counts_each_state` in `tests/docs/test_geovista_citations.py`, as the one in `tests/docs/test_geovista_ledger.py` reads, against `citations.summary`.
- [ ] **Step 2:** Run → FAIL (`summary` undefined in the grammar).
- [ ] **Step 3:** Move `summary` and its state order into the grammar; `geovista_ledger` imports it (`summary = geovista_citations.summary`). The tests in `tests/docs/test_geovista_ledger.py` stay as they are, and still pass.
- [ ] **Step 4:** Run `tests/docs/test_geovista_citations.py` (test env) and `tests/docs/test_geovista_ledger.py` (geovista env) → PASS.
- [ ] **Step 5:** Commit — `docs: move the ledger summary into the citation grammar`.

### Task 2: The report

**Files:**
- Create: `.github/scripts/verification_report.py`
- Test: `tests/test_verification_report.py`

**Interfaces:**
- Produces: `@dataclass(frozen=True) class Cited`: `path: Path`, `line: int`; `def citations_of(texts: Mapping[Path, str], names: Namespace) -> dict[str, list[Cited]]` (decision anchor → where it is cited, entries excluded); `def group(path: Path, root: Path) -> str`; `def report(specs: list[Path], texts: Mapping[Path, str], names: Namespace, root: Path) -> str`; `def main(argv: list[str] | None = None, root: Path = REPO) -> int`.
- Consumes: the conventions module's `decisions`, `ledger`, `opened`, `VERIFIED`, `AGREED`, `is_test`, `cites`; the grammar's `corpus`, `namespace`, `specifications`, `source_lines`, `prose`, `scan`, `decision_anchor`, `summary`.

- [ ] **Step 1: Write the failing tests** in `tests/test_verification_report.py`, over a fixture tree in `tmp_path` holding two specifications (`demo spec` with a ledger, `lone spec` with bulleted decisions), a source file, a test, a page and a plan:
  - `test_report_lists_each_decision_with_its_state_and_citations` (cite ledger spec §2 decision 11): the demo spec's section heads with its prefix and title and the summary line; decision 1 lists `tests: tests/test_demo.py:3` and `source: src/code.py:1`, in the group order of Global Constraints.
  - `test_report_flags_a_silent_test_and_an_uncited_decision`: a verified row whose test no longer cites it, and an Agreed decision cited nowhere, each under "Findings".
  - `test_a_plan_citing_bare_is_counted_against_nothing` (Review Focus 1).
  - `test_a_specification_citing_its_own_decision_counts`, and its entry does not (Review Focus 2).
  - `test_an_unknown_prefix_exits_two` (Review Focus 3).
  - `test_bulleted_decisions_are_reported_without_a_crash` (Review Focus 4).
  - `test_the_report_appends_to_the_job_summary` (Review Focus 5).
  - `test_main_reports_one_specification_by_prefix`: `main(["demo"], root=tmp_path)` prints only the demo spec, exit 0.
  - `test_the_report_reads_this_repository`: `main([], root=REPO)` exits 0 and its output names `ledger spec`.
- [ ] **Step 2: Run** `pixi run --frozen -e test-py313 python -m pytest tests/test_verification_report.py -q` → FAIL (no script).
- [ ] **Step 3: Implement** the script. Load `tests/test_spec_conventions.py` by path as `check_status_references.py` does; read the corpus with the grammar's `corpus(root)` plus every file under `docs/src/developer/plans/`. A citation is a `scan()` result whose slug is a decision anchor; a specification's own entry lines are skipped. Output, per specification:

  ```markdown
  ## ledger spec: Decision Ledger Specification

  ✅ 10 · ✍️ 2 · ⏳ 2 · 🗄️ 0: 12 of 14 decisions in force verified

  ### Decision 1: A decision is cited as `<prefix> spec §2 decision N`.

  ✅ verified (2026-10-31, {pull}`2786`)

  - **source:** `src/geovista/common.py:653`
  - **tests:** `tests/docs/test_geovista_citations.py:212`, …
  ```

  and a final `## Findings` section, or `No findings.`
- [ ] **Step 4: Run** the tests → PASS; also `ruff`.
- [ ] **Step 5: Commit** — `ci: add the verification report`.

### Task 3: The task and its documentation

**Files:**
- Modify: `pyproject.toml` (`[tool.pixi.feature.test.tasks.verification-report]`), `docs/src/developer/specs/index.rst`

- [ ] **Step 1:** Add the task: `args = [{ "arg" = "prefix", "default" = "" }]`, `cmd = "python .github/scripts/verification_report.py{% if prefix | length %} {{ prefix }}{% endif %}"`, `description = "Report how each specification decision is verified, and where it is cited"`.
- [ ] **Step 2:** Run `pixi run -e test verification-report heights` and `pixi run -e test verification-report` → exit 0, reports read sensibly.
- [ ] **Step 3:** In the index's "Decisions and Verification", add **The verification report**: what it shows, how to run it, and that it is never a gate (ledger spec §3.8). Docs build `-W --keep-going` → PASS; humanize.
- [ ] **Step 4:** Commit — `docs: document the verification report`.

### Task 4: The ledger records row 3, and landing

- [ ] **Step 1:** Ledger spec §10: decision 11 → `✅ verified (<DATE>, {pull}`<PR>`)` with `tests/test_verification_report.py`. Conventions suite → PASS.
- [ ] **Step 2:** `changelog/<PR>.contributor.rst` (a tool for contributors), crediting `:user:`claude``.
- [ ] **Step 3:** Full suite with images, mypy, docs build, `check-spec-status <PR>` → all pass. Final review.
- [ ] **Step 4 (last commit):** ledger spec §8 row 3 → `✅ landed (<DATE>, {pull}`<PR>`)`.
