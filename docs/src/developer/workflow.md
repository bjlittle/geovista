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

Every rule gives its reason and where it was agreed. An exception sits inside
the rule it narrows, with its own reason. Rules that a check enforces are on the
{ref}`Repository Checks <gv-developer-checks>` page instead, and the conventions
of the design specifications are on the {ref}`Specifications <gv-developer-specs>`
page, which these rules link to where they meet.

## Before You Start

### 1. 👥 Check the Premise, and Raise the Issue That Tracks It

Before stating a diagnosis or a status, reproduce it: search upstream for an
existing report, check whether a merged fix already exists, re-measure each
number and quote code from the file. A gap with no tracking issue gets one, and
is cited by its number. Writing the citation is what tests the claim, and it has
caught wrong diagnoses before they were filed upstream ({issue}`2569`).

### 2. 👥 Raise a Question of Scope Openly

When related work turns up mid-task, finish what was asked, then propose the
related piece with a reason. Neither narrow nor widen a change without saying
so. Once a widening is built and tested, say that it is done, so that it can be
objected to ({pull}`2597`).

### 3. 🤖 Ask the Maintainer One Specific Question at a Time

Name the options, say what each gives and recommend one. A question nobody
could answer with confidence today, such as how something will be used a year
from now, is turned into a choice that can be made now ({pull}`XXXX`).

### 4. 👥 Start Substantial Work From a Design Specification

A change with design choices worth recording gets a specification first. Work
whose issue already says what to build goes straight to implementation, with
the issue as its design ({issue}`2531`).

## Specifications and Plans

### 5. 👥 Land a Specification in Its Own Pull Request

A specification is reviewed and merged on its own, before any plan is written,
and is changed freely afterwards, since it is a living document. A small
amendment to a convention may share one pull request with the edits that apply
it, which the author offers as a choice ({pull}`2564`, {pull}`2778`).

### 6. 👥 Keep Specifications and Plans in the Developer Guide

A specification is `docs/src/developer/specs/YYYY-MM-DD-<topic>-design.md`, and
is published. A plan is `docs/src/developer/plans/YYYY-MM-DD-<project>-<topic>.md`,
kept in the repository but not published. An agent framework that defaults to
another place, such as `docs/superpowers/`, is overridden ({pull}`2573`).

### 7. 👥 Ship a Plan With Its Implementation in One Draft Pull Request

The plan is the first commit, and the maintainer reviews it before the
implementation goes on top. The pull request is marked ready once the
implementation has landed on it, and the plan is frozen once it merges
({pull}`2573`).

### 8. 👥 Mark a Roadmap Row First and Last

The pull request that delivers a roadmap row sets the row to `🚧 in progress`
in its first commit, citing itself, and to `✅ landed` in its last, dated that
day. If the merge slips to another day, the date is corrected before it lands
({pull}`2874`).

### 9. 👩 Leave a Judgement Label to the Person It Attests

Only the reviewer named in a `✍️ signed off` row adds the `signed-off` label,
since GitHub records the account and not the person (ledger spec §2 decision 7).
*Except:* an agent may add `spec: open item`, which records what an issue is,
not anyone's judgement (items spec §2 decision 11).

### 10. 👥 Prove a Verified Decision's Test by Breaking It

A `✅ verified` decision's test must fail when the decision regresses. Break
each clause the decision states, not just its example, and watch the test fail
before citing it as evidence ({pull}`2796`, {pull}`2826`).

## Writing

### 11. 🤖 Humanize Prose Before It Is Published

Documentation, docstrings, changelog fragments, pull request descriptions,
commit messages and issue bodies get a humanizer pass before they go out, as a
step and not a checkpoint. `AGENTS.md` files, code comments and plans are left
alone ({pull}`2544`).

### 12. 👥 Name People by Their Handle

Write {user}`bjlittle`, or ``:user:`bjlittle` `` in reStructuredText, never a
first name, and don't assume anyone's pronouns. In text on GitHub, leave out a
bare `@handle`, which sends a notification ({pull}`2573`).

### 13. 👥 Cite a Design Specification by Its Citation

Name a part of one as `ledger spec §2 decision 7` or `row 4 of ledger spec §8`,
which the build links, and a whole specification with a link to its page. This
holds in changelog fragments too ({pull}`2884`).

### 14. 👥 Title Pages and Sections in Headline Style

The {ref}`title style <gv-developer-documentation-title-style>` applies to every
hand-written title ({pull}`2712`).

## Pull Requests

### 15. 🤖 Label Agent Work `agentic`

Every issue and pull request an agent raises carries the `agentic` label, beside
its `type:` labels. The `gh` command runs as the repository owner, so nothing
else marks the work as an agent's. It is not the `bot` label, which marks
dependabot and the scheduled workflows. The same applies in
`bjlittle/geovista-data` ({pull}`2540`).

### 16. 🤖 Credit the Agent in Its Changelog Fragments

A changelog fragment an agent writes ends ``(:user:`claude`)``, never with the
maintainer's handle ({pull}`2425`).

### 17. 👥 Give a Pull Request a Changelog Fragment, or Skip It Openly

A pull request carries a fragment unless it is labelled `skip-changelog`. A
change to the README alone usually skips it, unless its cause is upstream and
would be news to readers elsewhere. An agent offers that choice, and does not
make it silently ({pull}`2554`).

### 18. 👥 Close an Issue Only From the Pull Request That Fixes It

A closing keyword never goes in a companion pull request in another repository,
which merges first, or before an issue the pull request leaves open, even
negated: GitHub reads "doesn't close" as closing ({pull}`2889`).

### 19. 👥 Give Every Deferred Piece of Work an Issue

A minor point left by a review, an older defect found on the way, or a follow-up
is raised as an issue and linked from the plan's record and the pull request's
description. It is never left only in a review thread ({pull}`2599`).

### 20. 🤖 Confirm a Push Before Reporting It

The remote branch must show the local commit, checked with `git ls-remote`,
before the work is called pushed ({pull}`2740`).

## Review

### 21. 👥 Reproduce a Finding Before Fixing It

A review finding names the symptom it hit, not the extent of the bug, so ask how
far it reaches. The same confusion often runs the other way too ({pull}`2551`,
{pull}`2553`).

### 22. 👥 Answer Every Finding in Its Thread

The reply states the commit that fixed it and what changed. A finding is
answered when its thread has a reply, not when the commit lands ({pull}`2565`).

### 23. 👥 Prefer Progress to Perfection When Findings Repeat

When a review keeps finding edge cases in the same logic, fix a real regression
or a more principled rule, then name the line past which cases are accepted, and
raise further variations for discussion ({pull}`2877`).

## Other Projects

### 24. 🤖 Disclose an Agent's Hand in Another Project's Issue

An issue an agent drafts for another project opens with a note that an agent
researched and drafted it, measures what it asks for and offers a follow-up pull
request. The maintainer reviews it before it is posted, as with
[scientific-python/lazy-loader#181](https://github.com/scientific-python/lazy-loader/issues/181).

## Keeping These Rules

### 25. 🤖 Record a New Rule on This Page

The pull request that establishes a rule adds it here, never only to an agent's
memory, so that every session and every contributor sees the same rules
({pull}`XXXX`).

### 26. 👥 Keep a Rule's Number for Good

A new rule takes the next free number, in whichever section it belongs. A rule
that no longer holds is retired in place, marked `🗄️`, with the date, the reason
and what replaced it. It is never deleted or renumbered, so that
`workflow rule 8` always names the same rule ({pull}`XXXX`).
