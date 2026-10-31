# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Render design specification citations as cross-references.

The transform runs on the doctree, after parsing, so it never sees a source
format, only nodes. A citation therefore links the same way from a docstring, a
page in reStructuredText and a specification in MyST, and no source is edited to
make it so: ``typing spec §3.2`` in a docstring stays the characters it was
written as (citation spec §4.2).

What a citation is, and which anchor it names, is not decided here. That is the
grammar of ``geovista_citations``, which the conventions test reads with too.

It is a port of ``tephpy``'s ``tephpy_citation_xrefs``. The ``geovista_`` prefix
claims a top-level name, since ``docs/src/_ext`` is on ``sys.path`` for the whole
build.

"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

from docutils import nodes
import geovista_citations
from sphinx import addnodes
from sphinx.ext.autosummary import autosummary_table
from sphinx.transforms import SphinxTransform
from sphinx.util import logging

if TYPE_CHECKING:
    import re

    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

logger = logging.getLogger(__name__)

#: Text inside any of these stays plain. ``reference`` and ``pending_xref`` are on
#: the list because a citation in link text would otherwise nest one anchor inside
#: another, which is invalid HTML.
SKIP = (
    nodes.literal,
    nodes.literal_block,
    # a ">>>" example, which subclasses neither of the above
    nodes.doctest_block,
    nodes.comment,
    nodes.raw,
    nodes.reference,
    addnodes.desc_signature,
    addnodes.pending_xref,
)

#: The members of :data:`SKIP` that keep a citation plain because it is already a
#: link. In a section heading such a citation loses its link exactly where the
#: transform's would, so it is reported, and still left alone.
LINKS = (nodes.reference, addnodes.pending_xref)

#: The specifications, relative to the documentation source.
SPECS = Path("developer") / "specs"

#: Derived once per build from the anchors on disk, and read by every transform.
#: Populated on ``builder-inited``, which runs before Sphinx forks its parallel
#: readers, so each inherits them.
PATTERN: re.Pattern[str] | None = None
OWNERS: dict[str, str] = {}

#: A digest of the registry above, compared in :func:`_outdated` with the one the
#: environment carries from the previous build.
FINGERPRINT = ""

#: Where that digest is kept between builds. The environment is pickled, so the
#: attribute survives to the next build of the same tree.
ENV_FINGERPRINT = "geovista_citation_registry"


class CitationTransform(SphinxTransform):
    """Replace each citation in ordinary prose with a reference to its anchor."""

    default_priority = 400

    def apply(self, **kwargs: object) -> None:  # noqa: ARG002
        """Rewrite every eligible text node in the document."""
        # what a page links depends on this code and the grammar's, neither a
        # source sphinx watches, so an edit to either must re-read every page
        self.env.note_dependency(__file__)
        self.env.note_dependency(geovista_citations.__file__)
        if PATTERN is None:
            return
        owner = OWNERS.get(self.env.docname)
        for text in list(self.document.findall(nodes.Text)):
            blocker = _blocker(text)
            if blocker is not None and not isinstance(blocker, LINKS):
                continue
            replacement = _convert(str(text), owner, self.env.docname)
            if replacement is None:
                continue
            heading = _heading(text)
            if heading is not None:
                logger.warning(
                    "citation in the section heading %r does not reach the reader "
                    "as a link to the section it names: the theme rebuilds the "
                    "page navigation from the headings, keeping the citation's "
                    "text and dropping its anchor. Cite the specification in the "
                    "prose below the heading instead (citation spec §4.2)",
                    heading.astext(),
                    location=text,
                    type="geovista",
                    subtype="citation",
                )
            if blocker is None:
                text.parent.replace(text, replacement)


class DecisionTargets(SphinxTransform):
    """Give each decision of a specification its anchor (ledger spec §3.1).

    No source declares a decision's anchor; the build names each numbered item of
    a specification's Decisions after its number. It runs after docutils moves
    the ``(…-2)=`` target onto its section, at priority 260, so the section can be
    found by its id, and before :class:`CitationTransform` links to the anchors.
    The standard domain records each as an anonymous label, which the explicit
    title of a citation's reference resolves.
    """

    default_priority = 300

    def apply(self, **kwargs: object) -> None:  # noqa: ARG002
        """Name the items of the document's Decisions, if it is a specification."""
        self.env.note_dependency(__file__)
        self.env.note_dependency(geovista_citations.__file__)
        owner = OWNERS.get(self.env.docname)
        if owner is None:
            return
        for section in self.document.findall(nodes.section):
            if f"{owner}-2" not in section["ids"]:
                continue
            listing = next(
                (c for c in section.children if isinstance(c, nodes.enumerated_list)),
                None,
            )
            if listing is None:
                return
            start = listing.get("start", 1)
            for offset, item in enumerate(listing.children):
                name = geovista_citations.decision_anchor(owner, start + offset)
                item["names"].append(name)
                self.document.note_explicit_target(item, item)
            return


def _heading(node: nodes.Node) -> nodes.title | None:
    """Return the section heading ``node`` sits in, or ``None``.

    Only a section heading, a ``title`` directly under a ``section``, is copied
    into the page navigation. The caption of a table, a topic or an admonition is
    not, so a citation in one is a link like any other.

    Parameters
    ----------
    node : docutils.nodes.Node
        The text node under consideration.

    Returns
    -------
    docutils.nodes.title or None
        The heading, whose text names the offender in the warning, since MyST gives
        a section title no usable line number.

    """
    parent = node.parent
    while parent is not None:
        if isinstance(parent, nodes.title) and isinstance(parent.parent, nodes.section):
            return parent
        parent = parent.parent
    return None


def _blocker(node: nodes.Node) -> nodes.Node | None:
    """Return the innermost ancestor that keeps ``node`` plain, or ``None``.

    Parameters
    ----------
    node : docutils.nodes.Node
        The text node under consideration.

    Returns
    -------
    docutils.nodes.Node or None
        The innermost enclosing member of :data:`SKIP`, or ``None`` for ordinary
        prose. ``autosummary_table`` subclasses ``comment`` but is a rendered
        table, and an API summary sits inside one, so it is never a blocker.

    """
    parent = node.parent
    while parent is not None:
        if not isinstance(parent, autosummary_table) and isinstance(parent, SKIP):
            return parent
        parent = parent.parent
    return None


def _convert(source: str, owner: str | None, docname: str) -> list[nodes.Node] | None:
    """Split ``source`` into runs of text and the references between them.

    Parameters
    ----------
    source : str
        The text node's contents.
    owner : str or None
        The citation prefix of the document, or ``None`` if it owns no sections.
    docname : str
        The document being read, recorded on each reference for its warnings.

    Returns
    -------
    list of docutils.nodes.Node or None
        The replacement nodes, or ``None`` when nothing here is a citation.

    """
    out: list[nodes.Node] = []
    cursor = 0
    for citation in geovista_citations.scan(source, PATTERN, owner):
        if citation.slug is None:
            # a bare section number with nothing to be relative to, which the
            # conventions test reports; here it is left as written
            continue
        out.append(nodes.Text(source[cursor : citation.start]))
        out.append(_xref(docname, citation.slug, citation.text))
        cursor = citation.end
    if not out:
        return None
    out.append(nodes.Text(source[cursor:]))
    return out


def _xref(docname: str, slug: str, shown: str) -> addnodes.pending_xref:
    """Build a ``std:ref`` cross-reference to ``slug``, displaying ``shown``.

    ``refwarn`` is set, so that a citation which stops resolving fails a build run
    with ``--fail-on-warning``, even where the conventions test was not run.

    Parameters
    ----------
    docname : str
        The referring document.
    slug : str
        The anchor, e.g. ``typing-spec-3-2``.
    shown : str
        The citation as written, which is what the link displays.

    Returns
    -------
    sphinx.addnodes.pending_xref
        Resolved later by the standard domain.

    """
    inner = nodes.inline(shown, shown, classes=["std", "std-ref"])
    return addnodes.pending_xref(
        "",
        inner,
        refdoc=docname,
        refdomain="std",
        reftype="ref",
        reftarget=slug,
        refexplicit=True,
        refwarn=True,
    )


def _build_registry(app: Sphinx) -> None:
    """Derive the citation pattern and the owners from the anchors on disk.

    The prefixes are declared nowhere: adding a specification adds its prefix.
    Finding no anchors leaves ``PATTERN`` as ``None``, which makes the transform a
    no-op, since every reference it could emit would be one nothing resolves.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The application, read for its source directory.

    """
    global FINGERPRINT, PATTERN  # noqa: PLW0603
    root = Path(app.srcdir)
    names = geovista_citations.namespace(
        geovista_citations.specifications(root / SPECS)
    )
    PATTERN = names.signed if names.anchors else None
    OWNERS.clear()
    OWNERS.update(
        {
            path.relative_to(root).with_suffix("").as_posix(): prefix
            for path, prefix in names.owners.items()
        }
    )
    FINGERPRINT = _fingerprint(names.anchors, OWNERS)


def _fingerprint(anchors: frozenset[str], owners: dict[str, str]) -> str:
    """Digest what the transform reads, so a build can tell it has changed.

    Parameters
    ----------
    anchors : frozenset of str
        The anchors, from which the pattern is built.
    owners : dict
        The owning prefix keyed by docname, which a bare section number resolves
        against.

    Returns
    -------
    str
        A digest that changes when, and only when, one of those two does.

    """
    material = "\n".join(
        (
            *sorted(anchors),
            "--",
            *(f"{docname} {prefix}" for docname, prefix in sorted(owners.items())),
        )
    )
    return sha256(material.encode("utf-8")).hexdigest()


def _outdated(
    _app: Sphinx,
    env: BuildEnvironment,
    added: set[str],
    changed: set[str],
    _removed: set[str],
) -> set[str]:
    """Re-read every document when the registry differs from the last build's.

    The transform's answers are baked into each pickled doctree, and the registry
    is a dependency of none of them, so renumbering a section would otherwise
    leave every unedited page linking to what the old registry named.

    Parameters
    ----------
    _app : sphinx.application.Sphinx
        The application. Unread.
    env : sphinx.environment.BuildEnvironment
        The environment, which carries the previous build's digest.
    added : set of str
        Documents new since the last build.
    changed : set of str
        Documents Sphinx has already found out of date.
    _removed : set of str
        Documents gone since the last build. Unread.

    Returns
    -------
    set of str
        The documents to re-read on top of those Sphinx found itself.

    """
    if getattr(env, ENV_FINGERPRINT, None) == FINGERPRINT:
        return set()
    setattr(env, ENV_FINGERPRINT, FINGERPRINT)
    # on a first build every document is already added, so this is empty
    return set(env.found_docs) - added - changed


def setup(app: Sphinx) -> dict[str, object]:
    """Register the transform and the two handlers that keep its registry honest.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The application.

    Returns
    -------
    dict
        The extension metadata. ``env_version`` is declared because the extension
        stores its digest in the environment.

    """
    app.connect("builder-inited", _build_registry)
    app.connect("env-get-outdated", _outdated)
    app.add_transform(DecisionTargets)
    app.add_transform(CitationTransform)
    return {
        "version": "0.1.0",
        "env_version": 2,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
