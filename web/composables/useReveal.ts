/**
 * Reveal-on-scroll directive helper (no dependencies).
 * Adds the `is-visible` class to elements with `.reveal` as they enter the viewport.
 * Call `useReveal()` in a page's setup; it wires an IntersectionObserver on mount.
 */
export function useReveal() {
  onMounted(() => {
    if (typeof IntersectionObserver === "undefined") return;
    const els = document.querySelectorAll(".reveal");
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.12 },
    );
    els.forEach((el) => io.observe(el));
    onBeforeUnmount(() => io.disconnect());
  });
}
