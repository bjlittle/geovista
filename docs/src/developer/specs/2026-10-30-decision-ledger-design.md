# Decision Ledger Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the specifications it
> governs. It states how the decisions of every `geovista` specification are cited, who
> agreed each one and when, how one is retired, and how its delivery is verified. Cite it
> as `ledger spec §…`. Read it as current; the roadmap states what has actually landed.

- **Date:** 2026-10-30 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `ledger spec §…`
- **Scope:** the decisions of every specification as a ledger: how a decision is cited, the
  provenance it carries, how it is retired, and the evidence that it was delivered
- **Lineage:** [docs spec](2026-10-06-published-specs-design.md) › **ledger spec**
- **Children:** none
- **Extends:** docs spec §3.2, whose citation form gains a decision,
  docs spec §3.5, whose suite gains the ledger, and
  docs spec §3.6, whose status vocabulary gains the states of a decision and of its
  verification. It inherits that specification's anchors (docs spec §3.3) and families
  (docs spec §3.7) unchanged, and builds on the renumber guard of
  citation spec §4.6
- **Published:** in the specifications index

(ledger-spec-1)=
## 1. Purpose

Every specification records, in its Decisions section, what was agreed before its work
began, and its roadmap records which work landed. Nothing records whether the work kept what
was decided. A roadmap row names the pull request that landed it, but not which decisions
that pull request honoured, so "every row has landed" and "every decision was delivered" are
different claims, and only the first is written down anywhere.

The measurement, taken on 2026-10-30:

| | count |
|---|---|
| specifications | 9 |
| decisions | 69 |
| of those, numbered | 40, in four specifications |
| specifications saying who agreed their decisions | 6, each once for the whole list |
| decisions naming the pull request they were agreed in | 0 |
| citations of a decision, written as `<prefix> spec §2 decision N` | 53 |
| of those, in code and tests | 2 |
| of those, linking to the decision itself | 0 |
| decisions with recorded evidence of delivery | 0 |

The 53 citations show that the need is already felt. Contributors cite decisions in the
specifications (34), in plans (17), in `src/geovista/common.py` and in a test docstring.
But such a citation links at best to the top of the Decisions section it names, and nothing
checks that the decision it names exists, or that it still holds.

This specification makes each decision a permanent, citeable entry in a ledger, carrying
who agreed it, when, and in which pull request. It gives every specification a
Verification section that shows, decision by decision, the evidence that it was delivered.
The aim is verification: confidence that what a specification decided is what the code
does, readable on the published page and held in place by the suite.

(ledger-spec-2)=
## 2. Decisions

These were decided with {user}`bjlittle` on 2026-10-30. This is the first specification
to record its decisions in the form they describe (§3.2).

1. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **A decision is cited as
   `<prefix> spec §2 decision N`.** The form is explicit, at the cost of length. A form such
   as `§2.3` would collide with the number of a subsection, and a reader meeting
   `heights spec §2 decision 3` in a comment needs no convention explained to know what it
   names.
2. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **Decisions are only ever
   appended, and keep their numbers.** A decision is never deleted, renumbered or moved,
   and its number is never reused, so a citation written in code today names the same
   decision for as long as the specification exists.
3. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **A decision that no longer
   holds is retired, not removed.** Its entry keeps its text and records why it was
   retired, by whom, when, and what replaced it, if anything did. A change to what a
   decision means is a retirement and a new decision. A correction or clarification that
   leaves its meaning as it was is an edit, and whether an edit crosses that line is left
   to review.
4. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **Every decision carries its
   provenance, state first.** An entry opens with its state, then the date it was agreed,
   who agreed it and the pull request it was banked in, in the grammar the open items of
   docs spec §3.6 already use. One grammar, and one checker, serve both.
5. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **Every specification has a
   Verification section, a table with one row per decision.** The rows run from 1 to N,
   always, so a decision with no evidence is a visible row and not an absence. The table
   was chosen over a list for how it scans: a reader looking for the gaps reads one column.
6. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **Evidence is a test that
   cites the decision, or a reviewer's sign-off.** A test is named by its file, which the
   suite checks exists and cites the decision. A sign-off names the reviewer, the date and
   the pull request, and says what the reviewer checked. Some decisions concern scope or
   process, and no test can show them honestly.
7. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **A sign-off is a label,
   confirmed against GitHub.** The reviewer a sign-off names must have added the
   `signed-off` label to the pull request it names, so a sign-off cannot be written into a
   specification by someone who did not give it. GitHub records who added a label and when,
   and keeps that record when the label is removed, where a comment can be edited after the
   fact. An approval cannot serve: an author cannot approve their own pull request, and
   `geovista-bot` gives this repository's approvals on request. GitHub records the account,
   not the person, so an agent acting through a reviewer's account never adds the label.
8. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **The ledger is complete
   when the roadmap is.** Once no roadmap row is `in progress` or `not started`, no
   decision is pending, unless a `candidate` row is to deliver it and its row says which.
9. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **Each state carries an
   emoji.** A decision is 🤝 agreed or 🗄️ retired. Its verification is ⏳ pending,
   ✅ verified, ✍️ signed off or 🗄️ retired. The two retirements share one emoji, as they
   are one event seen from two sections.
10. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **Verification is the last
    section of a specification.** It follows References, so adding it renumbers no section
    and moves no citation.
11. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **A report gathers the
    evidence on demand, and is never a gate.** A pixi task lists, for every specification
    or for one, each decision with its state and every place in the repository that cites
    it. The ledger in each specification is the record; the report is a view of it.
12. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **Every existing
    specification is brought into the ledger.** The nine published before this one are
    numbered, given their provenance and verified, so that the ledger describes the whole
    collection, not only what is written from today.
13. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **This specification is
    governed by its own ledger.** Its decisions are written in the form of §3.2 from the
    day it is banked, and its own Verification section is complete when its roadmap is.
14. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **Provenance is read from
    history.** A decision brought in from an existing specification is dated by, and cites
    the pull request of, the commit that first added it. The specification's Date line is
    true only of the decisions written with the file, and a decision added later would
    otherwise carry a date and a pull request that pass every check and are false.
15. **🤝 Agreed** (2026-10-30, {user}`bjlittle`, {pull}`2785`) — **The workflow is documented
    where contributors meet it.** The specifications index says how to add, cite, retire,
    verify and sign off a decision, and the repository checks page explains each new failure
    and how to fix it.

(ledger-spec-3)=
## 3. Design

(ledger-spec-3-1)=
### 3.1 Citing a Decision

A decision is cited as `heights spec §2 decision 3`: the citation of the section that holds
the decisions, followed by the word `decision` and its number. Every specification keeps its
decisions in its second section, titled Decisions, and the suite holds that it does, so the
section in the form never varies. Within a specification, `§2 decision 3` means its own
decision, as a bare section number does (docs spec §3.2). A citation names one decision; two
are cited as two citations, as each end of a range is.

Each decision carries an anchor, `<prefix>-spec-2-decision-N`, as
`heights-spec-2-decision-3`, and the citation transform of citation spec §4.2 links the
whole citation to it, not to the top of the section. A citation of a decision that does not
exist fails the suite, as a citation of a section that does not exist does. How an anchor is
placed on a list item in MyST is left to row 1 of §8.

Decisions are numbered items that open with a bold title, so the renumber guard already
freezes them (citation spec §4.6). It learns the two states of §3.2 and §3.3, so it reads a
decision's title after its state, as it does an open item's. Row 5 of the citation spec's
roadmap, which would make items and rows citeable in their own right, stays a candidate: a
decision is cited here by a form of its own, and its trigger counts items and rows, not
decisions.

The citation specification decided "Sections only": that an item within a section gets no
anchor or link of its own. A decision is such an item, so row 1 of §8 retires that decision,
replaced by §2 decision 1, and brings the citation specification into the ledger so the
retirement can be written in the form of §3.3. A plural citation already written, such as
`crs spec §2 decisions 4 and 14`, becomes one citation per decision.

(ledger-spec-3-2)=
### 3.2 A Decision's Entry

```markdown
3. **🤝 Agreed** (2026-10-28, {user}`bjlittle`, {pull}`2771`) — **A missing height is no
   height.** A masked or NaN height is stored as NaN, and its point is drawn at sea level…
```

The state is first, in bold. The parenthesis holds the date the decision was agreed, who
agreed it, as one or more `{user}` roles, and the pull request that banked it. The bold run
after the dash is the decision's title, and the reasoning follows, as it does today. The
date is when the decision was agreed, which can be earlier than the day its pull request
merged.

(ledger-spec-3-3)=
### 3.3 Retiring a Decision

```markdown
5. **🗄️ Retired** (2026-11-04, {user}`bjlittle`, {pull}`2801`; agreed 2026-10-28,
   {pull}`2771`) — **Heights are given once.** A mesh that carries heights and is given
   more is refused… Retired because a layer may now restate its heights; replaced by
   §2 decision 12.
```

The parenthesis holds the retirement's date, who retired it and the pull request that did,
then the date and pull request of the original agreement, so the entry keeps its history
whole. The title and text stay as they were agreed, and a sentence after them says why the
decision was retired and what, if anything, replaced it: a later decision of this
specification, a decision of another, or nothing. A replacement is cited in the form of
§3.1, so the suite can check that it exists and is in force. The text is not struck through,
as the documentation enables no MyST extension that would do it, and the state says what a
strike-through would.

(ledger-spec-3-4)=
### 3.4 The Verification Section

```markdown
| Decision | Status | Evidence |
|---|---|---|
| 1 | ✅ verified (2026-10-30, {pull}`2777`) | `tests/bridge/test_heights.py` |
| 4 | ⏳ pending | |
| 5 | 🗄️ retired (2026-11-04, {pull}`2801`) | replaced by §2 decision 12 |
| 6 | ✍️ signed off (2026-10-30, {user}`bjlittle`, {pull}`2777`) | Checked in review that no public API accepts both a height and a z-level. |
```

The table has one row per decision, in order, from 1 to N. A row is added in the pull
request that adds its decision, and starts pending. Its states:

| state | meaning | Status carries | Evidence holds |
|---|---|---|---|
| `⏳ pending` | not yet shown to be delivered | nothing | optionally, the `candidate` row to deliver it |
| `✅ verified` | a test exercises it | the date and pull request | each test file, as a path |
| `✍️ signed off` | a reviewer checked it | the date, reviewer and pull request | what the reviewer checked |
| `🗄️ retired` | its decision is retired | the date and pull request | what replaced it, if anything |

A test file named as evidence cites the decision, in a comment or a docstring, and may cite
several. A test is named by its file, not its function, since a function is renamed far more
often than a file is moved. A verified row can gain evidence later, and a signed-off row can
become verified when a test is written for it. The suite reads the table by its header,
`Decision`, `Status` and `Evidence`, as it reads a roadmap by its header, so neither table's
vocabulary is mistaken for the other's.

A summary line follows the table, counting each state, as in "✅ 3 · ✍️ 1 · ⏳ 1 · 🗄️ 1:
4 of 5 decisions in force verified". The build writes it from the table, so nobody keeps it
up to date. How the build writes it is left to row 1 of §8.

(ledger-spec-3-5)=
### 3.5 When the Ledger Is Complete

A ledger is complete when no row is pending. §2 decision 8 asks for that once no roadmap row
is `in progress` or `not started`, with one exception: a pending decision that a `candidate`
row is to deliver names that row in its Evidence cell, as `row 5 of §4`. The suite asserts
it from row 1 of §8 on, so the last row of a roadmap cannot land while a decision it should
have delivered is still pending, unless the pull request says so in the ledger.

(ledger-spec-3-6)=
### 3.6 What the Suite Holds

Row 1 of §8 appends one item to the list of docs spec §3.5, named Ledger. For every
specification it asserts that:

1. Its second section is titled Decisions, and its entries are numbered 1 to N without a
   gap.
2. Each entry opens with a state of §3.2 or §3.3, and carries a date, at least one `{user}`
   role and a `{pull}` role; a retired one also carries the date and pull request of its
   agreement.
3. Its last numbered section is titled Verification, and its table has one row per
   decision, in order.
4. A decision is retired exactly when its row is.
5. Each test file a verified row names exists, and cites that decision.
6. Every citation of a decision, anywhere in the corpus of docs spec §3.5, names a decision
   that exists.
7. The ledger is complete when §3.5 says it must be.
8. A retirement's replacement, when it names one, is a decision that exists and is in force.

A roadmap is recognised by its header, `#`, `Scope` and `Status`, as the Verification table
is by its own (§3.4). A specification not yet brought into the ledger is named in a list the
test keeps, beside the row of §8 that brings it in. Each of rows 4 to 6 shortens the list
and row 6 empties it, so the exemption cannot outlive the work it waits on.

(ledger-spec-3-7)=
### 3.7 What GitHub Answers

`.github/scripts/check_status_references.py` already asks GitHub whether each status cites
real work (docs spec §3.6). Row 2 of §8 extends it to the ledger:

- the pull request a decision's entry cites exists, and is merged or is the pull request
  being checked;
- a signed-off row's reviewer added the `signed-off` label to the pull request it cites, and
  the label is on it still, read from the pull request's events, which name who added each
  label and when;
- a verified row's pull request is merged on its date, as a landed roadmap row's is.

These need the network, so they run where the existing checks do: on every pull request, and
in the nightly `drift` run. A sign-off that cites its own pull request fails until the
reviewer adds the label, and passes once they do. Three things make that hold the merge,
and not merely show a failure:

1. **The workflow listens for labels.** `ci-spec-status.yml` triggers on `pull_request` with
   the types `opened`, `synchronize`, `reopened`, `labeled` and `unlabeled`, so adding or
   removing the label re-runs the check. GitHub's default types omit both, and a trigger on
   comments is not needed.
2. **The job always reports.** The workflow drops its `paths:` filter. The job decides for
   itself whether the pull request touches a specification or the files that check them,
   and passes at once when it does not. A required check that never reports holds a pull
   request at "Expected — Waiting for status" for ever, so the filter has to go first.
3. **The job is required.** Once rows 1 and 2 have merged, {user}`bjlittle` adds
   `status references`, the job's name, to the required checks of `main`'s branch
   protection. It is a repository setting, which no pull request can change, and adding it
   before the filter goes would hold every pull request that changes no specification.

With all three, a pull request carrying a sign-off nobody gave cannot merge, and auto-merge
waits for the label.

Row 2 creates the label. The label covers the pull request, not a decision. Adding it says
the reviewer checked every sign-off row that cites the pull request, and each row says which
decision it covers and what was checked. A pull request carries few sign-offs, and one
review covers them together.

A pull request merged without its sign-off, by an override, is reported by the nightly run.
The reviewer can still sign off on the merged pull request, as GitHub accepts labels there,
and a follow-up pull request then moves the row's date to the label's. Until someone does,
the row returns to pending, so the ledger never records a sign-off that was not given.

(ledger-spec-3-8)=
### 3.8 The Report

```console
$ pixi run -e test verification-report           # every specification
$ pixi run -e test verification-report heights   # one, by prefix
```

For each specification the report lists every decision with its state, then every place in
the repository that cites it, grouped as source, tests, documentation, specifications and
plans. It flags what does not agree: a verified row whose test no longer cites its decision,
and a decision in force that nothing anywhere cites. It writes Markdown to standard output,
and to the job summary when it runs in CI. It fails only when it cannot read a
specification; a gap it reports is a finding, not a failure.

(ledger-spec-3-9)=
### 3.9 Bringing the Nine Specifications In

Row 1 of §8 brings in the docs and citation specifications, and rows 4 to 6 the other seven,
one family or a few small specifications at a time. For each:

1. **Number.** The five whose decisions are a bulleted list (docs, typing, zlevel, checks
   and citation) number them in their present order.
2. **Provenance.** Each decision is agreed by {user}`bjlittle`, on the date and in the pull
   request of the commit that first added it, found with `git log -S` on its title
   (§2 decision 14). For one, crs spec §2 decision 14 came with {pull}`2752` on 2026-10-27,
   three days after the file. A change to its wording since is an edit, unless it changed
   the decision's meaning, which the review of the pull request judges.
3. **Verify.** For each decision whose roadmap rows have landed, the test that exercises it
   gains a citation of it, and its row becomes verified, citing the pull request in which a
   test first cites the decision. For new work that is the pull request delivering it, so
   the rule reads the same forward and back. Where no test can show it, {user}`bjlittle`
   signs it off on the pull request doing the work. A decision whose work has not landed
   stays pending.
4. **Retire.** A decision that later work has already overtaken is retired, citing the pull
   request that overtook it where history shows one, and {user}`bjlittle` signs off the
   retirement on the pull request doing the work. Rows 4 to 6 therefore need a judgement on
   each decision, and are not mechanical.
5. **Report.** A decision found not to have been delivered, though the rows that should have
   delivered it landed, becomes an open item of its specification, with an issue.

(ledger-spec-3-10)=
### 3.10 What Changes in the Parent

Row 1 of §8 adds an "Extended by a child specification" note to docs spec §3.2 for the
citation form, to docs spec §3.5 for the new item, and to docs spec §3.6 for the new states,
each pointing here. The vocabulary of a decision and of its verification is stated here
(§3.2 to §3.4), and docs spec §3.6 points to it without repeating it.

(ledger-spec-3-11)=
### 3.11 Documenting the Workflow

Row 1 of §8 documents the workflow where a contributor meets it (§2 decision 15). The
specifications index, `docs/src/developer/specs/index.rst`, gains a section on decisions and
verification beside its section on statuses. It says how to add a decision, cite one, retire
one, verify one with a test, and sign one off, saying who may add the `signed-off` label,
and that an agent never does. The repository checks page, `docs/src/developer/checks.rst`,
gains each failure of §3.6 under the `spec-conventions` check and each of §3.7 under
`spec-statuses`, saying how to fix it. Row 2 adds the re-run on a review, and row 3 the
report, to the same section of the index. `docs/AGENTS.md` gains the rule an agent needs, in
its line on specifications.

(ledger-spec-4)=
## 4. Alternatives Considered

- **A verification table in a closing comment on each pull request.** It would sit where the
  work was reviewed, but anyone with sufficient rights can edit or delete a comment, it is
  outside version control, and nothing on the published page leads to it.
- **A review comment as the sign-off**, quoting the citation of the decision. It names a
  decision where a label names only the pull request, but a comment can be edited after
  the fact, and a check re-run by comments needs a trigger that runs with the repository's
  secrets for a comment from anyone. A label is one click, and its record cannot be edited
  (§2 decision 7).
- **An approving review as the sign-off.** An author cannot approve their own pull request,
  and `geovista-bot` approves on request, so an approval shows neither who checked nor
  what.
- **The generated report as the record.** A report built from the citations in the
  repository can show where a decision is cited, but not that a reviewer signed it off, nor
  why it was retired. It is kept as a view of the ledger (§2 decision 11).
- **A short citation form, `§2.3`.** It collides with the number of a subsection.
- **Provenance after the decision**, as a line beneath its text, or in a table of its own
  after the list. The first reads gently but scans poorly, and the second separates a
  decision from its history. State first matches the open items (§2 decision 4).
- **The ledger as a numbered list**, mirroring the decisions. It leaves more room for a
  sentence per entry, but scans as a block of text; the table's Evidence column holds the
  sentence a sign-off needs.
- **Immutable wording.** Retiring a decision to correct a typo would bury the history that
  matters under history that does not (§2 decision 3).
- **A test function as evidence.** It is finer, but breaks each time a test is renamed.
- **Verification after the Roadmap.** It would renumber the sections after it in every
  specification, and every citation of them.
- **Starting the ledger from today.** It would leave 69 decisions, and the work already
  delivered against them, outside it (§2 decision 12).

(ledger-spec-5)=
## 5. Testing

The items of §3.6 join `tests/test_spec_conventions.py`, each written as a rule returning
one message per fault, with fixtures that show it firing and a test of the repository that
shows it holding, as the existing items are. The fixtures build their emojis and section
signs instead of writing them, since the module sits inside its own corpus.
`tests/test_status_references.py` runs the rules of §3.7 against a fixed record of the work,
including a `signed-off` label added by the reviewer a row names, one added by someone else,
one added and then removed, and none. The report of §3.8 is tested against a small fixture
collection, for its grouping, its flags and its Markdown.

(ledger-spec-6)=
## 6. Scope

In scope: how a decision is cited, the provenance it carries, how it is retired, the
Verification section and its states, what the suite and GitHub check of them, the report,
and bringing the nine existing specifications into the ledger.

Out of scope: what any decision says; whether an edit to a decision's wording changes its
meaning, which is left to review (§2 decision 3); plans, which are frozen and may cite a
decision but are not governed by the ledger; and emojis for the states of a roadmap row or
an open item other than `landed`, which §7 holds open.

(ledger-spec-7)=
## 7. Open Items

Each carries the status grammar of docs spec §3.6.

1. **Open** — **The other states have no emoji.** A roadmap row that has landed carries ✅,
   and with this specification so do the states of a decision and of its verification. A
   row `in progress`, `not started` or `candidate`, and an open item, carry none. Giving
   them emojis would make every status in the collection read alike, but it changes the
   vocabulary of docs spec §3.6 and every specification that uses it, so it is a change of
   its own.

(ledger-spec-8)=
## 8. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | The ledger: decision anchors and citations, the grammar of §3.2 and §3.3, the Verification section and its summary, the suite of §3.6, the parent's notes, the documentation of §3.11, this specification's own Verification table, and the docs and citation specifications brought in, retiring "Sections only" | ✅ landed (2026-10-31, {pull}`2786`) |
| 2 | What GitHub answers (§3.7): the pull request each entry cites, each sign-off's label, the trigger on labels, and a job that always reports, after which `status references` becomes a required check | not started |
| 3 | The verification report (§3.8) | not started |
| 4 | The typing, zlevel and checks specifications brought into the ledger | not started |
| 5 | The crs specification brought into the ledger | not started |
| 6 | The globe, scene and heights specifications brought into the ledger | not started |

Statuses follow docs spec §3.6. Rows 2 to 6 each need row 1. Row 1 brings in the docs and
citation specifications itself, as it retires a decision of the citation specification and
adds notes to the docs specification. Rows 2 and 3 need nothing else, and can land in either
order. Once row 2 has merged, `status references` becomes a required check, a repository
setting {user}`bjlittle` changes (§3.7). Rows 4 to 6 can land in any order after row 1, but
best after that change: a sign-off they record before it is held by review alone, and is
checked against GitHub by the nightly run. Row 6 brings in the three specifications together
because each extends the one before, and their decisions cite one another.

(ledger-spec-9)=
## 9. References

- docs spec §3.2, §3.3, §3.5, §3.6, §3.7: the citation form, anchors, the conventions
  test, the status vocabulary and families this specification builds on.
- citation spec §4.2, §4.6: the citation transform, and the renumber guard that already
  freezes numbered items.
- `.github/scripts/check_status_references.py` and `tests/test_spec_conventions.py`: the
  checks this specification extends.

(ledger-spec-10)=
## 10. Verification

Each row follows §3.4.

| Decision | Status | Evidence |
|---|---|---|
| 1 | ✅ verified (2026-10-31, {pull}`2786`) | `tests/docs/test_geovista_citations.py`, `tests/docs/test_geovista_citation_xrefs.py` |
| 2 | ✅ verified (2026-10-31, {pull}`2786`) | `tests/test_renumbering.py` |
| 3 | ✅ verified (2026-10-31, {pull}`2786`) | `tests/test_spec_conventions.py` |
| 4 | ✅ verified (2026-10-31, {pull}`2786`) | `tests/test_spec_conventions.py` |
| 5 | ✅ verified (2026-10-31, {pull}`2786`) | `tests/test_spec_conventions.py` |
| 6 | ✅ verified (2026-10-31, {pull}`2786`) | `tests/test_spec_conventions.py` |
| 7 | ⏳ pending |  |
| 8 | ✅ verified (2026-10-31, {pull}`2786`) | `tests/test_spec_conventions.py` |
| 9 | ✅ verified (2026-10-31, {pull}`2786`) | `tests/test_spec_conventions.py` |
| 10 | ✅ verified (2026-10-31, {pull}`2786`) | `tests/test_spec_conventions.py` |
| 11 | ⏳ pending |  |
| 12 | ⏳ pending |  |
| 13 | ✅ verified (2026-10-31, {pull}`2786`) | `tests/test_spec_conventions.py` |
| 14 | ✍️ signed off (2026-10-31, {user}`bjlittle`, {pull}`2786`) | Checked in review that the provenance of the docs and citation specifications' decisions is that of the commit `git log -S` finds for each. |
| 15 | ✍️ signed off (2026-10-31, {user}`bjlittle`, {pull}`2786`) | Checked in review that the specifications index and the repository checks page document the workflow of §3.11. |
