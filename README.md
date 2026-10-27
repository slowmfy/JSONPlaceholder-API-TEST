# JSONPlaceholder-API-TEST

Application console en Python permettant d'interagir avec l'API REST publique [JSONPlaceholder](https://jsonplaceholder.typicode.com). Cette API simule un backend typique (utilisateurs, posts, commentaires) et permet de s'exercer aux appels HTTP (GET, POST, PUT, DELETE) et à la manipulation de données JSON.

## Fonctionnalités

| Option | Action | Requête |
|---|---|---|
| 1 | Lister les utilisateurs (nom, email, ville) | `GET /users` |
| 2 | Afficher les détails d'un utilisateur | `GET /users/{id}` |
| 3 | Lister les posts d'un utilisateur | `GET /posts?userId={id}` |
| 4 | Afficher les commentaires d'un post | `GET /comments?postId={id}` |
| 5 | Créer un post | `POST /posts` |
| 6 | Mettre à jour un post (titre et/ou contenu) | `PUT /posts/{id}` |
| 7 | Supprimer un post (avec confirmation) | `DELETE /posts/{id}` |

## Structure

```
api.py            Client HTTP : JSONPlaceholderClient et exception APIError
main.py           Menu console, saisies et affichage
requirements.txt  Dépendances
rapport.md        Choix techniques et difficultés
```

## Installation

Prérequis : Python 3.x.

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
===== JSONPlaceholder =====
1. Lister les utilisateurs
2. Afficher les détails d'un utilisateur
3. Lister les posts d'un utilisateur
4. Afficher les commentaires d'un post
5. Créer un post
6. Mettre à jour un post
7. Supprimer un post
0. Quitter
Votre choix : 2
ID de l'utilisateur : 1
  Nom        : Leanne Graham (@Bret)
  Email      : Sincere@april.biz
  ...

Votre choix : 2
ID de l'utilisateur : 999
Erreur : Ressource introuvable (GET /users/999).
```

`Ctrl+C` ou l'option `0` permettent de quitter.

## Limites de l'API

JSONPlaceholder simule les écritures : `POST`, `PUT` et `DELETE` renvoient une réponse réaliste, mais rien n'est réellement enregistré sur le serveur. Un post créé (toujours `id: 101`) n'est donc pas récupérable ensuite.
