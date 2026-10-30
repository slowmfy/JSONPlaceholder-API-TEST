# JSONPlaceholder-API-TEST

Application Python permettant d'interagir avec l'API REST publique [JSONPlaceholder](https://jsonplaceholder.typicode.com). Cette API simule un backend typique (utilisateurs, posts, commentaires, albums, photos, tâches) et permet de s'exercer aux appels HTTP (GET, POST, PUT, PATCH, DELETE) et à la manipulation de données JSON.

L'application est multilingue (français, anglais), valide les saisies avant d'appeler l'API, journalise ses actions et gère proprement les erreurs réseau. Elle propose deux interfaces qui partagent le même code Python : un **menu console** et une **interface web Angular**.

## Fonctionnalités

| Option | Action | Requête(s) |
|---|---|---|
| 1 | Lister les utilisateurs (nom, email, ville) | `GET /users` |
| 2 | Afficher les détails d'un utilisateur | `GET /users/{id}` |
| 3 | Lister les posts d'un utilisateur | `GET /users/{id}`, `GET /posts?userId={id}` |
| 4 | Afficher les commentaires d'un post | `GET /posts/{id}`, `GET /comments?postId={id}` |
| 5 | Créer un post | `GET /users/{id}`, `POST /posts` |
| 6 | Mettre à jour un post (titre et/ou contenu) | `GET /posts/{id}`, `PUT /posts/{id}` |
| 7 | Supprimer un post (avec confirmation) | `GET /posts/{id}`, `DELETE /posts/{id}` |
| 8 | Rapport utilisateur (posts, commentaires, post le plus commenté) | `GET /users/{id}`, `GET /posts?userId={id}`, `GET /comments?postId=…` |

## Structure

```
main.py            Point d'entrée console : logs, choix de la langue, lancement du menu
menu.py            Interface console (affichage et saisies uniquement)
web_api.py         API web FastAPI utilisée par l'interface Angular
frontend/          Interface web Angular
api_client.py      JsonPlaceholderClient : tous les appels à l'API
resources.py       Description des 6 ressources (champs, validateurs, filtres)
models.py          User, Post, Comment, Album, Photo, Todo, UserReport
validators.py      Contrôle des saisies utilisateur (identifiants, textes, emails, URL)
exceptions.py      Hiérarchie d'exceptions (AppError, APIError, ValidationError…)
i18n.py            Chargement des traductions
logging_config.py  Configuration des logs et de leur rotation
config.py          Paramètres (URL, timeout, logs, limites)
locales/           Fichiers de traduction (fr.json, en.json)
tests/             Tests unitaires pytest
docs/explication.md    Lire le code sans connaître Python, explication de chaque test
docs/rapport.md        Choix d'architecture, difficultés, multilingue
docs/cas_de_tests.md   Cas de tests manuels
```

Le code Python est commenté pour un lecteur débutant. Si vous n'avez jamais utilisé Python, commencez par [docs/explication.md](docs/explication.md).

## Démarrage rapide (Windows)

Le script `start.ps1` prépare ce qui manque (environnement virtuel, dépendances Python et Angular, compilation de l'interface), puis lance l'application. Les étapes déjà faites sont sautées.

```powershell
.\start.ps1            # interface web, ouvre http://127.0.0.1:8000
.\start.ps1 console    # menu console
.\start.ps1 dev        # développement Angular avec rechargement automatique
.\start.ps1 test       # tests unitaires
```

Options : `-Rebuild` force la recompilation Angular, `-NoBrowser` n'ouvre pas le navigateur. Si PowerShell refuse d'exécuter le script (politique d'exécution), utilisez `start.bat` (mêmes arguments, ou double-clic).

## Installation manuelle

Prérequis : Python 3.11 ou plus récent.

```bash
git clone https://github.com/slowmfy/JSONPlaceholder-API-TEST.git
cd JSONPlaceholder-API-TEST
python -m venv venv
```

Activer l'environnement virtuel :

- Windows (PowerShell) : `.\venv\Scripts\Activate.ps1`
- Linux / macOS : `source venv/bin/activate`

Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
python main.py
```

Exemple de session :

```
1 - Français
2 - English
Choisissez une langue / Choose a language : 1

===== JSONPlaceholder =====
1. Lister les utilisateurs
...
8. Rapport utilisateur
0. Quitter
Votre choix : 8
Identifiant de l'utilisateur : 1
Utilisateur : Leanne Graham
Email : Sincere@april.biz
Nombre de posts : 10
Nombre total de commentaires : 50
Post le plus commenté :
  Titre : sunt aut facere repellat provident occaecati excepturi optio reprehenderit
  Commentaires : 5
  (10 posts sont à égalité, le premier est affiché.)

Votre choix : 2
Identifiant de l'utilisateur : abc
« abc » n'est pas un nombre entier.
Identifiant de l'utilisateur : 999
Utilisateur 999 introuvable.
```

`Ctrl+C` ou l'option `0` permettent de quitter.

## Interface web (Angular)

```
Navigateur (Angular)  →  web_api.py (FastAPI)  →  JsonPlaceholderClient  →  JSONPlaceholder
```

L'interface Angular n'appelle pas JSONPlaceholder directement. Elle passe par `web_api.py`, qui réutilise le client, les validateurs et les fichiers de traduction de l'application console. Les contrôles de saisie restent ainsi définis à un seul endroit (`validators.py`).

Prérequis supplémentaire : [Node.js](https://nodejs.org) 22.22.3 (ou plus récent en version 22), ou 24.15 et plus.

**Utilisation simple** (un seul serveur) :

```bash
cd frontend
npm install
npm run build
cd ..
python web_api.py
```

Puis ouvrir http://127.0.0.1:8000. La documentation interactive de l'API web est sur http://127.0.0.1:8000/docs.

**Développement** (rechargement automatique quand on modifie le code Angular), dans deux terminaux :

```bash
python web_api.py                 # terminal 1 : API sur le port 8000
cd frontend && npm start          # terminal 2 : interface sur http://localhost:4200
```

`ng serve` redirige les appels `/api` vers le port 8000 (voir `frontend/proxy.conf.json`).

L'interface couvre les 6 ressources de JSONPlaceholder :

| Ressource | Où la trouver | Actions |
|---|---|---|
| Utilisateurs | Menu « Utilisateurs », fiche utilisateur | Lister, rechercher, voir, créer, modifier, supprimer, rapport |
| Posts | Menu « Posts », onglet de la fiche utilisateur | Lister, filtrer, rechercher, voir, créer, modifier, supprimer |
| Commentaires | Page d'un post | Lister, créer, modifier, supprimer |
| Albums | Menu « Albums », onglet de la fiche utilisateur | Lister, filtrer, rechercher, voir, créer, modifier, supprimer |
| Photos | Page d'un album | Galerie, créer, modifier, supprimer |
| Tâches | Menu « Tâches », onglet de la fiche utilisateur | Lister, filtrer, cocher, créer, modifier, supprimer |

La page **Explorateur API** envoie n'importe quelle requête (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) sur n'importe quelle route de JSONPlaceholder, routes imbriquées comprises (`/users/1/todos`), et affiche le statut, la durée, le JSON brut et la commande `curl` équivalente.

Les écritures étant simulées par JSONPlaceholder, l'interface met à jour la copie affichée : les changements disparaissent au rechargement de la page.

La langue se choisit dans l'en-tête et est mémorisée.

## Validation des emails

Les adresses sont contrôlées côté serveur dans `validators.py`, pour toutes les interfaces :

- 254 caractères au maximum, dont 64 avant le `@` ;
- avant le `@` : caractères autorisés par la RFC 5322, sans point au début, à la fin ni en double ;
- après le `@` : un domaine valide, avec une extension d'au moins 2 lettres. Les domaines accentués (`contact@société.fr`) sont acceptés.

Seul le format est vérifié. Prouver qu'une adresse existe demanderait d'y envoyer un message de confirmation.

## Journalisation

Les logs notent les requêtes HTTP et leurs codes retour, les créations, modifications et suppressions, les saisies refusées et les erreurs. Ils ne sont pas affichés à l'écran :

- le menu console écrit dans `app.log` ;
- l'API web écrit dans `web.log`.

**Règle contre la saturation du disque** (réglages dans `config.py`) :

| Réglage | Valeur | Effet |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Les messages `DEBUG`, très détaillés, ne sont pas enregistrés |
| `LOG_MAX_BYTES` | 1 Mo | Un journal qui atteint cette taille devient une archive (`app.log` → `app.log.1`) |
| `LOG_BACKUP_COUNT` | 3 | Trois archives sont gardées, la plus ancienne est supprimée |

Chaque journal occupe ainsi 4 Mo au maximum, soit 8 Mo pour les deux. Les fichiers sont séparés car, sous Windows, un journal ouvert par un autre programme ne peut pas être archivé. Pour la même raison, deux menus console lancés en même temps peuvent perdre des messages une fois la limite atteinte.

Pour lire un journal dans PowerShell avec les accents corrects : `Get-Content app.log -Encoding UTF8 -Tail 20`.

## Ajouter une langue

Copier `locales/en.json` sous un nouveau nom (par exemple `locales/es.json`) et traduire les valeurs, y compris `language_name`. La langue est proposée automatiquement au démarrage, sans modifier le code. Une clé manquante est remplacée par sa version française.

## Tests

```bash
python -m pytest
```

Les tests unitaires couvrent la validation des saisies, le traitement des réponses JSON, la gestion des erreurs (timeout, API inaccessible, 404, JSON invalide), le menu console, les calculs du rapport utilisateur, la cohérence des fichiers de traduction, la rotation des journaux et l'API web (codes HTTP et messages d'erreur). Ils n'ont pas besoin du réseau : l'API est simulée.

Chaque test est expliqué dans [docs/explication.md](docs/explication.md). Les cas de tests manuels sont décrits dans [docs/cas_de_tests.md](docs/cas_de_tests.md).

## Limites de l'API

JSONPlaceholder simule les écritures : `POST`, `PUT` et `DELETE` renvoient une réponse réaliste, mais rien n'est réellement enregistré sur le serveur. Un post créé (toujours `id: 101`) n'est donc pas récupérable ensuite.
