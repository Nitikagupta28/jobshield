// site.js - runs on every page: dark-mode toggle, mobile menu, footer year.

(function () {
  const root = document.documentElement;

  // ----- dark / light mode -----
  const themeBtn = document.getElementById("themeToggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) { /* storage can be blocked; ignore */ }
    });
  }

  // ----- mobile menu -----
  const nav = document.getElementById("nav");
  const toggle = document.getElementById("navToggle");
  if (nav && toggle) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  // ----- footer year -----
  const year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();