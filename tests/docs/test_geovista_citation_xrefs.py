# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Tests of the transform that links specification citations at build time.

The transform is ``docs/src/_ext/geovista_citation_xrefs.py``, a port of
``tephpy``'s, and these tests are a port of ``tephpy``'s tests of it. It needs
``sphinx``, so each test guards on it through ``require``, which skips without it
and fails under ``--browser-strict``, as the documentation job runs. This module
sits inside the corpus the citation grammar governs, so it builds the section sign
rather than write it.

"""

from __future__ import annotations

import importlib.util
import io
import logging
from pathlib import Path
import sys
import textwrap
import types
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import NoReturn

#: The local extensions, which a build imports by bare name.
EXT = Path(__file__).parents[2] / "docs" / "src" / "_ext"

#: The documentation source, whose specifications the registry is built from.
SRC = Path(__file__).parents[2] / "docs" / "src"

#: The section sign, built rather than written: see the module docstring.
SECTION = "\N{SECTION SIGN}"

#: A citation that resolves, so the transform converts it, and the tests below are
#: about where it sits rather than what it says.
CITED = f"docs spec {SECTION}3.5"

#: A heading carrying it.
TITLED = f"Rendering and {CITED}"


def _load(name: str) -> types.ModuleType:
    """Load a local extension by path, reusing a copy already registered from it."""
    path = (EXT / f"{name}.py").resolve()
    registered = sys.modules.get(name)
    if registered is not None and Path(registered.__file__).resolve() == path:
        return registered
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def docs(require: Callable[[str], NoReturn]) -> types.SimpleNamespace:
    """Provide the transform and the doctree modules it reads, or skip without them.

    Returns
    -------
    types.SimpleNamespace
        The transform as ``cx``, and ``nodes``, ``addnodes`` and ``new_document``.

    """
    try:
        from docutils import nodes  # noqa: PLC0415
        from docutils.utils import new_document  # noqa: PLC0415
        from sphinx import addnodes  # noqa: PLC0415
    except ImportError:
        require("sphinx is not installed")

    # the transform imports the grammar by bare name, as a build does
    sys.path.insert(0, str(EXT))
    try:
        cx = _load("geovista_citation_xrefs")
    finally:
        sys.path.remove(str(EXT))

    return types.SimpleNamespace(
        cx=cx, nodes=nodes, addnodes=addnodes, new_document=new_document
    )


def app(srcdir: Path) -> types.SimpleNamespace:
    """Return as much of a Sphinx application as the registry handler reads."""
    return types.SimpleNamespace(srcdir=srcdir)


def env(docs, *docnames: str, fingerprint: str | None = None) -> types.SimpleNamespace:
    """Return as much of a build environment as the outdated handler reads."""
    stub = types.SimpleNamespace(found_docs=set(docnames))
    if fingerprint is not None:
        setattr(stub, docs.cx.ENV_FINGERPRINT, fingerprint)
    return stub


def outdated(docs, environment, added=frozenset(), changed=frozenset()) -> set[str]:
    """Call the handler the way Sphinx does, which is positionally."""
    return docs.cx._outdated(None, environment, added, changed, frozenset())


def document(docs, *children: object, docname: str = "probe") -> object:
    """Return as much of a parsed document as the transform reads."""
    doc = docs.new_document(f"{docname}.md")
    doc.settings.env = types.SimpleNamespace(docname=docname)
    doc.extend(children)
    return doc


def rewrite(docs, doc) -> list[str]:
    """Run the transform over ``doc``, and return the anchors it linked."""
    docs.cx.CitationTransform(doc).apply()
    return [xref["reftarget"] for xref in doc.findall(docs.addnodes.pending_xref)]


class Registrar:
    """Record what ``setup`` asks of the application, which is all it does."""

    def __init__(self) -> None:
        self.connected = {}
        self.transforms = []

    def connect(self, event, handler) -> None:
        """Record an event handler."""
        self.connected[event] = handler

    def add_transform(self, transform) -> None:
        """Record a transform."""
        self.transforms.append(transform)


@pytest.fixture
def registry(docs) -> Iterator[None]:
    """Restore the module globals, which building the registry mutates in place."""
    cx = docs.cx
    pattern, owners, fingerprint = cx.PATTERN, dict(cx.OWNERS), cx.FINGERPRINT
    yield
    cx.PATTERN = pattern
    cx.FINGERPRINT = fingerprint
    cx.OWNERS.clear()
    cx.OWNERS.update(owners)


@pytest.fixture
def warned(docs) -> Iterator[list[str]]:
    """Collect what the transform reports, without standing up a build to do it.

    Attached to the extension's own logger rather than read from ``caplog``, which
    reaches records through the root: Sphinx stops its namespace propagating there
    once any build in the process has set up its logging.
    """
    reported: list[str] = []

    class Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            reported.append(record.getMessage())

    logger = logging.getLogger(docs.cx.logger.logger.name)
    handler = Collect()
    level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    yield reported
    logger.setLevel(level)
    logger.removeHandler(handler)


@pytest.mark.usefixtures("registry")
def test_a_citation_in_prose_becomes_a_reference_displaying_it(docs, warned):
    """The ordinary case: a link to the anchor, displaying the citation as written."""
    docs.cx._build_registry(app(SRC))
    nodes = docs.nodes
    doc = document(docs, nodes.paragraph("", "", nodes.Text(TITLED)))

    linked = rewrite(docs, doc)

    assert linked == ["docs-spec-3-5"]
    (xref,) = doc.findall(docs.addnodes.pending_xref)
    assert xref.astext() == CITED
    assert xref["refwarn"] is True
    assert doc.astext() == TITLED
    assert warned == []


@pytest.mark.usefixtures("registry")
def test_a_run_becomes_one_reference_per_citation(docs):
    """A prefix carries across a comma, so each section of the run links."""
    docs.cx._build_registry(app(SRC))
    nodes = docs.nodes
    text = f"See typing spec {SECTION}3.2, {SECTION}4 there."
    doc = document(docs, nodes.paragraph("", "", nodes.Text(text)))

    assert rewrite(docs, doc) == ["typing-spec-3-2", "typing-spec-4"]
    assert doc.astext() == text


@pytest.mark.usefixtures("registry")
def test_a_bare_section_resolves_only_inside_a_specification(docs):
    """A bare section number means the document it is written in, if that has any."""
    docs.cx._build_registry(app(SRC))
    nodes = docs.nodes
    owner = "developer/specs/2026-10-06-published-specs-design"
    text = f"See {SECTION}4."

    inside = document(docs, nodes.paragraph("", "", nodes.Text(text)), docname=owner)
    outside = document(docs, nodes.paragraph("", "", nodes.Text(text)))

    assert rewrite(docs, inside) == ["docs-spec-4"]
    assert rewrite(docs, outside) == []


@pytest.mark.usefixtures("registry")
@pytest.mark.parametrize(
    "kind", ["literal", "literal_block", "comment", "raw", "reference"]
)
def test_a_citation_the_skip_set_holds_stays_plain(docs, warned, kind):
    """Literals stay examples, and a link is never nested inside a link."""
    docs.cx._build_registry(app(SRC))
    nodes = docs.nodes
    doc = document(docs, nodes.paragraph("", "", getattr(nodes, kind)("", CITED)))

    assert rewrite(docs, doc) == []
    assert warned == []


@pytest.mark.usefixtures("registry")
def test_a_citation_in_an_autosummary_table_is_linked(docs):
    """A rendered table subclassing ``comment``, as the API summaries are."""
    from sphinx.ext.autosummary import autosummary_table  # noqa: PLC0415

    docs.cx._build_registry(app(SRC))
    nodes = docs.nodes
    table = autosummary_table("", nodes.paragraph("", "", nodes.Text(TITLED)))
    doc = document(docs, table)

    assert rewrite(docs, doc) == ["docs-spec-3-5"]


@pytest.mark.usefixtures("registry")
def test_a_citation_in_a_section_heading_is_reported(docs, warned):
    """Converted, but the page navigation keeps the text and drops the anchor."""
    docs.cx._build_registry(app(SRC))
    nodes = docs.nodes
    heading = nodes.title("", "", nodes.Text(TITLED))
    doc = document(docs, nodes.section("", heading, ids=["rendering"]))

    assert rewrite(docs, doc) == ["docs-spec-3-5"]
    (message,) = warned
    assert TITLED in message, "the warning does not say which heading it is about"


@pytest.mark.usefixtures("registry")
def test_a_citation_linked_by_hand_in_a_section_heading_is_reported(docs, warned):
    """An author's own link is dropped from the navigation just as the transform's."""
    docs.cx._build_registry(app(SRC))
    nodes = docs.nodes
    linkage = nodes.reference("", CITED, refuri="https://example.com/spec")
    heading = nodes.title("", "", nodes.Text("Rendering and "), linkage)
    doc = document(docs, nodes.section("", heading, ids=["rendering"]))

    assert rewrite(docs, doc) == []
    (message,) = warned
    assert "Rendering and " + CITED in message


@pytest.mark.usefixtures("registry")
def test_a_citation_quoted_as_a_literal_in_a_section_heading_is_not_reported(
    docs, warned
):
    """A literal is copied into the navigation whole, so nothing is lost."""
    docs.cx._build_registry(app(SRC))
    nodes = docs.nodes
    heading = nodes.title(
        "", "", nodes.Text("Rendering and "), nodes.literal("", CITED)
    )
    doc = document(docs, nodes.section("", heading, ids=["rendering"]))

    assert rewrite(docs, doc) == []
    assert warned == []


@pytest.mark.usefixtures("registry")
def test_a_citation_in_a_table_caption_is_not_reported(docs, warned):
    """Only a section heading is copied into the navigation, not every title."""
    docs.cx._build_registry(app(SRC))
    nodes = docs.nodes
    doc = document(docs, nodes.table("", nodes.title("", "", nodes.Text(TITLED))))

    assert rewrite(docs, doc) == ["docs-spec-3-5"]
    assert warned == []


@pytest.mark.usefixtures("registry")
def test_the_registry_is_built_from_the_specifications_on_disk(docs):
    """Nothing declares the prefixes: the anchors in the tree are the registry."""
    docs.cx._build_registry(app(SRC))

    assert docs.cx.PATTERN is not None
    owner = "developer/specs/2026-10-06-published-specs-design"
    assert docs.cx.OWNERS[owner] == "docs-spec"


@pytest.mark.usefixtures("registry")
def test_a_build_finding_no_anchors_clears_the_previous_registry(docs, tmp_path):
    """Two builds share a process, and the second must not inherit the first."""
    docs.cx._build_registry(app(SRC))
    assert docs.cx.PATTERN is not None, "nothing is asserted unless this holds"
    assert docs.cx.OWNERS, "nothing is asserted unless this holds"

    docs.cx._build_registry(app(tmp_path))

    assert docs.cx.PATTERN is None
    assert docs.cx.OWNERS == {}


@pytest.mark.usefixtures("registry")
def test_a_registry_with_no_anchors_converts_nothing(docs, tmp_path):
    """A reference no anchor can resolve would be worse than plain text."""
    docs.cx._build_registry(app(tmp_path))
    nodes = docs.nodes
    doc = document(docs, nodes.paragraph("", "", nodes.Text(TITLED)))

    assert rewrite(docs, doc) == []


@pytest.mark.usefixtures("registry")
def test_the_fingerprint_follows_the_specifications_on_disk(docs, tmp_path):
    """A registry the transform would read differently must digest differently."""
    specs = tmp_path / "developer" / "specs"
    specs.mkdir(parents=True)
    (specs / "a.md").write_text("(alpha-spec-1)=\n## 1. Alpha\n", encoding="utf-8")
    docs.cx._build_registry(app(tmp_path))
    before = docs.cx.FINGERPRINT

    docs.cx._build_registry(app(tmp_path))
    assert before == docs.cx.FINGERPRINT, "the digest depends on the call"

    (specs / "b.md").write_text("(beta-spec-1)=\n## 1. Beta\n", encoding="utf-8")
    docs.cx._build_registry(app(tmp_path))
    assert before != docs.cx.FINGERPRINT, "adding a prefix left the digest unchanged"


@pytest.mark.usefixtures("registry")
def test_an_unchanged_registry_re_reads_nothing(docs, tmp_path):
    """The ordinary edit stays incremental."""
    docs.cx._build_registry(app(tmp_path))
    unchanged = env(docs, "index", "guide", fingerprint=docs.cx.FINGERPRINT)

    assert outdated(docs, unchanged) == set()


@pytest.mark.usefixtures("registry")
def test_a_changed_registry_re_reads_the_documents_sphinx_would_not(docs, tmp_path):
    """The registry is a hidden input to every cached doctree."""
    docs.cx._build_registry(app(tmp_path))
    stale = env(docs, "index", "guide", "prose", fingerprint="the last build's")

    assert outdated(docs, stale) == {"index", "guide", "prose"}
    assert getattr(stale, docs.cx.ENV_FINGERPRINT) == docs.cx.FINGERPRINT


@pytest.mark.usefixtures("registry")
def test_a_first_build_re_reads_nothing_extra(docs, tmp_path):
    """A cold cache has every document added already; the digest is still kept."""
    docs.cx._build_registry(app(tmp_path))
    cold = env(docs, "index", "guide")

    assert outdated(docs, cold, added={"index", "guide"}) == set()
    assert getattr(cold, docs.cx.ENV_FINGERPRINT) == docs.cx.FINGERPRINT


def test_setup_registers_every_handler_the_transform_relies_on(docs):
    """A build that stopped connecting one of them would pass every other test."""
    registrar = Registrar()

    metadata = docs.cx.setup(registrar)

    assert registrar.connected["builder-inited"] is docs.cx._build_registry
    assert registrar.connected["env-get-outdated"] is docs.cx._outdated
    assert registrar.transforms == [docs.cx.CitationTransform]
    assert metadata["env_version"]
    assert metadata["parallel_read_safe"] is True
    assert metadata["parallel_write_safe"] is True


#: The configuration of the end-to-end build.
CONF = """
extensions = ["geovista_citation_xrefs", "myst_parser", "sphinx.ext.autodoc"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
suppress_warnings = ["app"]
"""

#: Two small specifications, the second owning a section the page cites.
SPECS = {
    "2026-01-01-alpha-design.md": "# Alpha\n\n(alpha-spec-1)=\n## 1. One\n\nText.\n",
    "2026-01-02-beta-design.md": (
        "# Beta\n\n(beta-spec-1)=\n## 1. One\n\nSee {s}1 and alpha spec {s}1.\n"
    ),
}

#: A module whose docstring cites a section, as an API page will.
MODULE = '"""A module citing alpha spec {s}1."""\n'


@pytest.mark.usefixtures("docs")
def test_a_build_links_citations_in_a_page_and_a_docstring(tmp_path):
    """End to end, in parallel: the registry survives the fork, and every link lands."""
    from sphinx.application import Sphinx  # noqa: PLC0415
    from sphinx.util.docutils import docutils_namespace  # noqa: PLC0415

    src = tmp_path / "src"
    (src / "developer" / "specs").mkdir(parents=True)
    (src / "conf.py").write_text(CONF, encoding="utf-8")
    for name, body in SPECS.items():
        (src / "developer" / "specs" / name).write_text(
            body.format(s=SECTION), encoding="utf-8"
        )
    (src / "cited.py").write_text(MODULE.format(s=SECTION), encoding="utf-8")
    pages = ["page", "api", "developer/specs/2026-01-01-alpha-design"]
    pages.append("developer/specs/2026-01-02-beta-design")
    toctree = textwrap.indent("\n".join(pages), " " * 3)
    (src / "index.rst").write_text(f"Index\n=====\n\n.. toctree::\n\n{toctree}\n")
    (src / "page.rst").write_text(
        f"Page\n====\n\nSee beta spec {SECTION}1, and ``alpha spec {SECTION}1``.\n"
    )
    (src / "api.rst").write_text("API\n===\n\n.. automodule:: cited\n")

    warning = io.StringIO()
    with pytest.MonkeyPatch.context() as patch, docutils_namespace():
        patch.syspath_prepend(str(src))
        patch.syspath_prepend(str(EXT))
        app_ = Sphinx(
            str(src),
            str(src),
            str(tmp_path / "html"),
            str(tmp_path / "doctrees"),
            "html",
            status=None,
            warning=warning,
            parallel=2,
        )
        app_.build()

    html = tmp_path / "html"
    page = (html / "page.html").read_text(encoding="utf-8")
    api = (html / "api.html").read_text(encoding="utf-8")
    beta = (html / "developer/specs/2026-01-02-beta-design.html").read_text(
        encoding="utf-8"
    )

    assert warning.getvalue() == ""
    assert 'beta-design.html#beta-spec-1"' in page
    words = ("alpha", "spec", f"{SECTION}1")
    literal = " ".join(f'<span class="pre">{word}</span>' for word in words)
    assert literal in page, "the literal citation was not left as code"
    assert 'alpha-design.html#alpha-spec-1"' in api
    assert '#beta-spec-1"' in beta
    assert 'alpha-design.html#alpha-spec-1"' in beta
