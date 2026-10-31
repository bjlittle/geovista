# Decision Ledger, Row 2: What GitHub Answers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land row 2 of ledger spec §8: the status check asks GitHub about the ledger —
each decision's pull request, each verified or retired row's pull request, and each
sign-off's `signed-off` label — and `ci-spec-status.yml` re-runs on a label and reports
on every pull request, so that `status references` can become a required check.

**Architecture:** `.github/scripts/check_status_references.py` gains a second lookup
beside its `Resolver`, a `Labeller` reading a pull request's label events, and a ledger
pass that reads entries and rows with the grammar the conventions test uses. The
workflow drops its `paths:` filter for an in-job decision, so the job always reports.

**Tech Stack:** Python 3.13+, the GitHub REST API (issues and issue events), GitHub
Actions, pytest.

**Spec:** `docs/src/developer/specs/2026-10-30-decision-ledger-design.md` (ledger spec),
§2 decision 7 and §3.7 above all.

## Global Constraints

- The label is named exactly `signed-off`.
- A sign-off holds when the reviewer its row names (`{user}`) added `signed-off` to the pull request it cites, and the label is on it still (ledger spec §3.7).
- A sign-off's date is within a day of the reviewer's adding of the label; a verified or retired row's date is within a day of its pull request's merge, as a landed roadmap row's is. Neither is checked against the pull request being checked (`--pull`), which has not merged.
- A decision entry's every `{pull}` exists, is a pull request, and has merged, or is the pull request being checked.
- The workflow triggers on `pull_request` types `opened`, `synchronize`, `reopened`, `labeled`, `unlabeled`, and has no `paths:` filter; its `references` job reports on every pull request, passing at once when none of the watched files changed.
- The watched files are every file the script loads plus `docs/src/developer/specs/**`, as the `paths:` filter named them.
- Exit codes stay: 0 holds, 1 a finding, 2 GitHub unreachable or rate limited.
- An agent never adds the `signed-off` label. Creating the label is a repository change bjlittle confirms first.
- `<PR>` is this pull request's number and `<DATE>` its merge day; `<LABELLED>` is the day bjlittle adds `signed-off` to #2786.

## Review Focus

1. **A sign-off whose label was added, removed and added again by someone else**: it does not hold, since the reviewer named is not who put the label there now. Test in Task 1.
2. **A pull request with more than 100 events**: the events are read across pages. Test in Task 1 (a resolver fed two pages).
3. **A label event whose actor is gone** (`"actor": null`, a deleted account): read as no one, never a crash. Test in Task 1.
4. **A pull request that changes no specification, labelled**: the job runs, decides nothing changed, and passes, so a required check never waits for ever. Test in Task 2 (the workflow's shape) and by the pull request itself.
5. **The four sign-offs #2786 recorded before the label existed**: they fail the new check until bjlittle labels #2786, then hold. Covered in Task 4.

---

### Task 1: The ledger, asked of GitHub

**Files:**
- Modify: `.github/scripts/check_status_references.py`
- Test: `tests/test_status_references.py`

**Interfaces:**
- Produces: `@dataclass(frozen=True) class Labelling`: `action: str` (`"labeled"` or `"unlabeled"`), `label: str`, `login: str | None`, `when: date`; `type Labeller = Callable[[str, int], list[Labelling]]`; `def labeller(token: str | None = None) -> Labeller` (GitHub, cached, every page); `def check_ledger(path: Path, text: str, resolve: Resolver, labelled: Labeller, *, pull: int | None = None) -> list[str]`; `main(argv=None, resolve=None, labelled=None)`.
- Consumes: `conventions.decisions`, `conventions.ledger`, `conventions.opened`, `conventions.VERIFIED`, `conventions.SIGNED_OFF`, `conventions.LEDGER_RETIRED`, `conventions.USER`, `conventions.dated`, `conventions.where`.

- [ ] **Step 1: Write the failing tests** in `tests/test_status_references.py`, with a `labels` fixture standing in for GitHub's events, as `record` does for its issues:
  - `test_a_decision_cites_a_merged_pull`: an entry citing #10 holds; one citing #12 (open) reports `#12 has not merged`; one citing #99 reports `does not exist`; with `pull=12` the open one holds.
  - `test_a_verified_row_merged_on_its_date`: `✅ verified (2026-10-07, {pull}`10`)` holds; `(2026-10-01, …)` reports `verified on 2026-10-01, but #10 merged on 2026-10-07`.
  - `test_a_sign_off_is_the_reviewers_label` (cite ledger spec §2 decision 7): `signed-off` added by `bjlittle` on #10 holds; added by `someone` reports `the signed-off label on #10 was added by someone, not bjlittle`; none reports `#10 carries no signed-off label`; added then removed reports the same; with `pull=10` and no label, it still fails (Review Focus 1, and §3.7: it fails until the reviewer gives it).
  - `test_a_sign_off_dated_by_its_label`: the label added on 2026-10-09, the row dated 2026-10-01 → `signed off on 2026-10-01, but the label was added on 2026-10-09`.
  - `test_a_label_event_with_no_actor_is_no_one` (Review Focus 3).
  - `test_the_labeller_reads_every_page` (Review Focus 2): a fake `urlopen` serving two pages linked by a `Link: <…>; rel="next"` header.
  - `test_main_checks_the_ledger_and_counts_its_references`: `main(["--pull", "12"], resolve=…, labelled=…)` over a fixture tree reports a sign-off fault and exits 1.
- [ ] **Step 2: Run them to verify they fail** — `pixi run --frozen -e test-py313 python -m pytest tests/test_status_references.py -q` → the new tests FAIL (names undefined).
- [ ] **Step 3: Implement.** `labeller` reads `GET /repos/{repository}/issues/{number}/events?per_page=100`, following the `Link` header's `rel="next"`, keeping only `labeled`/`unlabeled` events, and caches per pull request. `check_ledger` reads each entry's carried `{pull}` roles and each row's state through `conventions.opened`; the label holds when the last `signed-off` event is `labeled`, and its adder is the `login` of that event. `main` runs `check_ledger` after `check` in both modes, and counts the ledger's references in its summary line. Update the module docstring with the three new rules.
- [ ] **Step 4: Run them to verify they pass**, with the conventions suite: `pixi run --frozen -e test-py313 python -m pytest tests/test_status_references.py tests/test_spec_conventions.py -q -n 8` → PASS.
- [ ] **Step 5: Commit** — `ci: ask GitHub about the ledger, and each sign-off's label`

### Task 2: The workflow re-runs on a label and always reports

**Files:**
- Modify: `.github/workflows/ci-spec-status.yml`
- Test: `tests/test_status_references.py` (`test_the_workflow_runs_when_anything_the_script_reads_changes`)

- [ ] **Step 1: Rewrite the failing test** as `test_the_workflow_watches_everything_the_script_reads`: the workflow's `pull_request` trigger has no `paths`, its `types` are exactly the five of Global Constraints, and the `references` job's `WATCHED` environment value (newline-separated globs) names every file the script loads and `docs/src/developer/specs/**`.
- [ ] **Step 2: Run it** → FAIL (`paths` still present).
- [ ] **Step 3: Implement.** Drop `paths:`; add `types:`. In `references`, check out with `fetch-depth: 0`, then a `changed` step that compares `git diff --name-only "${BASE_SHA}...${HEAD_SHA}"` against `WATCHED` with `fnmatch`-style globbing (a short `python3 -c` over stdin, no third-party action), writing `watched=true|false` to `GITHUB_OUTPUT`. The pixi and check steps run only when `watched == 'true'`; the job succeeds either way. Keep `bash -l {0}` errexit-safe: the real check stays the last command (root `AGENTS.md`). Note in a comment why the filter moved into the job: a required check that never reports holds a pull request for ever.
- [ ] **Step 4: Run** `pixi run --frozen -e test-py313 python -m pytest tests/test_status_references.py -q`, and `pixi run --frozen -e devs pre-commit run --files .github/workflows/ci-spec-status.yml` (zizmor, actionlint) → PASS.
- [ ] **Step 5: Commit** — `ci: re-run the status check on a label, and report on every pull request`

### Task 3: The documentation catches up

**Files:**
- Modify: `docs/src/developer/specs/index.rst`, `docs/src/developer/checks.rst`

- [ ] **Step 1:** In the index's "Signing off a decision", the gate is present tense: the named reviewer adds `signed-off`, and the pull request's checks fail until they do; a pull request merged without it is reported nightly, and the reviewer can still label the merged pull request.
- [ ] **Step 2:** Under `spec-statuses` on the checks page, add each new message of Task 1 and its fix, and that the check now runs on every pull request and on a label.
- [ ] **Step 3:** Docs build with `-W --keep-going` → `build succeeded`; humanize the prose; commit — `docs: document the sign-off check`.

### Task 4: The ledger records row 2

**Files:**
- Modify: `docs/src/developer/specs/2026-10-30-decision-ledger-design.md`, `2026-10-06-published-specs-design.md`, `2026-10-26-citation-links-design.md`

- [ ] **Step 1:** With bjlittle's go-ahead, create the label: `gh label create signed-off --description "A reviewer signs off the decisions this pull request records (ledger spec §2 decision 7)" --color 0e8a16`.
- [ ] **Step 2:** Ask bjlittle to add `signed-off` to #2786, whose four sign-offs predate the label (Review Focus 5). Then move those four rows' dates to `<LABELLED>`, and run `GH_TOKEN="$(gh auth token)" pixi run --frozen -e test check-spec-status <PR>` → all hold.
- [ ] **Step 3:** Ledger spec §10: decision 7 becomes `✅ verified (<DATE>, {pull}`<PR>`)` with `tests/test_status_references.py`, which cites it (Task 1). Run the conventions suite → PASS.
- [ ] **Step 4:** Commit — `docs: record the sign-off check in the ledger`

### Task 5: Landing

- [ ] **Step 1:** `changelog/<PR>.internal.rst`, crediting `:user:`claude``, validated with `.github/scripts/changelog.py`.
- [ ] **Step 2:** Full suite with images, mypy, the docs build with `-W --keep-going`, `check-spec-status <PR>` and `check-spec-status drift` → all pass.
- [ ] **Step 3 (last commit):** ledger spec §8 row 2 → `✅ landed (<DATE>, {pull}`<PR>`)`; redate every `<DATE>` if the merge slips.
- [ ] **Step 4 (after merge, bjlittle):** add `status references` to the required checks of `main`'s branch protection (ledger spec §3.7).
