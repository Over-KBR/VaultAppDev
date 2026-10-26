# VaultApp — Extension navigateur

## Prérequis

- VaultApp doit être **lancée et déverrouillée** sur ton PC pour que l'extension fonctionne.
- L'API Flask démarre automatiquement avec VaultApp sur le port `27842`.

---

## Installation Chrome

1. Ouvre Chrome et va sur `chrome://extensions/`
2. Active le **Mode développeur** (interrupteur en haut à droite)
3. Clique sur **Charger l'extension non empaquetée**
4. Sélectionne le dossier `extension/` (celui qui contient `manifest.json`)
5. L'icône 🔐 apparaît dans ta barre d'outils

---

## Installation Firefox

1. Dans le dossier `extension/`, **renomme** `manifest_firefox.json` en `manifest.json`
   (remplace le manifest Chrome)
2. Ouvre Firefox et va sur `about:debugging`
3. Clique sur **Ce Firefox** puis **Charger un module complémentaire temporaire**
4. Sélectionne le fichier `manifest.json` du dossier `extension/`

> ⚠️ En Firefox, l'extension temporaire est supprimée à la fermeture du navigateur.
> Pour une installation permanente, il faudrait signer l'extension sur addons.mozilla.org.

---

## Utilisation

1. Lance **VaultApp.exe** et déverrouille-toi avec ton mot de passe maître
2. Va sur un site (ex: github.com)
3. Clique sur l'icône 🔐 dans la barre d'outils
4. L'extension affiche les comptes enregistrés pour ce site
5. Clique **Remplir** — les champs login et mot de passe sont remplis automatiquement

---

## Ajouter les icônes

Le dossier `extension/icons/` doit contenir :
- `icon16.png` (16×16 px)
- `icon48.png` (48×48 px)
- `icon128.png` (128×128 px)

Tu peux exporter le logo de VaultApp (`assets/logo.ico`) en PNG aux bons formats
avec un outil comme [CloudConvert](https://cloudconvert.com) ou Paint.

---

## Architecture

```
Navigateur (Extension)
        │
        │  HTTP GET /status
        │  HTTP GET /accounts?url=...
        │  HTTP POST /fill
        ▼
API Flask locale (127.0.0.1:27842)   ← src/api.py
        │
        ▼
VaultApp (Base SQLite chiffrée)
```

La communication reste **locale** (localhost uniquement).
Les mots de passe ne transitent pas sur le réseau.
