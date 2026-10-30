# Rapport – Client JSONPlaceholder

## 1. Choix d'architecture

Le code est découpé par responsabilité. Chaque module ne dépend que des modules situés en dessous de lui :

```
main.py / web_api.py   points d'entrée : console et API web pour Angular
  └─ menu.py           affichage et saisies (aucun appel HTTP, aucun texte en dur)
       ├─ validators.py    contrôle des saisies avant tout appel à l'API
       ├─ i18n.py          chargement des traductions (locales/*.json)
       └─ api_client.py    JsonPlaceholderClient : seul module qui parle à l'API
            ├─ resources.py    description des 6 ressources
            └─ models.py       User, Post, Comment, Album, Photo, Todo, UserReport
exceptions.py   erreurs partagées    config.py   paramètres    logging_config.py   logs
```

**Client HTTP (`JsonPlaceholderClient`).** Toutes les requêtes passent par une méthode centrale `_request` : la gestion des erreurs (timeout, connexion, 404, autres codes, JSON invalide) n'est écrite qu'une fois. Les méthodes renvoient des objets métier et non du JSON brut : le menu ne connaît ni `requests` ni la structure des réponses. La session HTTP est injectable, ce qui permet de simuler l'API dans les tests.

**Modèles.** Les dataclasses de `models.py` traduisent le JSON (`userId` → `user_id`) et vérifient sa structure : un champ manquant lève une `InvalidResponseError` et non un `KeyError` en plein affichage. Les calculs du rapport utilisateur y sont aussi, faciles à tester.

**Exceptions.** Toutes héritent de `AppError` et portent une *clé de traduction* et des paramètres (`ResourceNotFoundError("user_not_found", id=999)`) plutôt qu'un texte. Le menu traduit la clé dans la langue choisie. Il attrape `AppError` autour de chaque action, et `Exception` en dernier recours (journalisée, avec un message neutre à l'écran) : aucune trace Python n'est montrée et l'application continue.

**Validation.** `validators.py` reçoit le texte saisi et renvoie la valeur nettoyée ou lève une `ValidationError`. Le menu redemande la saisie tant qu'elle est invalide. Sont contrôlés : identifiant obligatoire, entier, positif et borné ; champs texte non vides et de longueur limitée ; email (RFC 5321 et 5322) ; URL ; réponse oui/non. La cohérence avec les données est vérifiée avant l'écriture : l'auteur d'un post doit exister, le post à modifier ou supprimer aussi.

**Journalisation.** Les logs vont dans `app.log` (console) et `web.log` (API web), et non à l'écran, pour ne pas mélanger diagnostic et interface : requêtes HTTP et codes retour, créations, modifications, suppressions, saisies refusées et erreurs. Pour éviter la saturation du disque, le niveau `DEBUG` n'est pas enregistré et une rotation limite chaque journal à 4 Mo (1 Mo en cours et 3 archives).

## 2. Gestion du multilingue

**Solution retenue.** Aucun texte n'est écrit dans le code : le menu n'utilise que des clés (`t("menu_quit")`). Les textes sont dans `locales/<code>.json`. Au démarrage, `i18n.available_languages()` **parcourt le dossier `locales/`** : chaque fichier JSON valide devient une langue proposée, avec le nom lu dans sa clé `language_name`.

**Ajouter une troisième langue sans modifier le code :** copier `en.json` en `es.json`, traduire les valeurs (dont `"language_name": "Español"` et `answer_yes`/`answer_no`). Au lancement suivant, le menu affiche `3 - Español`. Aucune ligne de Python n'est touchée.

**Avantages.**
- Un traducteur peut travailler sans connaître Python, et chaque texte se corrige à un seul endroit.
- Les paramètres (`"Utilisateur {id} introuvable."`) permettent à chaque langue de placer les valeurs où sa grammaire l'exige.
- Une clé absente est cherchée en français, puis la clé elle-même est affichée : une traduction incomplète ne fait jamais planter l'application. Un fichier invalide est ignoré et journalisé.
- Des tests automatiques vérifient que toutes les langues ont les mêmes clés et les mêmes paramètres, et que chaque clé utilisée dans le code existe.

**Limites.** Les logs restent en français : ils s'adressent au développeur. Les pluriels ne sont pas gérés finement ; le module standard `gettext` serait la solution classique.

## 3. Difficultés rencontrées

- **Comportements de l'API à connaître.** `/users/999` renvoie 404, mais `/posts?userId=999` renvoie 200 avec une liste vide : l'application vérifie donc l'existence de l'utilisateur avant de lister ses posts. Un `PUT` sur un post inexistant renvoie 500 au lieu de 404 : le post est récupéré d'abord.
- **Écritures simulées.** POST/PUT/DELETE répondent normalement mais rien n'est enregistré (un post créé a toujours l'id 101). L'utilisateur en est informé après chaque écriture.
- **Mise à jour partielle.** `PUT` remplace toute la ressource : un champ laissé vide reprend l'ancienne valeur.
- **Rapport utilisateur.** Récupérer les commentaires post par post coûterait 10 appels. L'API accepte un filtre répété (`/comments?postId=1&postId=2…`) : le rapport ne fait que 3 appels au total. Chaque post ayant exactement 5 commentaires, tous sont à égalité : le premier est retenu et l'égalité est signalée.
- **Validation des identifiants.** `int()` accepte `"1_000"` ou `"١٢"` et refuse les nombres de plus de 4300 chiffres avec une `ValueError` : une expression régulière ASCII et un contrôle de longueur évitent ces pièges.
- **Validation des emails.** Une expression simple accepte `a@b..fr` ou `a@-b.fr`. Le contrôle sépare donc la partie locale et le domaine, puis applique les règles de chacun. Il a été vérifié sur les 510 adresses réelles de l'API. Seul le format est contrôlé : prouver qu'une adresse existe demanderait un message de confirmation.
- **Rotation des journaux sous Windows.** Un fichier ouvert par un autre programme ne peut pas être renommé. Un essai réel avec un journal partagé a perdu des messages et des archives : la console et l'API web ont donc chacune leur fichier.
- **Tester sans réseau.** L'injection de la session HTTP dans le client et de `input`/`print` dans le menu rend les erreurs reproductibles. Un `Mock` accepte toutefois tout : un filtre `?resource=1` plantait avec le vrai client, ce que seul un test avec le vrai client a montré.

## 4. Interface web

Une interface Angular a été ajoutée à côté du menu console. Elle valide l'architecture : `web_api.py` (FastAPI) n'est qu'une couche d'adaptation, comme `menu.py`, et réutilise le client, la validation, le rapport et les traductions. Les erreurs sont renvoyées sous forme de clé de traduction et de code HTTP (422, 404, 502/504), puis affichées dans la langue choisie, à côté du champ concerné. Les fichiers `locales/*.json` servent aux deux interfaces.

L'interface couvre les 6 ressources de JSONPlaceholder. Pour éviter 30 méthodes et 30 formulaires écrits à la main, `resources.py` décrit chaque ressource une seule fois ; le client, l'API web et les formulaires Angular s'appuient sur cette table. Un explorateur d'API donne accès à toutes les routes de JSONPlaceholder. Comme `PATCH` et `DELETE` renvoient 200 même sur un identifiant inexistant, l'existence de l'élément est vérifiée avant chaque écriture.

## 5. Tests

- **Tests unitaires pytest** (`tests/`) : validation des saisies, réponses JSON, gestion des erreurs, menu console, rapport, traductions, journaux, API web. Ils fonctionnent sans réseau et sont expliqués un par un dans [explication.md](explication.md). Lancement : `python -m pytest`.
- **Cas de tests manuels** : voir [cas_de_tests.md](cas_de_tests.md).
