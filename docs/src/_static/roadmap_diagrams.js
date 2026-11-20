/*
 * The diagrams of the order between roadmap rows (diagram spec §4.4, §4.5),
 * drawn by docs/src/_ext/geovista_roadmap_diagrams.py.
 *
 * Full screen, sphinxcontrib-mermaid's viewer copies a diagram, strips its size
 * and fits it to the screen, where the open work, many specifications wide,
 * shrinks past reading, with no zoom. A roadmap diagram's copy keeps the size
 * its viewBox gives instead, and roadmap_diagrams.css lets the viewer scroll it.
 * Set with priority, as the viewer's own rules size the copy with priority too.
 */
document.addEventListener("DOMContentLoaded", () => {
    const copies =
        '.mermaid-container-fullscreen pre.mermaid[id^="roadmap-diagram"] > svg';
    const keepSize = (svg) => {
        const box = svg.viewBox && svg.viewBox.baseVal;
        if (!box || !box.width || svg.dataset.roadmapSized === "true") {
            return;
        }
        svg.style.setProperty("width", `${box.width}px`, "important");
        svg.style.setProperty("height", `${box.height}px`, "important");
        svg.style.setProperty("max-width", "none", "important");
        svg.style.setProperty("max-height", "none", "important");
        svg.dataset.roadmapSized = "true";
    };
    new MutationObserver(() => {
        document.querySelectorAll(copies).forEach(keepSize);
    }).observe(document.body, { childList: true, subtree: true });
});
