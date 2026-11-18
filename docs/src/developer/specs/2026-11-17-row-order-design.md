# Roadmap Row Order Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the specifications it
> governs. It states how a roadmap row says which rows it lands after, before or with, in
> its own specification or another's, and what checks that the orderings agree with each
> other and with what has landed. Cite it as `order spec §…`. Read it as current; the
> roadmap states what has actually landed.

- **Date:** 2026-11-17 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `order spec §…`
- **Scope:** the order between the roadmap rows of every specification: where an ordering
  is written, the words it is written in, an ordering against a release, the check that
  reads them all into one graph, the report of rows landing together, and the developer
  guide's account of them
- **Lineage:** [docs spec](2026-10-06-published-specs-design.md) ›
  [ledger spec](2026-10-30-decision-ledger-design.md) ›
  [items spec](2026-11-02-open-items-design.md) › **order spec**
- **Children:** none
- **Extends:** items spec §3.4, whose row *landing with* another becomes one relation of
  four, and items spec §7 item 15, which it designs before row 8 of items spec §8 builds it
- **Published:** in the specifications index

(order-spec-1)=
## 1. Purpose

A roadmap row often depends on another. It lands after the row whose work it builds on,
before the row that removes what it needs, or with a row of another specification in one
pull request. The specifications say so in prose, in the paragraph under each roadmap, and
in at least eight ways: *lands with*, *lands before*, *lands with or after*, *needs*,
*after row N*, *is planned once … has landed*, *waits on* and *once row N lands*. Nothing
reads them together, so nothing sees a cycle, a row that waits on one that can never land,
or a row marked landed before the row it needs.

The layers specification met the cost. Row 5 of heights spec §9 was to land with
row 4 of globe spec §9, which had no design of its own, so that row could not land until
someone designed it, and only a reviewer reading the whole chain found it
(items spec §7 item 15, {issue}`2955`).

This specification gives an ordering one form and one place, the Scope cell of the row,
so that row 8 of items spec §8 can check the order across every specification. It settles
the form now, while the orderings to move are few, since every specification written in
free prose would widen the move.

(order-spec-2)=
## 2. Decisions

1. **🤝 Agreed** (2026-11-17, {user}`bjlittle`, {pull}`2987`) — **An ordering is written in
   the Scope cell of its row.** It follows the scope, so a reader meets it beside the row it
   governs, and the table keeps its three columns, which six tools read by their header
   (§3.3). Chosen by {user}`bjlittle` over a column of its own, which would reshape every
   roadmap and every reader, and over a fixed sentence under the table (§5). See §4.1.
2. **🤝 Agreed** (2026-11-17, {user}`bjlittle`, {pull}`2987`) — **Each ordering opens with
   `· 🔗`.** The middle dot separates it from the scope, as it separates the parts of an
   item's provenance, and 🔗 lets the eye find it at the end of a long scope. A row with two
   orderings repeats both. See §4.1.
3. **🤝 Agreed** (2026-11-17, {user}`bjlittle`, {pull}`2987`) — **Four relations, and no
   others.** *after*, *before*, *with* and *with or after*, each followed by the row it
   names. *needs* and *is planned once … has landed* are *after*, since workflow rule 2.7
   already plans a row once the rows it depends on have merged. *waits on* a row summarises
   the orderings it stands for, and goes. What is not a row stays in the prose. See §4.2.
4. **🤝 Agreed** (2026-11-17, {user}`bjlittle`, {pull}`2987`) — **A bare row is the
   specification's own.** `row 1` names a row of the same roadmap, and a row of another
   specification is cited in full, as `row 2 of layers spec §9`. See §4.1.
5. **🤝 Agreed** (2026-11-17, {user}`bjlittle`, {pull}`2987`) — **An ordering is written
   once.** It goes on the row its reason belongs to: the row that waits, for *after*, *with*
   and *with or after*, and the earlier row for *before*. The check reads both directions
   into one graph, and the same ordering written on both rows is a fault, so two copies
   cannot drift apart. See §4.3.
6. **🤝 Agreed** (2026-11-17, {user}`bjlittle`, {pull}`2987`) — **A release is written in
   the cell too, and checked only for its form.** `· 🔗 before 0.6` fixes the form of a
   commitment to a release with the rest. Checking it against the released tags would need
   them in the suite, which reads text alone, and in CI's shallow clones. Chosen by
   {user}`bjlittle` over leaving releases in prose and over checking them against tags.
   See §4.4.
7. **🤝 Agreed** (2026-11-17, {user}`bjlittle`, {pull}`2987`) — **The check fails on an
   order that cannot hold.** A cycle, a word outside the four relations, an ordering written
   twice, a row naming one that does not exist, a `not started` row with or after a
   `candidate`, and a status that contradicts an ordering, as a row after row 3 landed while
   row 3 has not. See §4.5.
8. **🤝 Agreed** (2026-11-17, {user}`bjlittle`, {pull}`2987`) — **A row landing with
   another that still owes open items is reported, not failed.** The pull request landing
   both must answer the other row's items as well as its own, and the verification report it
   already gets lists them. Nothing is wrong until that pull request is opened. See §4.6.
9. **🤝 Agreed** (2026-11-17, {user}`bjlittle`, {pull}`2987`) — **_Landing with_ becomes
   `🔗 with`.** The one ordering items spec §3.4 already gives a form, and the seventh check
   of items spec §3.7 holds, become one relation of four, and that check becomes a case of
   the check of §4.5. See §4.7.
10. **🤝 Agreed** (2026-11-17, {user}`bjlittle`, {pull}`2987`) — **The developer guide
    teaches the form.** The specifications index shows how to write an ordering, the
    Repository Checks page names what the check refuses, and `docs/AGENTS.md` carries the
    rule, each in the pull request whose row they describe. Asked for by {user}`bjlittle`.
    See §4.8.
11. **🤝 Agreed** (2026-11-17, {user}`bjlittle`, {pull}`2987`) — **An ordering written in
    prose fails.** A form that only the cell is checked in would let a new specification
    write its orderings under the table again, where nothing reads them. The suite refuses an
    ordering word followed by a cited row outside the cell, as it refuses a citation written
    without its section sign. Chosen by {user}`bjlittle`, from the builder check of this
    specification. See §4.5.

(order-spec-3)=
## 3. What Exists Today

Measured on 2026-11-17 at `679cfd7d`.

(order-spec-3-1)=
### 3.1 The One Ordering With a Form

items spec §3.4 has a row that owes the work of another specification's row name it in its
scope, *landing with* it, as row 5 of heights spec §9 does with row 2 of layers spec §9.
`landing_together` in `tests/test_spec_conventions.py` reads the words *landing with* and
the citation after them, and fails when one of the two rows has landed without the other,
or in another pull request (items spec §7 item 14). It is the only ordering a check reads.

Three other Scope cells state an order in their own words: *once row 5 of globe spec §9
adds …* (row 3 of scene spec §9), *before row 5 of globe spec §9*
(row 4 of heights spec §9), and *once every class has landed*, which cites no row
(row 14 of crs spec §10).

(order-spec-3-2)=
### 3.2 The Prose Under the Roadmaps

Every other ordering is a sentence in the paragraph under a roadmap, mixed with the reasons
for it. A search for the phrases of §1 finds them under the roadmaps of eleven
specifications. Some of what it finds is no ordering: items spec §3.4 and §7 describe
orderings in general, and positions spec §8 times `geodesic.line` *before row 5*. Others
order a row against something that is not a row: a renderer in CI, the regions design, an
upstream release, an issue, as *after {issue}`2756`* under scene spec §9, or a release of
`geovista`. Two sentences order rows against 0.6: *Rows 1 and 2 land before 0.6 is
released* under scene spec §9, and *Row 3 of globe spec §9 lands with row 2, before 0.6 is
released* under heights spec §9. The plan of row 1 lists each sentence it moves.

(order-spec-3-3)=
### 3.3 The Readers of a Roadmap

A roadmap is read by its header, `| # | Scope | Status |`, in six places:
`geovista_citations.rows`, which the others share, the index's Status column in
`geovista_status`, the verification report, the renumber guard and its tests, and the
conventions test. A new column would change all six, and every roadmap of fifteen
specifications with them. An ordering in the Scope cell changes one: the renumber guard
takes a row's scope as its title and pairs the rows of two versions of a roadmap by how
alike their titles read, so many scopes gaining an ordering in one pull request could read
as rows reworded past recognition. Row 1 has it strip the orderings before pairing. The
other five read the scope as they do today.

(order-spec-4)=
## 4. Design

(order-spec-4-1)=
### 4.1 The Form of an Ordering

An ordering follows the scope of its row, opened by a middle dot, a space and 🔗:

```text
| 3 | The lift, on the globe and on a map · 🔗 after row 2 | 📋 not started |
| 5 | A surface below sea level …, in the subsurface tier · 🔗 after row 3 · 🔗 with row 2 of layers spec §9 | 📋 not started |
```

The first `· 🔗` ends the scope, and each after it opens one more ordering, so a scope that
is itself a list of commas reads as it did. A bare `row N` names a row of the same roadmap,
and a row of another specification is cited in full, in the grammar every citation uses,
so the build links it and the renumber guard follows it. A range is refused, as
`landing_together` refuses one today: each ordering names one row.

🔗 is U+1F517, which needs no variation selector. The grammar reads it with one as
without, as it reads the roadmap states (ledger spec §2 decision 16).

(order-spec-4-2)=
### 4.2 The Four Relations

| Relation | The row lands | Written today as |
|---|---|---|
| `after` | in a later pull request than the row it names | *after row N*, *needs row N*, *is planned once row N has landed*, *once row N lands*, and *Rows 1 to 4 come in order* |
| `before` | in an earlier pull request | *lands before row N* |
| `with` | in the same pull request | *landing with row N*, *lands with row N* |
| `with or after` | in the same pull request or a later one | *lands with or after row N* |

*waits on* a row goes, since each sentence that says it summarises orderings written out
beside it, as *Rows 3 to 5 each wait on a row of globe spec §9* does under heights spec §9.
What is not a row stays in the prose: a renderer in CI, an upstream release, and a
`candidate`'s trigger, which docs spec §2 decision 6 already governs.

(order-spec-4-3)=
### 4.3 Which Row Writes It

An ordering is written once, on the row its reason belongs to. That is the row that waits,
for `after`, `with` and `with or after`, and the earlier row for `before`, which is written
when the later row is another specification's and its reason is the earlier row's own, as
heights spec §9 writes row 4 *before row 5 of globe spec §9*, whose gallery migration it
must precede. The check reads each ordering in both directions, so `· 🔗 before row 5` on
row 4 and `· 🔗 after row 4` on row 5 are the same ordering, and writing both is a fault.

A `with` between rows of two specifications waits on both, so it is written on the row
whose work the other row does: row 5 of heights spec §9 writes
`· 🔗 with row 2 of layers spec §9`, which builds its tier, and row 8 of items spec §8
writes `· 🔗 with row 2 of order spec §9`, which builds its check.

(order-spec-4-4)=
### 4.4 An Ordering Against a Release

A row that must land before a release of `geovista` writes it as `· 🔗 before 0.6`, a
version of two or three numbers. Only `before` takes a release, as only *before 0.6 is
released* is written today. The check holds its form and nothing more: whether 0.6 has been
released is in the repository's tags, which the conventions test does not read, and which
CI's shallow clones do not fetch.

(order-spec-4-5)=
### 4.5 The Check

The conventions test reads every ordering of every roadmap into one graph of rows, and
fails on each of these, naming the row and the ordering:

1. **A word outside the four relations**, or `· 🔗` followed by something that is neither a
   relation and a row nor `before` and a version, or `before` a row of its own roadmap,
   which the later row writes as `after` (§4.3).
2. **A row that does not exist**, in its own roadmap or the one it cites.
3. **An ordering written twice**, on both rows or twice on one.
4. **An ordering written in prose.** Under a roadmap, or in a scope before its first
   `· 🔗`, an ordering word of §4.2's last column, *waits on*, *follows* or *builds on*,
   followed by a cited row, fails, naming the cell form it should take. A word followed by
   something that is not a row, such as a renderer, an issue or a release in words,
   passes, and code is skipped, so a specification can still quote the old forms. This
   stops a new specification writing its orderings where nothing reads them. The guard
   reads a paragraph whole, since prose wraps between the words and the row, and refuses
   a 🔗 left in a scope by an opener mistyped, which would hide its ordering.
5. **A cycle**, in one specification or across several: row 2 after row 1, and row 1 after
   row 2, or `with` and `before` between the same two rows.
6. **A `not started` row ordered `after`, `with` or `with or after` a `candidate`**, which
   can never land while the `candidate` waits on its trigger (items spec §7 item 15).
7. **A status that contradicts an ordering.** A row `after` another is `in progress` or
   `landed` only once the other has landed, on its date or before and in another pull
   request. A row `before` another has landed by the time the other lands, likewise. A row
   `with` another lands in the same pull request, and one `with or after` another in the
   same one or once the other has landed. Rows landed on the same day pass on their dates
   alone, since the order within a day is GitHub's to say.

Form, items 1 to 4, comes with row 1 of §9, and the graph, items 5 to 7, with row 2.

(order-spec-4-6)=
### 4.6 Rows Landing Together

A row `with` another lands in one pull request with it, and that pull request answers the
open items both rows owe (items spec §3.5). The verification report each pull request gets
(ledger spec §3.8, items spec §3.9) lists, for each row `in progress`, the rows that land
with it and the items each owes. `in progress` is how the report already knows a row is
being delivered, as it does for the row's own items, so it needs no pull request to read. The check does not fail on them: until that pull request is
opened, a row owing items is the ordinary state of the roadmap.

(order-spec-4-7)=
### 4.7 Moving Today's Orderings

Row 1 of §9 moves every ordering of §3 into the cell of its row, in the form of §4.1, and
leaves the reasons in the prose. *landing with* becomes `🔗 with`. *once every class has
landed* on row 14 of crs spec §10 becomes one `after` for each class's row.
Rows 1 and 2 of scene spec §9 and row 3 of globe spec §9 each gain `· 🔗 before 0.6`,
landed or not, so the commitment stays on record. An ordering against an issue stays in the prose. A plan is
frozen, so its orderings stay as they were written.

Row 1 moves the orderings as they are written, and its plan lists each sentence it moves
beside the cell it becomes, so that {user}`bjlittle` reviews the move with the plan before
any is made. A faithful move can still set an order nobody meant once item 7 of §4.5 holds
it, as *Rows 1 to 4 come first and in order* under crs spec §10 would hold its row 3 behind
row 5 of globe spec §9, through the rows that row 2 there stands for. Such a sentence is
rewritten to say what was meant before it moves.

Row 1 also teaches `landing_together` to read `· 🔗 with`, since it rewrites every *landing
with* it reads, and a check that finds nothing passes. Row 2 then folds it into
item 7 of §4.5, and the seventh check of items spec §3.7 names this specification as
where its rule now lives. Its tests keep their cases, written in the new form.

(order-spec-4-8)=
### 4.8 The Developer Guide

Each row teaches what it builds, in the pull request that lands it:

- **The specifications index** gains a section beside Statuses, Decisions and Verification
  and Open Items, showing a roadmap whose rows carry orderings, the four relations, which
  row writes one, and a release. Row 1 writes it, and row 2 adds what the check refuses and
  what the report shows.
- **The Repository Checks page** adds the orderings to the rule of the Specification
  Conventions check, and each fault of §4.5 to what it says when it fails.
- **`docs/AGENTS.md`** gains the rule in a line: an ordering is `· 🔗 <relation> <row>` in
  the Scope cell, written once.

No rule of how we work changes, since a check enforces this one, and workflow rule 2.7
already plans a row after the rows it depends on.

(order-spec-5)=
## 5. Alternatives Considered

- **A column of its own**, as `| # | Scope | Order | Status |`. The cleanest to read and to
  parse. Rejected by {user}`bjlittle` as too disruptive now: it reshapes every roadmap of
  fifteen specifications and changes the six readers of §3.3.
- **A fixed sentence under the table**, as *Row 3 lands after row 1.* The least disruption.
  Rejected because it leaves orderings among their reasons, which is what makes today's
  hard to read, for a person or a parser.
- **One emoji per relation**, such as 🔗 for `with` and an arrow for `after`. Rejected: the
  word already says the relation, and the arrows that read well carry a variation selector.
- **An ordering written on both rows.** Each row would show all its orderings. Rejected:
  two copies drift, and the check would have to hold them equal.
- **A release left in the prose, or checked against the tags.** The first leaves a
  commitment to a release in free text, which this design ends for rows. The second needs
  tags in a suite that reads text alone, and in CI's shallow clones. Rejected by
  {user}`bjlittle` for the form check of §4.4.

(order-spec-6)=
## 6. Testing

`tests/test_spec_conventions.py` holds §4.1 to §4.5, the grammar shared with the build in
`docs/src/_ext/geovista_citations.py`, as the rules of items spec §3.7 are. Each fault of
§4.5 has a fixture that shows it firing, and the repository test shows every roadmap
holding it. `tests/test_verification_report.py` holds §4.6.

(order-spec-7)=
## 7. Scope

In scope: the order between roadmap rows, in one specification or across several, and
against a release of `geovista`; the check of that order; the report of rows landing
together; and the developer guide's account of them.

Out of scope: a `candidate`'s trigger, which docs spec §2 decision 6 governs; an order
against anything that is not a row or a release, such as an upstream release or a
renderer; the order of a plan's tasks; and the plans, which are frozen.

(order-spec-8)=
## 8. Open Items

Each carries the grammar of items spec §3.2.

1. **❓ Open** (🔎 2026-11-17, {pull}`2990` · 🎯 row 2 of §9 · 🎫 {issue}`2991`) — **The
   prose guard's advice is wrong for a row ordered against something else.** It refuses
   *Once rows 1 and 2 have landed, the issue closes* as an ordering, and says to write it in
   the row's Scope cell, which cannot say when an issue closes. The message should name
   rewording as the other way out. The final review of row 1 found it.

(order-spec-9)=
## 9. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | The form: the grammar of §4.1 to §4.4 in `geovista_citations`, items 1 to 4 of §4.5, every ordering of today moved into its cell with `landing_together` reading `🔗 with` and the renumber guard pairing rows without their orderings (§3.3, §4.7), and the developer guide's account of the form (§4.8) | ✅ landed (2026-11-18, {pull}`2990`) |
| 2 | The graph: items 5 to 7 of §4.5, `landing_together` folded into them (§4.7), the report of §4.6, and their pages (§4.8) · 🔗 after row 1 | 🚧 in progress ({pull}`2994`) |

Statuses follow docs spec §3.6. Row 1 keeps every check reading what it moves, so it is
safe to land alone. Row 2 is the check that row 8 of items spec §8 owes for
items spec §7 item 15.

(order-spec-10)=
## 10. References

- items spec §3.4 and items spec §7 item 15, {issue}`2955`, which this specification
  designs.
- docs spec §2 decision 6, which governs a `candidate`'s trigger.
- ledger spec §2 decision 16, which reads a state with or without its variation selector.
- workflow rule 2.7, which plans a row once the rows it depends on have merged.

(order-spec-11)=
## 11. Verification

Each row follows ledger spec §3.4.

| Decision | Status | Evidence |
|---|---|---|
| §2 decision 1 | ✅ verified (2026-11-18, {pull}`2990`) | `tests/test_spec_conventions.py` |
| §2 decision 2 | ✅ verified (2026-11-18, {pull}`2990`) | `tests/test_spec_conventions.py` |
| §2 decision 3 | ✅ verified (2026-11-18, {pull}`2990`) | `tests/test_spec_conventions.py` |
| §2 decision 4 | ✅ verified (2026-11-18, {pull}`2990`) | `tests/test_spec_conventions.py` |
| §2 decision 5 | ✅ verified (2026-11-18, {pull}`2990`) | `tests/test_spec_conventions.py` |
| §2 decision 6 | ✅ verified (2026-11-18, {pull}`2990`) | `tests/test_spec_conventions.py` |
| §2 decision 7 | ⏳ pending | |
| §2 decision 8 | ⏳ pending | |
| §2 decision 9 | ⏳ pending | |
| §2 decision 10 | ⏳ pending | |
| §2 decision 11 | ✅ verified (2026-11-18, {pull}`2990`) | `tests/test_spec_conventions.py` |
