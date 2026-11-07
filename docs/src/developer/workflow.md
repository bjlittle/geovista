(gv-developer-workflow)=
(tippy-gv-developer-workflow)=

# {fa}`route` How We Work

```{eval-rst}
.. readingtime::
```

These are the rules `geovista` is developed by. They bind everyone who
contributes, people and AI agents alike, and an agent reads this page at the
start of every session. Each rule says who it applies to:

| Mark | Applies to |
|---|---|
| 👥 | everyone |
| 👩 | people only, and an agent never acts on it |
| 🤖 | AI agents only |

A rule opens with its status. `🤝 Agreed` gives the date, who agreed it and the
pull request or issue where. `🗄️ Retired` gives the same for its retirement,
then when it was agreed, why it no longer holds and what replaced it. An
exception sits inside the rule it narrows, with its own reason. Cite a rule by
its section and number, as `workflow rule 2.4`.

Rules that a check enforces are on the
{ref}`Repository Checks <gv-developer-checks>` page instead, and the conventions
of the design specifications are on the {ref}`Specifications <gv-developer-specs>`
page, which these rules link to where they meet.

## 1. Before You Start

### 1.1 👥 Check the Premise, and Raise the Issue That Tracks It

🤝 Agreed (2026-10-06, {user}`bjlittle`, {pull}`2564`)

Before stating a diagnosis or a status, reproduce it: search upstream for an
existing report, check whether a merged fix already exists, re-measure each
number and quote code from the file. A gap with no tracking issue gets one, and
is cited by its number. Writing the citation is what tests the claim, and it has
caught wrong diagnoses before they were filed upstream, as with {issue}`2569`.

### 1.2 👥 Raise a Question of Scope Openly

🤝 Agreed (2026-10-05, {user}`bjlittle`, {pull}`2549`)

When related work turns up mid-task, finish what was asked, then propose the
related piece with a reason. Neither narrow nor widen a change without saying
so. Once a widening is built and tested, say that it is done, so that it can be
objected to, as in {pull}`2597`.

### 1.3 🤖 Ask the Maintainer One Specific Question at a Time

🤝 Agreed (2026-11-06, {user}`bjlittle`, {pull}`2897`)

Name the options, say what each gives and recommend one. A question nobody
could answer with confidence today, such as how something will be used a year
from now, is turned into a choice that can be made now.

### 1.4 👥 Start Substantial Work From a Design Specification

🤝 Agreed (2026-10-02, {user}`bjlittle`, {issue}`2531`)

A change with design choices worth recording gets a specification first. Work
whose issue already says what to build goes straight to implementation, with
the issue as its design.

## 2. Specifications and Plans

### 2.1 👥 Land a Specification in Its Own Pull Request

🤝 Agreed (2026-10-06, {user}`bjlittle`, {pull}`2564`)

A specification is reviewed and merged on its own, before any plan is written,
and is changed freely afterwards, since it is a living document. A small
amendment to a convention may share one pull request with the edits that apply
it, which the author offers as a choice, as in {pull}`2778`.

### 2.2 👥 Keep Specifications and Plans in the Developer Guide

🤝 Agreed (2026-10-07, {user}`bjlittle`, {pull}`2573`)

A specification is `docs/src/developer/specs/YYYY-MM-DD-<topic>-design.md`, and
is published. A plan is `docs/src/developer/plans/YYYY-MM-DD-<project>-<topic>.md`,
kept in the repository but not published. An agent framework that defaults to
another place, such as `docs/superpowers/`, is overridden.

### 2.3 👥 Ship a Plan With Its Implementation in One Draft Pull Request

🤝 Agreed (2026-10-07, {user}`bjlittle`, {pull}`2573`)

The plan is the first commit, and the maintainer reviews it before the
implementation goes on top. The pull request is marked ready once the
implementation has landed on it, and the plan is frozen once it merges.

### 2.4 👥 Mark a Roadmap Row First and Last

🤝 Agreed (2026-11-04, {user}`bjlittle`, {pull}`2874`)

The pull request that delivers a roadmap row sets the row to `🚧 in progress`
in its first commit, citing itself, and to `✅ landed` in its last, dated that
day. If the merge slips to another day, the date is corrected before it lands.

### 2.5 👩 Leave a Judgement Label to the Person It Attests

🤝 Agreed (2026-10-30, {user}`bjlittle`, {pull}`2785`)

Only the reviewer named in a `✍️ signed off` row adds the `signed-off` label,
since GitHub records the account and not the person (ledger spec §2 decision 7).
*Except:* an agent may add `spec: open item`, which records what an issue is,
not anyone's judgement (items spec §2 decision 11).

### 2.6 👥 Prove a Verified Decision's Test by Breaking It

🤝 Agreed (2026-11-01, {user}`bjlittle`, {pull}`2796`)

A `✅ verified` decision's test must fail when the decision regresses. Break
each clause the decision states, not just its example, and watch the test fail
before citing it as evidence.

## 3. Writing

### 3.1 🤖 Humanize Prose Before It Is Published

🤝 Agreed (2026-10-04, {user}`bjlittle`, {pull}`2544`)

Documentation, docstrings, changelog fragments, pull request descriptions,
commit messages and issue bodies get a humanizer pass before they go out, as a
step and not a checkpoint. `AGENTS.md` files, code comments and plans are left
alone.

### 3.2 👥 Name People by Their Handle

🤝 Agreed (2026-10-07, {user}`bjlittle`, {pull}`2573`)

Write {user}`bjlittle`, or ``:user:`bjlittle` `` in reStructuredText, never a
first name, and don't assume anyone's pronouns. In text on GitHub, leave out a
bare `@handle`, which sends a notification.

### 3.3 👥 Cite a Design Specification by Its Citation

🤝 Agreed (2026-11-05, {user}`bjlittle`, {pull}`2884`)

Name a part of one as `ledger spec §2 decision 7` or `row 4 of ledger spec §8`,
which the build links, and a whole specification with a link to its page. This
holds in changelog fragments too.

### 3.4 👥 Title Pages and Sections in Headline Style

🤝 Agreed (2026-10-23, {user}`bjlittle`, {pull}`2712`)

The {ref}`title style <gv-developer-documentation-title-style>` applies to every
hand-written title.

## 4. Pull Requests

### 4.1 🤖 Label Agent Work `agentic`

🤝 Agreed (2026-10-03, {user}`bjlittle`, {pull}`2540`)

Every issue and pull request an agent raises carries the `agentic` label, beside
its `type:` labels. The `gh` command runs as the repository owner, so nothing
else marks the work as an agent's. It is not the `bot` label, which marks
dependabot and the scheduled workflows. The same applies in
`bjlittle/geovista-data`.

### 4.2 🤖 Credit the Agent in Its Changelog Fragments

🤝 Agreed (2026-08-11, {user}`bjlittle`, {pull}`2425`)

A changelog fragment an agent writes ends ``(:user:`claude`)``, never with the
maintainer's handle.

### 4.3 👥 Give a Pull Request a Changelog Fragment, or Skip It Openly

🤝 Agreed (2026-10-05, {user}`bjlittle`, {pull}`2554`)

A pull request carries a fragment unless it is labelled `skip-changelog`. A
change to the README alone usually skips it, unless its cause is upstream and
would be news to readers elsewhere. An agent offers that choice, and does not
make it silently.

### 4.4 👥 Close an Issue Only From the Pull Request That Fixes It

🤝 Agreed (2026-11-07, {user}`bjlittle`, {pull}`2891`)

A closing keyword never goes in a companion pull request in another repository,
which merges first, or before an issue the pull request leaves open, even
negated: GitHub reads "doesn't close" as closing, as {pull}`2889` found.

### 4.5 👥 Give Every Deferred Piece of Work an Issue

🤝 Agreed (2026-10-09, {user}`bjlittle`, {pull}`2599`)

A minor point left by a review, an older defect found on the way, or a follow-up
is raised as an issue and linked from the plan's record and the pull request's
description. It is never left only in a review thread.

### 4.6 🤖 Confirm a Push Before Reporting It

🤝 Agreed (2026-10-27, {user}`bjlittle`, {pull}`2740`)

The remote branch must show the local commit, checked with `git ls-remote`,
before the work is called pushed.

## 5. Review

### 5.1 👥 Reproduce a Finding Before Fixing It

🤝 Agreed (2026-10-05, {user}`bjlittle`, {pull}`2551`)

A review finding names the symptom it hit, not the extent of the bug, so ask how
far it reaches. The same confusion often runs the other way too, as in
{pull}`2553`.

### 5.2 👥 Answer Every Finding in Its Thread

🤝 Agreed (2026-10-06, {user}`bjlittle`, {pull}`2565`)

The reply states the commit that fixed it and what changed. A finding is
answered when its thread has a reply, not when the commit lands.

### 5.3 👥 Prefer Progress to Perfection When Findings Repeat

🤝 Agreed (2026-11-04, {user}`bjlittle`, {pull}`2877`)

When a review keeps finding edge cases in the same logic, fix a real regression
or a more principled rule, then name the line past which cases are accepted, and
raise further variations for discussion.

## 6. Other Projects

### 6.1 🤖 Disclose an Agent's Hand in Another Project's Issue

🤝 Agreed (2026-10-07, {user}`bjlittle`, https://github.com/scientific-python/lazy-loader/issues/181)

An issue an agent drafts for another project opens with a note that an agent
researched and drafted it, measures what it asks for and offers a follow-up pull
request. The maintainer reviews it before it is posted.

## 7. Keeping These Rules

### 7.1 🤖 Record a New Rule on This Page

🤝 Agreed (2026-11-07, {user}`bjlittle`, {pull}`2897`)

The pull request that establishes a rule adds it here, never only to an agent's
memory, so that every session and every contributor sees the same rules.

### 7.2 👥 Only Ever Add a Rule

🤝 Agreed (2026-11-07, {user}`bjlittle`, {pull}`2897`)

A new rule goes at the end of its section, and a new section at the end of the
page, so that `workflow rule 2.4` always names the same rule. A rule is never
deleted, moved or renumbered. One that no longer holds is retired in place, its
status becoming `🗄️ Retired` with why and what replaced it. A rule filed in the
wrong section is retired there and added again where it belongs.
