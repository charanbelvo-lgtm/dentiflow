/* DentiFlow static demo: all data intentionally lives in localStorage. */
(function () {
  const demoUser = () => {
    try {
      const path = (location.pathname.split("/").pop() || "").toLowerCase();
      const raw = localStorage.getItem("dentiflowUser");
      if (raw) {
        const u = JSON.parse(raw);
        if (u && u.role) return u;
      }
      if (path.includes("patient-dashboard")) {
        const pat = { name: "Ashwini Goud", role: "patient", email: "budigeashwinigoud@gmail.com" };
        localStorage.setItem("dentiflowUser", JSON.stringify(pat));
        return pat;
      }
      if (path.includes("admin-dashboard")) {
        const adm = { name: "Dr. Rajesh Verma", role: "admin", email: "admin@dentiflow.com" };
        localStorage.setItem("dentiflowUser", JSON.stringify(adm));
        return adm;
      }
      return { name: "Dr. Ananya Sharma", role: "doctor", email: "doctor@dentiflow.com" };
    } catch (e) {
      return { name: "Dr. Ananya Sharma", role: "doctor", email: "doctor@dentiflow.com" };
    }
  };

  const initials = name => {
    if (!name) return "DF";
    const clean = name.replace(/^Dr\.?\s+/i, "").trim();
    const parts = clean.split(/\s+/).filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    if (parts.length === 1 && parts[0].length >= 2) return parts[0].slice(0, 2).toUpperCase();
    return (name.slice(0, 2) || "DF").toUpperCase();
  };

  function formatNameFromEmail(email) {
    if (!email || !email.includes("@")) return "";
    const prefix = email.split("@")[0];
    return prefix
      .split(/[._-]+/)
      .filter(Boolean)
      .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join(" ");
  }

  window.toast = function (message, type) {
    const node = document.createElement("div");
    node.className = "toast";
    node.textContent = (type === "success" ? "✓ " : "") + message;
    document.body.appendChild(node);
    setTimeout(() => node.remove(), 2800);
  };

  const DEFAULT_APPOINTMENTS = [
    {
      id: "APT-001",
      time: "09:00",
      patientName: "Aravind Menon",
      patientContact: "+91 98450 11223",
      patientEmail: "aravind@dentiflow.com",
      doctor: "Dr. Ananya Sharma",
      category: "Root canal review",
      chair: "Chair 01",
      status: "In progress",
      isTreating: true,
      token: "#01",
      waitTime: "Now in chair",
      fee: 6500,
      paymentMethod: "UPI",
      paymentStatus: "Paid (Online)",
      date: "2026-05-27"
    },
    {
      id: "APT-002",
      time: "10:30",
      patientName: "Vishal Rao",
      patientContact: "+91 98450 33445",
      patientEmail: "vishal@dentiflow.com",
      doctor: "Dr. Rohan Patel",
      category: "Scaling follow-up",
      chair: "Chair 02",
      status: "Checked in",
      isTreating: false,
      token: "#02",
      waitTime: "12 mins",
      fee: 1500,
      paymentMethod: "Card",
      paymentStatus: "Paid (Online)",
      date: "2026-05-27"
    },
    {
      id: "APT-003",
      time: "12:00",
      patientName: "Medha Iyer",
      patientContact: "+91 98450 55667",
      patientEmail: "medha@dentiflow.com",
      doctor: "Dr. Meera Nair",
      category: "Pediatric consultation",
      chair: "Chair 03",
      status: "Waiting",
      isTreating: false,
      token: "#03",
      waitTime: "30 mins",
      fee: 500,
      paymentMethod: "UPI",
      paymentStatus: "Paid (Online)",
      date: "2026-05-27"
    },
    {
      id: "APT-004",
      time: "14:15",
      patientName: "Sameer Khan",
      patientContact: "+91 98450 77889",
      patientEmail: "sameer@dentiflow.com",
      doctor: "Dr. Vikram Rao",
      category: "Dental Implants Evaluation",
      chair: "Chair 01",
      status: "Waiting",
      isTreating: false,
      token: "#04",
      waitTime: "50 mins",
      fee: 2500,
      paymentMethod: "Clinic",
      paymentStatus: "Pay at clinic",
      date: "2026-05-27"
    }
  ];

  function getAppointments() {
    const raw = localStorage.getItem("dentiflowAppointments");
    if (!raw) {
      localStorage.setItem("dentiflowAppointments", JSON.stringify(DEFAULT_APPOINTMENTS));
      return DEFAULT_APPOINTMENTS.slice();
    }
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) && parsed.length ? parsed : DEFAULT_APPOINTMENTS.slice();
    } catch (e) {
      return DEFAULT_APPOINTMENTS.slice();
    }
  }

  function saveAppointments(list) {
    localStorage.setItem("dentiflowAppointments", JSON.stringify(list));
  }

  function hydrateUser() {
    const user = demoUser();
    const role = user.role || "doctor";
    document.documentElement.className = "role-" + role;
    document.body.classList.remove("role-doctor", "role-patient", "role-admin", "role-reception");
    document.body.classList.add("role-" + role);
    document.body.setAttribute("data-active-role", role);

    const path = (location.pathname.split("/").pop() || "index.html").toLowerCase();
    const doctorPages = [
      "dashboard.html", "admin-dashboard.html", "clinical.html", "dental-chart.html",
      "treatment-plans.html", "patients.html", "patient-detail.html",
      "billing.html", "inventory.html", "reports.html"
    ];
    if (role === "patient" && doctorPages.includes(path)) {
      location.replace("./patient-dashboard.html");
      return;
    }

    document.querySelectorAll("[data-user-name]").forEach(x => {
      if (x !== document.body) x.textContent = user.name;
    });
    document.querySelectorAll("span[data-user-role], div[data-user-role], [data-role-label]").forEach(x => {
      if (x !== document.body) {
        x.textContent = role === "patient" ? "Patient portal" : (role === "admin" ? "Admin workspace" : (role === "reception" ? "Reception desk" : "Clinical workspace"));
      }
    });
    document.querySelectorAll("[data-avatar]").forEach(x => {
      if (x !== document.body) x.textContent = initials(user.name);
    });

    filterSidebarByRole(role);
  }

  function filterSidebarByRole(role) {
    if (role === "patient") {
      const forbiddenTerms = [
        "clinical", "dental-chart", "chart", "treatment-plans", "treatment_plans",
        "patients", "patient-detail", "billing", "inventory", "reports"
      ];

      // Aggressively remove any clinical/practice links
      document.querySelectorAll(".sidebar .nav a, .sidebar a, .doctor-only, [data-role*='doctor'], [data-role*='admin']").forEach(link => {
        if (link.dataset && link.dataset.role === "patient") return;
        const href = (link.getAttribute("href") || "").toLowerCase();
        const text = (link.textContent || "").toLowerCase();

        const isForbidden = link.classList.contains("doctor-only") ||
                            link.getAttribute("data-role")?.includes("doctor") ||
                            link.getAttribute("data-role")?.includes("admin") ||
                            forbiddenTerms.some(term => href.includes(term) || text.includes(term)) ||
                            (href.includes("dashboard.html") && !href.includes("patient-dashboard"));

        if (isForbidden) {
          link.remove();
        }
      });

      // Nav labels: strictly keep only "Patient Workspace" and "Settings"
      document.querySelectorAll(".sidebar .nav-label").forEach((lbl) => {
        const text = (lbl.textContent || "").toLowerCase();
        if (text.includes("patient")) {
          lbl.textContent = "Patient Workspace";
          lbl.setAttribute("data-role", "patient");
        } else if (text.includes("setting")) {
          lbl.textContent = "Settings";
          lbl.setAttribute("data-role", "patient");
        } else if (text.includes("practice") || text.includes("admin") || text.includes("clinical") || text.includes("workspace")) {
          lbl.remove();
        }
      });

      // Remove bottom switcher
      document.querySelectorAll(".sidebar-bottom a").forEach(link => {
        const text = (link.textContent || "").toLowerCase();
        if (text.includes("patient view") || text.includes("doctor view")) {
          link.remove();
        }
      });

      // Ensure Book & Wait Time link exists in nav
      const nav = document.querySelector(".sidebar .nav");
      if (nav && !nav.querySelector('a[href*="patient-dashboard"]')) {
        const bookLink = document.createElement("a");
        bookLink.href = "./patient-dashboard.html";
        bookLink.setAttribute("data-role", "patient");
        bookLink.innerHTML = "<span>Book &amp; Wait Time</span>";
        if (location.pathname.includes("patient-dashboard")) bookLink.classList.add("active");
        const firstLabel = nav.querySelector(".nav-label");
        if (firstLabel && firstLabel.nextSibling) {
          nav.insertBefore(bookLink, firstLabel.nextSibling);
        } else {
          nav.prepend(bookLink);
        }
      }
    }
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
    // Switch to patient mode when clicking "Patient view"
    document.querySelectorAll('a[href*="patient-dashboard.html"]').forEach(link => {
      link.addEventListener("click", () => {
        localStorage.setItem("dentiflowUser", JSON.stringify({
          name: "Ashwini Goud",
          role: "patient",
          email: "budigeashwinigoud@gmail.com"
        }));
      });
    });
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

    // Seed default registered demo users if not present
    try {
      let registered = JSON.parse(localStorage.getItem("dentiflowRegisteredUsers") || "[]");
      const defaults = [
        { email: "doctor@dentiflow.com", name: "Dr. Ananya Sharma", role: "doctor" },
        { email: "admin@dentiflow.com", name: "Dr. Rajesh Verma", role: "admin" },
        { email: "budigeashwinigoud@gmail.com", name: "Ashwini Goud", role: "patient" },
        { email: "patient@dentiflow.com", name: "Ashwini Goud", role: "patient" },
        { email: "reception@dentiflow.com", name: "Pooja Hegde", role: "reception" }
      ];
      defaults.forEach(d => {
        if (!registered.some(r => r.email.toLowerCase() === d.email.toLowerCase())) {
          registered.push(d);
        }
      });
      localStorage.setItem("dentiflowRegisteredUsers", JSON.stringify(registered));
    } catch (e) {}

    let currentMode = "signup"; // Default: FIRST ASK TO CREATE ACCOUNT
    const tabSignIn = document.getElementById("tab-btn-signin");
    const tabSignUp = document.getElementById("tab-btn-signup");
    const eyebrow = document.getElementById("auth-eyebrow");
    const title = document.getElementById("auth-title");
    const subtitle = document.getElementById("auth-subtitle");
    const submitBtn = document.getElementById("auth-submit-btn");
    const demoSection = document.getElementById("demo-login-section");
    const switchPrompt = document.getElementById("auth-switch-prompt");
    const switchLink = document.getElementById("auth-switch-link");
    const nameLabel = document.getElementById("auth-name-label");
    const nameInput = form.querySelector("[name=name]");
    const emailInput = form.querySelector("[name=email], input[type=email]");
    const phoneField = document.getElementById("signup-phone-field");
    const phoneInput = form.querySelector("[name=phone]");
    const passwordInput = form.querySelector("[name=password]");
    const confirmField = document.getElementById("signup-confirm-field");
    const confirmInput = form.querySelector("[name=confirm_password]");
    const termsField = document.getElementById("signup-terms-field");
    const termsCheckbox = document.getElementById("auth-terms-checkbox");
    const roleRadios = form.querySelectorAll("input[name=role]");

    function setMode(mode) {
      currentMode = mode;
      const isSignup = mode === "signup";

      if (tabSignUp) {
        tabSignUp.classList.toggle("active", isSignup);
        tabSignUp.setAttribute("aria-selected", isSignup ? "true" : "false");
      }
      if (tabSignIn) {
        tabSignIn.classList.toggle("active", !isSignup);
        tabSignIn.setAttribute("aria-selected", !isSignup ? "true" : "false");
      }

      if (eyebrow) eyebrow.textContent = isSignup ? "FIRST TIME USER?" : "WELCOME BACK";
      if (title) title.textContent = isSignup ? "Create an Account" : "Sign in to DentiFlow";
      if (subtitle) subtitle.textContent = isSignup 
        ? "Please create your account first to access your DentiFlow workspace." 
        : "Enter your registered credentials to sign in.";

      if (nameLabel) nameLabel.textContent = isSignup ? "Full Name *" : "Your name";
      if (nameInput) {
        nameInput.required = isSignup;
        nameInput.placeholder = isSignup ? "Enter your full name" : "Your name";
      }

      if (phoneField) phoneField.style.display = isSignup ? "block" : "none";
      if (phoneInput) phoneInput.required = isSignup;

      if (confirmField) confirmField.style.display = isSignup ? "block" : "none";
      if (confirmInput) confirmInput.required = isSignup;

      if (termsField) termsField.style.display = isSignup ? "block" : "none";
      if (demoSection) demoSection.style.display = isSignup ? "none" : "block";

      if (submitBtn) submitBtn.textContent = isSignup ? "Create Account & Continue →" : "Sign in →";

      if (switchPrompt) {
        switchPrompt.innerHTML = isSignup
          ? 'Already have an account? <a href="#" id="auth-switch-link" style="color:var(--blue);font-weight:600;">Sign in here</a>'
          : 'First time user? <a href="#" id="auth-switch-link" style="color:var(--blue);font-weight:600;">Create an account first</a>';
        const newLink = document.getElementById("auth-switch-link");
        if (newLink) {
          newLink.addEventListener("click", e => {
            e.preventDefault();
            setMode(currentMode === "signup" ? "signin" : "signup");
          });
        }
      }

      updateRoleHints();
    }

    if (tabSignIn) tabSignIn.addEventListener("click", () => setMode("signin"));
    if (tabSignUp) tabSignUp.addEventListener("click", () => setMode("signup"));
    if (switchLink) {
      switchLink.addEventListener("click", e => {
        e.preventDefault();
        setMode(currentMode === "signup" ? "signin" : "signup");
      });
    }

    // Check URL query and hash (e.g. ?mode=signin or #signin)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("mode") === "signin" || window.location.hash === "#signin") {
      setMode("signin");
    } else {
      setMode("signup"); // Default to Create Account first!
    }

    function updateRoleHints() {
      const selectedRole = form.querySelector("input[name=role]:checked")?.value || "doctor";
      if (nameInput && currentMode === "signin") {
        if (selectedRole === "patient") {
          nameInput.placeholder = "Ashwini Goud (Patient)";
        } else if (selectedRole === "admin") {
          nameInput.placeholder = "Dr. Rajesh Verma (Admin)";
        } else {
          nameInput.placeholder = "Dr. Ananya Sharma (Doctor)";
        }
      }
      if (emailInput && !emailInput.value) {
        if (selectedRole === "patient") {
          emailInput.placeholder = "budigeashwinigoud@gmail.com";
        } else if (selectedRole === "admin") {
          emailInput.placeholder = "admin@dentiflow.com";
        } else {
          emailInput.placeholder = "doctor@dentiflow.com";
        }
      }
    }

    roleRadios.forEach(r => r.addEventListener("change", updateRoleHints));
    updateRoleHints();

    document.querySelectorAll("[data-demo-role]").forEach(btn => btn.addEventListener("click", () => {
      const chosen = btn.dataset.demoRole;
      let user = { role: chosen };
      if (chosen === "patient") {
        user.name = "Ashwini Goud";
        user.email = "budigeashwinigoud@gmail.com";
      } else if (chosen === "admin") {
        user.name = "Dr. Rajesh Verma";
        user.email = "admin@dentiflow.com";
      } else if (chosen === "reception") {
        user.name = "Pooja Hegde";
        user.email = "reception@dentiflow.com";
      } else {
        user.name = "Dr. Ananya Sharma";
        user.email = "doctor@dentiflow.com";
      }
      localStorage.setItem("dentiflowUser", JSON.stringify(user));
      location.href = chosen === "patient" ? "./patient-dashboard.html" : (chosen === "admin" ? "./admin-dashboard.html" : "./dashboard.html");
    }));

    form.addEventListener("submit", e => {
      e.preventDefault();
      const selectedRole = form.querySelector("input[name=role]:checked")?.value || "doctor";
      const nameVal = nameInput?.value.trim();
      const emailVal = emailInput?.value.trim();
      const passVal = passwordInput?.value;
      const phoneVal = phoneInput?.value.trim();

      if (currentMode === "signup") {
        if (!nameVal) {
          toast("Please enter your full name", "error");
          nameInput?.focus();
          return;
        }
        if (!emailVal || !emailVal.includes("@")) {
          toast("Please enter a valid email address", "error");
          emailInput?.focus();
          return;
        }
        if (!passVal || passVal.length < 4) {
          toast("Password must be at least 4 characters", "error");
          passwordInput?.focus();
          return;
        }
        const confirmVal = confirmInput?.value;
        if (passVal !== confirmVal) {
          toast("Passwords do not match. Please verify.", "error");
          confirmInput?.focus();
          return;
        }
        if (termsCheckbox && !termsCheckbox.checked) {
          toast("Please accept the terms of service to continue", "error");
          return;
        }

        let displayName = nameVal;
        if ((selectedRole === "doctor" || selectedRole === "admin") && !/^dr\.?\s+/i.test(displayName)) {
          displayName = "Dr. " + displayName;
        }

        const newUser = {
          name: displayName,
          role: selectedRole,
          email: emailVal,
          phone: phoneVal || "+91 98765 43210",
          createdAt: new Date().toISOString()
        };

        // Save to current session
        localStorage.setItem("dentiflowUser", JSON.stringify(newUser));

        // Save to registered users list in localStorage
        try {
          const registered = JSON.parse(localStorage.getItem("dentiflowRegisteredUsers") || "[]");
          const existingIdx = registered.findIndex(u => u.email && u.email.toLowerCase() === emailVal.toLowerCase());
          if (existingIdx >= 0) {
            registered[existingIdx] = newUser;
          } else {
            registered.push(newUser);
          }
          localStorage.setItem("dentiflowRegisteredUsers", JSON.stringify(registered));
        } catch (err) {
          // ignore
        }

        toast(`Welcome to DentiFlow, ${displayName}! Your ${selectedRole} account has been created.`, "success");
        setTimeout(() => {
          location.href = selectedRole === "patient" ? "./patient-dashboard.html" : (selectedRole === "admin" ? "./admin-dashboard.html" : "./dashboard.html");
        }, 300);
        return;
      }

      // Sign In mode: verify that account exists first!
      const registered = JSON.parse(localStorage.getItem("dentiflowRegisteredUsers") || "[]");
      const foundUser = registered.find(u => u.email && u.email.toLowerCase() === (emailVal || "").toLowerCase());

      if (!foundUser && !emailVal.endsWith("@dentiflow.com")) {
        toast("No account found for this email. Please create an account first!", "error");
        setMode("signup");
        if (emailInput) emailInput.value = emailVal;
        if (nameInput) setTimeout(() => nameInput.focus(), 100);
        return;
      }

      let displayName = foundUser?.name || nameVal;
      if (!displayName && emailVal) {
        displayName = formatNameFromEmail(emailVal);
      }
      if (!displayName) {
        displayName = selectedRole === "patient" ? "Ashwini Goud" : (selectedRole === "admin" ? "Dr. Rajesh Verma" : "Dr. Ananya Sharma");
      } else if ((selectedRole === "doctor" || selectedRole === "admin") && !/^dr\.?\s+/i.test(displayName)) {
        displayName = "Dr. " + displayName;
      }

      const user = {
        name: displayName,
        role: foundUser?.role || selectedRole,
        email: emailVal
      };

      localStorage.setItem("dentiflowUser", JSON.stringify(user));
      toast(`Welcome back, ${displayName}!`, "success");
      setTimeout(() => {
        location.href = user.role === "patient" ? "./patient-dashboard.html" : (user.role === "admin" ? "./admin-dashboard.html" : "./dashboard.html");
      }, 300);
    });
  }

  function openModal(modalId) {
    const modal = typeof modalId === "string" ? document.getElementById(modalId) : modalId;
    if (!modal) return;
    modal.hidden = false;
    modal.style.display = "grid";
    const user = demoUser();
    const nameField = modal.querySelector("#book-patient-name");
    const phoneField = modal.querySelector("#book-patient-phone");
    if (nameField && (!nameField.value || nameField.value === "Ashwini Goud" || nameField.value === "Dr. Ananya Sharma")) {
      nameField.value = user.name;
    }
    if (phoneField && (!phoneField.value || phoneField.value.includes("@"))) {
      phoneField.value = user.email || "+91 98765 43210";
    }
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.hidden = true;
    modal.style.display = "none";
  }

  function playClinicChime() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      if (ctx.state === "suspended") {
        ctx.resume();
      }
      // Melodic clinic chime chord: C5 (523.25Hz), E5 (659.25Hz), G5 (783.99Hz)
      const notes = [523.25, 659.25, 783.99];
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        const startTime = ctx.currentTime + idx * 0.14;
        osc.frequency.setValueAtTime(freq, startTime);
        gain.gain.setValueAtTime(0.0001, startTime);
        gain.gain.exponentialRampToValueAtTime(0.28, startTime + 0.03);
        gain.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.42);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(startTime);
        osc.stop(startTime + 0.48);
      });
    } catch (e) {
      console.warn("Chime audio context error:", e);
    }
  }

  function callPatientToChair(aptId) {
    let list = getAppointments();
    const apt = list.find(a => a.id === aptId);
    if (!apt) return;

    // Previous patient in that chair is completed
    list.forEach(a => {
      if (a.chair === apt.chair && a.id !== apt.id && a.isTreating) {
        a.isTreating = false;
        a.status = "Completed";
      }
    });

    apt.status = "In progress";
    apt.isTreating = true;
    saveAppointments(list);

    // Audio chime sound
    playClinicChime();

    // Prominent toast notification
    toast(`📢 Calling ${apt.patientName} to ${apt.chair} (${apt.doctor})! Patient alerted on queue display.`, "success");

    renderAppointmentsAndQueue();
  }

  function completePatientVisit(aptId) {
    let list = getAppointments();
    const apt = list.find(a => a.id === aptId);
    if (!apt) return;

    apt.status = "Completed";
    apt.isTreating = false;
    saveAppointments(list);

    toast(`✓ Visit completed for ${apt.patientName}! ${apt.chair} is sanitized & available.`, "success");

    renderAppointmentsAndQueue();
  }

  function setupActions() {
    document.querySelectorAll("[data-toast]").forEach(x => x.addEventListener("click", () => toast(x.dataset.toast, "success")));
    document.querySelectorAll("[data-modal]").forEach(btn => btn.addEventListener("click", e => {
      e.preventDefault();
      openModal(btn.dataset.modal);
    }));
    document.querySelectorAll("[data-close-modal]").forEach(btn => btn.addEventListener("click", e => {
      e.preventDefault();
      closeModal(btn.closest(".modal-backdrop"));
    }));
    document.querySelectorAll(".modal-backdrop").forEach(backdrop => {
      backdrop.addEventListener("click", e => {
        if (e.target === backdrop) closeModal(backdrop);
      });
    });
    document.addEventListener("keydown", e => {
      if (e.key === "Escape") {
        document.querySelectorAll(".modal-backdrop").forEach(closeModal);
      }
    });
    if (location.search.includes("book=1") || location.hash === "#book") {
      openModal("app-modal");
    }
    document.querySelectorAll("form[data-action]").forEach(form => form.addEventListener("submit", e => {
      e.preventDefault(); toast(form.dataset.action || "Saved to this browser", "success"); form.reset();
    }));

    // Global action delegator for Queue & Appointments
    document.addEventListener("click", e => {
      const callBtn = e.target.closest("[data-action='call-patient']");
      if (callBtn) {
        e.preventDefault();
        callPatientToChair(callBtn.dataset.id);
        return;
      }
      const completeBtn = e.target.closest("[data-action='complete-patient']");
      if (completeBtn) {
        e.preventDefault();
        completePatientVisit(completeBtn.dataset.id);
        return;
      }
      const completeTreatingBtn = e.target.closest("[data-action='complete-current-treating']");
      if (completeTreatingBtn) {
        e.preventDefault();
        const list = getAppointments();
        const treating = list.find(a => a.isTreating) || list.find(a => a.status === "In progress") || list[0];
        if (treating) {
          completePatientVisit(treating.id);
        } else {
          toast("No patient currently in procedure", "info");
        }
        return;
      }
      const refreshBtn = e.target.closest("[data-action='refresh-queue']");
      if (refreshBtn) {
        e.preventDefault();
        renderAppointmentsAndQueue();
        toast("Appointment schedule & queue refreshed", "success");
        return;
      }
    });
  }

  function setupPayment() {
    document.querySelectorAll("[data-payment]").forEach(form => form.addEventListener("submit", e => {
      e.preventDefault(); const amount = form.querySelector("input").value || "0";
      localStorage.setItem("dentiflowPayment", JSON.stringify({ amount, date: new Date().toLocaleDateString("en-IN") }));
      toast("Payment of ₹" + Number(amount).toLocaleString("en-IN") + " recorded"); form.reset();
    }));
  }

  function setupAppointmentBooking() {
    const forms = document.querySelectorAll("#booking-form");
    if (!forms.length) return;

    forms.forEach(form => {
      // Doctor selection highlight
      form.querySelectorAll(".doc-card").forEach(card => {
        card.addEventListener("click", () => {
          form.querySelectorAll(".doc-card").forEach(c => c.classList.remove("selected"));
          card.classList.add("selected");
          const radio = card.querySelector("input[type=radio]");
          if (radio) radio.checked = true;
        });
      });

      // Category selection & price calculation
      function updateBill() {
        const checkedCat = form.querySelector('input[name="category"]:checked');
        const price = Number(checkedCat?.dataset.price || 500);
        const name = checkedCat?.value || "Consultation & Diagnosis";
        const sanitization = 100;
        const tax = Math.round(price * 0.05);
        const total = price + sanitization + tax;

        const nameEl = form.querySelector("#bill-procedure-name");
        const priceEl = form.querySelector("#bill-procedure-price");
        const taxEl = form.querySelector("#bill-tax");
        const totalEl = form.querySelector("#bill-total-price");
        const submitBtn = form.querySelector("#btn-confirm-booking");

        if (nameEl) nameEl.textContent = name;
        if (priceEl) priceEl.textContent = "₹" + price.toLocaleString("en-IN");
        if (taxEl) taxEl.textContent = "₹" + tax.toLocaleString("en-IN");
        if (totalEl) totalEl.textContent = "₹" + total.toLocaleString("en-IN");

        const method = form.querySelector('input[name="paymentMethod"]:checked')?.value || "UPI";
        if (submitBtn) {
          if (method === "Clinic") {
            submitBtn.textContent = `Confirm Booking (Pay ₹${total.toLocaleString("en-IN")} at Clinic)`;
          } else {
            submitBtn.textContent = `Pay ₹${total.toLocaleString("en-IN")} & Confirm Appointment`;
          }
        }
      }

      form.querySelectorAll(".category-card").forEach(card => {
        card.addEventListener("click", () => {
          form.querySelectorAll(".category-card").forEach(c => c.classList.remove("selected"));
          card.classList.add("selected");
          const radio = card.querySelector("input[type=radio]");
          if (radio) radio.checked = true;
          updateBill();
        });
      });

      // Payment method change
      form.querySelectorAll('input[name="paymentMethod"]').forEach(radio => {
        radio.addEventListener("change", () => {
          const val = radio.value;
          const upiGroup = form.querySelector("#upi-input-group");
          const cardGroup = form.querySelector("#card-input-group");
          if (upiGroup) upiGroup.style.display = val === "UPI" ? "block" : "none";
          if (cardGroup) cardGroup.style.display = val === "Card" ? "block" : "none";
          updateBill();
        });
      });

      // Initial bill update
      updateBill();

      // Form submission
      form.addEventListener("submit", e => {
        e.preventDefault();
        const user = demoUser();
        const patientName = form.querySelector("#book-patient-name")?.value.trim() || user.name;
        const patientContact = form.querySelector("#book-patient-phone")?.value.trim() || user.email || "+91 98765 43210";
        const doctor = form.querySelector('input[name="doctor"]:checked')?.value || "Dr. Ananya Sharma";
        const categoryInput = form.querySelector('input[name="category"]:checked');
        const category = categoryInput?.value || "Consultation & Diagnosis";
        const basePrice = Number(categoryInput?.dataset.price || 500);
        const total = basePrice + 100 + Math.round(basePrice * 0.05);
        const date = form.querySelector("#book-date")?.value || "2026-05-27";
        const time = form.querySelector("#book-time")?.value || "10:30";
        const paymentMethod = form.querySelector('input[name="paymentMethod"]:checked')?.value || "UPI";
        const isClinicPay = paymentMethod === "Clinic";

        const list = getAppointments();
        const tokenNum = list.length + 1;
        const chair = doctor.includes("Patel") ? "Chair 02" : (doctor.includes("Nair") ? "Chair 03" : "Chair 01");
        const waitMins = Math.max(15, (tokenNum - 1) * 15);

        const newAppointment = {
          id: "APT-" + Date.now().toString().slice(-4),
          time: time,
          patientName: patientName,
          patientContact: patientContact,
          patientEmail: (user.role === "patient" && user.email) ? user.email : (patientName.toLowerCase().replace(/[^a-z0-9]/g, "") + "@gmail.com"),
          doctor: doctor,
          category: category,
          chair: chair,
          status: "Checked in",
          isTreating: false,
          token: "#" + String(tokenNum).padStart(2, "0"),
          waitTime: waitMins + " mins",
          fee: total,
          paymentMethod: paymentMethod,
          paymentStatus: isClinicPay ? "Pay at clinic" : `Paid (${paymentMethod})`,
          date: date
        };

        // If user is patient, add to front of waiting queue (index 1) so it is immediately active
        if (user.role === "patient") {
          newAppointment.waitTime = "15 mins";
          newAppointment.token = "#02";
          list.splice(1, 0, newAppointment);
        } else {
          list.push(newAppointment);
        }

        saveAppointments(list);

        // Record payment in localStorage
        localStorage.setItem("dentiflowPayment", JSON.stringify({
          amount: total,
          method: paymentMethod,
          date: new Date().toLocaleDateString("en-IN"),
          appointmentId: newAppointment.id
        }));

        // Close modal
        document.querySelectorAll(".modal-backdrop").forEach(closeModal);

        // Show confirmation toast
        const payMsg = isClinicPay ? "Appointment confirmed! Pay at clinic counter." : `Appointment booked & payment of ₹${total.toLocaleString("en-IN")} confirmed!`;
        toast(payMsg, "success");

        // Re-render views
        renderAppointmentsAndQueue();
      });
    });

    document.querySelectorAll("[data-book-doctor]").forEach(btn => {
      btn.addEventListener("click", () => {
        const docName = btn.dataset.bookDoctor;
        openModal("app-modal");
        if (docName) {
          const radio = document.querySelector(`input[name="doctor"][value="${docName}"]`);
          if (radio) {
            radio.checked = true;
            document.querySelectorAll("#doctor-options-container .doc-card").forEach(c => c.classList.remove("selected"));
            radio.closest(".doc-card")?.classList.add("selected");
          }
        }
      });
    });
  }

  function renderAppointmentsAndQueue() {
    const user = demoUser();
    let list = getAppointments();

    // 1. Patient view logic
    const patientContainer = document.getElementById("patient-view-container");
    const doctorContainer = document.getElementById("doctor-view-container");

    if (patientContainer && doctorContainer) {
      if (user.role === "patient") {
        patientContainer.style.display = "block";
        doctorContainer.style.display = "none";

        const titleEl = document.getElementById("page-title");
        const subEl = document.getElementById("page-subtitle");
        const eyebrowEl = document.getElementById("page-eyebrow");
        if (titleEl) titleEl.textContent = "My Appointments & Queue";
        if (subEl) subEl.textContent = "Track your scheduled visit, assigned doctor, and live waiting time.";
        if (eyebrowEl) eyebrowEl.textContent = "PERSONAL CARE QUEUE";

        // Filter appointments strictly for this patient
        let patientApts = list.filter(a =>
          a.patientName.toLowerCase() === user.name.toLowerCase() ||
          (user.email && a.patientEmail && a.patientEmail.toLowerCase() === user.email.toLowerCase())
        );

        // If newly logged in patient has no appointment yet, create one so they see their details immediately
        if (patientApts.length === 0) {
          const initialApt = {
            id: "APT-1029",
            time: "10:30",
            patientName: user.name,
            patientContact: user.email || "+91 98765 43210",
            patientEmail: user.email || (user.name.toLowerCase().replace(/[^a-z0-9]/g, "") + "@gmail.com"),
            doctor: "Dr. Ananya Sharma",
            category: "Root canal review",
            chair: "Chair 01",
            status: "Checked in",
            isTreating: false,
            token: "#02",
            waitTime: "15 mins",
            fee: 6500,
            paymentMethod: "UPI",
            paymentStatus: "Paid (Online)",
            date: "2026-05-27"
          };
          list.splice(1, 0, initialApt);
          saveAppointments(list);
          patientApts = [initialApt];
        }

        const activeApt = patientApts[0];

        // Update Wait Time Banner
        const waitTitle = document.getElementById("patient-wait-title");
        const waitSub = document.getElementById("patient-wait-subtitle");
        const tokenEl = document.getElementById("patient-token");
        const waitTimeEl = document.getElementById("patient-wait-time");
        const docNameEl = document.getElementById("patient-doc-name");
        const chairEl = document.getElementById("patient-chair");
        const countEl = document.getElementById("patient-apt-count");

        if (waitTitle) waitTitle.textContent = `Estimated Wait Time: ${activeApt.waitTime || "15 mins"}`;
        if (waitSub) waitSub.textContent = `Your appointment for ${activeApt.category} is scheduled with ${activeApt.doctor}. 1 patient is currently in chair ahead of you.`;
        if (tokenEl) tokenEl.textContent = activeApt.token || "#02";
        if (waitTimeEl) waitTimeEl.textContent = `~${activeApt.waitTime || "15 mins"}`;
        if (docNameEl) docNameEl.textContent = activeApt.doctor;
        if (chairEl) chairEl.textContent = activeApt.chair || "Chair 01";
        if (countEl) countEl.textContent = `${patientApts.length} Scheduled`;

        // Render Patient's Table ONLY
        const tbody = document.getElementById("patient-appointments-tbody");
        if (tbody) {
          tbody.innerHTML = patientApts.map(apt => `
            <tr>
              <td><b>${apt.time}</b> &bull; ${apt.date}</td>
              <td><b>${apt.category}</b></td>
              <td>${apt.doctor}</td>
              <td><span class="pill">${apt.chair}</span></td>
              <td><span class="pill ${apt.paymentStatus.includes('Paid') ? 'green' : 'orange'}">${apt.paymentStatus}</span></td>
              <td><span class="pill ${apt.status === 'In progress' ? 'green' : 'orange'}">${apt.status} (${apt.token})</span></td>
              <td><button class="btn btn-soft" data-toast="Reschedule request sent to reception">Reschedule</button></td>
            </tr>
          `).join("");
        }

      } else {
        // DOCTOR / STAFF VIEW
        patientContainer.style.display = "none";
        doctorContainer.style.display = "block";

        const titleEl = document.getElementById("page-title");
        const subEl = document.getElementById("page-subtitle");
        const eyebrowEl = document.getElementById("page-eyebrow");
        if (titleEl) titleEl.textContent = "Appointments";
        if (subEl) subEl.textContent = "Coordinate every chair, clinician, and patient.";
        if (eyebrowEl) eyebrowEl.textContent = "SCHEDULE & QUEUE";

        const treating = list.find(a => a.isTreating) || list.find(a => a.status === "In progress");
        const nowTreatingName = document.getElementById("now-treating-name");
        const nowTreatingDetails = document.getElementById("now-treating-details");
        if (nowTreatingName) {
          nowTreatingName.innerHTML = treating 
            ? `${treating.patientName} &bull; ${treating.category}` 
            : "No active procedure &bull; Chairs available";
        }
        if (nowTreatingDetails) {
          nowTreatingDetails.textContent = treating
            ? `Patient is currently in ${treating.chair} with ${treating.doctor}. Procedure in progress (started ${treating.time} &bull; active).`
            : "All chairs are currently sanitized and ready for the next scheduled patient.";
        }

        const queueStrip = document.getElementById("queue-strip-container");
        if (queueStrip) {
          const waitingList = list.filter(a => !a.isTreating && a.status !== "Completed");
          let chipsHtml = `<span class="queue-member-chip" style="background:rgba(255,255,255,.28);font-weight:700;">Now: ${treating ? treating.patientName : 'Chair Open'}</span>`;
          if (waitingList.length > 0) {
            chipsHtml += `<span class="queue-member-chip">Next: ${waitingList[0].patientName} (${waitingList[0].token} &bull; ${waitingList[0].waitTime})</span>`;
          }
          if (waitingList.length > 1) {
            chipsHtml += `<span class="queue-member-chip">Queued: ${waitingList[1].patientName} (${waitingList[1].token} &bull; ${waitingList[1].waitTime})</span>`;
          }
          if (waitingList.length > 2) {
            chipsHtml += `<span class="queue-member-chip">+${waitingList.length - 2} more in queue</span>`;
          }
          queueStrip.innerHTML = chipsHtml;
        }

        const queueCount = list.filter(a => a.status !== "Completed").length;
        const queueCountEl = document.getElementById("doc-queue-count");
        const badgeEl = document.getElementById("live-members-badge");
        const headlineEl = document.getElementById("doctor-queue-headline");
        if (queueCountEl) queueCountEl.textContent = queueCount;
        if (badgeEl) badgeEl.textContent = `${queueCount} members in queue`;
        if (headlineEl) headlineEl.textContent = `Showing all scheduled and queue patients (${queueCount} currently waiting)`;

        // Render Doctor Table
        const tbody = document.getElementById("doctor-appointments-tbody");
        if (tbody) {
          tbody.innerHTML = list.map(apt => `
            <tr data-apt-id="${apt.id}">
              <td><b>${apt.time}</b></td>
              <td class="patient">
                <span class="avatar">${initials(apt.patientName)}</span>
                ${apt.patientName}
              </td>
              <td>${apt.category}</td>
              <td>${apt.doctor}</td>
              <td><b>${apt.chair}</b></td>
              <td><span class="pill ${apt.paymentStatus.includes('Paid') ? 'green' : 'orange'}">${apt.paymentStatus}</span></td>
              <td><span class="pill ${apt.status === 'In progress' ? 'green' : (apt.status === 'Checked in' ? 'orange' : (apt.status === 'Completed' ? 'blue' : ''))}">${apt.status}</span></td>
              <td>
                ${apt.status === 'In progress'
                  ? `<button class="btn btn-primary" data-action="complete-patient" data-id="${apt.id}" style="padding:6px 14px;font-size:13px;font-weight:600;">✓ Complete</button>`
                  : (apt.status === 'Completed'
                    ? `<span class="pill green" style="padding:6px 12px;font-size:12px;font-weight:600;">Done ✓</span>`
                    : `<button class="btn btn-soft" data-action="call-patient" data-id="${apt.id}" style="padding:6px 14px;font-size:13px;font-weight:600;color:var(--blue);">Call patient</button>`
                  )
                }
              </td>
            </tr>
          `).join("");
        }
      }
    }

    // 2. Patient dashboard sync
    const dashWaitBadge = document.getElementById("patient-dash-wait");
    const dashProc = document.getElementById("patient-dash-proc");
    const dashMeta = document.getElementById("patient-dash-meta");
    const heroDesc = document.getElementById("patient-hero-desc");
    if (dashWaitBadge || dashProc) {
      const patientApts = list.filter(a =>
        a.patientName.toLowerCase() === user.name.toLowerCase() ||
        (user.email && a.patientEmail && a.patientEmail.toLowerCase() === user.email.toLowerCase())
      );
      const active = patientApts[0] || list[1] || list[0];
      if (dashWaitBadge) dashWaitBadge.textContent = `⏱ ${active.waitTime || "15 mins"} wait • Token ${active.token || "#02"}`;
      if (dashProc) dashProc.textContent = active.category;
      if (dashMeta) dashMeta.innerHTML = `${active.date} &bull; ${active.time}<br>DentiFlow Care &bull; ${active.chair}`;
      if (heroDesc) heroDesc.textContent = `${active.category} with ${active.doctor} • Thursday, ${active.date} at ${active.time} (Est. Wait: ${active.waitTime || "15 mins"}).`;

      const patientTable = document.getElementById("patient-appointments-list");
      if (patientTable) {
        const displayApts = patientApts.length ? patientApts : [active];
        patientTable.innerHTML = displayApts.map(apt => `
          <tr>
            <td><b>${apt.token || "#02"}</b></td>
            <td><b>${apt.doctor}</b></td>
            <td>${apt.category}</td>
            <td>${apt.date} &bull; ${apt.time}</td>
            <td><span class="pill orange">⏱ ${apt.waitTime || "15 mins"}</span></td>
            <td><span class="pill green">${apt.status || "In Waiting Lounge"}</span></td>
            <td><span class="pill ${apt.paymentStatus && apt.paymentStatus.includes('Paid') ? 'green' : 'orange'}">${apt.paymentStatus || 'Paid (Online)'}</span></td>
          </tr>
        `).join("");
      }
    }

    // 3. Doctor Dashboard sync
    const dashNowTreating = document.getElementById("dash-now-treating-patient");
    const dashWaitingCount = document.getElementById("dash-waiting-count");
    const dashLiveQueuePill = document.getElementById("dash-live-queue-pill");
    const dashQueueList = document.getElementById("dash-live-queue-list");
    if (dashNowTreating || dashWaitingCount) {
      const treating = list.find(a => a.isTreating) || list[0];
      const waitingMembers = list.filter(a => a.status !== "Completed");
      if (dashNowTreating && treating) {
        dashNowTreating.innerHTML = `${treating.patientName} &bull; ${treating.category}`;
      }
      if (dashWaitingCount) dashWaitingCount.textContent = waitingMembers.length;
      if (dashLiveQueuePill) dashLiveQueuePill.textContent = `${waitingMembers.length} waiting`;
      if (dashQueueList) {
        dashQueueList.innerHTML = waitingMembers.slice(0, 4).map((apt, idx) => `
          <div class="row between" style="padding:12px 0;border-bottom:1px solid var(--line)">
            <span>
              <b>${apt.token || ('0' + (idx + 1))}</b> - ${apt.patientName}<br>
              <small class="muted">${apt.isTreating ? `Now in ${apt.chair} with ${apt.doctor}` : `${apt.waitTime} &bull; ${apt.chair}`}</small>
            </span>
            <span class="pill ${apt.isTreating ? 'green' : (idx === 1 ? 'orange' : '')}">${apt.isTreating ? 'Now Treating' : (idx === 1 ? 'Next' : 'Waiting')}</span>
          </div>
        `).join("");
      }
    }
  }

  function setupClinical() {
    const params = new URLSearchParams(window.location.search);
    const patientParam = params.get("patient");
    const select = document.getElementById("clinical-patient-select");
    const alertBox = document.getElementById("patient-note-alert");
    const badge = document.getElementById("selected-patient-badge");
    const subjective = document.getElementById("clinical-subjective");

    if (patientParam && select) {
      let found = false;
      for (let i = 0; i < select.options.length; i++) {
        if (select.options[i].value.toLowerCase().includes(patientParam.toLowerCase()) ||
            select.options[i].text.toLowerCase().includes(patientParam.toLowerCase())) {
          select.selectedIndex = i;
          found = true;
          break;
        }
      }
      if (!found) {
        const opt = new Option(`${patientParam} • DF-2026-006 (Current Queue)`, patientParam, true, true);
        select.add(opt);
      }
      if (alertBox) {
        alertBox.style.display = "block";
        if (badge) badge.textContent = patientParam;
      }
      if (subjective) {
        setTimeout(() => subjective.focus(), 150);
      }
    }
  }

  function setupProfile() {
    const user = demoUser();
    const profileForm = document.querySelector("form[data-action]");
    if (profileForm) {
      const inputs = profileForm.querySelectorAll("input");
      if (inputs.length >= 3) {
        if (user.name) inputs[0].value = user.name;
        if (user.role) inputs[1].value = user.role === "patient" ? "Patient" : (user.role === "admin" ? "Practice Director" : (user.role === "reception" ? "Front Desk Executive" : "Chief Dental Surgeon"));
        if (user.email) inputs[2].value = user.email;
      }
      profileForm.addEventListener("submit", () => {
        const newName = inputs[0]?.value.trim();
        const newRole = inputs[1]?.value.trim();
        const newEmail = inputs[2]?.value.trim();
        if (newName) {
          const updated = { ...user, name: newName };
          if (newEmail) updated.email = newEmail;
          localStorage.setItem("dentiflowUser", JSON.stringify(updated));
          hydrateUser();
          renderAppointmentsAndQueue();
        }
      });
    }

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
        toast("Profile photo saved");
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
          detail.querySelector("[data-detail-number]").textContent = "Tooth #" + number;
          detail.querySelector("[data-detail-state]").textContent = (states[number] || "healthy").replace("-", " ");
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
    setupLogin();
    setupActions();
    setupPayment();
    setupAppointmentBooking();
    renderAppointmentsAndQueue();
    setupClinical();
    setupProfile();
    setupChart();
  });
})();
