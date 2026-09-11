/* DentiFlow app script: 100% matched with original design interaction + Firebase session support */
(function () {
  const demoUser = () => window.CURRENT_USER || JSON.parse(localStorage.getItem("dentiflowUser") || '{"name":"Dr. Ananya Sharma","role":"doctor"}');
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
    document.querySelectorAll("[data-user-name]").forEach(x => {
      if (!x.textContent.trim() || x.textContent.trim() === "Dr. Ananya Sharma" || x.textContent.trim() === "Aravind Menon") {
        x.textContent = user.name;
      }
    });
    document.querySelectorAll("[data-user-role]").forEach(x => {
      if (!x.textContent.trim()) x.textContent = user.role === "patient" ? "Patient portal" : "Clinical workspace";
    });
    document.querySelectorAll("[data-avatar]").forEach(x => {
      x.textContent = initials(user.name);
    });
  }

  function setupNav() {
    const toggle = document.querySelector("[data-menu]");
    const side = document.querySelector(".sidebar");
    if (toggle && side) toggle.addEventListener("click", () => side.classList.toggle("open"));
  }

  function setupSearch() {
    const input = document.querySelector("[data-search]");
    if (!input) return;
    input.addEventListener("input", () => {
      const query = input.value.toLowerCase();
      document.querySelectorAll("[data-searchable]").forEach(row => {
        row.hidden = query && !row.textContent.toLowerCase().includes(query);
      });
    });
  }

  function setupActions() {
    document.querySelectorAll("[data-toast]").forEach(x => x.addEventListener("click", () => toast(x.dataset.toast, "success")));
    document.querySelectorAll("[data-modal]").forEach(btn => btn.addEventListener("click", () => {
      const modal = document.getElementById(btn.dataset.modal);
      if (modal) modal.hidden = false;
    }));
    document.querySelectorAll("[data-close-modal]").forEach(btn => btn.addEventListener("click", () => {
      btn.closest(".modal-backdrop").hidden = true;
    }));
    document.querySelectorAll("form[data-action]").forEach(form => form.addEventListener("submit", e => {
      e.preventDefault();
      toast(form.dataset.action || "Saved successfully", "success");
      form.reset();
    }));
  }

  function setupPayment() {
    document.querySelectorAll("[data-payment]").forEach(form => form.addEventListener("submit", e => {
      e.preventDefault();
      const amount = form.querySelector("input").value || "0";
      toast("Payment of INR " + Number(amount).toLocaleString("en-IN") + " recorded", "success");
      form.reset();
    }));
  }

  function setupProfile() {
    const input = document.querySelector("[data-photo]");
    if (!input) return;
    const preview = document.querySelector("[data-photo-preview]");
    const saved = localStorage.getItem("dentiflowPhoto");
    if (saved && preview) preview.src = saved;
    input.addEventListener("change", () => {
      const file = input.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        localStorage.setItem("dentiflowPhoto", reader.result);
        if (preview) preview.src = reader.result;
        toast("Profile photo saved", "success");
      };
      reader.readAsDataURL(file);
    });
  }

  function setupChart() {
    const chart = document.querySelector("[data-dental-chart]");
    if (!chart) return;
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
        const number = tooth.dataset.tooth;
        if (detail) {
          detail.dataset.selected = number;
          const numEl = detail.querySelector("[data-detail-number]");
          if (numEl) numEl.textContent = "Tooth #" + number;
          const stateEl = detail.querySelector("[data-detail-state]");
          if (stateEl) stateEl.textContent = (states[number] || "healthy").replace("-", " ");
        }
        chart.querySelectorAll(".tooth").forEach(paint);
      });

      tooth.addEventListener("contextmenu", e => {
        e.preventDefault();
        const options = ["healthy", "watch", "cavity", "filling", "crown", "missing"];
        states[tooth.dataset.tooth] = options[(options.indexOf(states[tooth.dataset.tooth] || "healthy") + 1) % options.length];
        localStorage.setItem("dentiflowTeeth", JSON.stringify(states));
        paint(tooth);
        toast("Tooth #" + tooth.dataset.tooth + " marked " + states[tooth.dataset.tooth]);
      });
    });

    const reset = document.querySelector("[data-reset-chart]");
    if (reset) reset.addEventListener("click", () => {
      localStorage.removeItem("dentiflowTeeth");
      location.reload();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    hydrateUser();
    setupNav();
    setupSearch();
    setupActions();
    setupPayment();
    setupProfile();
    setupChart();
  });
})();
