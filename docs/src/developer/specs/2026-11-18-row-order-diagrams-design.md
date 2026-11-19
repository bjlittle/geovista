# Roadmap Row Order Diagrams Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the specifications it
> draws. It states how the order between roadmap rows, which the conventions test reads as
> one graph, is drawn as diagrams: one of the open work across every specification, and one
> under each roadmap. Cite it as `diagram spec §…`. Read it as current; the roadmap states
> what has actually landed.

- **Date:** 2026-11-18 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `diagram spec §…`
- **Scope:** the diagrams of the order between roadmap rows: the graph they are drawn from,
  how a row and an ordering are drawn, which rows are ready, the view of each roadmap and
  the view of the open work, the verification report that shows them on a pull request and
  the job that runs it, and the developer guide's account of them
- **Lineage:** [docs spec](2026-10-06-published-specs-design.md) ›
  [ledger spec](2026-10-30-decision-ledger-design.md) ›
  [items spec](2026-11-02-open-items-design.md) ›
  [order spec](2026-11-17-row-order-design.md) › **diagram spec**
- **Children:** none
- **Extends:** order spec §4.5, whose graph it draws, and order spec §4.6, whose report
  gains the diagrams; the form of an ordering and the checks are inherited unchanged
- **Published:** in the specifications index

(diagram-spec-1)=
## 1. Purpose

Since row 2 of order spec §9 landed, the conventions test reads every ordering of every roadmap
into one graph and refuses an order that cannot hold. The graph exists only inside the
test, though. A reader sees it as clauses at the end of Scope cells, spread across sixteen
specifications, and has to assemble it in their head to answer the two questions it is
most often asked:

- **Where could work go next?** Choosing a new task means finding the rows that are not
  started and whose rows before them have landed, across every specification.
- **What follows the row I am on?** Working on a row, a developer wants to see what it
  holds back, in its own specification and in others, and what landing it will free.

This specification draws the graph, so that both questions are answered by looking. It
also shows the grammar of an ordering at work: each relation of order spec §4.2 is drawn
as one kind of arrow, beside the cells that write it.

Its goals are a view of the open work across the collection, a view of each roadmap under
its table, and the same views on a pull request, as the branch has them. Its non-goals are
planning, estimating or editing work from a diagram, and drawing anything but rows and
their orderings. Its anti-goals are a diagram that disagrees with what the checks hold, and
a diagram that someone has to keep up to date.

(diagram-spec-2)=
## 2. Decisions

1. **🤝 Agreed** (2026-11-18, {user}`bjlittle`, {pull}`2998`) — **Two views.** The specifications
   index shows the open work across every specification, for choosing where work goes
   next, and each specification shows its own roadmap's rows and orderings, for seeing
   where it stands and what follows the row in progress. See §4.4 and §4.5.
2. **🤝 Agreed** (2026-11-18, {user}`bjlittle`, {pull}`2998`) — **The build draws every
   diagram, from the graph the checks read.** The reading of the graph moves from the
   conventions test into the shared grammar, `geovista_citations`, which the test, the
   build and the report all load, and nothing generated is committed. Chosen by
   {user}`bjlittle` over diagrams committed beside each specification and held fresh by a
   test, which every pull request changing a status would have to regenerate. See §4.1.
3. **🤝 Agreed** (2026-11-18, {user}`bjlittle`, {pull}`2998`) — **A specification's diagram
   sits under its roadmap table.** The table and the diagram are read together. Chosen by
   {user}`bjlittle` over the header banner, before §1, where it would sit apart from the
   rows it draws. See §4.4.
4. **🤝 Agreed** (2026-11-18, {user}`bjlittle`, {pull}`2998`) — **The index shows the open
   work, not the whole collection.** Its view holds the rows that have not landed and the
   landed rows they wait on. The spike of §3.4 drew every ordered row as well, and found it
   too tall to read, mostly rows long landed. See §4.5.
5. **🤝 Agreed** (2026-11-18, {user}`bjlittle`, {pull}`2998`) — **A row's colour is its
   state, and a row that can start is marked ready.** A row is ready when it has not
   started, and every row it, or a row it lands together with, waits on has landed, and
   none of them is a candidate. Ready follows the rows that land together, so a row
   `with` one that still waits is not ready. See §4.2 and §4.3.
6. **🤝 Agreed** (2026-11-18, {user}`bjlittle`, {pull}`2998`) — **Every diagram carries a key
   of the relations.** Each relation is drawn as one kind of arrow, named by the words a
   Scope cell writes, and `before` is drawn as `after` read from the other row, so the key
   explains the grammar as well as the diagram. See §4.2.
7. **🤝 Agreed** (2026-11-18, {user}`bjlittle`, {pull}`2998`) — **Each row links to itself.**
   A row's box links to its row in its roadmap table, in its own specification or another,
   so a label can stay short. See §4.6.
8. **🤝 Agreed** (2026-11-18, {user}`bjlittle`, {pull}`2998`) — **A pull request shows the
   diagrams of the specifications it changes.** The verification report draws each, as the
   branch has it, in the job summary of a job that runs on each push to a pull request.
   Chosen by {user}`bjlittle` over a comment on the pull request, which would need to
   write to it, and so a trigger that zizmor flags for a pull request from a fork. The
   preview build of the documentation shows the same diagrams on the pages. See §4.7.
9. **🤝 Agreed** (2026-11-18, {user}`bjlittle`, {pull}`2998`) — **A specification's diagram
   shows the rows of others it orders against, and only those, in their own colours.**
   They are drawn small, at its edge, and link to their own rows, and a row its roadmap
   frees shows as ready there. Chosen by {user}`bjlittle` over drawing them greyed, which
   would hide on a pull request the rows of another roadmap its work frees. A roadmap with
   no ordering in or out draws no diagram. See §4.4 and §4.7.

(diagram-spec-3)=
## 3. What Exists Today

(diagram-spec-3-1)=
### 3.1 The Graph

`tests/test_spec_conventions.py` reads the graph (order spec §4.5). `ordering_edges` reads
each ordering once as an edge, its first row landing first, with `with` as a pair;
`row_statuses` reads every row's status by its anchor; `landed_on` reads a landed row's
date and pull requests; and `landing_together`, through Tarjan's algorithm in
`strongly_connected`, finds the rows each row's orderings force into its pull request.
The rules that fail, `order_cycles`, `order_candidates` and `order_statuses`, read the
graph through them.

(diagram-spec-3-2)=
### 3.2 The Build

`geovista_status` already writes a column into the specifications index at build time,
reading each roadmap with the parser the conventions test reads it with (docs spec §3.8),
so a diagram drawn by the build has a model to follow. `sphinxcontrib.mermaid` is a
documentation extension already, and the Codecraft and Packaging pages draw diagrams with
it, rendered in the reader's browser. Its `mermaid` node takes the diagram's text, so an
extension can place one without a directive in the page.

(diagram-spec-3-3)=
### 3.3 The Report

`.github/scripts/verification_report.py` reports each specification's roadmap, decisions
and open items (ledger spec §3.8, items spec §3.9), and the rows a row in progress lands
with (order spec §4.6). It appends to the job summary when `GITHUB_STEP_SUMMARY` is set,
but no workflow runs it: it is a pixi task, `verification-report`, run by hand
({issue}`2997`, §8 item 1).

(diagram-spec-3-4)=
### 3.4 The Spike

A throwaway script drew the graph as Mermaid, reading it with the functions of §3.1 at
`d4861563`, and `mmdc` 12.2.0 rendered it on 2026-11-18. Each specification is a box, each
ordering an arrow by its relation, each row coloured by its state, and a row ready to
start is green:

```{figure} figures/2026-11-18-row-order-diagrams-design/open-work.png
:alt: A flowchart of thirty roadmap rows in boxes, one per specification, joined by arrows. Landed rows are grey, rows not started are white, and six rows ready to start are green: row 3 of the crs specification, rows 3 and 5 of the floors specification, rows 3 and 4 of the heights specification, and row 1 of the layers specification.

The open work of every roadmap at `d4861563`: 26 rows not landed and the 4 landed rows
they wait on.
```

It measured the collection at 69 ordered rows, of 110, in twelve specifications, joined by
65 orderings, ten of them between specifications. The open work is 26 rows with 31
orderings, and reads well as one picture. Every ordered row, drawn the same way, is
1,816 pixels tall and mostly grey, which is why the index draws the open work alone
(§2 decision 4). Ready computed from each row's own orderings named row 5 of heights spec §9
and row 2 of crs spec §10, each `with` a row that still waits, so ready reads the rows landing together
(§2 decision 5). A label cut to 34 characters loses its meaning, and a link to the row
serves better than a longer one (§2 decision 7). `click … href` gave a link at Mermaid's
default `strict` security level, which disables only callbacks, so the documentation's
Mermaid configuration need not change.

(diagram-spec-4)=
## 4. Design

(diagram-spec-4-1)=
### 4.1 One Reading of the Graph

The reading of §3.1 moves into `geovista_citations`, beside `split_scope` and `ordering`,
which it already reads with: the edges, the statuses, a landed row's date and pull
requests, the strongly connected parts and the rows landing together, and the naming of a
row from its anchor. The conventions test imports them and keeps its rules, the build and
the report import them, and so the three cannot read the graph differently. A diagram
draws what the checks hold, and a defect in the reading shows in both.

One function writes the text of a diagram, Mermaid's `flowchart`, from the edges, the
statuses, the rows to draw and where each row links, and the build and the report both
call it.

(diagram-spec-4-2)=
### 4.2 How a Row and an Ordering Are Drawn

A row is a box labelled by its number and the opening words of its scope, inside a box for
its specification. Its state sets its colour:

| State | Drawn |
|---|---|
| `✅ landed` | grey, with grey text |
| `🚧 in progress` | amber |
| `📋 not started` | white |
| `💡 candidate` | white, its border dashed |
| ready (§4.3) | green, its border heavy |

An ordering is an arrow from the row that lands first:

| Relation | Drawn |
|---|---|
| `after` | a solid arrow, from the row named to the row that waits |
| `before` | the same arrow as `after`, written on the other row |
| `with` | a heavy arrow with a head at each end |
| `with or after` | a dotted arrow, from the row named to the row that waits |

Each diagram has a key beneath it giving the arrows and the colours, in the words a Scope
cell writes, and saying that `before` is `after` from the other row. The colours keep their
meaning in the documentation's dark theme.

(diagram-spec-4-3)=
### 4.3 Ready

A row is ready when it is `📋 not started`, every row that it, or any row landing together
with it, lands after or with or after has landed, and none of the rows landing together
with it is a `💡 candidate` or `🚧 in progress`. Rows landing together are those of
order spec §4.6, a strongly connected part of the graph, so a row `with` another that still
waits is not ready. Nor is one landing with a row in progress, since it can land only in
that row's pull request, and green would invite starting it alone; this is the builder
check's question, settled as the author's call. Ready is a reading of the graph for the
reader, and nothing fails on it.

(diagram-spec-4-4)=
### 4.4 The Diagram of a Specification

Directly under its roadmap table, each specification shows every row of its roadmap, and
each row of another specification that one of its rows orders against or is ordered
against by. Those are drawn small, in their own state's colour, ready included, in a box
of their own specification, and are the only rows of others drawn. So a row of another
roadmap that this one frees shows green at its edge (§2 decision 9). A roadmap of which no row carries or
receives an ordering draws no diagram, since it would show its rows alone. The build
places the diagram, so no specification writes anything for it.

(diagram-spec-4-5)=
### 4.5 The Open Work

The specifications index gains a section beside the table of docs spec §3.2, whose
Status column sums each roadmap, holding one diagram: every row of every roadmap that has
an ordering and has not landed, with each landed row one of them waits on or lands with.
Rows ready to start stand out in green, and the section says what ready means. A row with
no ordering is in its specification's diagram, and its Status cell, but not here.

(diagram-spec-4-6)=
### 4.6 Links

Each row's box links to the anchor of its row, on its specification's page, so a reader
moves from the picture to the table and its scope. Mermaid's `click … href` gives the link
at its default security level (§3.4).

The report's diagrams, in the job summary of §4.7, carry no links: the author's call, from
the builder check. The published `stable` documentation predates the specifications,
`latest` lacks whatever the pull request adds, a link to the pull request's preview build
fails until that build finishes, and GitHub may not follow a link from a diagram at all.
The preview's own diagrams link every row.

(diagram-spec-4-7)=
### 4.7 A Pull Request's Diagrams

The verification report draws, after each specification's roadmap, the diagram of §4.4,
for each specification it reports. A job runs it on each push to a pull request, for the
specification files that pull request changes, read from the files its diff names as the
spec status workflow reads them, and writes it to the job summary, which GitHub renders
with its diagrams; for a pull request that changes no specification, the summary says so.
The job reads the branch, so a row marked `🚧 in progress` by the plan's commit is amber on
that push's run, and on the run of the push that marks it `✅ landed`, each row it frees is
green, in its own roadmap or at the edge for another's (§4.4). A specification whose
diagram changes only because of another's row is not reported: chosen by {user}`bjlittle`
over reading the graph at the base and the head to find each one, since the rows at the
edge already show it. The
job needs to read the repository only, and runs on `pull_request`, the trigger zizmor
leaves alone. The report stays a view, never a gate (ledger spec §3.8): the job fails
only when the report cannot run.

(diagram-spec-4-8)=
### 4.8 The Developer Guide

The specifications index's section on ordering roadmap rows says where the diagrams are,
how to read one, and what ready means, and `docs/AGENTS.md` carries the rule in a line:
the diagrams are drawn by the build, under each roadmap and on the index, and the job
summary of each pull request shows those of the specifications it changes.

(diagram-spec-5)=
## 5. Alternatives Considered

- **Diagrams committed beside each specification, held fresh by a test**, as the lock file
  is. They would show in a diff and in GitHub's view of the file, but every pull request
  changing a status would regenerate them, and two open pull requests would conflict on
  generated text. Rejected by {user}`bjlittle` (§2 decision 2).
- **The build importing the conventions test**, as the report does today. Quick, but the
  documentation would depend on a test module. Rejected for §4.1, which moves the reading
  where both belong.
- **The whole collection as one picture.** Rejected after the spike of §3.4, for its
  height and its history; each specification's diagram shows its own landed rows.
- **The diagram in the header banner.** Rejected by {user}`bjlittle` (§2 decision 3).
- **A comment on the pull request**, updated on each push, as the coverage and
  documentation bots post theirs. Seen without a click, but it needs to write to pull
  requests, which a pull request from a fork gets only from a trigger zizmor flags, and it
  adds a comment to every pull request that changes a specification. Rejected by
  {user}`bjlittle` (§2 decision 8); it can come later without changing anything else.
- **Graphviz**, through `sphinx.ext.graphviz`. It lays out a graph well, but needs `dot` on
  every machine that builds the documentation, and GitHub does not render it in a job
  summary. Mermaid is already an extension, and GitHub renders it.

(diagram-spec-6)=
## 6. Testing

`tests/docs/test_geovista_citations.py` holds the reading of the graph once it moves
(§4.1), and the conventions test keeps its rules, reading through it. The diagram's text is
tested as text: each state's colour, each relation's arrow, ready, the rows a
specification's view draws, the open work's rows, and each row's link. A build test holds
that each specification with an ordering has its diagram directly under its roadmap table,
that one without has none, and that the index has the open work.
`tests/test_verification_report.py` holds the report's diagrams. The job is held by the
repository tests that read the workflows.

(diagram-spec-7)=
## 7. Scope

In scope: the reading of the graph moved into the grammar, the diagrams' text, the
diagram under each roadmap and the open work on the index, the report's diagrams and the
job that runs it on each pull request, and the developer guide's account of them.

Out of scope: any new check of the order, which order spec §4.5 holds; a diagram of
anything but rows and their orderings, such as open items or decisions; a comment on the
pull request; and the plans, which are frozen.

(diagram-spec-8)=
## 8. Open Items

Each carries the grammar of items spec §3.2.

1. **❓ Open** (🔎 2026-11-18, {pull}`2998` · 🎯 row 3 of §9 · 🎫 {issue}`2997`) — **The
   verification report is never run in CI.** Its docstring says it appends to the job
   summary in CI, and order spec §4.6 speaks of the report each pull request gets, but no
   workflow has ever run it, so its findings reach nobody who does not run it by hand.
   The job of §4.7 runs it.

(diagram-spec-9)=
## 9. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | One reading of the graph: the reading of order spec §4.5 moved into `geovista_citations`, with the conventions test reading through it, and the text of a diagram (§4.1 to §4.3) | ✅ landed (2026-11-19, {pull}`2999`) |
| 2 | The diagram under each roadmap and the open work on the index, drawn by the build, with their key and links, and the developer guide's account (§4.4 to §4.6, §4.8) · 🔗 after row 1 | 🚧 in progress ({pull}`3001`) |
| 3 | The report's diagrams, and the job that runs the report on each pull request (§4.7) · 🔗 after row 1 | 📋 not started |

Statuses follow docs spec §3.6. Row 1 changes no page and no report, so it is safe to land
alone, and rows 2 and 3 can land in either order.

(diagram-spec-10)=
## 10. References

- order spec §4.5, whose graph this specification draws, and order spec §4.6, whose report
  gains the diagrams.
- docs spec §3.8, whose Status column the build already writes, and docs spec §3.9, which
  governs the figure of §3.4.
- ledger spec §3.8, which keeps the report a view, never a gate.
- workflow rule 2.9, under which the spike of §3.4 was run.

(diagram-spec-11)=
## 11. Verification

Each row follows ledger spec §3.4.

| Decision | Status | Evidence |
|---|---|---|
| §2 decision 1 | ⏳ pending | |
| §2 decision 2 | ⏳ pending | |
| §2 decision 3 | ⏳ pending | |
| §2 decision 4 | ⏳ pending | |
| §2 decision 5 | ✅ verified (2026-11-19, {pull}`2999`) | `tests/docs/test_geovista_citations.py` |
| §2 decision 6 | ⏳ pending | |
| §2 decision 7 | ⏳ pending | |
| §2 decision 8 | ⏳ pending | |
| §2 decision 9 | ⏳ pending | |
