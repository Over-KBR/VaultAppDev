/**
 * popup.js — Logique du popup VaultApp
 *
 * Au clic sur l'icône dans le navigateur :
 * 1. Récupère le domaine de l'onglet actif
 * 2. Ping /status pour voir si VaultApp est lancée et déverrouillée
 * 3. Si OK, appelle /accounts?url=... pour lister les comptes du site
 * 4. Au clic sur "Remplir", appelle /fill pour obtenir login+mdp
 *    puis envoie un message au content script pour injecter dans la page
 */

const API = "http://127.0.0.1:27842";

// ── Utilitaires UI ────────────────────────────────────────────

function showState(id) {
  document.querySelectorAll(".state").forEach(el => el.classList.remove("active"));
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function showToast(message, durationMs = 2000) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), durationMs);
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ── Fetch avec timeout ────────────────────────────────────────

async function fetchWithTimeout(url, options = {}, timeoutMs = 3000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timer);
    return res;
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}

// ── Rendu de la liste des comptes ─────────────────────────────

function renderAccounts(accounts, tabId) {
  const container = document.getElementById("accounts-items");
  const list = document.getElementById("accounts-list");
  const label = document.getElementById("accounts-label");
  const footer = document.getElementById("footer");

  container.innerHTML = "";

  if (accounts.length === 0) {
    showState("state-empty");
    footer.style.display = "block";
    return;
  }

  label.textContent = accounts.length === 1
    ? "1 compte disponible"
    : `${accounts.length} comptes disponibles`;

  list.classList.add("active");
  footer.style.display = "block";

  accounts.forEach(account => {
    const item = document.createElement("div");
    item.className = "account-item";

    // Couleur de fond de l'icône
    const bgColor = hexToRgba(account.category_color || "#7c5cfc", 0.15);

    item.innerHTML = `
      <div class="account-icon" style="background:${bgColor}">
        ${account.category_icon || "🔑"}
      </div>
      <div class="account-info">
        <div class="account-name">${escapeHtml(account.name)}</div>
        <div class="account-login">${escapeHtml(account.login || "Pas de login")}</div>
      </div>
      <button class="fill-btn" data-id="${account.id}">Remplir</button>
    `;

    // Clic sur "Remplir"
    item.querySelector(".fill-btn").addEventListener("click", async (e) => {
      e.stopPropagation();
      await fillAccount(account.id, tabId);
    });

    // Clic sur la ligne = remplir aussi
    item.addEventListener("click", async () => {
      await fillAccount(account.id, tabId);
    });

    container.appendChild(item);
  });
}

// ── Remplissage d'un compte ───────────────────────────────────

async function fillAccount(accountId, tabId) {
  try {
    const res = await fetchWithTimeout(`${API}/fill`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_id: accountId }),
    });

    if (!res.ok) {
      showToast("❌ Erreur lors du remplissage");
      return;
    }

    const data = await res.json();

    // Envoyer au content script pour injecter dans la page
    chrome.tabs.sendMessage(tabId, {
      action: "fill_credentials",
      login: data.login,
      password: data.password,
    }, (response) => {
      if (chrome.runtime.lastError) {
        // Content script pas disponible (page spéciale, etc.)
        showToast("⚠️ Impossible de remplir sur cette page");
        return;
      }
      if (response && response.filled) {
        showToast("✅ Rempli !");
      } else {
        showToast("⚠️ Aucun champ trouvé sur la page");
      }
    });

  } catch (err) {
    showToast("❌ VaultApp ne répond plus");
  }
}

// ── Échappement HTML ──────────────────────────────────────────

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Point d'entrée ────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", async () => {

  // Récupérer l'onglet actif
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const tabUrl = tab?.url || "";
  const tabId = tab?.id;

  // Afficher le domaine
  try {
    const domain = new URL(tabUrl).hostname.replace(/^www\./, "");
    document.getElementById("current-domain").textContent = domain;
  } catch {
    document.getElementById("current-domain").textContent = "";
  }

  // Bouton "Ouvrir VaultApp" (no-op — l'app doit être lancée manuellement)
  document.getElementById("open-app-btn").addEventListener("click", () => {
    showToast("Lance VaultApp.exe sur ton PC 🖥️", 3000);
  });

  // 1. Ping /status
  let status;
  try {
    const res = await fetchWithTimeout(`${API}/status`);
    status = await res.json();
  } catch {
    showState("state-not-running");
    document.getElementById("footer").style.display = "block";
    return;
  }

  if (!status.unlocked) {
    showState("state-locked");
    document.getElementById("footer").style.display = "block";
    return;
  }

  // 2. Charger les comptes pour ce domaine
  try {
    const res = await fetchWithTimeout(`${API}/accounts?url=${encodeURIComponent(tabUrl)}`);
    const data = await res.json();

    // Cacher l'état loading
    showState("__none__");

    renderAccounts(data.accounts || [], tabId);

  } catch {
    showState("state-not-running");
    document.getElementById("footer").style.display = "block";
  }
});
