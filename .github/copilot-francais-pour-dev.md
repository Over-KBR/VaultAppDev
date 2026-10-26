# Guide de développement VaultApp (français)

Ce document explique en français le fonctionnement du dépôt et complète les instructions officielles de Copilot, qui se trouvent dans [`copilot-instructions.md`](./copilot-instructions.md). Il est destiné aux développeurs et aux futures sessions Copilot.

## Vue d'ensemble

VaultApp est un gestionnaire de mots de passe Windows composé de deux applications qui coopèrent :

1. une application de bureau Python avec interface CustomTkinter ;
2. une extension Chrome/Firefox qui demande à l'application de remplir les identifiants du site courant.

L'application de bureau conserve les données dans une base SQLite locale et expose une petite API Flask sur `127.0.0.1:27842`. L'extension ne communique qu'avec cette API locale.

## Commandes utiles

Depuis la racine du dépôt, se placer dans `Application/` :

```powershell
cd Application
```

Installer les dépendances déclarées :

```powershell
python -m pip install -r requirements.txt
```

Lancer tous les tests :

```powershell
python -m pytest tests\ -v
```

Lancer un seul test :

```powershell
python -m pytest tests\test_unit.py::TestCrypto::test_encrypt_decrypt_roundtrip -v
```

Sélectionner les tests par mot-clé :

```powershell
python -m pytest tests\test_unit.py -k generate_password -v
```

Lancer l'application depuis les sources :

```powershell
python main.py
```

Lancer l'application en mode debug sans demander de mot de passe maître :

```powershell
python main.py --debug
```

Ou, sous Windows, double-cliquer sur `Application/run_debug.bat` pour ouvrir une console dédiée qui reste visible après la fermeture.

Ce mode crée un coffre fictif dans un dossier temporaire, l'ouvre directement et supprime les données à la fermeture. Il n'utilise pas la base réelle, ne démarre pas l'API destinée à l'extension et désactive les copies dans le presse-papiers. La console annonce chaque clic, décrit ce qui est attendu, affiche l'écran après le clic et imprime la trace des erreurs Tkinter non interceptées. Les erreurs déjà présentées par l'application restent également visibles dans ses boîtes de dialogue ou notifications. Des comptes d'exemple permettent de tester l'audit, les doublons, la recherche, les catégories, l'historique et les formulaires. Dans les paramètres, le mot de passe maître initial fictif est `debug-only`.

Construire l'exécutable Windows :

```powershell
python build.py
```

`build.py` lance d'abord toute la suite `tests/`, puis utilise PyInstaller pour créer `dist/VaultApp.exe`. `installer.iss`, compilé avec Inno Setup depuis `Application/`, s'attend à trouver cet exécutable. Il n'y a pas actuellement de configuration de lint ou de formatage séparée.

## Parcours de l'application

### Démarrage et navigation

- `Application/main.py` crée `src.ui.app.VaultApp`.
- Au démarrage, `VaultApp` initialise la base et la table d'historique, charge le thème enregistré, puis démarre le serveur Flask avant le déverrouillage. Tant que le coffre est verrouillé, l'API connaît l'état verrouillé mais ne possède pas la clé.
- L'utilisateur passe par l'écran d'accueil, puis par l'écran de connexion/création (`welcome_screen.py`, `login_screen.py`). Après déverrouillage, `main_screen.py` affiche les comptes et les catégories.
- Le verrouillage automatique est réglé dans les paramètres, vaut cinq minutes par défaut, et est réinitialisé par les événements souris/clavier. Le verrouillage retire la clé de l'API.
- L'écran principal contient une liste filtrable de comptes, une vue Favoris, les catégories, un audit de sécurité et l'accès aux paramètres.

### Modules et responsabilités

- `src/ui/` : fenêtre, écrans, dialogues et widgets CustomTkinter.
- `src/ui/theme.py` : couleurs sombre/clair, polices, dimensions et gestionnaire de thème partagé.
- `src/models.py` : dataclasses `Account` et `Category`, ainsi que les palettes/icônes de catégorie.
- `src/database.py` : schéma SQLite, migration des colonnes, accès aux comptes/catégories/paramètres et changement de mot de passe maître.
- `src/crypto.py` : dérivation de clé, vérification du mot de passe maître et chiffrement/déchiffrement.
- `src/history.py` : anciennes versions de mots de passe chiffrées.
- `src/generator.py` et `src/strength.py` : génération et analyse de la force des mots de passe, calcul du score du coffre.
- `src/clipboard.py` : copie dans le presse-papiers avec effacement programmé.
- `src/vault_io.py` : sauvegarde chiffrée et import remplaçant les comptes/catégories.
- `src/api.py` : serveur Flask utilisé par l'extension.
- `Extension/` : interface popup, script de remplissage, service worker et manifeste Chrome.

## Stockage et chiffrement

- Le fichier de base est `%APPDATA%\VaultApp\vault.db`. Si `APPDATA` n'est pas défini, le répertoire personnel sert de base au chemin. Chaque connexion active WAL et les clés étrangères.
- Au premier lancement, un sel aléatoire et une valeur de vérification dérivée du mot de passe maître sont enregistrés dans la table `config`. Les catégories par défaut sont également créées.
- La clé est dérivée par PBKDF2-HMAC-SHA256 avec 600 000 itérations, une clé de 32 octets et un sel de 16 octets.
- Chaque valeur chiffrée utilise AES-GCM et un nonce aléatoire de 12 octets.
- Les mots de passe, notes et secrets TOTP des comptes sont chiffrés dans SQLite. Les noms, logins, URL, métadonnées de catégories et paramètres ne le sont pas : ne pas supposer que l'ensemble de la base est chiffré.
- Les tests utilisent `tmp_db` et `db_with_data` dans `tests/conftest.py`. Ces fixtures redirigent la base vers un fichier temporaire et initialisent les tables requises. Ne jamais faire pointer les tests vers le coffre réel de `%APPDATA%`.

### Changement du mot de passe maître

Le changement de mot de passe maître est une opération dépendante de la clé : le sel, la valeur de vérification, la clé dérivée et toutes les données chiffrées doivent rester cohérents. La fonction `database.change_master_password()` opère dans une transaction SQLite avec rollback en cas d'échec. Lors d'une évolution de ce flux, examiner chaque table chiffrée, notamment `accounts` et `password_history`, puis compléter les tests pertinents.

## Historique, audit et presse-papiers

- `password_history` conserve au maximum trois anciennes versions par compte. Une modification du compte ajoute l'ancien mot de passe uniquement si le mot de passe a changé ; la suppression du compte supprime aussi son historique grâce à la clé étrangère.
- L'audit du tableau de bord (`dashboard_screen.py`) signale les mots de passe faibles, réutilisés et inchangés depuis plus de 180 jours. Le score est calculé par `calculate_vault_score()` dans `strength.py`.
- `zxcvbn` est utilisé si disponible ; un score heuristique de secours est prévu sinon.
- Le générateur s'appuie sur `secrets` et assure la présence d'au moins un caractère de chaque groupe activé.
- `src/totp.py` génère localement des codes RFC 6238 à six chiffres, valables 30 secondes. Les secrets Base32 sont chiffrés dans SQLite, migrés lors de l'initialisation et préservés dans les exports `.vault` ainsi que lors du changement de mot de passe maître. Ils ne doivent jamais être renvoyés par l'API navigateur.
- Le délai d'effacement du presse-papiers est réglable sur 15, 30 ou 60 secondes. Il s'applique aux mots de passe et aux identifiants copiés depuis la liste ou le formulaire.
- Un compte peut conserver une clé TOTP Base32. Le code à six chiffres reste affiché au maximum jusqu'à son expiration, sa copie est automatiquement effacée du presse-papiers au plus tard à cette échéance, et le mode debug bloque la copie comme pour les mots de passe.
- Les exports `.vault` ont l'en-tête `VAULT2` et contiennent un JSON chiffré avec AES-GCM. L'import remplace les comptes et catégories ; les paramètres et les informations du mot de passe maître ne sont pas dans l'export.
- L'état Favori est une métadonnée SQLite associée au compte et fait partie de l'export chiffré `.vault`. Toute nouvelle colonne doit être ajoutée via une migration non destructive dans `init_database()` et couverte par un test d'import/export.

## Contrat entre l'application et l'extension

L'API est définie dans `Application/src/api.py` et l'interface de l'extension se trouve surtout dans `Extension/popup.js` et `Extension/content.js`.

- `GET /status` indique que l'application tourne et si elle est déverrouillée.
- `GET /accounts?url=...` exige un coffre déverrouillé et retourne les comptes associés au domaine sans leurs mots de passe.
- `POST /fill` reçoit un `account_id`, exige un coffre déverrouillé et retourne le login et le mot de passe du compte sélectionné.
- Le popup récupère l'URL de l'onglet actif, demande les comptes correspondants, puis envoie les identifiants obtenus à `content.js`.
- Le script de contenu cherche les champs de mot de passe visibles, tente de trouver un champ login associé, puis déclenche des événements DOM pour les frameworks de formulaires courants.
- L'API écoute sur `127.0.0.1:27842`. Les réponses CORS autorisent les origines d'extensions Chrome/Mozilla. CORS n'est pas une authentification et ne bloque pas un client local non navigateur.
- `/fill` n'est pas à usage unique dans le code actuel et ne vide pas de tampon après la réponse.

Toute modification d'endpoint, de format JSON, d'origine CORS, d'hôte/port, de permissions ou du comportement de remplissage doit être vérifiée des deux côtés. L'API et l'extension forment une seule frontière fonctionnelle et de sécurité.

La correspondance d'une URL de compte doit comparer les noms d'hôte sur des frontières de domaine, et non chercher une simple sous-chaîne (pour éviter les domaines ressemblants). Une URL de compte vide reste volontairement valable pour tous les sites.

## Manifests et validation navigateur

- `Extension/manifest.json` est le manifeste Chrome Manifest V3.
- `Extension/manifest_firefox.json` est le manifeste Firefox Manifest V2, avec des chemins d'icônes relatifs au dossier `Extension/`. Il existe également un `manifest.json` dupliqué à la racine ; privilégier les manifests situés dans `Extension/`.
- Les tests automatisés couvrent surtout la crypto, SQLite/CRUD, l'historique, l'import/export, les scores de sécurité et les tests de régression/import. Ils ne pilotent pas l'interface graphique ni l'extension dans un navigateur ; après une modification de ces surfaces, faire un test manuel.

## Conventions de travail propres au dépôt

- Pour les données, passer par les fonctions de `src/database.py` plutôt que d'ajouter des accès SQLite dispersés.
- Garder synchronisés les contrats `Application/src/api.py`, `Extension/popup.js` et `Extension/content.js`.
- Conserver la comparaison de domaine avec frontières : `example.com` ne doit pas correspondre à `notexample.com`.
- Ne pas inclure de mot de passe dans `/accounts` : le mot de passe ne doit être demandé qu'après sélection par `/fill`.
- Toute évolution du chiffrement doit préserver les données existantes, le format de sauvegarde `VAULT2` et les chemins de changement du mot de passe maître.
- Pour l'interface, réutiliser le thème commun et les widgets existants ; les formulaires et dialogues sont des fenêtres CustomTkinter.
- Lors d'un changement de comportement, compléter les tests Python concernés et faire un contrôle manuel de l'interface ou du navigateur si ces composants sont touchés.

## Documentation de référence

- [`Extension/README.md`](../Extension/README.md) : installation et utilisation de l'extension.
- [`Application/build.py`](../Application/build.py) : tests préalables et création de l'exécutable.
- [`Application/tests/`](../Application/tests/) : couverture automatisée disponible.
