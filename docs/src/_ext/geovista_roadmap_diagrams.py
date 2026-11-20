# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Draw the order between roadmap rows, under each roadmap and as the open work.

The conventions test reads every ordering of every roadmap into one graph
(order spec §4.5), and the grammar of ``geovista_citations`` reads it, chooses the
rows a diagram draws and writes the diagram's Mermaid text
(diagram spec §4.1 to diagram spec §4.4). This extension draws those diagrams in
the build, so nobody writes or keeps one up to date:

- under each specification's roadmap table, its rows and the rows of others it
  orders against, with the key beneath (diagram spec §4.4), placed by a transform,
  so no specification writes anything for it;
- in the specifications index, where ``.. roadmap-open-work::`` stands, the open
  work of every roadmap (diagram spec §4.5).

Each row links to its row in its roadmap table (diagram spec §4.6), whose anchor
``geovista_citation_xrefs`` names. A row's colour and whether it is ready read
every roadmap, so every page drawing a diagram depends on every specification.
One added or removed changes the anchors, on which that extension reads every
page again.

"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from docutils import nodes
import geovista_citation_xrefs
import geovista_citations
from sphinx.errors import NoUri
from sphinx.transforms import SphinxTransform
from sphinx.util.docutils import SphinxDirective
from sphinxcontrib.mermaid import mermaid

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Sequence

    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

#: The graph of every roadmap, read once a build starts (:func:`_read_graph`):
#: its edges, statuses and labels, each specification's docname by its prefix and
#: prefix by its docname, and the specifications' paths.
GRAPH: dict[str, Any] = {}

#: The class of the container holding a diagram and its key, and the ids of the
#: two, which a full-screen copy of either keeps outside the container, so the
#: stylesheet reads them there too.
CLASS = "roadmap-diagram"
IDS = ("roadmap-diagram", "roadmap-diagram-key")

#: The title of the admonition the key folds into.
KEY_TITLE = "Key"

#: What opens each diagram and its key, the grammar's, so the verification
#: report draws them alike (diagram spec §4.7).
FRONT_MATTER = geovista_citations.DIAGRAM_FRONT_MATTER
KEY_FRONT_MATTER = geovista_citations.KEY_FRONT_MATTER


def _read_graph(app: Sphinx) -> None:
    """Read the graph of every roadmap, once a build starts.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The application, read for its source directory.

    """
    srcdir = Path(app.srcdir)
    # the folder geovista_citation_xrefs names the rows of, and re-reads pages for
    folder = srcdir / geovista_citation_xrefs.SPECS
    specs = geovista_citations.specifications(folder)
    names = geovista_citations.namespace(specs)
    texts = {spec: spec.read_text(encoding="utf-8") for spec in specs}
    docnames = {
        prefix: spec.relative_to(srcdir).with_suffix("").as_posix()
        for spec, prefix in names.owners.items()
    }
    GRAPH.clear()
    GRAPH.update(
        edges=geovista_citations.ordering_edges(texts, names),
        statuses=geovista_citations.row_statuses(texts, names),
        labels=geovista_citations.row_labels(texts, names),
        docnames=docnames,
        owners={docname: prefix for prefix, docname in docnames.items()},
        paths=[str(spec) for spec in specs],
    )


def _note(env: BuildEnvironment) -> None:
    """Note what a diagram reads: this module, the grammar and every roadmap."""
    env.note_dependency(__file__)
    env.note_dependency(geovista_citations.__file__)
    for path in GRAPH["paths"]:
        env.note_dependency(path)


def _code(
    rows: Sequence[str],
    small: Collection[str],
    page: Callable[[str], str | None] | None = None,
) -> str:
    """Write the diagram of ``rows``, each linking to its row where ``page`` says.

    ``page`` gives the address of a row's page, relative to the page drawing it,
    or ``None`` where the builder can give none, which leaves the row unlinked.
    """
    links = {}
    for anchor in rows if page is not None else ():
        prefix = geovista_citations.LABEL.match(anchor)["prefix"]
        address = page(GRAPH["docnames"][prefix])
        if address is not None:
            links[anchor] = f"{address}#{anchor}"
    return FRONT_MATTER + geovista_citations.diagram(
        rows,
        GRAPH["edges"],
        GRAPH["statuses"],
        GRAPH["labels"],
        small=small,
        links=links,
    )


def _drawn(rows: Sequence[str], small: Collection[str]) -> nodes.container:
    """Hold the diagram of ``rows``, and beneath it the key, folded into a dropdown.

    The diagram is written without links, and records its rows, so that
    :func:`_link` writes them for the builder that writes the page.

    Parameters
    ----------
    rows : sequence of str
        The anchors of the rows to draw, in order.
    small : collection of str
        The rows of other specifications, drawn small.

    Returns
    -------
    docutils.nodes.container
        A container of the diagram's Mermaid node, and an admonition holding the
        key's.

    """
    drawn, key = (
        mermaid(code=text, options={}, ids=[ident])
        for ident, text in zip(
            IDS,
            (_code(rows, small), KEY_FRONT_MATTER + geovista_citations.diagram_key()),
            strict=True,
        )
    )
    drawn["roadmap_rows"] = list(rows)
    drawn["roadmap_small"] = sorted(small)
    # the key folds away, as an admonition of class dropdown, which
    # sphinx-togglebutton opens and closes, so it costs no space until read
    folded = nodes.admonition(
        "", nodes.title(text=KEY_TITLE), key, classes=["admonition-key", "dropdown"]
    )
    container = nodes.container(classes=[CLASS])
    container += [drawn, folded]
    return container


def _link(app: Sphinx, doctree: nodes.document, docname: str) -> None:
    """Link each row of a page's diagram, for the builder that writes the page.

    A link read as the page was read would be the reading builder's, which the
    shared doctrees keep for another: a dirhtml build after html would link to
    html's files. A builder that cannot address a page, as latex, leaves its row
    unlinked, and a page that is part of another, as in singlehtml, links its
    anchor alone.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The application, read for its builder.
    doctree : docutils.nodes.document
        The page, as it is about to be written.
    docname : str
        The page's name.

    """

    def page(target: str) -> str | None:
        try:
            uri = app.builder.get_relative_uri(docname, target)
        except NoUri:
            return None
        return uri.partition("#")[0]

    for node in doctree.findall(mermaid):
        if "roadmap_rows" in node:
            node["code"] = _code(node["roadmap_rows"], node["roadmap_small"], page)


def _is_roadmap(table: nodes.table) -> bool:
    """Say whether a table is headed as a roadmap is, ``#``, ``Scope``, ``Status``."""
    head = next(iter(table.findall(nodes.thead)), None)
    row = next(iter(head.findall(nodes.row)), None) if head is not None else None
    if row is None:
        return False
    cells = [entry.astext().strip() for entry in row.findall(nodes.entry)]
    return bool(geovista_citations.roadmap_header(cells))


class RoadmapDiagram(SphinxTransform):
    """Draw a specification's diagram under its roadmap table (diagram spec §4.4).

    It runs after :mod:`geovista_citation_xrefs` names each row, at 300, and links
    each citation, at 400, so a row's anchor exists for its link. A roadmap no
    ordering touches draws nothing, and the diagram follows the last roadmap
    table, so it follows every row it draws.
    """

    default_priority = 420

    def apply(self, **kwargs: object) -> None:  # noqa: ARG002
        """Insert the diagram after the roadmap table of a specification's page."""
        owner = GRAPH.get("owners", {}).get(self.env.docname)
        if owner is None:
            return
        # a roadmap that gains an ordering later re-reads its page too
        _note(self.env)
        rows, small = geovista_citations.roadmap_view(
            owner, GRAPH["edges"], GRAPH["statuses"]
        )
        tables = [t for t in self.document.findall(nodes.table) if _is_roadmap(t)]
        if not rows or not tables:
            return
        last = tables[-1]
        last.parent.insert(last.parent.index(last) + 1, _drawn(rows, small))


class OpenWork(SphinxDirective):
    """Draw the open work of every roadmap, where it stands (diagram spec §4.5)."""

    has_content = False

    def run(self) -> list[nodes.Node]:
        """Return the open work's diagram and key, or nothing when there is none."""
        _note(self.env)
        rows = geovista_citations.open_work(GRAPH["edges"], GRAPH["statuses"])
        if not rows:
            return []
        return [_drawn(rows, ())]


def setup(app: Sphinx) -> dict[str, object]:
    """Register the transform, the directive and the handlers that read and link.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The application.

    Returns
    -------
    dict
        The extension metadata.

    """
    app.setup_extension("sphinxcontrib.mermaid")
    # it names each row a link points to, and reads every page again when a
    # specification comes or goes, whose rows a diagram may then draw
    app.setup_extension("geovista_citation_xrefs")
    app.connect("builder-inited", _read_graph)
    app.connect("doctree-resolved", _link)
    app.add_transform(RoadmapDiagram)
    app.add_directive("roadmap-open-work", OpenWork)
    return {
        "version": "0.1.0",
        "env_version": 1,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
