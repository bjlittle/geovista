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

Each row links to its row in its roadmap table (diagram spec §4.6). A row's colour
and whether it is ready read every roadmap, so every page drawing a diagram
depends on every specification, and on their folder, whose time changes when one
is added or removed.

"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from docutils import nodes
import geovista_citations
from sphinx.transforms import SphinxTransform
from sphinx.util.docutils import SphinxDirective
from sphinxcontrib.mermaid import mermaid

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence

    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

#: The graph of every roadmap, read once a build starts (:func:`_read_graph`):
#: its edges, statuses and labels, each specification's docname by its prefix and
#: prefix by its docname, the specifications' paths and their folder, and the
#: builder that links are made relative by.
GRAPH: dict[str, Any] = {}

#: The class of the container holding a diagram and its key.
CLASS = "roadmap-diagram"

#: What opens each diagram and its key. Mermaid's light theme keeps the colours
#: of diagram spec §4.2 on a dark page, whose own theme would invert them, and the
#: diagram keeps its own size, not shrunk to the page: the open work spans many
#: specifications, and shrunk, no label is legible. ``_static/roadmap_diagrams.css``
#: lets the page scroll a diagram wider than it, on a white ground.
FRONT_MATTER = (
    "---\n"
    "config:\n"
    "  theme: default\n"
    "  darkMode: false\n"
    "  flowchart:\n"
    "    useMaxWidth: false\n"
    "---\n"
)


def _read_graph(app: Sphinx) -> None:
    """Read the graph of every roadmap, once a build starts.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The application, read for its source directory and builder.

    """
    srcdir = Path(app.srcdir)
    folder = srcdir / app.config.geovista_roadmap_specs
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
        folder=str(folder),
        builder=app.builder,
    )


def _note(env: BuildEnvironment) -> None:
    """Note what a diagram reads: this module, the grammar and every roadmap."""
    env.note_dependency(__file__)
    env.note_dependency(geovista_citations.__file__)
    env.note_dependency(GRAPH["folder"])
    for path in GRAPH["paths"]:
        env.note_dependency(path)


def _drawn(
    docname: str, rows: Sequence[str], small: Collection[str]
) -> nodes.container:
    """Hold the diagram of ``rows``, each linking to its row, and the key beneath it.

    Parameters
    ----------
    docname : str
        The page drawing it, which each link is relative to.
    rows : sequence of str
        The anchors of the rows to draw, in order.
    small : collection of str
        The rows of other specifications, drawn small.

    Returns
    -------
    docutils.nodes.container
        A container of two Mermaid nodes, the diagram's and the key's.

    """
    builder = GRAPH["builder"]

    def href(anchor: str) -> str:
        prefix = geovista_citations.LABEL.match(anchor)["prefix"]
        page = builder.get_relative_uri(docname, GRAPH["docnames"][prefix])
        return f"{page}#{anchor}"

    code = geovista_citations.diagram(
        rows,
        GRAPH["edges"],
        GRAPH["statuses"],
        GRAPH["labels"],
        small=small,
        links={anchor: href(anchor) for anchor in rows},
    )
    container = nodes.container(classes=[CLASS])
    for text in (code, geovista_citations.diagram_key()):
        node = mermaid()
        node["code"] = FRONT_MATTER + text
        node["options"] = {}
        container += node
    return container


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
        last.parent.insert(
            last.parent.index(last) + 1, _drawn(self.env.docname, rows, small)
        )


class OpenWork(SphinxDirective):
    """Draw the open work of every roadmap, where it stands (diagram spec §4.5)."""

    has_content = False

    def run(self) -> list[nodes.Node]:
        """Return the open work's diagram and key, or nothing when there is none."""
        _note(self.env)
        rows = geovista_citations.open_work(GRAPH["edges"], GRAPH["statuses"])
        if not rows:
            return []
        return [_drawn(self.env.docname, rows, ())]


def setup(app: Sphinx) -> dict[str, object]:
    """Register the transform, the directive and the folder of specifications.

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
    # the folder of the specifications, relative to the source directory
    app.add_config_value(
        "geovista_roadmap_specs", "developer/specs", "env", types=frozenset({str})
    )
    app.connect("builder-inited", _read_graph)
    app.add_transform(RoadmapDiagram)
    app.add_directive("roadmap-open-work", OpenWork)
    return {
        "version": "0.1.0",
        "env_version": 1,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
