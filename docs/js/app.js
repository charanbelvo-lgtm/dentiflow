/* DentiFlow static demo: all data intentionally lives in localStorage. */
(function () {
  const demoUser = () => JSON.parse(localStorage.getItem("dentiflowUser") || '{"name":"Dr. Ananya Sharma","role":"doctor"}');
  const initials = name => (name || "DF").split(" ").map(x => x[0]).slice(0, 2).join("").toUpperCase();
  window.toast = function (message, type) {
    const node = document.createElement("div");
    node.className = "toast";
    node.textContent = (type === "success" ? "✓ " : "") + message;
    document.body.appendChild(node);
    setTimeout(() => node.remove(), 2800);
  };
  function hydrateUser() {
    const user = demoUser();
    document.querySelectorAll("[data-user-name]").forEach(x => x.textContent = user.name);
    document.querySelectorAll("[data-user-role]").forEach(x => x.textContent = user.role === "patient" ? "Patient portal" : "Clinical workspace");
    document.querySelectorAll("[data-avatar]").forEach(x => x.textContent = initials(user.name));
  }
  function setupNav() {
    const toggle = document.querySelector("[data-menu]");
    const side = document.querySelector(".sidebar");
    if (toggle && side) toggle.addEventListener("click", () => side.classList.toggle("open"));
    const path = location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".nav a").forEach(link => {
      if (link.getAttribute("href") === "./" + path || (path === "" && link.getAttribute("href") === "./index.html")) link.classList.add("active");
    });
    document.querySelectorAll("[data-logout]").forEach(x => x.addEventListener("click", e => {
      e.preventDefault(); localStorage.removeItem("dentiflowUser"); location.href = "./login.html";
    }));
  }
  function setupSearch() {
    const input = document.querySelector("[data-search]");
    if (!input) return;
    input.addEventListener("input", () => {
      const query = input.value.toLowerCase();
      document.querySelectorAll("[data-searchable]").forEach(row => { row.hidden = query && !row.textContent.toLowerCase().includes(query); });
    });
  }
  function setupLogin() {
    const form = document.querySelector("[data-login]");
    if (!form) return;
    const role = form.querySelector("[name=role]");
    document.querySelectorAll("[data-demo-role]").forEach(btn => btn.addEventListener("click", () => {
      const chosen = btn.dataset.demoRole;
      localStorage.setItem("dentiflowUser", JSON.stringify({ name: chosen === "patient" ? "Aravind Menon" : "Dr. Ananya Sharma", role: chosen }));
      location.href = chosen === "patient" ? "./patient-dashboard.html" : "./dashboard.html";
    }));
    form.addEventListener("submit", e => {
      e.preventDefault();
      const selected = form.querySelector("input[name=role]:checked")?.value || "doctor";
      localStorage.setItem("dentiflowUser", JSON.stringify({ name: selected === "patient" ? "Aravind Menon" : "Dr. Ananya Sharma", role: selected }));
      location.href = selected === "patient" ? "./patient-dashboard.html" : "./dashboard.html";
    });
    if (role) role.addEventListener("change", () => {});
  }
  function setupActions() {
    document.querySelectorAll("[data-toast]").forEach(x => x.addEventListener("click", () => toast(x.dataset.toast, "success")));
    document.querySelectorAll("[data-modal]").forEach(btn => btn.addEventListener("click", () => {
      const modal = document.getElementById(btn.dataset.modal); if (modal) modal.hidden = false;
    }));
    document.querySelectorAll("[data-close-modal]").forEach(btn => btn.addEventListener("click", () => btn.closest(".modal-backdrop").hidden = true));
    document.querySelectorAll("form[data-action]").forEach(form => form.addEventListener("submit", e => {
      e.preventDefault(); toast(form.dataset.action || "Saved to this browser", "success"); form.reset();
    }));
  }
  function setupPayment() {
    document.querySelectorAll("[data-payment]").forEach(form => form.addEventListener("submit", e => {
      e.preventDefault(); const amount = form.querySelector("input").value || "0";
      localStorage.setItem("dentiflowPayment", JSON.stringify({ amount, date: new Date().toLocaleDateString("en-IN") }));
      toast("Payment of ₹" + Number(amount).toLocaleString("en-IN") + " recorded"); form.reset();
    }));
  }
  function setupProfile() {
    const input = document.querySelector("[data-photo]");
    if (!input) return;
    const preview = document.querySelector("[data-photo-preview]");
    const saved = localStorage.getItem("dentiflowPhoto"); if (saved && preview) preview.src = saved;
    input.addEventListener("change", () => {
      const file = input.files[0]; if (!file) return;
      const reader = new FileReader(); reader.onload = () => { localStorage.setItem("dentiflowPhoto", reader.result); if (preview) preview.src = reader.result; toast("Profile photo saved"); }; reader.readAsDataURL(file);
    });
  }
  function setupChart() {
    const chart = document.querySelector("[data-dental-chart]"); if (!chart) return;
    const defaultStates = { "16": "cavity", "26": "filling", "36": "watch", "46": "crown" };
    const states = JSON.parse(localStorage.getItem("dentiflowTeeth") || JSON.stringify(defaultStates));
    const detail = document.querySelector("[data-tooth-detail]");
    function paint(tooth) {
      tooth.dataset.state = states[tooth.dataset.tooth] || "healthy";
      tooth.classList.toggle("selected", detail && detail.dataset.selected === tooth.dataset.tooth);
    }
    chart.querySelectorAll(".tooth").forEach(tooth => {
      paint(tooth);
      tooth.addEventListener("click", () => {
        const number = tooth.dataset.tooth; if (detail) { detail.dataset.selected = number; detail.querySelector("[data-detail-number]").textContent = "Tooth #" + number; detail.querySelector("[data-detail-state]").textContent = (states[number] || "healthy").replace("-", " "); }
        chart.querySelectorAll(".tooth").forEach(paint);
      });
      tooth.addEventListener("contextmenu", e => {
        e.preventDefault(); const options = ["healthy", "watch", "cavity", "filling", "crown", "missing"];
        states[tooth.dataset.tooth] = options[(options.indexOf(states[tooth.dataset.tooth] || "healthy") + 1) % options.length];
        localStorage.setItem("dentiflowTeeth", JSON.stringify(states)); paint(tooth); toast("Tooth #" + tooth.dataset.tooth + " marked " + states[tooth.dataset.tooth]);
      });
    });
    const reset = document.querySelector("[data-reset-chart]");
    if (reset) reset.addEventListener("click", () => { localStorage.removeItem("dentiflowTeeth"); location.reload(); });
  }
  document.addEventListener("DOMContentLoaded", () => { hydrateUser(); setupNav(); setupSearch(); setupLogin(); setupActions(); setupPayment(); setupProfile(); setupChart(); });
})();
