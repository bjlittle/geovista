# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Keep a parallel build within memory, and its output the same as a serial one.

``sphinx-build --jobs`` reads, and then writes, the pages in worker processes.
The build spends most of its time reading, as that is when the plots render and
the tutorial notebook runs. Reading in parallel needs more memory than reading
serially, and the output of a parallel build differs in four ways. This
extension handles each:

- sphinx-gallery leaves its idle workers alive for five minutes after it runs
  the examples, which outlasts reading the pages. Beside the processes reading
  them, the kernel running the tutorial notebook then died on Read the Docs,
  whose builders have about 7.7 GB. The workers are stopped before the pages
  are read, so a parallel build needs less memory than a serial one did with
  them.
- ``sphinx-tippy`` collects the tips of a page as it writes the page, and saves
  them all once the build finishes. Nothing carries the tips of a page written
  by a worker back to the main process, so they are lost. The pages are written
  serially instead, and are still read in parallel.
- ``sphinx.ext.viewcode`` records the module of each documented object,
  including a module that a re-exported object only resolves to, such as
  ``pooch.core`` for ``geovista.cache.CACHE``. A serial read soon discards a
  module that holds none of the documented objects, but merging the parallel
  reads keeps it, and its source is rendered. Such modules are discarded once
  the reads are merged.
- ``viewcode`` links the source of a module back to its objects by the module
  of whichever page reached it first. That varies with the order in which the
  parallel reads merge, and even a serial build gets ``geovista.themes`` wrong,
  as the ``geovista`` package page re-exports its objects and is read first. A
  module whose objects are all documented under its own name is linked back by
  that name instead.
- Sphinx records the pages in the order their reads merge, not the sorted order
  of a serial read, and ``sphinx-llms-txt`` uses that order for a page without a
  toctree of its own. The pages are sorted once the reads merge.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from joblib.externals.loky import reusable_executor

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment

__all__ = ["setup"]


def drop_unused_modules(app: Sphinx, env: BuildEnvironment) -> None:  # noqa: ARG001
    """Discard each ``viewcode`` module holding none of the documented objects.

    Parameters
    ----------
    app : Sphinx
        The sphinx application.
    env : BuildEnvironment
        The build environment, with the parallel reads merged.

    """
    modules = getattr(env, "_viewcode_modules", {})

    # an entry is either False, for a module that could not be analysed, or
    # its code, tags, the documented objects found in it and its refname
    for name, entry in list(modules.items()):
        if entry and not entry[2]:
            del modules[name]


def relink_modules(app: Sphinx, env: BuildEnvironment) -> None:  # noqa: ARG001
    """Link each ``viewcode`` module back to its objects by its own name.

    Parameters
    ----------
    app : Sphinx
        The sphinx application.
    env : BuildEnvironment
        The build environment, with the parallel reads merged.

    """
    modules = getattr(env, "_viewcode_modules", {})
    objects = env.get_domain("py").objects

    for name, entry in modules.items():
        if not entry:
            continue

        code, tags, used, refname = entry

        # only relink a module whose objects are all documented by its name, on
        # the page that viewcode links back to
        if refname != name and all(
            (found := objects.get(f"{name}.{fullname}")) is not None
            and found.docname == docname
            for fullname, docname in used.items()
        ):
            modules[name] = (code, tags, used, name)


def sort_docs(app: Sphinx, env: BuildEnvironment) -> None:  # noqa: ARG001
    """Record the pages in the order a serial build reads them.

    Parameters
    ----------
    app : Sphinx
        The sphinx application.
    env : BuildEnvironment
        The build environment, with the parallel reads merged.

    """
    env.all_docs = dict(sorted(env.all_docs.items()))


def release_gallery_workers(
    app: Sphinx,  # noqa: ARG001
    env: BuildEnvironment,  # noqa: ARG001
    docnames: list[str],  # noqa: ARG001
) -> None:
    """Stop the idle workers that ran the gallery examples.

    sphinx-gallery runs the examples in the reusable pool of ``loky`` workers,
    which keeps an idle worker, and its memory, for five minutes. That outlasts
    reading the pages, when the processes reading them and the kernel running
    the tutorial notebook need the memory, of which Read the Docs has about
    7.7 GB.

    Parameters
    ----------
    app : Sphinx
        The sphinx application.
    env : BuildEnvironment
        The build environment.
    docnames : list of str
        The pages about to be read.

    """
    # asking loky for the pool would create one, and its resource tracker, in a
    # build with none, so take the pool it holds. a rename stops the release,
    # which the unit test of this function reports
    executor = getattr(reusable_executor, "_executor", None)

    if executor is not None:
        executor.shutdown(wait=True)


def serial_write(app: Sphinx, builder: Builder) -> None:  # noqa: ARG001
    """Write the pages serially, so that ``sphinx-tippy`` keeps their tips.

    Sphinx has decided to write in parallel by the time this runs, so turning
    it off here raises none of the warnings that declaring ``sphinx-tippy``
    unsafe for parallel writing would, and which ``--fail-on-warning`` would
    turn into a failure.

    Parameters
    ----------
    app : Sphinx
        The sphinx application.
    builder : Builder
        The builder about to write the pages.

    """
    builder.parallel_ok = False


def setup(app: Sphinx) -> dict[str, bool]:
    """Configure the sphinx application.

    Parameters
    ----------
    app : Sphinx
        The sphinx application.

    Returns
    -------
    dict
        A dictionary declaring the extension safe for parallel reading and
        writing. Every hook runs in the main process.

    """
    app.connect("env-before-read-docs", release_gallery_workers)
    app.connect("env-updated", drop_unused_modules)
    app.connect("env-updated", relink_modules)
    app.connect("env-updated", sort_docs)
    app.connect("write-started", serial_write)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
