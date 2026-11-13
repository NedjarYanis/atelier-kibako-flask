/**
 * Atelier Kibako — Assistant visuel de configuration MariaDB / SQLite (/setup)
 */
(function () {
  const tabs = document.querySelectorAll(".setup-tab");
  const modePanels = document.querySelectorAll(".setup-mode-panel");
  const testBtn = document.getElementById("setup-test-btn");
  const saveBtn = document.getElementById("setup-save-btn");
  const togglePwdBtn = document.getElementById("toggle-password-btn");
  const pwdInput = document.getElementById("db-password");
  const diagBox = document.getElementById("setup-diagnostic");

  let activeMode = "fields";

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      activeMode = tab.dataset.mode;
      tabs.forEach((t) => t.classList.toggle("active", t === tab));
      modePanels.forEach((p) => {
        p.style.display = p.dataset.modePanel === activeMode ? "block" : "none";
      });
      hideDiagnostic();
    });
  });

  if (togglePwdBtn && pwdInput) {
    togglePwdBtn.addEventListener("click", () => {
      const isHidden = pwdInput.type === "password";
      pwdInput.type = isHidden ? "text" : "password";
      togglePwdBtn.textContent = isHidden ? "Masquer" : "Afficher";
    });
  }

  function hideDiagnostic() {
    if (!diagBox) return;
    diagBox.className = "diagnostic-box";
    diagBox.innerHTML = "";
  }

  function showDiagnostic(ok, html) {
    if (!diagBox) return;
    diagBox.className = `diagnostic-box show ${ok ? "ok" : "err"}`;
    diagBox.innerHTML = html;
  }

  function collectPayload() {
    const seedDemo = document.getElementById("seed-demo-checkbox")?.checked ?? true;
    if (activeMode === "sqlite") {
      return { mode: "sqlite", seed_demo: seedDemo };
    }
    if (activeMode === "uri") {
      return {
        mode: "uri",
        uri: document.getElementById("db-uri")?.value || "",
        seed_demo: seedDemo,
      };
    }
    return {
      mode: "fields",
      host: document.getElementById("db-host")?.value || "127.0.0.1",
      port: document.getElementById("db-port")?.value || "3306",
      database: document.getElementById("db-name")?.value || "atelier_kibako",
      user: document.getElementById("db-user")?.value || "root",
      password: document.getElementById("db-password")?.value || "",
      seed_demo: seedDemo,
    };
  }

  if (testBtn) {
    testBtn.addEventListener("click", async () => {
      testBtn.disabled = true;
      testBtn.textContent = "Test en cours…";
      try {
        const res = await fetch("/api/setup/test-db", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(collectPayload()),
        });
        const data = await res.json();
        if (data.ok) {
          showDiagnostic(
            true,
            `<strong>Connexion réussie (${data.dialect})</strong><br>
             Version : <span class="mono">${data.version}</span> · Latence : <span class="mono">${data.latency_ms} ms</span><br>
             ${data.message || ""}`
          );
        } else {
          showDiagnostic(
            false,
            `<strong>Échec de connexion</strong><br>
             Détail : <span class="mono">${data.error || "Erreur inconnue"}</span><br>
             <em>Conseil :</em> ${data.advice || ""}`
          );
        }
      } catch (err) {
        showDiagnostic(false, `<strong>Erreur réseau :</strong> ${err.message}`);
      } finally {
        testBtn.disabled = false;
        testBtn.textContent = "Tester la connexion";
      }
    });
  }

  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      saveBtn.disabled = true;
      saveBtn.textContent = "Initialisation ORM…";
      try {
        const res = await fetch("/api/setup/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(collectPayload()),
        });
        const data = await res.json();
        if (data.ok) {
          showDiagnostic(
            true,
            `<strong>${data.message}</strong><br>
             Mode actif : <span class="mono">${data.db_mode}</span> · URI : <span class="mono">${data.masked_uri}</span><br>
             Catalogue initialisé : ${data.categories_created} catégorie(s) et ${data.products_created} boîte(s) à musique ajoutée(s).<br>
             <a href="/catalogue" style="text-decoration:underline;font-weight:700;">Découvrir le catalogue →</a>`
          );
        } else {
          showDiagnostic(
            false,
            `<strong>Erreur d'initialisation</strong><br>
             Détail : <span class="mono">${data.error || "Erreur inconnue"}</span><br>
             <em>Conseil :</em> ${data.advice || ""}`
          );
        }
      } catch (err) {
        showDiagnostic(false, `<strong>Erreur réseau :</strong> ${err.message}`);
      } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = "Sauvegarder & Initialiser l'ORM";
      }
    });
  }
})();
