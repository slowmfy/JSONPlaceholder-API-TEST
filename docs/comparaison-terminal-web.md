# Différences entre la version terminale et la version web

Le projet propose deux interfaces différentes, mais elles utilisent le même
coeur Python. Cette séparation permet de changer l'interface sans recopier la
logique d'accès à l'API, de validation ou de calcul des rapports.

## 1. Vue d'ensemble

| Élément | Version terminale | Version web |
|---|---|---|
| Point d'entrée | `main.py` | `web_api.py` + Angular |
| Interface | Menu texte dans PowerShell | Pages dans un navigateur |
| Affichage | `print()` et questions interactives | Composants Angular et formulaires |
| Réseau | `menu.py` appelle `JsonPlaceholderClient` | Angular appelle `web_api.py`, qui utilise le client |
| Traductions | `i18n.py` dans le menu | `/api/translations/{code}` et pipe Angular |
| Erreurs | Message traduit dans le terminal | Code HTTP, clé de traduction et champ en erreur |
| Validation | Avant l'appel API, pendant la saisie | Backend partagé, avec erreur affichée sous le champ |

## 2. Parcours d'une demande

### Terminal

Pour afficher l'utilisateur `1` :

1. `main.py` choisit la langue.
2. `menu.py` demande l'identifiant.
3. `validators.py` vérifie l'identifiant.
4. `api_client.py` envoie `GET /users/1`.
5. `models.py` transforme le JSON en `User`.
6. `menu.py` affiche les informations.

Le terminal reste ouvert après une erreur lorsque c'est possible et redemande une
saisie invalide.

### Web

Pour afficher le même utilisateur :

1. Angular affiche la page et envoie une requête à `/api/users/1`.
2. `web_api.py` valide la route et l'identifiant.
3. `api_client.py` appelle JSONPlaceholder.
4. `models.py` transforme la réponse.
5. `web_api.py` renvoie du JSON au navigateur.
6. Angular affiche les données ou l'erreur dans la page.

Le navigateur ne contacte jamais directement JSONPlaceholder. Cette règle évite
de dupliquer les contrôles et centralise les erreurs côté Python.

## 3. Fonctionnalités communes

Les deux interfaces partagent :

- les six ressources : utilisateurs, posts, commentaires, albums, photos et tâches ;
- les appels HTTP de `JsonPlaceholderClient` ;
- les modèles et le rapport utilisateur ;
- les validateurs d'identifiants, textes, emails, URLs et téléphones ;
- les fichiers de traduction français et anglais ;
- la gestion des erreurs réseau, timeout, 404, réponses invalides et statuts HTTP.

Le téléphone nouvellement créé ou modifié doit respecter le format français :
`01 23 45 67 89`. Les données déjà présentes dans JSONPlaceholder peuvent avoir
un autre format, par exemple `1-770-736-8031 x56442`, et sont affichées telles
quelles lors d'une lecture.

## 4. Différences d'utilisation

### Terminal

Lancer :

```powershell
.\start.ps1 console
```

Le programme demande d'abord la langue, puis affiche huit options :
lister les utilisateurs, consulter un utilisateur, consulter ses posts,
consulter les commentaires, créer, modifier ou supprimer un post, et afficher
un rapport utilisateur.

Cette version est adaptée à une démonstration simple, à un environnement sans
navigateur et aux tests de saisie interactive. Les actions sont séquentielles :
on choisit une option, on répond aux questions, puis le menu réapparaît.

### Web

Lancer :

```powershell
.\start.ps1 web
```

Puis ouvrir `http://127.0.0.1:8000`.

La version web propose des listes, recherches, fiches, onglets, formulaires,
modifications rapides et un explorateur API. Elle permet aussi de gérer les
six ressources, alors que le menu terminal expose principalement les actions
historiques autour des utilisateurs, posts, commentaires et rapports.

En développement, on peut utiliser :

```powershell
.\start.ps1 dev
```

Angular est alors servi par `ng serve` avec rechargement automatique.

## 5. Création et modification

Dans le terminal, les informations sont demandées une par une. La saisie
incorrecte provoque une nouvelle question avant tout appel réseau.

Dans le web, un formulaire regroupe les champs. Le navigateur affiche l'erreur
près du champ concerné, mais la validation Python reste obligatoire : un client
HTTP externe ne peut pas contourner les règles du backend.

Les écritures JSONPlaceholder sont simulées dans les deux versions. Une création,
modification ou suppression peut donc afficher un succès puis disparaître après
un rechargement.

## 6. Tests associés

- `tests/test_menu.py` et `tests/test_main.py` vérifient principalement le
  terminal.
- `tests/test_web_api.py` vérifie les routes FastAPI et les codes HTTP.
- `tests/test_api.py`, `tests/test_models.py`, `tests/test_resources.py` et
  `tests/test_validators.py` vérifient le coeur partagé.
- `tests/test_i18n.py` et `tests/test_logging_config.py` vérifient les services
  communs aux deux interfaces.

Cette organisation permet de savoir si une régression vient de l'interface
terminale, de l'interface web ou d'un module partagé.
