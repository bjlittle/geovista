# Open Items Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the specifications it
> governs. It states how a gap found while delivering a specification is captured as one of
> its open items, which roadmap row owes it, what tracks it on GitHub, and how it is
> settled, moved or promoted. Cite it as `items spec §…`. Read it as current; the roadmap
> states what has actually landed.

- **Date:** 2026-11-02 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `items spec §…`
- **Scope:** the open items of every specification: how one is cited, the state and
  provenance it carries, the issue that tracks it, the roadmap row that owes it, and what
  happens to it when that row lands
- **Lineage:** [docs spec](2026-10-06-published-specs-design.md) ›
  [ledger spec](2026-10-30-decision-ledger-design.md) › **items spec**
- **Children:** none
- **Extends:** docs spec §3.6, whose open items gain an issue, a row that owes them, the
  state ⏭️ Deferred in a new sense, and the state 🎓 Graduated, and ledger spec §3.8, whose
  report gains each specification's roadmap and open items. It cites items and rows in the
  way ledger spec §3.1 cites decisions, and delivers row 5 of citation spec §9
- **Published:** in the specifications index

(items-spec-1)=
## 1. Purpose

A specification is written before its work, and delivering that work finds what the
specification missed. Landing a roadmap row is when that happens most: a review notices an
input the design never named, or a test shows a decision holding only in part. Each such
gap is follow-on work, and the specification is only a true picture of what is left to do
if the gap is written into it.

Today that depends on someone noticing. Row 5 of ledger spec §8 found that
`Transform.from_points` refuses a `pint` quantity, a gap in crs spec §2 decision 13. It was
raised as {issue}`2802`, and was written into the crs specification only because
{user}`bjlittle` asked whether it had been. Of the 33 items still open or deferred in the
collection when this specification was written, 23 cite no issue, and none but that one says
which roadmap row must settle it. A row can land while a question it depended on is still
open, and nothing notices.

The ledger gave decisions a state, a provenance and evidence, checked by the suite and by
GitHub. This specification does the same for open items. Each gap is an open item with an
issue of its own, owed by a row of its specification's roadmap. A row cannot land past an
item it owes without settling or moving it, and an item that keeps moving becomes a row of
its own. With the Decisions, the Roadmap and the Verification table, the Open Items are the
fourth part of a specification that a reader can trust to say what is left.

(items-spec-2)=
## 2. Decisions

These were decided with {user}`bjlittle` on 2026-11-02.

1. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **A gap found while
   delivering a specification is captured as one of its open items.** A gap may surface in
   a review, a plan, a test or a conversation, but it is not captured until the
   specification it affects says so. An issue on its own is a fallback, and §2 decision 2
   makes even that visible.
2. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **Every open item has an
   issue of its own, labelled `spec: open item`.** One issue per item, so the item and its
   issue open and close together. The label lets GitHub filter them, and lets the check
   run both ways: every item cites a labelled issue, and every open labelled issue is cited
   by exactly one item. This replaces docs spec §3.6's allowance for an **Open** item with
   nothing beside it.
3. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **Every open item names the
   roadmap row that owes it.** An item is follow-on work, and work in a specification
   belongs to a row. The row is one of the item's own specification, which is where the
   item is written.
4. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **Every open item records
   where it was found.** The date, and the pull request in which the gap surfaced, as a
   decision records where it was agreed. The pull request may be another specification's,
   as #2802's was.
5. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **A row cannot land while
   an item it owes is open, unless its pull request settles or moves the item.** Landing is
   when gaps surface, and some rightly belong to later rows, so a hard gate would push a
   finished pull request to settle an item with a thin answer. A move is allowed, and is
   reviewed and recorded instead.
6. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **A move is written into the
   item.** It names the row the item moved from, the date and the pull request, and the
   item becomes ⏭️ Deferred. The trail shows how often an item has moved, so one that
   keeps moving is plain to see.
7. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **An item moves at most
   twice, then graduates.** At the third landing that owes it, an item is resolved,
   abandoned with a reason, or promoted to a roadmap row of its own, at least a
   `candidate`. An item that outlives two rows is work in its own right, and the roadmap is
   where work is tracked. Promotion is a choice the landing pull request can make, so it is
   never blocked.
8. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **Work waiting upstream is
   owed by a `candidate` row with its trigger.** No state of its own exempts it. When the
   upstream release arrives there is work to do, and the row is where it is planned.
9. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **Each state, and each part
   of an item's provenance, carries an emoji.** ❓ Open, ⏭️ Deferred, 🏁 Resolved,
   🚫 Abandoned and 🎓 Graduated, and 🔎 found, 🎯 owed by, ⬅️ moved from and 🎫 the issue,
   separated by `·`. Resolved is not ✅, which the ledger keeps for a decision a test
   holds.
10. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **Every numbered item, in
    any section, is cited as `<prefix> spec §N item M` or `item M of <prefix> spec §N`, and
    a row as `row N of §M`, each checked and linked.** All three forms are written today
    without being checked: items of Open Items, such as `typing spec §8 item 9` in
    `pyproject.toml`, items of design sections, such as `scene spec §4.4 item 2` in
    `globe.py`, and every 🎯 of §2 decision 3 is a citation of a row. Taking every item in
    both forms means no citation in use changes. A citation that names nothing fails, as one
    of a decision does. Chosen by {user}`bjlittle` over Open Items alone.
11. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **An agent may add the
    `spec: open item` label.** It records what an issue is, not anyone's judgement, unlike
    `signed-off` (ledger spec §2 decision 7).
12. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **The report shows each
    specification's roadmap and open items beside its ledger.** One view for each
    specification, read as {user}`bjlittle` reads one: Decisions, Roadmap, Verification and
    Open Items. It stays a view, never a gate (ledger spec §2 decision 11).
13. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **Every existing item is
    brought in, and this specification is governed by its own rules.** The 46 items already
    written are given their provenance, and each open one its issue and its row, so the
    rules describe the whole collection, not only what is written from today.
14. **🤝 Agreed** (2026-11-02, {user}`bjlittle`, {pull}`2803`) — **The workflow is documented
    where contributors meet it.** The specifications index says how to raise an item with
    its issue and label, cite one, owe it to a row, and move, settle or promote it when a
    row lands. The repository checks page explains each new failure and how to fix it, as
    ledger spec §2 decision 15 asked of the ledger.

(items-spec-3)=
## 3. Design

(items-spec-3-1)=
### 3.1 Citing an Item and a Row

An item is a top-level item of the first numbered list of a section: an open item, or a
numbered step of a design section, such as the items of scene spec §4.4. A later list in
the same section, such as the steps of a procedure after its design, has no items a
citation can reach. An item is cited as `typing spec §8 item 9`, the citation of its
section, then the word `item` and its number, or the other way round, as
`item 9 of typing spec §8`. Within a specification, `§8 item 9`
and `item 9 of §8` mean its own item. The section is always named, because specifications
number their Open Items section differently, seventh in one and eighth in another. Each item
carries an anchor, `<prefix>-spec-N-item-M`, and the citation transform links the whole
citation to it, as it links a decision (ledger spec §3.1).

The Decisions section is the exception: its entries are decisions, cited only as
`§2 decision N` (ledger spec §2 decision 1), so a citation of an item of §2 fails. When the
citation specification weighed anchors for every item and row, it estimated 600 to 700 more
lines than sections alone, and deferred them to row 5 of citation spec §9 until they were
cited often enough to be worth it.

A row is cited as `row 5 of §10`, or across specifications as `row 5 of crs spec §10`, with
an anchor `<prefix>-spec-N-row-M`. A range, `rows 3 to 11 of §10`, names both ends, and each
end is checked. The forms are those the collection already writes, so no citation in use
changes; what changes is that each now names something that exists.

Items and rows are numbered and keep their numbers, so the renumber guard of
citation spec §4.6 already freezes a titled item, an untitled one once something cites it,
and every row. Together the two forms deliver
row 5 of citation spec §9 before its trigger. That trigger is more than twenty citations of items
and rows outside the specifications, and there were 11 when this specification was
written. The reason to deliver it now is this specification's own: 🎯 is a citation of a
row, and the landing gate of §3.5 cannot hold an item to a row it cannot read.
Row 1 of §8 lands that row, and retires the test that held it back.

(items-spec-3-2)=
### 3.2 An Item's Entry

```markdown
13. **❓ Open** (🔎 2026-11-02, {pull}`2799` · 🎯 row 5 of §10 · 🎫 {issue}`2802`)
    — **Coordinates as quantities.** §4.9 names …
```

The state is first, in bold. The parenthesis holds the parts of the item's provenance, each
led by its emoji and separated by `·`. The bold run after the dash is the item's title,
and its reasoning follows.

| State | Meaning | Parenthesis Carries |
|---|---|---|
| ❓ Open | a gap still to settle | 🔎, 🎯, 🎫 |
| ⏭️ Deferred | an open item moved at least once | 🔎, 🎯, one ⬅️ per move, 🎫 |
| 🏁 Resolved | settled | the date and the pull request, issue or link that settled it, then 🔎, 🎫 |
| 🚫 Abandoned | dropped, its reason in its text | the date and where the reasoning was recorded, then 🔎, 🎫 |
| 🎓 Graduated | promoted to a row of its own | the date and pull request, `to row N of §M`, then 🔎, 🎫 |

| Part | Meaning |
|---|---|
| 🔎 date, {pull} | found: when, and in which pull request, the gap surfaced |
| 🎯 row N of §M | owed by: the row of this specification that must settle it |
| ⬅️ row N, date, {pull} | moved from: the row it was owed by before, and the move's date and pull request |
| 🎫 {issue} | the issue that tracks it, required while it is open or deferred |

A terminal state leads with its own date and reference, then keeps 🔎 and 🎫, so the
history is never dropped. An item settled before this specification keeps its history as
it is: no issue is raised for it after the fact, so it carries 🎫 only if it cited an issue
already, and it may lead with the issue or link that settled it, as docs spec §3.6
allows. A deferred item after two moves, and its graduation:

```markdown
13. **⏭️ Deferred** (🔎 2026-11-02, {pull}`2799` · 🎯 row 7 of §10 · ⬅️ row 5,
    2026-12-01, {pull}`2850` · ⬅️ row 6, 2027-01-10, {pull}`2900` · 🎫 {issue}`2802`)
    — **Coordinates as quantities.** …

13. **🎓 Graduated** (2027-02-03, {pull}`2950`, to row 14 of §10 · 🔎 2026-11-02,
    {pull}`2799` · 🎫 {issue}`2802`) — **Coordinates as quantities.** …
```

An item's title and text stay as they were written. A resolution or an abandonment adds
sentences after them, saying what was settled or why the item was dropped.

(items-spec-3-3)=
### 3.3 The Issue and Its Label

Every item cites one issue, and no other item cites it. The issue carries the label
`spec: open item`, which joins the repository's `type:`, `status:` and `feature:` families
of labels, and its title is the item's. Raising an item raises its issue, in the same pull
request. Settling the item closes the issue, by a closing keyword in the pull request that
settles it, or by hand once it merges.

The label is a fact about the issue, so whoever raises the item adds it, an agent
included (§2 decision 11). Row 1 of §8 creates it, a repository change {user}`bjlittle`
confirms first.

(items-spec-3-4)=
### 3.4 The Row That Owes an Item

🎯 names a row of the item's own specification that has not landed. An item is written in
the specification whose work owes it, which is not always the one being delivered when it
is found: {issue}`2802` surfaced in a pull request of the ledger specification, and is owed
by row 5 of crs spec §10.

When no row fits, the pull request that writes the item adds one, as `not started` when
the work is planned, or as a `candidate` with its trigger when it waits on something
outside the project (§2 decision 8). A `candidate` row's trigger is asserted or admitted,
as docs spec §2 decision 6 requires of every row.

(items-spec-3-5)=
### 3.5 Landing a Row

A row's status may become `✅ landed` only when no ❓ Open or ⏭️ Deferred item names it in
🎯. The pull request that lands it does, for each item it owes, one of these:

- **settles it**, as 🏁 Resolved or 🚫 Abandoned;
- **moves it**, writing ⬅️ with the row it leaves, and 🎯 with a later row, which may be one
  it adds (§3.6);
- **promotes it**, as 🎓 Graduated, to a row it adds.

The suite reads every landed row against every open item, so the rule needs no list of
exemptions: an item owed by a row that has landed is a fault in whichever pull request made
it so.

(items-spec-3-6)=
### 3.6 Moving an Item, and Graduation

A move appends one ⬅️ to the item and changes its 🎯, and the item becomes ⏭️ Deferred. A
later row is any row of the same roadmap that has not landed. An item may carry two ⬅️ and
no more. When the row named by an item with two ⬅️ lands, the item is resolved, abandoned,
or graduates, and a third ⬅️ fails the suite (§2 decision 7).

Graduating, the item's title becomes the scope of a new row, `not started` or a
`candidate` with its trigger, and the item records the row it became. Its issue moves with
it: the row cites it, as a `not started` row may (docs spec §3.6), and the issue keeps its
label until the row lands, so the label still finds every gap in flight.

(items-spec-3-7)=
### 3.7 What the Suite Holds

Row 1 of §8 adds one item to the list of docs spec §3.5, named Open Items. For every
specification it asserts that:

1. Each item of an Open Items section opens with a state of §3.2, and its parenthesis
   carries the parts that state needs, in order: 🎫 always while it is open or deferred,
   and on a settled item only if it has one.
2. An open or deferred item's 🎯 names a row of its own roadmap that has not landed.
3. A deferred item carries one or two ⬅️, and an open one none; no item carries three.
4. A graduated item names a row that exists, and that row cites the item's issue.
5. No two items cite the same issue.
6. Every citation of an item or a row, anywhere in the corpus of docs spec §3.5, names one
   that exists.

The second assertion is the landing gate of §3.5, since landing a row is changing its
status. A specification not yet brought in is named in a list the test keeps, beside the row
of §8 that brings it in, as the ledger's was (ledger spec §3.6), and the last row empties
it.

(items-spec-3-8)=
### 3.8 What GitHub Answers

`.github/scripts/check_status_references.py` gains, for every item:

- its issue exists, is an issue, and carries `spec: open item`;
- the pull requests of 🔎, ⬅️ and a terminal state exist, and have merged, or are the pull
  request being checked;
- a ⬅️ date is within a day of its pull request's merge, and a terminal date follows
  docs spec §3.6, which lets it come before the merge that records it.

The nightly `drift` run also lists every open issue carrying the label, and reports any that
no item cites. That is the half of §2 decision 2 that catches a gap raised as an issue and
never written into a specification. It already reports an ❓ Open item whose issue has
closed, and now does the same for ⏭️ Deferred.

(items-spec-3-9)=
### 3.9 The Report

The verification report of ledger spec §3.8 gains two sections for each specification,
around its ledger: the Roadmap first, each row with its status, and Open Items last, each
item with its state, its 🎯 and the number of times it has moved. Its findings gain:

- an item on its last move, which must settle or graduate when its row lands;
- an item owed by a row `in progress`, which that row's pull request must answer.

A gap the suite or GitHub already refuses is not repeated as a finding.

(items-spec-3-10)=
### 3.10 Bringing the Items In

Rows 3 to 5 of §8 bring in the items already written, one family or a few small
specifications at a time. For each item:

1. **State.** Its state takes its emoji, and its terminal date and reference move to the
   front of the parenthesis. An item written as **Deferred** before this specification,
   such as globe spec §8 item 6 and globe spec §8 item 10, deferred until users ask for
   them, has never moved, so it becomes ❓ Open, owed by a new `candidate` row whose
   trigger is that a user asks for it, admitted as one no check can observe
   (docs spec §2 decision 6). Chosen by {user}`bjlittle`, as the same shape as
   §2 decision 8.
2. **Found.** 🔎 is the date and pull request of the commit that first added the item,
   found with `git log -S` on its title, as a decision's provenance is
   (ledger spec §2 decision 14).
3. **Issue.** An open item without an issue gets one, labelled. An issue cited by several
   items, as {issue}`2568` is by four items of the typing specification, stays with one
   and the others get their own.
4. **Owed.** An open item gets its 🎯, which needs {user}`bjlittle`'s judgement: the row
   whose work it belongs to, or a new row. Rows 3 to 5 are therefore not mechanical.
5. **Report.** An open item that no longer holds is settled in the same pull request, with
   the reason.

Row 1 brings in the docs, zlevel, checks and citation specifications itself, since their
items are all settled and need only steps 1 and 2.

(items-spec-3-11)=
### 3.11 What Changes in the Parents

Row 1 of §8 adds an "Extended by a child specification" note to docs spec §3.6, saying
that an open item's states, parts and issue are stated here, and that its sentence allowing
an **Open** item with nothing beside it no longer holds. It adds the same note to
ledger spec §3.8 for the report. Ledger spec §7 item 1 asks whether the other states should
carry emojis; this specification answers it for open items, and the row that brings the
ledger specification in settles or narrows that item to roadmap rows.

(items-spec-3-12)=
### 3.12 Documenting the Workflow

Row 1 of §8 documents the workflow where a contributor meets it (§2 decision 14). The
specifications index gains a section on open items, beside its section on decisions: how
to raise one with its issue and label, cite one, owe it to a row, move it, and settle or
promote it when a row lands, with an example of each state. It says who may add the
`spec: open item` label, and that an agent may. The repository checks page gains each
failure of §3.7 under `spec-conventions` and each of §3.8 under `spec-statuses`, saying how
to fix it, and `docs/AGENTS.md` gains the rule an agent needs in its line on
specifications. Row 2 adds the report's roadmap and open items to the index's paragraph on
the report, and each bring-in row adds nothing, since the workflow is the same for every
specification.

(items-spec-4)=
## 4. Alternatives Considered

- **An issue only where the specification cannot hold the work.** Fewer issues, but an item
  with none is invisible on GitHub, and the check could run in only one direction.
- **Refusing a row's landing until every item it owes is settled.** The strongest gate, but
  it rewards settling an item with a thin answer to land a finished pull request.
- **No gate, with the report flagging an item owed by a landed row.** No friction, but the
  report is never a gate, so this relies on someone reading it.
- **A cap on moves, after which an item must settle or be abandoned.** The number is
  arbitrary, and the easy way past it is to abandon the item and raise it again, which
  breaks its trail.
- **Escalation, a further move needing the `signed-off` label.** It never blocks, but
  stretches the label's meaning, and still lets an item drift while each move is agreed.
- **A state for work waiting upstream.** Simpler to write, but it is a second kind of item
  the gate has to exempt, and hides that an upstream release brings work.
- **✅ for Resolved.** The ledger keeps ✅ for a decision a test holds, and an item settled
  in a specification is not that.

(items-spec-5)=
## 5. Testing

The items of §3.7 join `tests/test_spec_conventions.py`, each a rule returning one message
per fault, with fixtures that show it firing and a test of the repository that shows it
holding. The fixtures build their emojis and section signs, since the module sits inside its
own corpus. `tests/test_status_references.py` runs the rules of §3.8 against a fixed record
of issues and labels, including a labelled issue no item cites, an item whose issue lacks
the label, and an item whose issue closed. The anchors and links of §3.1 are tested as a
decision's are, and the report of §3.9 against its fixture collection.

(items-spec-6)=
## 6. Scope

In scope: how an item and a row are cited, an item's states and provenance, its issue and
label, the row that owes it, moving and graduation, what the suite and GitHub check, the
report's roadmap and open items, and bringing the existing items in.

Out of scope: what any item says, and whether an item is resolved well, which is left to
review; emojis for a roadmap row's states, which ledger spec §7 item 1 keeps; and plans,
which are frozen, and may raise a gap but must write it into the specification to capture
it.

(items-spec-7)=
## 7. Open Items

Each carries the status grammar of §3.2.

1. **🏁 Resolved** (2026-11-02, {pull}`2807` · 🔎 2026-11-02, {pull}`2803` ·
   🎫 {issue}`2804`) — **A near-miss citation is not flagged.** A citation written in
   a form the grammar does not read is neither linked nor checked, and reads as a citation
   to a person, so review passes it. Four were found in two days: `(§2, decision 1)` and
   `decision 12 of §2` in the crs specification, `decision 12 of the CRS specification` on
   the repository checks page, and a prefix followed by `row` with no `§` in §1 of this
   specification. The grammar row 1 of §8 teaches could flag a prefix followed by `row`,
   `item` or `decision` with no `§`, and a section followed by a comma and one of them.
   Found while writing this specification ({pull}`2803`), and owed by row 1 of §8. Row 1
   added `near_misses` to `tests/test_spec_conventions.py`, flagging the two forms above
   and a third, `decision N of §M`, and fixed the six citations it found, all comma
   near-misses in the crs and globe specifications.
2. **🏁 Resolved** (2026-11-02, {pull}`2807` · 🔎 2026-11-02, {pull}`2807` ·
   🎫 {issue}`2806`) — **Cited untitled items are not frozen.** §3.1 says the
   renumber guard of citation spec §4.6 freezes every item, but it freezes only those
   opening with a bold title, and leaves an untitled list, such as the steps of a
   procedure, free to change. Of the 222 top-level numbered items, 32 are untitled, and
   two are cited from code already, as `scene spec §4.4 item 2` in `globe.py`. Settled by
   {user}`bjlittle` on 2026-11-02, as option (b): the guard freezes an untitled item once
   something cites it, pairing it by its text, and an uncited one stays free. Found while
   planning row 1 of §8, which owes it. Row 1 made the renumber guard do exactly that: it
   now freezes an untitled item once something cites it, pairing the item by its text.
3. **❓ Open** (🔎 2026-11-02, {pull}`2807` · 🎯 row 6 of §8 · 🎫 {issue}`2809`) — **A
   graduation to a row that has moved on passes.** `item_graduated` does not check the
   target row's status, so a graduation to a row that has already landed passes. A check of
   the status alone would fail every graduated item once its row moves on, as §3.6 means it
   to, so the check needs the row's status when the item graduated.
4. **❓ Open** (🔎 2026-11-02, {pull}`2807` · 🎯 row 6 of §8 · 🎫 {issue}`2810`) — **A heavily
   reworded cited untitled item can pass in place.** An insert and a removal before a cited
   untitled item, with the item itself heavily reworded, leave it at its own number. Its
   text no longer pairs, so the renumber guard pairs the leftover by number and passes it as
   reworded in place.
5. **❓ Open** (🔎 2026-11-02, {pull}`2807` · 🎯 row 6 of §8 · 🎫 {issue}`2811`) — **A citation
   such as item 9a is read as item 9.** The trailing form reads an item's number as digits
   alone, so `§8 item 9a` links item 9 with a stray letter, while the leading form reads
   `9a` and fails. The two forms should read a label alike.
6. **❓ Open** (🔎 2026-11-02, {pull}`2807` · 🎯 row 6 of §8 · 🎫 {issue}`2812`) — **An item
   state is matched by its prefix.** A state is read by its prefix, so a misspelt state such
   as `Openly` reads as Open. Item states should match exactly.
7. **❓ Open** (🔎 2026-11-02, {pull}`2807` · 🎯 row 6 of §8 · 🎫 {issue}`2813`) — **A new item
   can share an issue with an old-grammar item unseen.** `item_issues` reads only the
   specifications brought in, so a new 🎫 can cite an issue an old-grammar item already
   cites, and the clash surfaces only when that specification is brought in.
8. **❓ Open** (🔎 2026-11-02, {pull}`2807` · 🎯 row 6 of §8 · 🎫 {issue}`2814`) — **The
   renumber guard advises append when an item was removed.** Removing an uncited item before
   a cited one is reported with the advice to append rather than insert, which is wrong for
   a removal. The advice should follow the direction of the move.
9. **❓ Open** (🔎 2026-11-02, {pull}`2807` · 🎯 row 6 of §8 · 🎫 {issue}`2815`) — **An item's
   parenthetical is split on a middle dot inside a link or code span.** The parts are split
   on every middle dot, so one inside a link's text or a code span breaks the entry. It
   fails loudly, and no item holds one today.
10. **❓ Open** (🔎 2026-11-02, {pull}`2807` · 🎯 row 6 of §8 · 🎫 {issue}`2818`) — **A list
    after an unnumbered subheading is anchored by the grammar alone.** The grammar files a
    numbered list under the last numbered heading above it, while the build names only a
    numbered section's direct children. A list after an unnumbered subheading would be cited
    and checked in source but have no anchor in the build. Nothing in the corpus does this
    yet.

(items-spec-8)=
## 8. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | The items: citations of items and rows with their anchors (delivering row 5 of citation spec §9), the entry of §3.2, the suite of §3.7, the label, what GitHub answers (§3.8), the parents' notes, the documentation of §3.12, this specification's own Verification table and items, and the docs, zlevel, checks and citation specifications brought in | ✅ landed (2026-11-02, {pull}`2807`) |
| 2 | The report's roadmap and open items (§3.9) | not started |
| 3 | The typing specification's items brought in, with the `candidate` rows they wait on | not started |
| 4 | The crs specification's items brought in | not started |
| 5 | The globe, scene, heights and ledger specifications' items brought in | not started |
| 6 | Hardening: the open items found while landing row 1, §7 items 3 to 10 | not started |

Statuses follow docs spec §3.6. Rows 2 to 5 each need row 1, and can land in any order
after it. Rows 3 to 5 each raise the issues their specifications' items lack, and need
{user}`bjlittle`'s judgement on the row that owes each item (§3.10).

(items-spec-9)=
## 9. References

- docs spec §3.5, §3.6: the conventions test and the status vocabulary this specification
  builds on.
- ledger spec §3.1, §3.6, §3.7, §3.8: the citation of a decision, the suite, what GitHub
  answers and the report, which this specification follows and extends.
- citation spec §4.6 and row 5 of citation spec §9: the renumber guard, and the candidate
  row this specification delivers.
- {issue}`2802`: the gap whose capture prompted this specification.

(items-spec-10)=
## 10. Verification

Each row follows ledger spec §3.4.

| Decision | Status | Evidence |
|---|---|---|
| 1 | ✍️ signed off (2026-11-02, {user}`bjlittle`, {pull}`2807`) | Checked in review that the gaps found while delivering row 1 (#2804, #2806) were each captured as an open item with its own labelled issue. |
| 2 | ✅ verified (2026-11-02, {pull}`2807`) | `tests/test_spec_conventions.py`, `tests/test_status_references.py` |
| 3 | ✅ verified (2026-11-02, {pull}`2807`) | `tests/test_spec_conventions.py` |
| 4 | ✅ verified (2026-11-02, {pull}`2807`) | `tests/test_spec_conventions.py`, `tests/test_status_references.py` |
| 5 | ✅ verified (2026-11-02, {pull}`2807`) | `tests/test_spec_conventions.py` |
| 6 | ✅ verified (2026-11-02, {pull}`2807`) | `tests/test_spec_conventions.py`, `tests/test_status_references.py` |
| 7 | ✅ verified (2026-11-02, {pull}`2807`) | `tests/test_spec_conventions.py` |
| 8 | ⏳ pending | row 3 of §8 |
| 9 | ✅ verified (2026-11-02, {pull}`2807`) | `tests/test_spec_conventions.py` |
| 10 | ✅ verified (2026-11-02, {pull}`2807`) | `tests/test_spec_conventions.py`, `tests/test_renumbering.py`, `tests/docs/test_geovista_citations.py`, `tests/docs/test_geovista_citation_xrefs.py` |
| 11 | ✍️ signed off (2026-11-02, {user}`bjlittle`, {pull}`2807`) | Checked in review that the specifications index says an agent may add the `spec: open item` label. |
| 12 | ⏳ pending | row 2 of §8 |
| 13 | ⏳ pending | rows 1 to 5 of §8 |
| 14 | ⏳ pending | rows 1 to 2 of §8 |
