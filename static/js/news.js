document.addEventListener("DOMContentLoaded", () => {
  const filter = document.getElementById("faculty-filter");
  filter?.addEventListener("change", () => filter.form?.requestSubmit());

  const composer = document.getElementById("news-composer");
  const fields = document.getElementById("composer-fields");
  if (composer && fields) {
    const triggers = composer.querySelectorAll("[data-composer-open]");
    const setExpanded = (expanded) => {
      composer.dataset.expanded = String(expanded);
      fields.hidden = !expanded;
      triggers.forEach((trigger) => {
        if (trigger.matches("button")) {
          trigger.setAttribute("aria-expanded", String(expanded));
        }
      });
    };

    if (composer.dataset.expanded !== "true") {
      setExpanded(false);
    }

    triggers.forEach((trigger) => {
      trigger.addEventListener("click", () => {
        setExpanded(true);
        const target = trigger.dataset.focus
          ? document.getElementById(trigger.dataset.focus)
          : document.getElementById("id_content");
        target?.focus();
      });
    });
  }

  document.querySelectorAll(".news-avatar img").forEach((image) => {
    image.addEventListener("error", () => image.remove(), { once: true });
  });
});
