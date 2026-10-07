# geovista design specifications — publication and conventions

```{readingtime}
```

> **Living document.** This specification is maintained alongside the documentation system
> it describes. It states the conventions every `geovista` design specification follows:
> where they live, how their sections are addressed, how a citation is written, and what a
> reader may assume about a roadmap row that has not happened yet. Cite it as
> `docs spec §…`. Read it as current; the roadmap states what has actually landed.

- **Date:** 2026-10-06 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `docs spec §…`
- **Issue:** {issue}`2566`
- **Applies to:** every document under `docs/src/developer/specs/` and
  `docs/src/developer/plans/`
- **Scope:** how specifications are published and cited. What any individual specification
  says is its own business
- **Parent spec:** none. {ref}`typing spec §1 <typing-spec-1>` records that it inherited
  nothing because the conventions were not written down anywhere. This is that document
- **Published:** in the specifications index, since change 1 of {ref}`§4 <docs-spec-4>`
  took `orphan: true` off this document and the type coverage specification together

(docs-spec-1)=
## 1. Purpose

`geovista`'s design specifications are built and unreachable.

`myst_parser` registers `.md` of its own accord, whatever `source_suffix` in `conf.py`
names, so `sphinx` reads and renders
`docs/src/developer/specs/2026-10-06-type-coverage-design.md` today. No toctree holds it,
which warns as `toc.not_included` and fails `--fail-on-warning`, so it carries
`orphan: true` and the build stays green. Nothing links to it from anywhere in
`docs/src`. A reader who meets `typing spec 3.1` in a `pyproject.toml` comment has
nowhere to go, and a reader browsing the developer section is not told the collection
exists.

The measurement, taken on 2026-10-06:

| | count |
|---|---|
| published specifications reachable from the documentation | 0 |
| specifications rendered to HTML | 1 |
| citations in `pyproject.toml`, `.pre-commit-config.yaml` and `ci-typing.yml` | 7 |
| of those carrying a section sign | 0 |
| citation namespaces | 1 (`typing spec`) |

This specification closes that gap and states the conventions that keep it closed. It has
two halves, and only the first is a migration. **Publication** is where the documents live
so `sphinx` builds them and a reader can reach them. **Conventions** are how sections are
addressed, how a citation is written, and what a roadmap row commits to. Those are ongoing
contracts rather than migration steps, which is why this is a living specification rather
than a plan.

(docs-spec-2)=
## 2. Decisions

- **Specifications are published; plans are not.** A specification is maintained alongside
  the code it describes and is read as current. A plan records what was intended before
  implementation and is not updated afterwards, so publishing one would put a document on
  Read the Docs that is wrong by design. See {ref}`§3.1 <docs-spec-3-1>`.
- **A plan is withheld by `exclude_patterns`, not by `orphan: true`.** An orphan is a
  published page that nothing links to, which is a weaker claim than the one being made.
  See {ref}`§3.1 <docs-spec-3-1>`.
- **Sections are addressed by explicit anchors keyed to the section number**, never by the
  slug `docutils` derives from the heading text. See {ref}`§3.3 <docs-spec-3-3>`.
- **A citation carries the section sign.** `typing spec §3.1`, never `typing spec 3.1`. The
  sign is what makes the token unmistakable in running prose, and a form that a future
  transform cannot recognise is a citation written today that goes dead later. See
  {ref}`§3.2 <docs-spec-3-2>`.
- **A bare `§N` means the containing document's §N.** Inside a specification that is the
  ordinary way to name a neighbouring section. Outside the collection it is always an
  error, because `src/` and `tests/` own no sections. See {ref}`§3.2 <docs-spec-3-2>`.
- **A roadmap row either carries an assertion or carries an admission.** A row may state a
  trigger only if something fails when that trigger fires. A row whose trigger cannot be
  observed mechanically says so, in those words. See {ref}`§4 <docs-spec-4>`.
- **A status names the work that produced it.** A roadmap row that has landed, and an open
  item that has been settled, each carry the date and the pull request or issue that did
  it, from a closed vocabulary. See {ref}`§3.6 <docs-spec-3-6>`.

(docs-spec-3)=
## 3. Architecture

(docs-spec-3-1)=
### 3.1 Layout

```text
docs/src/developer/
├── index.rst       a card, and a toctree entry
├── plans/          tracked, excluded from the build
└── specs/          published
    ├── index.rst
    ├── 2026-10-06-published-specs-design.md
    └── 2026-10-06-type-coverage-design.md
```

`docs/Makefile` sets `SOURCEDIR = src`, so both directories sit inside the source tree and
`sphinx` reads the specifications natively. The plans are withheld by one entry in
`docs/src/conf.py`:

```python
exclude_patterns = [
    ...,
    "developer/plans/**",
]
```

The two directories stay siblings because the documents reference each other. A plan names
the specification it was derived from, and a specification's roadmap names the plans that
implement it, so a layout publishing one while moving the other breaks the links in one
direction and leaves them working in the other, which is the confusing kind of broken.
Those references also have to resolve in a checkout and in GitHub's web UI, where neither
is a `sphinx` reference.

Excluding the plans from the build takes them out of one more corpus. The reading-time
gate of `tests/docs/test_readingtime_coverage.py` derives its pages from the source tree
rather than from `sphinx`, so without a matching entry in its `EXCLUDED_DIRS` it would
hold a page `sphinx` no longer builds to carrying a banner nothing renders.
`_autoapi_templates` is the precedent, down to the test asserting that `conf.py` really
does exclude what the tuple claims it does.

A plan's own `orphan: true` and reading-time banner are left where they are. Neither does
anything once the page is excluded, and a plan is frozen, which means not editing it to
tidy a marker that has stopped mattering.

(docs-spec-3-2)=
### 3.2 The citation namespace

`docs/src/developer/specs/index.rst` carries the toctree and introduces the collection. It
states two things a reader cannot infer from any single document. First, that **these are
living documents**, so what they read is current and a divergence from the code is a
specification defect worth reporting. Second, that **the citation namespace has members**,
with the prefix naming which:

| citation | document |
|---|---|
| `docs spec §…` | this document |
| `typing spec §…` | `2026-10-06-type-coverage-design.md` |

Each specification declares its own prefix in its header banner, as both of these do. A new
specification chooses one unique across the collection and states it there.

The prefix is load-bearing rather than decorative. `sphinx` labels are global, so
`docs-spec-3-2` and `typing-spec-3-2` are distinct anchors naming unrelated sections, and a
reader who drops the prefix lands in the wrong document with nothing to tell them so.

Three details of the form. The prefix is matched without regard to case, so a sentence may
open with `Typing spec §3.2`. Where several sections are cited together the prefix carries
across the run, so `typing spec §3.2, §4` names two sections of one document; the separator
is a comma or a solidus, and the run may not wrap across a line, since a reader following
only the second line would read the tail as a reference to somewhere else. A dash is no
separator, so a range carries its prefix on both ends, as in
`typing spec §3.2–typing spec §3.4`. And a citation with no prefix means the containing
document:

> **A bare `§N` means this document. A reference to any other document names it.**

Stating it that way is what makes the unqualified form safe. Its meaning is fixed by where
it is written rather than by what the reader assumes, and the one thing it cannot be is a
silent reference to somewhere else.

The section sign is required. All seven of `geovista`'s first citations were written
without it, as `typing spec 3.1`, until change 1 of {ref}`§4 <docs-spec-4>` added it to
each. The sign is what separates a citation from an ordinary sentence containing a version
number, and a citation a transform cannot recognise renders as dead text rather than as a
link. Writing the seven correctly cost seven edits; leaving them would have cost a silent
gap in whatever is built on top.

(docs-spec-3-3)=
### 3.3 Section anchors

Every numbered heading carries an explicit MyST target immediately above it, keyed to the
section number with dots replaced by hyphens and prefixed by the document's slug:

```markdown
(docs-spec-3-2)=
### 3.2 The citation namespace
```

The target becomes the section's HTML `id`, so
`…/2026-10-06-published-specs-design.html#docs-spec-3-2` addresses this section directly.

Two reasons this is not optional. `docutils` derives its slug from the heading *text* and
discards the number, so `### 3.2 The citation namespace` would otherwise be addressable
only as `#the-citation-namespace`. Each specification renders as one long page, so a
citation landing at the top rather than at the section it names has not really resolved.
And prose-derived slugs collide silently: two sections both titled *Testing* produce one
slug, `docutils` disambiguates the second to `id1`, and that silently becomes `id2` the
moment a heading is inserted above it. Anchors derived from prose are unstable under
exactly the edits a living document invites.

Both specifications satisfy it, and change 1 of {ref}`§4 <docs-spec-4>` added the
assertion, so the next document is governed rather than merely well written.

(docs-spec-3-4)=
### 3.4 Cross-references inside a specification

A specification names its own sections constantly, and does it with a hand-written role:

```markdown
See {ref}`§3.1 <typing-spec-3-1>`.
```

That form carries two independent strings, and either can be wrong while the other reads
correctly. `` {ref}`§3.1 <typing-spec-3-4>` `` displays one section and opens another, and
both halves are invisible to everything that looks: a checker reading the text finds a
well-formed citation, and `sphinx` resolving the target finds an anchor that exists, so the
build stays clean. It is the failure mode a reader is least equipped to notice, because
nothing is broken from where they are standing.

`tephpy` removes the class outright by writing citations as plain text and deriving the
target from them at build time, so there is only one string and the two cannot disagree.
That is row 2 of {ref}`§4 <docs-spec-4>` and it is not built here.

So the roles stay for now, and the hazard is closed by assertion instead of by
construction: **a `{ref}` role naming a section must have a display text that agrees with
its target.** `` {ref}`§3.1 <typing-spec-3-1>` `` passes; the example above fails.

Converting them all to plain text now was the alternative, and it is rejected
because it would take working links away from readers today in exchange for a convention
whose machinery does not exist yet. When the transform lands it makes those citations links
again, the roles collapse to plain text, and this assertion retires with them.

(docs-spec-3-5)=
### 3.5 What holds the conventions

A convention that nothing checks decays. Renumbering a section strands every citation that
named the old number, and the failure is invisible, because a stale citation is still a
well-formed comment that still renders.

`tests/test_spec_conventions.py` derives its corpus from the repository rather than
declaring one, following `tests/docs/test_readingtime_coverage.py`, so a specification is
governed from the day it lands rather than from the day somebody remembers to list it.

The corpus is every text file in the repository, the specifications among them, less the
trees that are generated, fetched or frozen. Naming the areas instead would miss whatever
nobody thought to name. `developer/plans/` is outside it, for the reason it is outside the
build: a plan is frozen, so a rule it fails is a rule it cannot be edited to satisfy. The
first plan in the repository holds nine citations written before this document existed,
and the honest treatment of them is the same as the honest treatment of the plan, which is
to leave it saying what it said. A plan's citations are read by a person, who has the
specification in front of them.

The suite asserts:

1. **Pairing.** Every numbered heading carries a keyed anchor, and every anchor still has a
   heading beneath it. Both directions, because they catch different faults: a heading with
   no anchor is unaddressable, and an anchor left behind by a deleted section resolves to
   nothing. Reading only from the headings down misses the orphan, there being no heading
   left to start from.
2. **Keying.** An anchor sits immediately above the heading whose number it names. One that
   has drifted onto the wrong heading still resolves, so resolution alone does not see it.
3. **Resolution.** Every citation in the corpus names an anchor that exists.
4. **Form.** Every citation carries its section sign, no run wraps across a line, and a
   range carries its prefix on both ends, per {ref}`§3.2 <docs-spec-3-2>`.
5. **Agreement.** Every `{ref}` role naming a section displays the section it targets, per
   {ref}`§3.4 <docs-spec-3-4>`.
6. **Triggers.** Each observable roadmap condition of {ref}`§4 <docs-spec-4>`.
7. **Status.** Every roadmap Status cell and every open item opens with a word from the
   vocabulary of {ref}`§3.6 <docs-spec-3-6>`, and every terminal status carries an ISO date
   and at least one reference: an `{issue}` or `{pull}` role, or a link to an issue or pull
   request in another repository. This is the one rule a specification breaks by *not*
   editing it: a row goes stale by the work landing elsewhere, so the check has to read the
   column rather than the diff.

It also holds the publication of {ref}`§3.1 <docs-spec-3-1>` in place: no specification
carries `orphan: true`, the index's toctree lists every specification, and its namespace
table names every declared prefix.

Code is skipped, both fenced and inline. That is not a refinement, it is what lets a
specification quote its own rules: {ref}`§3.3 <docs-spec-3-3>` above illustrates the anchor
rule with a literal `(docs-spec-3-2)=` and its heading *inside* a fence, and
{ref}`§3.4 <docs-spec-3-4>` shows a deliberately mismatched `{ref}` role inline. A checker
reading either finds a duplicate anchor, a heading in the wrong place and a disagreeing
role, and fails on the passages documenting the rules it enforces. Skipping a fence means
matching the opening rail rather than counting delimiters, since a block opened with four
backticks may quote a three-backtick one.

The suite also asserts it is not vacuous. A corpus that finds no specifications, or no
citations, passes every rule above by never having looked, and that is the failure a gate
derived from a glob fails by.

**What this cannot catch.** A citation that is well formed and resolves, and names the
wrong section, is indistinguishable from a correct one. These checks are syntactic. What
narrows that class is the rule in {ref}`§3.2 <docs-spec-3-2>` giving the unqualified form a
local meaning, together with review, and nothing here should be read as claiming otherwise.

(docs-spec-3-6)=
### 3.6 Status, dates and the work that closed it

A roadmap row that says `landed` records that something happened and throws away which
thing. The change is in the history somewhere, with a number, a date, an argument in its
description and a review thread under it, and none of that is reachable from the row that
caused it. The same is true of an open item that quietly stops being open: the next reader
cannot tell a decision that was taken from one that was dropped.

So a status is three parts, in this order: the state, when it reached that state, and the
work that put it there.

```markdown
| 1 | The hook, the ratchet and its test | ✅ landed (2026-10-06, {pull}`2565`) |
```

```markdown
- **Resolved** (2026-10-06, {pull}`2565`) — **The ratchet needs twenty-three entries.**
  Measured against `main` rather than inferred: `examples/` still reports 28 errors…
```

The vocabulary is closed, so that a reader scanning a column is reading a known set rather
than inferring one from English:

| status | where | carries |
|---|---|---|
| `candidate` | roadmap row | the trigger that would promote it |
| `not started` | roadmap row | the issue tracking it, if one is raised |
| `in progress` | roadmap row | the pull request, open |
| `✅ landed` | roadmap row | the date, and every pull request that did it |
| **Open** | open item | the issue, if one is raised; otherwise the row that owns it |
| **Resolved** | open item | the date, and the pull request or issue that settled it |
| **Deferred** | open item | the horizon it is deferred to, and the issue holding it |
| **Abandoned** | open item | the date, and where the reasoning was recorded |

A terminal status — `landed`, **Resolved**, **Abandoned** — always carries a date and a
reference. The two non-terminal ones may carry neither: **Open** with nothing beside it is
a true statement about work nobody has started, and the convention is not improved by
forcing an issue into existence to satisfy a column.

Dates are ISO, and they are the date the state changed rather than the date the line was
written. Several references are listed in the order the work happened, so a row whose first
attempt needed a follow-up says so instead of naming only the one that finished.

What this buys is not bookkeeping. A reader who asks why the ratchet has twenty-three
entries and not the twenty-two {ref}`typing spec §3.2 <typing-spec-3-2>` predicted gets
from the row to
{pull}`2565` to the measurement that corrected it, without anybody having transcribed the
measurement into the specification. The specification stays the design; the references
carry the evidence.

(docs-spec-4)=
## 4. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | Publication, the `§` form, and `tests/test_spec_conventions.py` | ✅ landed (2026-10-07, {pull}`2573`) |
| 2 | Citation cross-reference transform | candidate |
| 3 | Citation integrity hook | candidate |
| 4 | Rendered-output gate | candidate |
| 5 | GitHub reference roles and hardcoded-link detection | candidate |

`candidate` and `not started` are different states, which is why
{ref}`§3.6 <docs-spec-3-6>` separates them. A `not started` row is wanted and unscheduled.
A `candidate` row is described, and whether it is wanted is the question the triggers below
answer.

Change 1 created `docs/src/developer/specs/index.rst`, added `developer/plans/**` to
`exclude_patterns` and to the reading-time gate's `EXCLUDED_DIRS`, gave
`docs/src/developer/index.rst` a card and a toctree entry, removed `orphan: true` from both
specifications, added the section sign to the seven existing citations, and landed the
test of {ref}`§3.5 <docs-spec-3-5>`. Two of this document's rules changed on the way, and
{ref}`§8 <docs-spec-8>` records both.

Rows 2 to 5 are candidates rather than scheduled work. When this specification was written
`geovista` had seven citations in one namespace, against `tephpy`'s 1,096 across nineteen,
and the machinery those rows describe is roughly 2,075 lines ({ref}`§9 <docs-spec-9>`).
Building it now would be engineering ahead of the need. Each row therefore names the
condition that ends that objection, and change 1 asserts every condition that can be
observed:

- **Rows 2 to 4** activate together, when the corpus outgrows review. What the transform of
  row 2 buys is a link for every plain-text citation and the retirement of the hand-written
  roles, and both grow with the number of citations. Row 3 shares its grammar, `tephpy`
  keeping one definition of a citation because two would disagree silently in both
  directions, and row 4 checks its output. *Asserted:* the test fails when the citations
  outside the specification collection, hand-written roles included, exceed thirty-five,
  five times the seven there were when this was written and the point at which reading
  them all stops being something anyone does.
- **Row 4** carries a pairing of its own. The input gate cannot tell whether the transform
  ran at all, and the output gate cannot tell a right target from a wrong one. *Asserted:*
  the test fails when a transform extension is registered in `conf.py` and the output gate
  is not wired into a task, which is the pairing rather than either half.
- **Row 5** has no observable trigger and is **revisited by hand**. Whether a `#` is a
  reference or a comment character is a judgement, and `see # 65` and `x = 1  # 3 files`
  put the same characters in the same places. A threshold over a token that ambiguous would
  fire on noise, and one tuned not to would fire on nothing. If this row is still open when
  it should not be, that is because someone did not re-read this table.

(docs-spec-5)=
## 5. Alternatives considered

- **Hand-writing a cross-reference role for every citation**, rather than deriving the
  target at build time. Rejected for {ref}`§3.4 <docs-spec-3-4>`'s reason: it manufactures
  one fresh opportunity per citation for a reference that displays correctly and opens the
  wrong section, which no gate can see. It is tolerated for the existing roles only because
  an assertion closes it and the transform retires it.
- **Publishing the plans alongside the specifications.** Simpler, one fewer rule. Rejected
  because a plan is not updated after implementation, so a published plan is a page on Read
  the Docs that is wrong by design and gives a reader no way to tell it from a page that is
  not.
- **Tracking the inherited infrastructure in an issue instead of a roadmap.** Rejected
  because an issue is unpublished, nothing holds it to being current, and the inventory
  belongs beside the conventions it would extend. {issue}`2566` tracks the work; this
  document holds the design.
- **Building rows 2 to 5 now, with change 1.** One change, nothing deferred, and the
  conventions arrive with the machinery that enforces them. Rejected as roughly 2,075 lines
  of extension, gates and tests serving seven citations in one namespace, where the
  namespace is the thing that gives most of it something to do.
- **Recording the candidate rows without triggers, to be revisited.** The cheapest option
  and the status quo elsewhere in this repository. Rejected on the evidence of the sentence
  it would repeat: the type coverage specification says its `orphan: true` marker holds
  "until the specs tree gains an index" and that the marker "comes off with the same
  change". Nothing was watching, nothing came off, and it took a direct question to notice.

(docs-spec-6)=
## 6. Testing

`tests/test_spec_conventions.py` holds {ref}`§3.1 <docs-spec-3-1>` to
{ref}`§3.6 <docs-spec-3-6>`, and the roadmap triggers of {ref}`§4 <docs-spec-4>`.

It sits in `tests/` rather than `tests/docs/` because it reads source files and needs no
built artefact, which puts it beside `tests/test_typing_ratchet.py`. That is the right
neighbourhood: both exist to stop a convention decaying quietly. `tests/docs` guards
the rendered output and skips without a browser; a gate that can skip is a gate that can
pass by not running.

A trigger assertion fails with a message naming its roadmap rows and what firing means, so
the person whose change carries the count past the ceiling is told which decision they have
just made rather than which number no longer matches.

(docs-spec-7)=
## 7. Scope

In scope: where specifications and plans live, how a reader reaches them, how a section is
addressed, how a citation is written, and what a roadmap row commits to.

Out of scope: what any individual specification says; the structure of the developer guide
beyond one card and one toctree entry; the Diátaxis quadrants, which are for users where
specification content is contributor material; and `docs/AGENTS.md`, which covers authoring
and building the documentation rather than this one collection inside it.

(docs-spec-8)=
## 8. Open items

Each carries the grammar of {ref}`§3.6 <docs-spec-3-6>`, so a reader can tell a decision
that was taken from one that was dropped.

1. **Open** (owned by row 2 of {ref}`§4 <docs-spec-4>`) — **The `{ref}` agreement
   assertion assumes the display text is the section number.**
   `` {ref}`§3.1 <typing-spec-3-1>` `` is the only form in use, and a role displaying a
   section's title instead would fail the check while being correct. Both specifications
   write it the one way today. If a second form becomes wanted, the assertion widens; it is
   not widened in advance for a form nobody has asked for. Row 2 owns it because the
   transform retires the roles, and this assertion with them.
2. **Open** (owned by rows 2 to 4 of {ref}`§4 <docs-spec-4>`) — **The threshold of
   thirty-five citations is a judgement, not a measurement.** It was five times the seven
   citations there were when it was set, chosen to fire before review stops being credible
   rather than at the point it does. This item once waited on a second namespace to measure
   against; `docs spec` became that namespace with change 1, which brought the count to
   fifteen, still too few to measure a better number from. Revising it is a change to this
   document.
3. **Open** ({issue}`2575`) — **Nothing proves the references in a status line point at
   real work.** {ref}`§3.5 <docs-spec-3-5>`'s seventh assertion checks that a terminal
   status carries a date and a reference, not that {pull}`2565` is the pull request that
   landed that row, or that it exists. Reaching GitHub from a test would make the suite
   fail on a network outage, and row 5 of {ref}`§4 <docs-spec-4>` is where reference
   checking belongs if it is ever wanted. Until then this is review's job, and saying so is
   the admission the rule in {ref}`§2 <docs-spec-2>` asks for.
4. **Resolved** (2026-10-07, {pull}`2573`) — **The status rule accepted only this
   repository's roles.** The seventh assertion of {ref}`§3.5 <docs-spec-3-5>` asked a
   terminal status for an `{issue}` or `{pull}` role, and the type coverage specification
   resolves one of its open items against an issue in `lazy-loader`, which neither role
   can name. A link to an issue or pull request in another repository now counts as the
   reference, so a decision settled elsewhere is cited where it was settled.
5. **Resolved** (2026-10-07, {pull}`2573`) — **Row 2's trigger fired on its own
   document.** It counted citation prefixes and failed past one, and this specification
   declares the second, `docs spec`, cited from the type coverage specification and from
   the files change 1 touches. The count also measured the wrong thing. A wrong prefix is
   the one mistake the transform cannot catch, since both anchors exist and either
   resolves, while what row 2 buys grows with the number of citations. Rows 2 to 4 now
   share the scale trigger of {ref}`§4 <docs-spec-4>`, decided while planning change 1.

(docs-spec-9)=
## 9. References

- {issue}`2566` — the tracking issue.
- [`bjlittle/tephpy`](https://github.com/bjlittle/tephpy) — where these conventions come
  from. Its own governing document is
  `docs/src/developer/specs/2026-08-03-published-specs-design.md`, cited there as
  `docs spec §…`. Surveyed on 2026-10-06 at `ee80574`:

  | piece | lines |
  |---|---|
  | `docs/src/_ext/tephpy_citations.py` — the shared citation grammar | 537 |
  | `docs/src/_ext/tephpy_citation_xrefs.py` — the build-time transform | 428 |
  | `.github/scripts/check_citations.py` — the integrity hook | 478 |
  | `.github/scripts/check_github_references.py` — issue and pull request roles | 322 |
  | `.github/scripts/check_rendered_citations.py` — the rendered-output gate | 310 |
  | **total** | **2,075** |

  serving 1,096 citations outside `docs/` across nineteen namespaces (5,063 counting the
  documentation itself, across twenty specifications), with four test suites
  (`test_citation_grammar.py`, `test_citations.py`, `test_citation_xrefs.py`,
  `test_rendered_citations.py`). It arrived over four plans rather than one change.
- {ref}`typing spec §1 <typing-spec-1>` — the document whose citations this governs, and
  whose unwatched `orphan: true` note is the argument for {ref}`§4 <docs-spec-4>`'s
  assertion rule.
- `tests/docs/test_readingtime_coverage.py` — the derived-corpus pattern
  {ref}`§3.5 <docs-spec-3-5>` follows, including an exemption tuple whose entries each carry
  the reason beside them.
