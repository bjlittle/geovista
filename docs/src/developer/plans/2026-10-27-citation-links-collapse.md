# Citation Links Row 4: Collapsing the Roles — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite every hand-written `{ref}` or `:ref:` role naming a specification section as the plain citation it displays, which the build-time transform of row 2 already links, so that a citation is one string that cannot disagree with itself; then hold the repository to plain citations.

**Architecture:** A one-off script, kept out of the repository and recorded here, rewrites each section role found by the grammar of `docs/src/_ext/geovista_citations.py` as its display text, adding the cited specification's prefix only where the plain text would otherwise resolve elsewhere. The rewrite is proven by the build: every page's citation links, as text and target, are the same before and after. The agreement assertion of `tests/test_spec_conventions.py` then retires, and in its place, under the same number, a rule that no role names a section.

**Tech Stack:** Python 3.13+, Sphinx, MyST, pytest, pixi.

**Spec:** `docs/src/developer/specs/2026-10-26-citation-links-design.md`, `citation spec §4.4`, `§4.6` (its changelog paragraph), `§4.7`, row 4 of `§9`. Parent: `docs spec §3.4`, `§3.5`, `§8` item 1.

## Global Constraints

- Today there are 267 section roles: 186 displaying a bare section, 81 a prefixed one; 259 in the specifications, 7 on `checks.rst`, 1 on `specs/index.rst`.
- A role becomes its display text exactly. Where that text would scan to another anchor in its place (a bare section of another specification, outside a run carrying its prefix), the prefix is added: `docs spec §3.6`, the target's prefix with hyphens read as spaces.
- A role naming no section, such as ``{ref}`the gallery <gallery>` ``, is untouched.
- No citation may wrap across a line or leave a range's far end without its prefix (`docs spec §3.2`); the conventions test reports any the rewrite creates, and each is fixed by hand.
- Items are appended, never renumbered (`citation spec §4.6`), so the agreement assertion is retired in place: item 5 of `docs spec §3.5` keeps its number and its new rule replaces its text.
- Commit through `pixi run --frozen -e geovista git commit`.

## Review Focus

1. **A role whose plain form names another section.** `{ref}`§3.6 <docs-spec-3-6>`` inside the citation links design must become `docs spec §3.6`, not `§3.6`, which there means `citation spec §3.6`. Task 2 resolves every rewrite with the grammar before writing it.
2. **A role that carried a run.** `{ref}`docs spec §3.5 <…>`, {ref}`§3.6 <…>`` becomes `docs spec §3.5, §3.6`, which the grammar reads as one run; the check of Task 2 confirms each.
3. **The proof.** The comparison of Task 2 is per page and per citation, text and target, so a citation that lost its link or gained a wrong one shows.
4. **Roles creeping back.** Without the rule of Task 3, a new role would bring back two strings that can disagree; the rule makes it loud.
5. **The renumber guard.** It still reads roles, which is harmless; it must stay clean on this pull request, whose rewritten lines are all changed.

---

### Task 1: Commit This Plan

- [ ] **Step 1:** Commit this file alone, push, open the draft pull request (`agentic`, `type: documentation`), and pause for review.

### Task 2: The Collapse

**Files:**
- Modify: every file holding a section role (the six specifications, `docs/src/developer/checks.rst`, `docs/src/developer/specs/index.rst`)

- [ ] **Step 1: Record the links before.** Build `html-noplot` on `main` and save, for every page, the list of its citation links as (text, `href`) from `tests/docs/test_rendered_citations.py`'s `Scan.linked`.
- [ ] **Step 2: Write the script** under `/tmp`, loading the grammar by path. For each file in `geovista_citations.corpus()` and each line, find each section role with `SPAN` and `section_role`; take its display text; scan the line with that role replaced, with the file's owner, and keep the text if the citation it yields resolves to the role's target, else write the target's prefix before the section sign and check again. Fail loudly, writing nothing, on any role that resolves wrong either way.
- [ ] **Step 3:** Run it. Expected: 267 roles rewritten, none refused.
- [ ] **Step 4:** Run `tests/test_spec_conventions.py`. Expected: pass, or a wrapped run or a range the rewrite created, each fixed by hand and listed in the ledger.
- [ ] **Step 5: Prove it.** Build `html-noplot` on the branch, record the links as in Step 1, and compare. Expected: every page's citation links identical as (text, `href`); the output check passes.
- [ ] **Step 6:** Commit `"docs: write every citation of a section as plain text"`.

### Task 3: One Form, Held

**Files:**
- Modify: `tests/test_spec_conventions.py` (`agreement`, its tests, the docstrings of `crossed` and the module)

**Interfaces:**
- Produces: `section_roles(path: Path, text: str, names: Namespace) -> list[str]`, one message per role naming a section, as `<where>: write <display> as plain text, which the build links`; and still one per role broken across lines.

- [ ] **Step 1: Write the failing test** `test_section_roles_finds_each_role_naming_a_section`: on the demo specification, a `{ref}` and a `:ref:` role naming a section are each reported with their display text; a role naming a label that is no section, and a plain citation, are not; a role broken across lines is reported.
- [ ] **Step 2:** Run it. Expected: fails, no `section_roles`.
- [ ] **Step 3:** Replace `agreement` and its tests with `section_roles` and `test_no_role_names_a_section` ("Plain text (item 5)"). `crossed` stays, as a span wrapped across a line still hides what follows from the grammar; its docstring says so without the agreement rule.
- [ ] **Step 4:** Run the conventions test. Expected: pass, the repository holding no section role.
- [ ] **Step 5:** Commit `"tests: hold every citation of a section to plain text"`.

### Task 4: The Prose

**Files:**
- Modify: `docs/src/developer/specs/2026-10-06-published-specs-design.md` (`§3.4`, `§3.5` item 5, `§8` item 1)
- Modify: `docs/src/developer/specs/2026-10-26-citation-links-design.md` (`§4.4`)
- Modify: the changelog guidelines page, and `docs/AGENTS.md`

- [ ] **Step 1:** `docs spec §3.4` describes citations as written and linked now: plain text, linked by the transform, one string. `§3.5` item 5 becomes **Plain text**: no role names a section, retiring the agreement rule in place. `§8` item 1 becomes `**Resolved** (<date>, {pull}`<PR>`)`, the display form it worried about gone with the roles.
- [ ] **Step 2:** `citation spec §4.4` records the rule that replaced the assertion.
- [ ] **Step 3:** The changelog guidelines say a fragment naming a roadmap row cites the row's pull request with a `:pull:` role (`citation spec §4.6`). `docs/AGENTS.md` gains one line: cite a specification section in plain text, never a role.
- [ ] **Step 4:** Run the conventions, repository-checks and reading-time tests, `check-spec-status <PR>`, and an incremental html build with `--fail-on-warning`. Expected: all pass.
- [ ] **Step 5:** Commit `"docs: say a section is cited in plain text"`.

### Task 5: Verification

- [ ] **Step 1:** Run the renumber guard against `origin/main` and its audit. Expected: clean.
- [ ] **Step 2:** Run `pixi run --frozen -e geovista tests-docs-browser html-gallery strict` under `xvfb-run`. Expected: pass.
- [ ] **Step 3:** Run `pixi run --frozen -e test tests-unit "not image"`. Expected: no failures.

### Task 6: Record and Land

- [ ] **Step 1:** Write `changelog/<PR>.documentation.rst`, crediting `:user:`claude``, and check it.
- [ ] **Step 2:** Final review on Opus; fix Critical and Important findings red first; record the review here; raise an `agentic` issue for anything deferred.
- [ ] **Step 3:** Comment on #2566 that rows 2 to 4 of `docs spec §4` have landed, leaving it open for the candidate rows.
- [ ] **Step 4: The landed row, last.** Row 4 of `citation spec §9` becomes `✅ landed (<date>, {pull}`<PR>`)`. Run `check-spec-status <PR>`, commit, push, confirm the remote head, and mark the pull request ready.

## After the Final Review

The whole-branch review, on Opus, proved the collapse exact twice over, independently of Task 2's proof: by source, every file's citations named the same anchors in the same order before and after (336 each, 267 roles to none), and at the head every page's citations matched its built links. It re-added a role of each kind and all were reported, and a role to a label that is no section was left alone. One Important finding and six Minor ones.

- **Fixed (Important):** the rule's message suggested a role's display text, so a role citing another specification's section by a bare number, followed literally, would have become a citation of the containing specification's section of that number, the silent wrong link the design removes. The suggestion is now built from the target, and is the display text only where that names the target where it is written (`test_section_roles_suggests_the_citation_its_target_needs`, red first).
- **Fixed (re-graded, inaccurate text this pull request left):** the citation links design's counts and tense in its section on the collapse, the pairing test's docstring, and "`{ref}` or `:ref:`" in the rule's statements.
- **Deferred to #2746:** the rule's gaps for `:std:ref:` and MyST anchor links and a role quoted in a reStructuredText code block, none of which exists today, and two cosmetic points.
- **Codex round:** the suggestion was checked by scanning the display text alone, which lost a prefix carried from an earlier citation on the line: after `other spec §1,`, a bare `§1` inherits `other spec`. It is now checked in the line, with the suggestion in the role's place (`test_section_roles_suggests_in_the_context_of_its_run`, over a comma and a solidus; the comma case red first).
- **Codex re-check:** each suggestion was checked with only its own role substituted, the line's other roles still blanked, so two roles whose suggestions were each right alone, `other spec §1` then `§1`, linked the wrong section when both were followed. A line's suggestions are now chosen together: every role written as its display text, any that names another section switched to its full form, until the choice settles (`test_section_roles_suggests_a_lines_citations_together`, over a comma and a solidus, both red first).
