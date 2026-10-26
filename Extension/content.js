/**
 * content.js — Script injecté dans chaque page
 *
 * Écoute les messages du popup et remplit les champs login/password
 * de la page active.
 *
 * Stratégie de détection des champs :
 * 1. Cherche input[type="password"] — c'est le champ mot de passe
 * 2. Cherche le champ login "associé" : input email/text le plus proche
 *    avant le champ password dans le DOM
 */
console.log("VaultApp content script chargé !");

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "fill_credentials") {
    const filled = fillCredentials(message.login, message.password);
    sendResponse({ filled });
  }
  return true; // Garder le canal ouvert pour la réponse async
});

/**
 * Remplit les champs login et password de la page.
 * Retourne true si au moins le champ password a été rempli.
 */
function fillCredentials(login, password) {
  // Trouver tous les champs password visibles
  const passwordFields = Array.from(
    document.querySelectorAll('input[type="password"]')
  ).filter(isVisible);

  if (passwordFields.length === 0) return false;

  let filled = false;

  passwordFields.forEach(pwdField => {
    // Remplir le mot de passe
    setNativeValue(pwdField, password);
    filled = true;

    // Chercher le champ login associé
    if (login) {
      const loginField = findLoginField(pwdField);
      if (loginField) {
        setNativeValue(loginField, login);
      }
    }
  });

  return filled;
}

/**
 * Trouve le champ login le plus proche avant le champ password.
 * Stratégies dans l'ordre :
 * 1. input[type="email"] dans le même formulaire
 * 2. input[type="text"] avec attribut username/login/email/user
 * 3. Le dernier input[type="text"] ou input[type="email"] visible avant le pwd
 */
function findLoginField(passwordField) {
  // Stratégie 1 : même formulaire
  const form = passwordField.closest("form");
  if (form) {
    const emailInForm = form.querySelector('input[type="email"]');
    if (emailInForm && isVisible(emailInForm)) return emailInForm;

    const namedInputs = form.querySelectorAll(
      'input[type="text"], input[name*="user"], input[name*="login"], input[name*="email"], input[autocomplete*="username"]'
    );
    for (const input of namedInputs) {
      if (isVisible(input) && input !== passwordField) return input;
    }
  }

  // Stratégie 2 : tous les inputs visibles sur la page avant le champ pwd
  const allInputs = Array.from(
    document.querySelectorAll('input[type="text"], input[type="email"]')
  ).filter(isVisible);

  // Prendre le dernier qui apparaît avant le champ password dans le DOM
  const pwdIndex = getDocumentPosition(passwordField);
  const candidates = allInputs.filter(
    input => getDocumentPosition(input) < pwdIndex
  );

  return candidates.length > 0 ? candidates[candidates.length - 1] : null;
}

/**
 * Simule une vraie saisie utilisateur pour déclencher les événements
 * React/Vue/Angular qui écoutent onChange/onInput.
 */
function setNativeValue(element, value) {
  const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, "value"
  )?.set;

  if (nativeInputValueSetter) {
    nativeInputValueSetter.call(element, value);
  } else {
    element.value = value;
  }

  // Déclencher les événements nécessaires pour React/Vue/Angular
  element.dispatchEvent(new Event("input",  { bubbles: true }));
  element.dispatchEvent(new Event("change", { bubbles: true }));
  element.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true }));
  element.focus();
}

/**
 * Retourne true si l'élément est visible dans la page.
 */
function isVisible(element) {
  if (!element) return false;
  const style = window.getComputedStyle(element);
  return (
    style.display !== "none" &&
    style.visibility !== "hidden" &&
    style.opacity !== "0" &&
    element.offsetWidth > 0 &&
    element.offsetHeight > 0
  );
}

/**
 * Retourne la position d'un élément dans le DOM (ordre d'apparition).
 * Utilisé pour trouver le champ login qui précède le champ password.
 */
function getDocumentPosition(element) {
  const allElements = Array.from(document.querySelectorAll("*"));
  return allElements.indexOf(element);
}
