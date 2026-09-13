/* DentiFlow static demo with Cloud Firestore Integration */
(function () {
  const FIREBASE_CONFIG = {
    apiKey: "AIzaSyBXk4zldg-m666vYri2j33YPnqi0cSfrEU",
    authDomain: "dentiflow-clinic.firebaseapp.com",
    projectId: "dentiflow-clinic",
    storageBucket: "dentiflow-clinic.firebasestorage.app",
    messagingSenderId: "617678572443",
    appId: "1:617678572443:web:1801ad76cea68d733baf3e",
    measurementId: "G-YR6NYPGXSM"
  };

  let firestoreDb = null;
  async function initFirebase() {
    try {
      const { initializeApp } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js");
      const { getFirestore, doc, setDoc } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js");
      const app = initializeApp(FIREBASE_CONFIG);
      firestoreDb = getFirestore(app);
      window._firestoreDb = firestoreDb;
      window._setDoc = setDoc;
      window._doc = doc;
      console.log("🔥 [DentiFlow GitHub Pages] Cloud Firestore initialized.");
    } catch (e) {
      console.warn("Firestore client init:", e);
    }
  }
  initFirebase();

  async function syncFirestore(collection, id, data) {
    try {
      if (window._firestoreDb && window._doc && window._setDoc) {
        await window._setDoc(window._doc(window._firestoreDb, collection, String(id)), {
          ...data,
          updated_at: new Date().toISOString()
        }, { merge: true });
        console.log(`🔥 [Firestore] Synced ${collection}/${id}`);
      }
    } catch (err) {
      console.warn("Firestore write error:", err);
    }
  }

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
    
    // Sync current session to Firestore
    syncFirestore("users", user.name.replace(/[^a-zA-Z0-9]/g, '_'), {
      name: user.name,
      role: user.role,
      last_sign_in: new Date().toISOString()
    });
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
      const userObj = { name: chosen === "patient" ? "Aravind Menon" : "Dr. Ananya Sharma", role: chosen };
      localStorage.setItem("dentiflowUser", JSON.stringify(userObj));
      syncFirestore("login_history", `sign_${Date.now()}`, {
        name: userObj.name,
        role: userObj.role,
        action: `Demo sign-in (${chosen})`
      });
      location.href = chosen === "patient" ? "./patient-dashboard.html" : "./dashboard.html";
    }));
    form.addEventListener("submit", e => {
      e.preventDefault();
      const selected = form.querySelector("input[name=role]:checked")?.value || "doctor";
      const userObj = { name: selected === "patient" ? "Aravind Menon" : "Dr. Ananya Sharma", role: selected };
      localStorage.setItem("dentiflowUser", JSON.stringify(userObj));
      syncFirestore("login_history", `sign_${Date.now()}`, {
        name: userObj.name,
        role: userObj.role,
        action: `User sign-in (${selected})`
      });
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
    document.querySelectorAll("form[data-action]").forEach(form => form.addEventListener("submit", async e => {
      e.preventDefault();
      const actionName = form.dataset.action || "Saved";
      const formData = new FormData(form);
      const payload = Object.fromEntries(formData.entries());
      
      // If it's a patient form, sync to Firestore
      if (payload.name || payload.patient_name) {
        const ptName = payload.name || payload.patient_name;
        const ptId = `DF-${Date.now().toString().slice(-4)}`;
        await syncFirestore("patients", ptId, {
          name: ptName,
          patient_id: ptId,
          phone: payload.phone || "",
          email: payload.email || "",
          primary_doctor_name: payload.doctor || "Dr. Ananya Sharma"
        });
      }

      toast(actionName + " & Synced to Cloud Firestore", "success");
      form.reset();
      const modal = form.closest(".modal-backdrop");
      if (modal) modal.hidden = true;
    }));
  }

  function setupPayment() {
    document.querySelectorAll("[data-payment]").forEach(form => form.addEventListener("submit", async e => {
      e.preventDefault();
      const amount = form.querySelector("input").value || "0";
      localStorage.setItem("dentiflowPayment", JSON.stringify({ amount, date: new Date().toLocaleDateString("en-IN") }));
      
      await syncFirestore("invoices", `INV_${Date.now()}`, {
        amount: Number(amount),
        date: new Date().toISOString(),
        status: "Paid"
      });

      toast("Payment of ₹" + Number(amount).toLocaleString("en-IN") + " recorded & synced to Firestore", "success");
      form.reset();
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
