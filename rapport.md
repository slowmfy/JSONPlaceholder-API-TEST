# Rapport – Client console JSONPlaceholder

## Choix techniques

**Séparation en deux fichiers.** `api.py` contient uniquement la communication HTTP (classe `JSONPlaceholderClient`), `main.py` uniquement l'interface console (menu, saisies, affichage). On pourrait ainsi remplacer la console par une interface graphique sans toucher au client HTTP.

**Une méthode centrale `_request`.** Toutes les requêtes passent par cette méthode, qui utilise `requests.request(...)` avec un timeout. La gestion d'erreurs n'est donc écrite qu'une seule fois. Chaque fonctionnalité (`get_users`, `create_post`, etc.) tient en une ligne.

**Une exception personnalisée `APIError`.** `_request` transforme toutes les erreurs possibles (timeout, absence de connexion, 404, autre code non-2xx, JSON invalide) en `APIError` avec un message lisible. `main.py` n'a besoin d'attraper qu'une seule exception et n'a pas à connaître la bibliothèque `requests`.

**`params=` et `json=`.** Les paramètres d'URL (`?userId=1`) sont passés via `params=`, et le corps des requêtes POST/PUT via `json=`. `requests` se charge de l'encodage et de l'en-tête `Content-Type`.

**Menu par dictionnaire.** Le menu associe chaque numéro à un libellé et une fonction (`{"1": ("Lister les utilisateurs", fonction), ...}`), ce qui évite une longue chaîne de `if/elif` et rend l'ajout d'une option trivial.

**Saisies validées.** `demander_entier()` redemande tant que la saisie n'est pas un entier positif (évite le crash de `int("abc")`), `demander_texte()` refuse un champ vide. Chaque action est entourée d'un `try/except APIError` : une erreur affiche un message mais le programme continue. `Ctrl+C` quitte proprement.

## Difficultés rencontrées et cas limites

- **Utilisateur inexistant** (`/users/999`) : l'API renvoie 404, transformé en `APIError` « Ressource introuvable ».
- **Posts d'un utilisateur inexistant** (`/posts?userId=999`) : l'API renvoie 200 avec une liste vide, pas une erreur. Il a fallu tester explicitement `if not posts` pour afficher « Aucun post ».
- **Écritures simulées** : un POST renvoie toujours `id: 101`, mais rien n'est enregistré (`GET /posts/101` renvoie 404). L'application le vérifie et prévient l'utilisateur.
- **PUT sur un id inexistant** : l'API renvoie une erreur 500 au lieu d'un 404. L'application fait donc d'abord un `GET /posts/{id}` pour vérifier que le post existe.
- **Mise à jour partielle** : PUT remplace la ressource entière. L'application récupère le post actuel et conserve l'ancienne valeur pour tout champ laissé vide.
- **Suppression** : une confirmation (o/n) est demandée avant d'envoyer le DELETE, dont la réponse est `{}` avec un code 200.
- **Environnement** : le module `requests` n'était pas installé dans l'environnement virtuel ; il a fallu installer les dépendances avec `pip install -r requirements.txt`.
- **Construction de l'URL** : une première version ajoutait un `/` en trop entre l'URL de base et l'endpoint (`//users`).
