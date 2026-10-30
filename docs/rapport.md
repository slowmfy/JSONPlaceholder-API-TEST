# Rapport – Client JSONPlaceholder

## 1. Objectif et périmètre

Le projet propose deux interfaces pour les six ressources de JSONPlaceholder :
utilisateurs, posts, commentaires, albums, photos et tâches. Le terminal réalise
les actions principales demandées (lecture, création, modification, suppression et
rapport utilisateur). L'interface web Angular expose ces mêmes ressources et ajoute
un explorateur de routes REST.

Les deux interfaces utilisent le même client HTTP, les mêmes modèles, les mêmes
validateurs et les mêmes traductions. Une règle corrigée dans `validators.py` est
donc appliquée de façon cohérente au terminal et à l'API web.

## 2. Architecture lisible et maintenable

```text
main.py / web_api.py       points d'entrée console et web
    menu.py                saisie et affichage du terminal
    api_client.py          unique client qui appelle JSONPlaceholder
    resources.py           description déclarative des ressources et champs
    models.py              objets métier et rapport utilisateur
    validators.py          contrôles réutilisés par les deux interfaces
    exceptions.py          erreurs prévues et clés de traduction
    i18n.py / locales/     traductions françaises et anglaises
    logging_config.py      journaux et rotation
    frontend/              interface Angular
    tests/                 tests unitaires pytest
```

`JsonPlaceholderClient` centralise les requêtes, les timeouts, les erreurs réseau,
les statuts HTTP et le décodage JSON. Les dataclasses convertissent les noms
camelCase de l'API (`userId`) en noms Python (`user_id`) et rejettent les champs
manquants ou mal typés. `resources.py` évite de répéter six fois les mêmes règles
dans l'API web et les formulaires.

## 3. Validation et erreurs

Les identifiants sont entiers, positifs et bornés. Les champs obligatoires, emails,
URLs, booléens et références sont contrôlés avant tout appel réseau. Les erreurs
prévues portent une clé (`error_invalid_phone`, `error_not_found`, etc.) plutôt
qu'un texte codé en dur. Le terminal traduit cette clé ; l'API web la renvoie avec
un code HTTP et le champ concerné.

Le téléphone d'une nouvelle création ou modification doit respecter le format
français national : dix chiffres, premier chiffre `0`, groupes de deux chiffres,
séparés facultativement par des espaces, tirets ou points. Exemple accepté :
`01 23 45 67 89`. Les lettres, extensions `x` et formats internationaux sont
refusés.

**Limite importante des données existantes.** JSONPlaceholder contient des
numéros qui ne suivent pas ce choix, par exemple `1-770-736-8031 x56442`. La
lecture les affiche car elle doit représenter fidèlement la réponse distante ;
la création et la modification appliquent, elles, la règle française. Cette
différence est volontaire et documentée dans le README et les cas manuels.

## 4. Fonctionnement de JSONPlaceholder

L'API est une fausse API de démonstration. Les `GET` permettent de lire des données
stables, mais les `POST`, `PUT`, `PATCH` et `DELETE` sont simulés : ils renvoient
une réponse réaliste sans persister la modification. Les créations peuvent donc
revenir avec un identifiant fixe et disparaître après rechargement.

Certaines routes ont aussi des comportements surprenants : un filtre sur un parent
inexistant peut renvoyer une liste vide au lieu d'un 404, et certains `PUT` sur une
ressource inconnue renvoient 500. Le client vérifie donc l'existence des parents et
des ressources avant les écritures.

## 5. Multilingue et journalisation

Chaque fichier JSON ajouté dans `locales/` devient une langue proposée au démarrage.
Pour ajouter l'espagnol, copier `en.json` en `es.json`, traduire les valeurs et
ajouter `language_name`. Aucun code Python n'est à modifier. Les tests contrôlent
les clés et paramètres communs aux langues.

Le terminal écrit dans `app.log`, l'API web dans `web.log`. Le niveau `INFO` et une
rotation de trois archives limitent chaque famille de logs à quatre mégaoctets.
Les logs sont destinés au diagnostic et ne sont pas affichés à l'utilisateur.

## 6. Tests et nettoyage réalisé

La suite comprend neuf fichiers de tests et couvre :

- les validateurs et les frontières (vide, trop long, mauvais type, téléphone français) ;
- les modèles et calculs du rapport ;
- les appels HTTP et chaque famille d'erreur ;
- le menu console et ses erreurs utilisateur ;
- les ressources déclaratives ;
- les traductions et l'ajout d'une langue ;
- la rotation des logs ;
- l'API web, ses codes HTTP et ses fichiers Angular.

Les tests ne dépendent pas du réseau : la session HTTP est simulée. Aucun test
présent n'est supprimé arbitrairement : chaque fichier couvre une responsabilité
distincte et plusieurs tests verrouillent des régressions différentes. Le doublon
de numéro de cas manuel a été corrigé (`TC035` puis `TC036`).

La suite vérifiée au moment de ce rapport contient **265 tests réussis**.
Le détail pédagogique est dans [explication.md](explication.md), et les scénarios
manuels dans [cas_de_tests.md](cas_de_tests.md).

## 7. Limites restantes

- L'API distante ne persiste pas les écritures ; ce n'est pas corrigeable côté client.
- Le format français est volontairement strict et ne couvre pas les numéros
  internationaux ni les extensions.
- Les tests unitaires utilisent des mocks : une vérification réelle du réseau
  nécessite un test manuel séparé.
- Les logs peuvent encore contenir des essais précédents ; ils sont des artefacts
  d'exécution, pas des sources de vérité du code.
