# geovista Citation Links — Design Specification

```{readingtime}
```

> **Living document.** This specification is maintained alongside the code, not archived
> behind it. It states how a citation of a specification section becomes a link, and how
> those links are kept pointing at the sections they mean while the specifications keep
> changing. Read it as current; the roadmap states what has actually landed.

- **Date:** 2026-10-26 (originated; maintained since)
- **Status:** living design specification
- **Citation prefix:** `citation spec §…`
- **Scope:** the shared citation grammar, the build-time transform that links citations,
  the check of the rendered output, the retirement of the hand-written section roles, and
  the guard that catches a renumbered section
- **Parent spec:** the published specifications design
  ([`2026-10-06-published-specs-design.md`](2026-10-06-published-specs-design.md)). This
  builds rows 2 and 4 of {ref}`docs spec §4 <docs-spec-4>`, closes row 3 as already
  covered, and retires the assertion of {ref}`docs spec §3.4 <docs-spec-3-4>`. It inherits
  that specification's citation form ({ref}`docs spec §3.2 <docs-spec-3-2>`), anchors
  ({ref}`docs spec §3.3 <docs-spec-3-3>`) and statuses
  ({ref}`docs spec §3.6 <docs-spec-3-6>`) unchanged

(citation-spec-1)=
## 1. Purpose

The specifications are living documents, and they are growing. Six are published, and the
globe-first CRS work has two of them and more to come. Each is cited by section: 215 times
from inside the specifications, with hand-written `{ref}` roles, and 68 times from
everywhere else. That second count is the trigger of rows 2 to 4 of
{ref}`docs spec §4 <docs-spec-4>`, which activate past seventy, and the next change to cite
a specification from code will pass it.

The links that matter are the ones a reader follows on the documentation site. Today those
are the 215 roles in the specifications and 7 more on the developer pages. Each is a link,
and `tests/test_spec_conventions.py` checks that each one resolves and displays the number
it targets. Nothing checks that it still names the section its author meant. Insert a new
section 3.3 into a specification and its old 3.3 becomes 3.4, and every citation of 3.4
written before the insertion now opens a different section, and resolves, and passes.
{ref}`docs spec §3.5 <docs-spec-3-5>` says as much: its checks are syntactic, and a
well-formed citation of the wrong section is indistinguishable from a right one.

The rest are plain text, and render as plain text. None is in an API docstring yet, but the
globe work will put `crs spec §N` into the docstrings of the functions it specifies, and a
reader of the API documentation will find a citation they cannot follow.

This specification makes every citation a link, from one string, and adds the check that
the links still mean what they meant.

(citation-spec-2)=
## 2. Decisions

All taken by {user}`bjlittle` on 2026-10-26, after the sweep of the published
specifications design on that date.

- **Build the machinery instead of raising the ceiling again.** The ceiling was doubled
  once, from thirty-five to seventy ({ref}`docs spec §8 <docs-spec-8>`). It is not raised a
  second time.
- **A reader following a link is the case that matters.** A link on a rendered page that
  opens the wrong section is the visible failure. A citation in a code comment is rarely
  followed; one in a docstring is, through the API documentation.
- **Renumbering stays allowed.** A new section can go where it belongs in the argument,
  between two others, and the sections after it take new numbers. Forbidding that, so that
  sections are only ever added at the end or subdivided, would protect the citations at the
  cost of the documents. Instead, a renumber must update every citation of the sections it
  moves, in the same pull request, and the guard of {ref}`§4.5 <citation-spec-4-5>` says
  which. A citation added on a branch older than a renumber is caught on its own pull
  request, before it merges.
- **Released changelog entries are corrected like everything else.** A link to the wrong
  section has no value, released or not, so the guard reads `CHANGELOG.rst` and changelog
  fragments, and its fix rewrites them.
- **The roles collapse into plain text as part of this work.** Keeping two forms of
  citation, and the assertion that holds the two halves of a role together, was the
  stop-gap {ref}`docs spec §3.4 <docs-spec-3-4>` described until the transform existed.
- **Sections only.** An item within a section, such as `typing spec §8 item 9`, and a row
  of a roadmap, such as "rows 2 to 4" of the docs spec's, are not given anchors or links of
  their own. Six references are written in a form a grammar could read, the link to the
  containing section lands within a screen of them, and a grammar for them would cost more
  to keep than it saves. {ref}`§4.6 <citation-spec-4-6>` protects them another way, and
  row 5 of {ref}`§9 <citation-spec-9>` is where the question comes back.

(citation-spec-3)=
## 3. What Exists Today

(citation-spec-3-1)=
### 3.1 Where the Citations Are

Measured on `main` at `7f11f403`, with the parser of `tests/test_spec_conventions.py`:

| where | role | plain | rendered |
|---|---:|---:|---|
| the six specifications | 215 | 4 | yes, as links (roles) or as text (plain) |
| developer pages, `checks.rst` and `specs/index.rst` | 7 | 1 | yes |
| test docstrings and strings in tests and scripts | 0 | 31 | no |
| comments in `src/` | 0 | 11 | no |
| comments in tests, scripts and `conf.py` | 0 | 9 | no |
| `pyproject.toml`, the `pre-commit` configuration, a workflow, `AGENTS.md` | 0 | 10 | no |
| docstrings in `src/`, which the API documentation renders | 0 | 0 | yes |
| changelog fragments and `CHANGELOG.rst` | 0 | 0 | yes |

About twenty-five references name an item or a roadmap row by its number, which
{ref}`§2 <citation-spec-2>` leaves without links of their own. Six are written as a
citation: four comments cite an item of `typing spec §8`, and `checks.rst` cites rows of the
roadmaps of two specifications. The rest name the number alone and leave the section to the
sentence around them: ten test docstrings name the assertions of
{ref}`docs spec §3.5 <docs-spec-3-5>` as "(item 1)" to "(item 7)", tests and changelog
fragments speak of "row 4" or "typing change 3", and a changelog fragment of "row 1 of the
roadmap". No grammar could read those, so only a number that never changes keeps them
true.

(citation-spec-3-2)=
### 3.2 What the Checks Catch

`tests/test_spec_conventions.py` holds the conventions of
{ref}`docs spec §3.5 <docs-spec-3-5>`. Every heading pairs with an anchor keyed to its
number, every citation resolves, carries its section sign and does not wrap, and every
role displays the section it targets. It reads the whole repository less the frozen plans,
and it never skips.

Every check reads a single tree. A renumber produces a tree in which every citation is well
formed and every anchor exists, so it passes, and the only evidence that anything moved is
in the difference between that tree and the one before it.

The audit behind this specification compared each of the 234 section citations then in the
repository with the specification as it stood in the commit that last wrote the citing
line. All 234 still name the section they were written against: two sections have been
renamed and none has moved. So nothing is stale yet, and nothing would say so if it were.

(citation-spec-3-3)=
### 3.3 Prior Art in tephpy

[`bjlittle/tephpy`](https://github.com/bjlittle/tephpy) built this first, and geovista's
conventions are a port of it. At `29896cf`:

| piece | lines |
|---|---:|
| `docs/src/_ext/tephpy_citations.py`, the shared grammar | 537 |
| `docs/src/_ext/tephpy_citation_xrefs.py`, the transform | 428 |
| `.github/scripts/check_citations.py`, the integrity hook | 478 |
| `.github/scripts/check_rendered_citations.py`, the rendered-output gate | 310 |

The transform runs on the doctree, after parsing, so a citation links the same way from a
docstring, a page in reStructuredText and a specification in MyST, and no source is edited.
Its registry of anchors is built on `builder-inited`, before Sphinx forks its parallel
readers, and a fingerprint of it marks every document outdated when an anchor changes. The
output gate reads the built HTML with a pattern deliberately looser than the grammar, so
that it cannot go blind at the same moment the grammar does.

tephpy has no answer to renumbering either. Its integrity hook (tephpy#86) asserts what
geovista's test already asserts, that each citation resolves and each anchor is keyed. Its
practice is to subdivide a section instead of renumbering it (tephpy#295), and the question
of what a released changelog entry should do when its section changes is still open
(tephpy#324). The guard of {ref}`§4.5 <citation-spec-4-5>` is new.

(citation-spec-4)=
## 4. Design

(citation-spec-4-1)=
### 4.1 One Grammar

What a citation is, and which anchor it names, is defined once. The grammar now in
`tests/test_spec_conventions.py`, from reading the lines of a file to resolving a run of
citations against the namespace, moves to `docs/src/_ext/geovista_citations.py`. The
conventions test, the transform and the guard all import it.

Three readers with one grammar cannot disagree about what a citation is. Two copies would
drift apart, and each direction of the drift is silent: a citation the test reads and the
transform does not renders as dead text, and one the transform links and the test does not
read is never checked.

`docs/src/_ext` is not an importable package. The build finds the module on `sys.path`, and
the tests and scripts load it by path, registering it in `sys.modules` before executing it,
as the tests of the other local extensions already do. The `geovista_` prefix claims a
top-level name, since the directory sits on `sys.path` for the whole build.

(citation-spec-4-2)=
### 4.2 The Transform

A Sphinx transform, `docs/src/_ext/geovista_citation_xrefs.py`, finds every citation in the
doctree's text and replaces it with a cross-reference to its anchor, displaying the
citation exactly as written. A bare `§N` inside a specification resolves to that
specification, as {ref}`docs spec §3.2 <docs-spec-3-2>` rules, and a run such as
`typing spec §3.2, §4` becomes two links.

It runs on everything the build renders: the specifications, the developer pages, the
changelog and the API documentation that `sphinx-autoapi` generates from docstrings. It
leaves alone text inside literals, code blocks, comments, raw blocks, signatures and
existing links, since a citation in a link would nest one anchor inside another.

It is a port of tephpy's, keeping three of its properties, which geovista's build needs as
much:

- **Parallel safe.** Read the Docs builds with `--jobs`, and the registry of anchors is
  built on `builder-inited`, before the readers fork. The extension declares itself safe to
  read and write in parallel, and `tests/docs/test_ext_parallel.py` holds it to that.
- **Incremental.** A fingerprint of the registry is kept in the environment, and when it
  changes, every document is read again, so an incremental build never links to an anchor
  that has gone.
- **Loud.** A citation naming an anchor that does not exist is a warning, which fails the
  build. The conventions test catches it first, but a build is the last place it can be
  caught.

(citation-spec-4-3)=
### 4.3 The Output Check

A transform that silently stops running leaves every citation as plain text, and the
conventions test, reading the source, cannot see it. So the built HTML is read too.

`tests/docs/test_rendered_citations.py` reads every page of a built site and asserts that
each citation on it is inside a link to an anchor that exists. Like tephpy's gate, it finds
citations with a pattern looser than the grammar and shares no code with it. It also fails
on one anchor nested inside another, which tephpy found Docutils' `contents` transform
produces from a citation in a heading (tephpy#96).

It joins `tests/docs`, so it runs in the job that builds the full gallery and runs that
suite under `--browser-strict`, where a missing build fails instead of skipping. Locally,
`pixi run -e geovista tests-docs-browser` builds and runs it. `OUTPUT_GATE` in the
conventions test, which pairs the transform with its output check (row 4 of
{ref}`docs spec §4 <docs-spec-4>`), changes to name this module.

(citation-spec-4-4)=
### 4.4 Collapsing the Roles

Once the transform links plain text, a script rewrites every section role as the plain
citation it displays: `` {ref}`§4 <docs-spec-4>` `` becomes `§4` in the docs spec, and
`` {ref}`typing spec §3.2 <typing-spec-3-2>` `` becomes `typing spec §3.2` anywhere. The 215
roles in the specifications and the 7 on the developer pages all go. A role whose display
text and target disagree cannot be rewritten without choosing between them, and there are
none today, since the assertion forbids it.

The rewrite is proven by the build: the set of citation links on every page, as page and
target, is the same before and after.

Then the assertion that held a role's two halves together retires, with the form it
policed. {ref}`docs spec §3.4 <docs-spec-3-4>` is rewritten to describe the transform, and
the fifth assertion of {ref}`docs spec §3.5 <docs-spec-3-5>` is marked retired in place,
not deleted, so the assertions after it keep their numbers.

(citation-spec-4-5)=
### 4.5 The Renumber Guard

On a pull request, the guard compares each specification the pull request changes with the
same specification on its base branch, and pairs every section on the base branch with its
counterpart in the pull request. It pairs by title first, compared case and punctuation
aside, so that the title style sweep of {pull}`2712` would have paired every section with
itself. The sections left unpaired on each side are then paired by the similarity of their
text, which finds a section that was renamed. Each section on the base branch is then one
of these:

- **Kept.** Paired with the section under the same anchor, whatever its title now. A rename
  is kept: every citation still names the same section.
- **Moved.** Paired with a section under a different anchor. Inserting a section before it,
  deleting one before it, or reordering does this, and a section can be moved and renamed
  in the same pull request.
- **Removed.** Paired with nothing. Its anchor may have gone, or may now hold another
  section, which is the case resolution cannot see.

A section rewritten so thoroughly that its text no longer resembles itself, and renamed
too, reads as removed, so the guard errs towards asking for its citations to be checked by
hand.

For each section moved or removed, the guard reads every citation of its old anchor in the
repository, using the grammar of {ref}`§4.1 <citation-spec-4-1>`, across the same corpus
as the conventions test: code, tests, configuration, documentation, changelog fragments,
`CHANGELOG.rst` and the specifications themselves, less the frozen plans. A citing line that
the pull request did not change was written against the old layout, and the guard fails on
it, naming the line, the citation and what became of the section:

```text
src/geovista/crs.py:42: crs spec §3.3 was "Domains", which is now §3.4
src/geovista/crs.py:57: crs spec §3.5 was "Seams", which was removed; §3.5 is now "Caps"
```

A citing line the pull request did change is its author's to have checked, and passes.

The same knowledge makes the fix. With `--fix`, the guard rewrites each citation of a moved
section to its new number, and the author reviews the diff. This is what corrects a
released changelog entry. A citation of a removed section has no new number to take, so
the fix leaves it for the author, who points it elsewhere or deletes it.

One case escapes that comparison. A pull request branched before a renumber merged can
add a citation meaning the old number. It changes no specification, and its own diff
shows nothing moving. So the guard also follows every line the pull request changed from
the commit on its branch that wrote the line to the merge of the branch into the base:
it pairs the cited specification change by change, as above, and reports a citation whose
section has since moved or been removed. That is the audit of
{ref}`§3.2 <citation-spec-3-2>`, run on the lines a pull request adds. It follows the
specification one change at a time because comparing the two ends loses a section renamed
in one change and grown in others, which is how a living section changes. A protected
branch that must be up to date before merging re-runs the guard whenever the base moves,
so such a citation cannot merge stale.

It has to happen on the pull request. The repository squash-merges, so once merged, a
line's commit on the base branch is the squash, whose tree already holds every renumber
that preceded it, and the history that would show the citation stale is gone. The same
audit still runs over the whole repository each night, as a backstop for a commit that
reached the base branch by another route, and opens an issue as the nightly check of
statuses does ({ref}`docs spec §3.6 <docs-spec-3-6>`), naming the `--fix` that corrects
it. A line older than the guard is followed from the commit at which every citation was
audited by hand, when the guard was written, so the audit only judges history the guard
was there to see.

The guard runs in `ci-citations.yml` on every pull request, since any can add a
citation, and each night, and locally with a pixi task against `origin/main`.
It cannot be a unit test, since it needs history. It is a repository check of its own,
declaring `CHECK`, with a row and a section on the repository checks page
({ref}`checks spec §3.2 <checks-spec-3-2>`).

(citation-spec-4-6)=
### 4.6 Items and Rows

Items and rows are referred to by number, and only six of the references are in a form the
grammar could read ({ref}`§3.1 <citation-spec-3-1>`), so the guard protects them by
refusing to renumber them. Two kinds are frozen:

- **Every numbered item that opens with a bold title**, in any specification. That takes in
  the open items of each specification, whose title is the bold run after the status, and
  lists such as the assertions of {ref}`docs spec §3.5 <docs-spec-3-5>`, which the tests
  name by number. A title that wraps is read whole. A numbered list without bold titles,
  such as the steps of a procedure, is not frozen.
- **Every row of a roadmap table**, the table whose header is `#`, `Scope` and `Status`,
  matched by its scope.

They are only ever appended. An item that stops applying is marked so in place, as
{ref}`§4.4 <citation-spec-4-4>` retires an assertion, and a row that splits takes letter
suffixes in place, as row 6 of the type coverage roadmap became 6a to 6c. The guard pairs
items and rows the way it pairs sections, and then pairs any left over by number, since an
item resolved or a row rescoped is rewritten in place, under its number. It fails on any
that has moved, or whose number is gone or now names another.

A changelog fragment that names a roadmap row cites the row's pull request with a `:pull:`
role, which is already the evidence the row carries ({ref}`docs spec §3.6 <docs-spec-3-6>`).
The changelog guidelines say so.

(citation-spec-4-7)=
### 4.7 What Changes in the Parent

- Rows 2 and 4 of {ref}`docs spec §4 <docs-spec-4>` land with the rows of
  {ref}`§9 <citation-spec-9>` that build them.
- Row 3, the integrity hook, is marked landed with row 1 there:
  `tests/test_spec_conventions.py` has asserted what tephpy's hook asserts since
  {pull}`2573`, and a second copy would be the drift {ref}`§4.1 <citation-spec-4-1>` exists
  to prevent.
- The ceiling test of rows 2 to 4 retires with row 2 of {ref}`§9 <citation-spec-9>`, and
  item 2 of {ref}`docs spec §8 <docs-spec-8>`, on the ceiling's value, is resolved by it.
- Item 1 of {ref}`docs spec §8 <docs-spec-8>`, on the display form the assertion assumes,
  is resolved by the collapse.
- `specs/index.rst` tells a reader that citations are links.

(citation-spec-5)=
## 5. Alternatives Considered

- **Raise the ceiling again.** Cheap, and it defers the cost, but the citations the globe
  work will put in docstrings would render as dead text, and nothing would catch a
  renumber. Rejected by {user}`bjlittle`.
- **Forbid renumbering.** Sections only appended or subdivided, as tephpy does in practice.
  It needs no guard, but a section that belongs between two others would go where it does
  not belong, and the documents would read worse to protect their references. Rejected by
  {user}`bjlittle`, in favour of a guard that makes a renumber update its citations.
- **Leave released changelog entries alone.** They would keep linking to whatever the old
  number now names. Rejected: a stale link is worth nothing.
- **Keep the roles and link only the plain text.** Smaller, but it leaves two forms of
  citation, the assertion between a role's halves, and a hand-written link that can say
  one section and open another.
- **Anchors and links for items and rows.** About 600 to 700 more lines than sections
  alone, and a grammar for row names, which are written as "change 3", "row 2", "6a" and
  "rows 2 to 4", that every new phrasing would either fail silently or need a change to.
  Six citations today. Deferred to row 5 of {ref}`§9 <citation-spec-9>`.
- **A unit test for the guard instead of a CI job.** A test reads one tree, and a renumber
  is only visible between two.
- **A nightly audit alone, instead of a check on every pull request.** It needs no job on
  every pull request, and {user}`bjlittle` first chose it. The final review of the guard
  found it blind under squash merging, as above, and on 2026-10-27 {user}`bjlittle` chose
  the check on every pull request, with the nightly audit kept as a backstop.

(citation-spec-6)=
## 6. Testing

- The grammar's tests move with it, and the conventions test runs unchanged against the
  repository, proving the move changed nothing.
- The transform is tested in a small Sphinx project the tests build, with two
  specifications and a page, for a citation in each kind of text it reads, each kind it
  skips, a run, a bare `§N` inside and outside a specification, and an anchor that does not
  exist. Only the first Sphinx application in a process builds cleanly
  (`tests/AGENTS.md`), which the project's setup accounts for.
- The output check is tested against small HTML pages: a linked citation passes, a bare
  one, a link to a missing anchor and a nested anchor each fail, and a page with no
  citations is not a vacuous pass for the site.
- The guard is tested against small git repositories the tests build: a move with an
  untouched citation fails and a touched one passes; a rename passes; a section deleted
  from the middle fails on the untouched citations of it and moves the ones after it; a
  section inserted while another is renamed pairs each correctly; a section rewritten past
  recognition reads as removed; a moved item or row fails and a split row passes; and
  `--fix` rewrites the untouched citations of moved sections, `CHANGELOG.rst` among them,
  and nothing else. A citation added on a branch that predates a renumber is tested as CI
  sees it, on the merge of the branch into a base renumbered since, and `--fix` gives it
  its section's new number. The nightly audit is tested on the same history merged.
- The collapse is tested by the before and after comparison of
  {ref}`§4.4 <citation-spec-4-4>`, run once, and recorded in its pull request.

(citation-spec-7)=
## 7. Scope

In scope are the shared grammar, the transform, the output check, the collapse of the
section roles, the renumber guard and its fix, the rules for items and rows, the edits to
the parent of {ref}`§4.7 <citation-spec-4-7>`, and the changelog guidelines. Out of scope
are citations of items and rows as links in their own right (row 5 of
{ref}`§9 <citation-spec-9>`), and row 5 of {ref}`docs spec §4 <docs-spec-4>`, GitHub
reference roles, which is unchanged.

(citation-spec-8)=
## 8. Open Items

Each carries the status grammar of {ref}`docs spec §3.6 <docs-spec-3-6>`. None is open
today.

(citation-spec-9)=
## 9. Roadmap

| # | Scope | Status |
|---|---|---|
| 1 | One grammar: `docs/src/_ext/geovista_citations.py`, imported by the conventions test | ✅ landed (2026-10-26, {pull}`2735`) |
| 2 | The transform and the output check, which land together; the ceiling test retires | ✅ landed (2026-10-27, {pull}`2738`) |
| 3 | The renumber guard, its fix, its nightly audit, and the rules for items and rows | not started ({issue}`2566`) |
| 4 | Collapsing the roles; the agreement assertion retires; the changelog guidelines | not started ({issue}`2566`) |
| 5 | Items and rows as citations in their own right | candidate: more than twenty citations of items and rows outside the specifications |

Statuses follow {ref}`docs spec §3.6 <docs-spec-3-6>`, and {issue}`2566` tracks rows 1 to
4. Rows 2 to 4 each build on row 1. Row 2 follows it, because the next change to cite a
specification from code fails the ceiling test until row 2 lands. Row 3 needs only row 1, so
it can come before or after row 2. Row 4 needs row 2.

Row 5's trigger is asserted by the conventions test from row 1 on. It counts, outside the
specifications, the citations followed by `item N` or `items N`, and those preceded by
`row N of` or `rows N to M of`, reading across line breaks. It fails past twenty, a little
over three times the six of {ref}`§3.1 <citation-spec-3-1>`.

(citation-spec-10)=
## 10. References

- {issue}`2566`, the tracking issue of rows 2 to 5 of {ref}`docs spec §4 <docs-spec-4>`.
- [`bjlittle/tephpy`](https://github.com/bjlittle/tephpy), the prior art of
  {ref}`§3.3 <citation-spec-3-3>`, and its issues
  [#86](https://github.com/bjlittle/tephpy/issues/86) (the integrity hook),
  [#96](https://github.com/bjlittle/tephpy/issues/96) (a citation in a heading),
  [#295](https://github.com/bjlittle/tephpy/issues/295) (subdividing instead of
  renumbering) and [#324](https://github.com/bjlittle/tephpy/issues/324) (released
  changelog citations).
- {pull}`2573`, which landed the conventions test, and {pull}`2730` and {pull}`2731`, which
  made the checks page and the specifications index the inventories their specifications
  had been keeping by hand.
