/*
 * Copyright (c) 2021, GeoVista Contributors.
 *
 * This file is part of GeoVista and is distributed under the 3-Clause BSD
 * license. See the LICENSE file in the package root directory for licensing
 * details.
 *
 * Repair the primary and secondary sidebar toggles.
 *
 * "sphinx-book-theme" renders its own ".primary-toggle" and ".secondary-toggle"
 * buttons in the article header, and hides the "pydata-sphinx-theme" pair in the
 * navigation bar. Both themes, however, bind their click handlers with
 *
 *     document.querySelector(".primary-toggle")
 *     document.querySelector(".secondary-toggle")
 *
 * which match only the *first* button of each kind in document order - the
 * hidden navbar ones. The buttons a reader actually sees are therefore inert: on
 * a narrow viewport both sidebars are off-canvas with no way to reveal them,
 * which strands every link they contain.
 *
 * Forward clicks from the inert buttons to the button carrying the handlers,
 * which restores every behaviour the themes intend - the off-canvas dialog on a
 * narrow viewport, and collapse-in-place on a wide one.
 *
 * Reported upstream as
 * https://github.com/executablebooks/sphinx-book-theme/issues/988 and
 * https://github.com/executablebooks/sphinx-book-theme/issues/999, and fixed on
 * "main" by https://github.com/executablebooks/sphinx-book-theme/pull/987, which
 * stops the redundant navigation bar - and so the duplicate buttons - from being
 * rendered at all. That is unreleased as of "sphinx-book-theme 1.4.0", but needs
 * nothing from us when it ships: "forward" below retires itself as soon as there
 * is only one button of a kind left to bind to.
 */

// each toggle and the dialog "pydata-sphinx-theme" opens from it
const GROUPS = [
  { toggle: ".primary-toggle", modal: "pst-primary-sidebar-modal" },
  { toggle: ".secondary-toggle", modal: "pst-secondary-sidebar-modal" },
];

// the viewport at which "sphinx-book-theme" switches the primary sidebar from a
// dialog to collapse-in-place, as per its own "fixSidebarToggle"
const WIDE = "(min-width: 992px)";

/**
 * Forward clicks from the inert buttons to the button holding the handlers.
 *
 * @param {string} toggle - selector matching every button of this kind
 * @param {string} modal - id of the dialog opened by this kind of button
 */
function forward(toggle, modal) {
  const toggles = document.querySelectorAll(toggle);

  // nothing to repair once there is only one button to bind to i.e., upstream
  // has dropped the duplicate
  if (toggles.length < 2) {
    return;
  }

  // the button that "querySelector" found, and so the only one with handlers
  const bound = toggles[0];
  const dialog = document.getElementById(modal);

  Array.from(toggles)
    .slice(1)
    .forEach((button) => {
      button.addEventListener("click", (event) => {
        // should upstream bind every button, its handler may already have run
        // and opened the dialog, and opening an open dialog throws an
        // "InvalidStateError" - so defer to it
        if (dialog && dialog.hasAttribute("open")) {
          return;
        }

        event.preventDefault();
        // "stopImmediatePropagation", rather than "stopPropagation", so that an
        // upstream handler bound to this same button *after* this one cannot
        // also fire and double-toggle
        event.stopImmediatePropagation();
        bound.click();
      });
    });
}

/**
 * Dismiss the primary sidebar dialog when the viewport grows wide.
 *
 * Opening the dialog moves the sidebar's classes onto it, and on a wide viewport
 * "sphinx-book-theme" collapses the sidebar by adding "pst-sidebar-hidden". A
 * dialog opened narrow and then widened therefore carries that class into a
 * viewport whose styling honours it, leaving the dialog open but invisible - and
 * an open dialog holds the top layer, so it blocks the whole page while offering
 * nothing to click. Escape cannot dismiss it either, as "pydata-sphinx-theme"
 * binds that to the dialog, which can no longer hold focus.
 *
 * Closing it hands back to "pydata-sphinx-theme", whose own "close" handler
 * returns the nodes and classes to the sidebar and restores focus.
 *
 * Only the primary sidebar is affected; "sphinx-book-theme" leaves the secondary
 * one alone, and its dialog is still the intended wide-viewport presentation.
 *
 * Unlike the duplicate buttons above, this is not fixed by
 * https://github.com/executablebooks/sphinx-book-theme/pull/987 - it is caused by
 * the class transfer rather than the duplication, and reproduces with the
 * redundant navigation bar removed. So this half outlives "forward".
 *
 * Reported upstream as
 * https://github.com/executablebooks/sphinx-book-theme/issues/1012
 */
function dismissOnWide() {
  const dialog = document.getElementById("pst-primary-sidebar-modal");

  if (!dialog) {
    return;
  }

  window.matchMedia(WIDE).addEventListener("change", (event) => {
    if (event.matches && dialog.hasAttribute("open")) {
      dialog.close();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  GROUPS.forEach(({ toggle, modal }) => forward(toggle, modal));
  dismissOnWide();
});
