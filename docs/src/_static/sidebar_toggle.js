/*
 * Copyright (c) 2021, GeoVista Contributors.
 *
 * This file is part of GeoVista and is distributed under the 3-Clause BSD
 * license. See the LICENSE file in the package root directory for licensing
 * details.
 *
 * Repair the primary sidebar toggle.
 *
 * "sphinx-book-theme" renders its own ".primary-toggle" button in the article
 * header, and hides the "pydata-sphinx-theme" one in the navigation bar. Both
 * themes, however, bind their click handler with
 *
 *     document.querySelector(".primary-toggle")
 *
 * which matches only the *first* button in document order - the hidden navbar
 * one. The button a reader actually sees is therefore inert: on a narrow
 * viewport the primary sidebar is off-canvas with no way to reveal it, which
 * strands every link it contains.
 *
 * Forward clicks from the inert buttons to the button carrying the handlers,
 * which restores both behaviours the themes intend - the off-canvas dialog on
 * a narrow viewport, and collapse-in-place on a wide one.
 *
 * See https://github.com/executablebooks/sphinx-book-theme/issues/865
 */
document.addEventListener("DOMContentLoaded", () => {
  const toggles = document.querySelectorAll(".primary-toggle");

  // nothing to repair once there is only one button to bind to i.e., upstream
  // has dropped the duplicate
  if (toggles.length < 2) {
    return;
  }

  // the button that "querySelector" found, and so the only one with handlers
  const bound = toggles[0];
  const dialog = document.getElementById("pst-primary-sidebar-modal");

  Array.from(toggles)
    .slice(1)
    .forEach((toggle) => {
      toggle.addEventListener("click", (event) => {
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
});
