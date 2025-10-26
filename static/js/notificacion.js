document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    document.querySelectorAll(".floating-alert").forEach(el => {
      el.remove();
    });
  }, 4000);
});
