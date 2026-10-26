/**
 * background.js — Service Worker VaultApp (Manifest V3)
 *
 * Rôle minimal : écouter les événements de navigation pour
 * mettre à jour le badge de l'extension si besoin.
 *
 * Dans Manifest V3, le service worker est dormant la plupart du temps
 * et se réveille sur événement. Il ne peut pas garder de state persistant
 * (utiliser chrome.storage pour ça si nécessaire).
 */

// Écouter l'installation de l'extension
chrome.runtime.onInstalled.addListener(() => {
  console.log("VaultApp Extension installée.");
});

// Optionnel : écouter les messages du popup ou du content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Réservé pour des extensions futures (ex: notifications)
  sendResponse({ ok: true });
  return true;
});
