# Decision Owners Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the specifications whose
> decisions it gives an owner. It states how each decision names the roadmap row that
> delivers it, how a row is held to the decisions it owns, and how the owner of every
> decision in the collection is named. Cite it as `owner spec §…`. Read it as current; the
> roadmap states what has actually landed.

- **Date:** 2026-11-24 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `owner spec §…`
- **Scope:** the row that owns each decision: the Row column of the Verification table,
  which row owns a decision, the gate on landing a row, moving an owner, the build's links
  and the line under each decision, the report, and the owner of every decision in the
  collection named
- **Lineage:** [docs spec](2026-10-06-published-specs-design.md) ›
  [ledger spec](2026-10-30-decision-ledger-design.md) › **owner spec**
- **Children:** none
- **Extends:** ledger spec §3.4, whose table gains a column, ledger spec §3.5, whose check
  at the end of a roadmap the gate of §4.3 holds at every row, and ledger spec §3.8, whose
  report names each row's decisions
- **Published:** in the specifications index

(owner-spec-1)=
## 1. Purpose

An open item names the roadmap row that owes it, and a row cannot land while an item it
owes is open (items spec §2 decision 3, items spec §2 decision 5). A decision names no
row. Its Verification row says whether it is delivered, and in which pull request, but not
which row of the roadmap delivers it. A developer who reads a decision and wants to see the
work that keeps its promise has to search the roadmap and the plans for it.

Of the 22 decisions pending today, 20 already name rows in their Evidence cell, though
ledger spec §3.4 asks it only of a `candidate` row, and 12 of them name a range, as
`rows 3 to 13 of §10`. Nothing reads them. The only check is ledger spec §3.5,
which waits until no row of the roadmap is left to start, so a row can land leaving a
decision it should have delivered pending, and nothing says so until the last row lands.
Nor does the pull request always lead to the row: 50 of the 134 decisions delivered were
verified or signed off in a pull request that landed no row of their own specification,
when the ledger brought the older specifications in (§3.2).

This specification gives every decision an owner: the row that delivers its promise. Its
goals, as {user}`bjlittle` put them, are that a developer can go from any decision to the
row that delivers it, and assess at a glance which decisions are delivered and by what;
that each decision's provenance says so explicitly; and that a gate holds the record, so a
reader can trust that nothing is missed. Its non-goals are changing how a decision is
agreed, verified, signed off or retired, and the owners of open items, which
items spec §3.4 already gives. Its anti-goals are an owner that can go stale without the
suite noticing, and an owner written in two places.

(owner-spec-2)=
## 2. Decisions

These were decided with {user}`bjlittle` on 2026-11-24, except where a decision says it is
the author's call.

1. **🤝 Agreed** (2026-11-24, {user}`bjlittle`, {pull}`3012`) — **Every decision names the
   one row that owns it, and keeps it.** The owner is the row whose pull request delivers
   the decision's promise. It stays once the decision is verified or signed off, as part
   of its provenance, so a decision long delivered still leads to its row. Chosen by
   {user}`bjlittle` for finding the work behind a decision, over an owner kept only while
   the decision is pending, which would serve the gate and nothing else. See §4.1 and §4.2.
2. **🤝 Agreed** (2026-11-24, {user}`bjlittle`, {pull}`3012`) — **The owner is a Row column
   of the Verification table.** It sits between the decision and its status, so a reader
   sees what is delivered and by which row side by side, and reads down one column to see
   what a row delivers. Chosen by {user}`bjlittle` over 🎯 in the decision's entry, which
   would write delivery into the record of an agreement that changes only when the
   decision is retired, and over each roadmap row listing its decisions, which leads from
   the row to the decision, the other way from the question asked. See §4.1.
3. **🤝 Agreed** (2026-11-24, {user}`bjlittle`, {pull}`3012`) — **A decision has one owner,
   never a range.** A range says where a decision is exercised; the owner is the row that
   must show it holds. A later row that exercises it adds evidence, as ledger spec §3.4
   allows. See §4.2.
4. **🤝 Agreed** (2026-11-24, {user}`bjlittle`, {pull}`3012`) — **A row cannot land while a
   decision it owns is pending.** Its pull request verifies the decision, signs it off,
   retires it or moves it to a later row. The suite holds it at every row, so the record
   can be trusted without being checked by hand. See §4.3.
5. **🤝 Agreed** (2026-11-24, {user}`bjlittle`, {pull}`3012`) — **Every decision in the
   collection names its owner, the oldest included.** Most of the decisions verified when
   the ledger brought the older specifications in name no row by their pull request, so
   their owners are read from their roadmaps, and each call is put to {user}`bjlittle` in
   the plan of row 1 of §9. Chosen by {user}`bjlittle` over owners for decisions agreed
   from now on, which would leave the older specifications without a way from a decision to
   its row. See §4.7.
6. **🤝 Agreed** (2026-11-24, {user}`bjlittle`, {pull}`3012`) — **The owner is a row of the
   decision's own roadmap.** The author's call, following items spec §3.4: the gate then
   reads one roadmap, and work that lies in another specification's row is owned by a row
   of this roadmap landing `with` it (order spec §4.1). See §4.2.
7. **🤝 Agreed** (2026-11-24, {user}`bjlittle`, {pull}`3012`) — **A move is written into the
   Row cell, with no limit and no graduation.** The author's call. A move names the row the
   decision leaves, the date and the pull request, as an item's does
   (items spec §2 decision 6), so a decision that keeps moving is plain to see. An item
   that outlives two rows is work of its own, and graduates to a row
   (items spec §2 decision 7). A decision is a promise about work, and one that cannot be
   delivered is retired. See §4.4.
8. **🤝 Agreed** (2026-11-24, {user}`bjlittle`, {pull}`3012`) — **A `candidate` row may own
   a pending decision.** The author's call. It replaces a `candidate` row named in the
   Evidence cell (ledger spec §3.4), and the gate of §4.3 then holds
   ledger spec §2 decision 8 at every row: when no row is left to start, a pending
   decision's owner is a `candidate`. Ledger spec §2 decision 8 stays in force, and its check retires into the
   gate. See §4.3.
9. **🤝 Agreed** (2026-11-24, {user}`bjlittle`, {pull}`3012`) — **The build links each Row
   cell to its row, and names the owner under each decision.** The author's call. A line
   under each decision's entry names its owner, linked to the row, so a reader of the
   decision reaches its row in one step, and nothing is written twice: the build reads the
   line from the Row column. See §4.5.
10. **🤝 Agreed** (2026-11-24, {user}`bjlittle`, {pull}`3012`) — **A retired decision keeps
    the owner it had, and needs none.** The author's call. A decision retired once
    delivered keeps its row, as its history; one retired before it was delivered may leave
    the cell empty, as nothing was owed. See §4.1.
11. **🤝 Agreed** (2026-11-24, {user}`bjlittle`, {pull}`3012`) — **A pull request that
    delivers a decision without landing a row of its roadmap adds one, and lands it.** An
    amendment that shares a pull request with the edits applying it (workflow rule 2.1), or
    a fix that verifies a decision, adds a row to the decision's roadmap and lands it in the
    same pull request, as {pull}`2882` added and landed row 8 of ledger spec §8 for
    ledger spec §2 decision 17. Chosen by {user}`bjlittle` for its honesty, so that
    "delivered by" always names the row that did, over naming the nearest landed row whose
    work the decision extends. See §4.2.

(owner-spec-3)=
## 3. What Exists Today

(owner-spec-3-1)=
### 3.1 The Ledger

Every specification ends with a Verification table, one row per decision, read by its
header, `Decision`, `Status` and `Evidence` (ledger spec §3.4). A row's first cell cites
its decision, and the build links it there. A pending row's Evidence may name the
`candidate` row to deliver it. Ledger spec §3.5 checks, once no roadmap row is
`in progress` or `not started`, that no decision is pending unless its Evidence names a
`candidate`; `ledger_complete` in `tests/test_spec_conventions.py` holds it. The report
lists each decision's state and every place that cites it (ledger spec §3.8), and since
items spec §3.9 and order spec §4.6, each roadmap row and the items it owes.

(owner-spec-3-2)=
### 3.2 What the Decisions Name Today

A throwaway script read the Verification table of each of the 17 specifications at
`c79f1d1b`, on 2026-11-24, and matched each decision's pull request against the pull
requests its roadmap's landed rows cite:

| Decisions | Count | Owner |
|---|---|---|
| verified or signed off in the pull request that landed one row of their own roadmap | 84 | that row, read mechanically |
| verified or signed off in a pull request that landed no row of their own roadmap | 50 | read from the roadmap, one call each |
| pending | 22 | 20 name rows in their Evidence, 12 as a range; 2 name none |
| retired | 3 | §2 decision 10 |

The 50 are the decisions of the specifications written before the ledger, which its rows 4
to 6 brought in (ledger spec §3.9): the checks, scene, heights, crs, docs, typing, zlevel
and citation specifications, and the globe specification's older rows. The script then
read the sections each decision cites ("See §4.2") against the sections each roadmap row's
scope cites, and found an owner for 2 of them: the older roadmaps' scopes cite no section.
Read by hand they are plainer. The zlevel and checks specifications have one landed row
each, for 12 of them; the rest lie among two to five landed rows, each scoped clearly
enough to read.

(owner-spec-3-3)=
### 3.3 The Owner of an Open Item

An item names its owner in its own entry, as 🎯 `row N of §M`, a row of its own
specification that has not landed (items spec §3.4). A row lands only once no open item
names it, and its pull request settles, moves or promotes each it owes (items spec §3.5).
A move is written as ⬅️ with the row left, the date and the pull request, and an item moves
at most twice (items spec §3.6). This specification follows that model where a decision
behaves as an item does, and says where it differs.

(owner-spec-4)=
## 4. Design

(owner-spec-4-1)=
### 4.1 The Row Column

```markdown
| Decision | Row | Status | Evidence |
|---|---|---|---|
| §2 decision 1 | row 1 of §9 | ✅ verified (2026-12-01, {pull}`3020`) | `tests/test_spec_conventions.py` |
| §2 decision 2 | row 2 of §9 · ⬅️ row 1, 2026-12-01, {pull}`3020` | ⏳ pending | |
| §2 decision 3 | row 6 of §9 | ⏳ pending | |
| §2 decision 4 | row 1 of §9 | 🗄️ retired (2026-12-03, {pull}`3024`) | replaced by §2 decision 5 |
```

The table gains a `Row` column, second, read by its header as the others are. Its cell
holds the owner as `row N of §M`, the roadmap's section, in the citation form the build
already links (items spec §2 decision 10), then any moves (§4.4). Every decision in force
has an owner; a retired one keeps the owner it had, and one retired before it was delivered
may leave the cell empty (§2 decision 10). The Evidence cell no longer names a row: a
`candidate` that is to deliver a pending decision is its owner.

(owner-spec-4-2)=
### 4.2 Which Row Owns a Decision

The owner is the row whose pull request delivers the decision's promise: the one that
verifies it or signs it off. It is one row of the decision's own roadmap (§2 decision 6).
Where several rows exercise a decision, the owner is the first row by whose landing the
whole decision holds, and the rest add evidence: a commitment kept class by class is owned
by the row that completes it, and a principle that holds from the row that first builds
what it governs is owned by that row. Where two rows land together in one pull request, either may own
it, and the one whose scope names the work does.

A decision's owner is named when the decision is written: in its specification's pull
request, which writes the roadmap, or in the pull request of a row that adds a decision,
as {pull}`3001` added diagram spec §2 decision 10. When no row fits, the pull request adds
one, as `not started`, or as a `candidate` with its trigger when the decision waits on
something outside the project, as items spec §3.4 does for an item.

A pull request that delivers a decision but lands no row of the decision's roadmap adds a
row for it, and lands that row in the same pull request (§2 decision 11). Its scope says
what the pull request delivered, so the roadmap records every change that delivers a
decision, and the owner never names a row that did not.

(owner-spec-4-3)=
### 4.3 Landing a Row

A row's status may become `✅ landed` only when no `⏳ pending` decision names it as its
owner. The pull request that lands it does, for each pending decision it owns, one of
these:

- **delivers it**, as `✅ verified` or `✍️ signed off`;
- **retires it**, under ledger spec §3.3;
- **moves it**, to a later row, under §4.4.

The suite reads every Verification table, and fails on:

1. a decision in force with no owner, or with more than one;
2. an owner, or a row moved from, that is not a row of the decision's own roadmap;
3. a pending decision whose owner has landed;
4. a pending decision whose Evidence names a row;
5. a decision verified or signed off whose owner is neither `✅ landed` nor
   `🚧 in progress`.

The third is the gate. It needs no list of exemptions: a pending decision owned by a row
that has landed is a fault in whichever pull request made it so. Since a pending decision
is owned by a row not landed, once no row is left to start its owner is a `candidate`, so
the gate holds ledger spec §2 decision 8 as a consequence, and `ledger_complete` retires
into it (§2 decision 8).

The fifth is the author's call, from the builder check. Without it, a delivered decision
could name a row not started, the stale owner §1 rules out. It does not ask that the
owner's pull request be the one in the Status cell: the 50 decisions of §3.2 would break
that, and so would a decision signed off and later verified in another pull request, as
ledger spec §3.4 allows.

(owner-spec-4-4)=
### 4.4 Moving an Owner

A move appends to the Row cell the row the decision leaves, the date and the pull request,
as ⬅️ `row N, date, {pull}`, after the new owner, which may be a row the pull request adds.
The trail stays once the decision is delivered. There is no limit on moves, and no
graduation (§2 decision 7): a decision that cannot be delivered is retired, with a reason,
under ledger spec §3.3. A correction of an owner named wrongly, before its row has landed,
is an edit and writes no move.

The check of what GitHub answers (ledger spec §3.7, items spec §3.8) reads a decision's
moves as it reads an item's: the pull request a move cites must exist, and have merged on
the move's date. This is the author's call, from the builder check, so that a move cannot
cite a pull request that does not exist.

(owner-spec-4-5)=
### 4.5 The Build

The build links each Row cell's owner to its row in the roadmap table, and each moved-from
row likewise, as it links a citation of a row in any other place. Under each decision's
entry in §2 it writes one line, read from the Row column, linking to the row:

- **Delivered by** row N of §M, once the decision is verified or signed off;
- **Owned by** row N of §M, while it is pending;
- for a retired decision, **Delivered by** its owner if it has one, and nothing if not.

Nothing is written in the specification for the line, so it cannot disagree with the
table.

(owner-spec-4-6)=
### 4.6 The Report

The verification report gives each decision's owner beside its state, and lists under each
roadmap row the decisions it owns, as it lists the items a row owes, so the pull request of
a row in progress shows what it must deliver before it lands. The report stays a view,
never a gate (ledger spec §3.8).

(owner-spec-4-7)=
### 4.7 Naming Every Owner

Row 1 of §9 names the owner of each of the 159 decisions of §3.2, and of this
specification's own, in one pull request, since the checks of §4.3 fail until every one has
one:

- the 84 delivered in the pull request that landed one row of their own roadmap take that
  row, read by a script;
- the 50 delivered in a pull request that landed none take the row their roadmap shows
  delivering them, read by hand, or a row added and landed for them under §2 decision 11,
  as row 16 of crs spec §10 and row 11 of globe spec §9 were;
- the 22 pending take one row each, the first by whose landing the whole decision holds
  (§4.2), in place of a range; those naming none take the row their specification plans
  for them;
- the 3 retired keep the owner they had, if they were delivered.

The plan of row 1 tables every call that is not mechanical, with its reason, for
{user}`bjlittle`'s review before it is built, as row 1 of order spec §9 tabled every
ordering it moved. Naming an owner writes no move, since no owner was named before:
globe spec §2 decision 1 names rows 3 to 5, of which row 3 has landed, and takes row 5, by
whose landing the whole decision holds, with no trail. Each Evidence cell that names a row loses it. A decision whose evidence no
longer holds, found on the way, becomes an open item of its specification
(workflow rule 2.8), and is not settled here.

(owner-spec-4-8)=
### 4.8 The Developer Guide

The specifications index's account of the Verification table gains the Row column, the
gate and the move, and `docs/AGENTS.md` carries the rule in a line: every decision names the
row that delivers it, and a row cannot land while a decision it owns is pending.
The ledger specification gains an "Extended by a child specification" note in
ledger spec §3.4 and ledger spec §3.5, as items spec §3.4 did for the order specification,
and the example table of ledger spec §3.4 gains the column.

(owner-spec-5)=
## 5. Alternatives Considered

- **🎯 in the decision's entry**, as an item carries it (items spec §3.2). The owner sits
  where the decision is read, but the entry is the record of an agreement, which changes
  only when it is retired (ledger spec §3.3), and a move would edit it. Rejected by
  {user}`bjlittle` (§2 decision 2); §4.5's line gives a reader of the entry the owner
  without writing it there.
- **Each roadmap row listing its decisions**, as `· ⚖️ decisions 3, 4, 6` in its Scope cell.
  It reads well from the roadmap, but a reader of a decision has to search for it, and
  Scope cells already carry their orderings. Rejected by {user}`bjlittle` (§2 decision 2).
- **Owners for decisions agreed from now on.** Cheap, but the older specifications would
  keep no way from a decision to its row. Rejected by {user}`bjlittle` (§2 decision 5).
- **A range of rows.** It records where a decision is exercised, but names no row the gate
  can hold to it (§2 decision 3).
- **A report, with no gate.** It would name a pending decision owned by a landed row, but
  nobody would have to act on it, and the record could not be trusted (§2 decision 4).
- **The owner read from the pull request that verified it.** Nothing new to write, but
  50 decisions name a pull request that landed no row of theirs (§3.2), and a decision
  still pending has no pull request to read.

(owner-spec-6)=
## 6. Testing

`tests/test_spec_conventions.py` holds the checks of §4.3, each broken by a fixture that
breaks its clause (workflow rule 2.6), and reads the Row column through the grammar in
`geovista_citations`, which `tests/docs/test_geovista_citations.py` holds. A build test holds
the Row cell's links and the line under each decision. `tests/test_verification_report.py`
holds the report's owners, and `tests/test_status_references.py` the check of a move's pull
request. The fixtures that write a Verification table gain the column.

(owner-spec-7)=
## 7. Scope

In scope: the Row column and its grammar, the owner of every decision named, the checks of
§4.3 with `ledger_complete` retired into them, the check of a move's pull request against
GitHub, the build's links and line, the report, and the developer guide's account of them.

Out of scope: the owners of open items, which items spec §3.4 gives; the diagrams of
diagram spec §4.4, which draw rows and their orderings alone; any change to how a decision
is agreed, verified, signed off or retired; and the plans, which are frozen.

(owner-spec-8)=
## 8. Open Items

None yet.

(owner-spec-9)=
## 9. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | The Row column: its grammar in `geovista_citations`, the checks of §4.3 with `ledger_complete` retired into them, a move's pull request checked against GitHub (§4.4), the owner of every decision named (§4.7), and the developer guide's account (§4.1 to §4.4, §4.8) | 🚧 in progress ({pull}`3014`) |
| 2 | The build's links and the line under each decision (§4.5), and the report's owners (§4.6) · 🔗 after row 1 | 📋 not started |

Statuses follow docs spec §3.6. Row 1 renders the new column as a plain table, so it is safe
to land alone, and row 2 makes it navigable.

(owner-spec-10)=
## 10. References

- items spec §3.4, items spec §3.5 and items spec §3.6, whose owner, gate and move of an
  open item this specification follows for a decision.
- ledger spec §3.4, ledger spec §3.5 and ledger spec §3.8, which it extends, and
  ledger spec §2 decision 8, which its gate holds at every row.
- order spec §4.1, by which a row of one roadmap lands with another's.
- workflow rule 2.6, under which each check is broken before it is cited, and
  workflow rule 2.9, under which the survey of §3.2 was run.

(owner-spec-11)=
## 11. Verification

Each row follows ledger spec §3.4. Until row 1 of §9 adds the Row column, each pending
decision names the row to deliver it in its Evidence cell.

| Decision | Row | Status | Evidence |
|---|---|---|---|
| §2 decision 1 | row 1 of §9 | ⏳ pending | |
| §2 decision 2 | row 1 of §9 | ⏳ pending | |
| §2 decision 3 | row 1 of §9 | ⏳ pending | |
| §2 decision 4 | row 1 of §9 | ⏳ pending | |
| §2 decision 5 | row 1 of §9 | ⏳ pending | |
| §2 decision 6 | row 1 of §9 | ⏳ pending | |
| §2 decision 7 | row 1 of §9 | ⏳ pending | |
| §2 decision 8 | row 1 of §9 | ⏳ pending | |
| §2 decision 9 | row 2 of §9 | ⏳ pending | |
| §2 decision 10 | row 1 of §9 | ⏳ pending | |
| §2 decision 11 | row 1 of §9 | ⏳ pending | |
