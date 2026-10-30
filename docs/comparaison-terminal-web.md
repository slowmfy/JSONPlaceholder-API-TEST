# Comparaison détaillée : terminal et interface web

## 1. Idée générale

Le projet possède deux façons d'utiliser la même application :

- la **version terminale**, pilotée au clavier dans PowerShell ;
- la **version web**, affichée dans un navigateur avec Angular.

Ce ne sont pas deux projets indépendants. Elles partagent le client HTTP,
les modèles, les validateurs, les erreurs, les traductions et les calculs du
rapport. La différence porte surtout sur la présentation et la façon de
collecter les actions de l'utilisateur.

```text
TERMINAL
PowerShell -> main.py -> menu.py -> api_client.py -> JSONPlaceholder

WEB
Navigateur Angular -> web_api.py -> api_client.py -> JSONPlaceholder
                         |
                         +-> validators.py, models.py, resources.py, i18n.py
```

Le navigateur ne contacte jamais directement JSONPlaceholder. Il appelle
`web_api.py`, qui applique les mêmes règles Python que le terminal.

## 2. Démarrage et processus

### Terminal

Depuis la racine du dépôt :

```powershell
.\start.ps1 console
```

Le script prépare le venv et les dépendances Python si nécessaire, puis lance
`main.py` dans le même terminal. L'utilisateur voit immédiatement :

1. le choix de la langue ;
2. le menu principal ;
3. les questions de l'action choisie.

Pour quitter : choisir `0` ou utiliser `Ctrl+C`.

### Web en mode normal

```powershell
.\start.ps1 web
```

Le script :

1. vérifie Python et les dépendances ;
2. vérifie Node.js et `frontend/node_modules` ;
3. compile Angular si le build est absent ou plus ancien ;
4. démarre `web_api.py` sur `http://127.0.0.1:8000` ;
5. sert les fichiers Angular compilés par FastAPI ;
6. ouvre éventuellement le navigateur.

Il n'y a donc qu'un serveur visible par l'utilisateur : le serveur Python sert
à la fois l'API `/api/...` et les fichiers du front.

### Web en développement

```powershell
.\start.ps1 dev
```

Ce mode démarre deux processus :

- FastAPI sur le port 8000 ;
- `ng serve` sur le port 4200, avec rechargement automatique.

Le proxy Angular redirige `/api` vers FastAPI. Le front de développement peut
donc être ouvert sur `http://localhost:4200`, tandis que la production locale
est ouverte sur `http://127.0.0.1:8000`.

## 3. Menu terminal et navigation web

### Menu terminal

Le terminal propose huit actions séquentielles :

1. lister les utilisateurs ;
2. afficher les détails d'un utilisateur ;
3. lister les posts d'un utilisateur ;
4. afficher les commentaires d'un post ;
5. créer un post ;
6. mettre à jour un post ;
7. supprimer un post ;
8. afficher le rapport utilisateur.

Chaque action demande les valeurs dans un ordre précis. Une erreur de saisie
fait généralement reposer la question. Après l'action, le menu est réaffiché.

Le terminal est adapté à une démonstration linéaire et à l'apprentissage des
appels API. Il n'y a pas de tableau, de lien cliquable, de recherche instantanée
ou de navigation parallèle entre plusieurs ressources.

### Navigation web

Les routes Angular sont :

| Route | Page | Fonction |
|---|---|---|
| `/users` | liste utilisateurs | recherche, création, modification, suppression |
| `/users/:id` | détail utilisateur | détails, édition, suppression et onglets |
| `/users/:id/report` | rapport | statistiques, commentaires et post principal |
| `/posts` | liste posts | filtre utilisateur, recherche par titre, CRUD |
| `/posts/:id` | détail post | détail, édition et commentaires |
| `/albums` | liste albums | filtre utilisateur, recherche, CRUD |
| `/albums/:id` | détail album | détail et galerie de photos |
| `/todos` | liste tâches | filtre utilisateur, statut, case à cocher, CRUD |
| `/explorer` | explorateur API | requête REST libre contrôlée |

Une URL inconnue revient vers `/users`. Les pages de détail utilisent des liens
pour revenir à la liste, ouvrir un rapport ou suivre une relation.

## 4. Utilisateurs

### Terminal

L'option 1 appelle `GET /users` et affiche une ligne par utilisateur avec
l'identifiant, le nom, l'email et la ville.

L'option 2 demande un identifiant, appelle `GET /users/{id}` et affiche :

- nom et nom d'utilisateur ;
- email ;
- téléphone ;
- site web ;
- rue, appartement, code postal et ville ;
- nom et phrase de l'entreprise.

Le terminal ne propose pas de recherche textuelle dans la liste.

### Web

La page `/users` ajoute :

- champ de recherche instantanée par nom ;
- bouton d'ajout ;
- tableau avec id, nom, email et ville ;
- lien vers la fiche ;
- bouton de rapport ;
- édition directement dans la ligne ;
- suppression avec confirmation.

La fiche `/users/:id` ajoute :

- email cliquable avec `mailto:` ;
- bouton modifier ;
- bouton supprimer ;
- bouton rapport ;
- onglet Posts ;
- onglet Albums ;
- onglet Tâches.

Les onglets chargent les ressources liées à l'utilisateur et peuvent créer ou
modifier des éléments avec la référence utilisateur préremplie ou masquée.

## 5. Posts et albums

### Terminal

Le terminal traite surtout les posts :

- liste des posts d'un utilisateur ;
- création avec auteur, titre et contenu ;
- remplacement avec `PUT` ;
- suppression après confirmation.

La création vérifie que l'auteur existe. La modification récupère le post
avant de l'écrire, notamment parce que JSONPlaceholder a des comportements
particuliers pour certaines ressources inexistantes.

### Web

Le composant générique `TitledList` sert aux pages `/posts` et `/albums`.
Il fournit :

- filtre par utilisateur ;
- recherche par titre ;
- compteur de résultats ;
- création ;
- édition ;
- suppression avec confirmation ;
- lien vers le détail pour les éléments distants.

Le même composant est réutilisé dans l'onglet Posts ou Albums d'un utilisateur.
Cela évite de copier le code pour deux ressources qui ont un champ `title`.

La page `/posts/:id` montre le post et sa liste de commentaires. La page
`/albums/:id` montre l'album et sa galerie de photos.

## 6. Commentaires, photos et tâches

Le terminal peut consulter les commentaires d'un post, mais ne propose pas les
écrans web spécialisés de toutes ces ressources.

Le web ajoute :

- commentaires créables, modifiables et supprimables depuis un post ;
- photos affichées en grille dans un album ;
- création, modification et suppression de photos ;
- tâches filtrables par utilisateur ;
- filtre `Terminées` / `Ouvertes` / `Toutes` ;
- case à cocher pour modifier rapidement `completed` ;
- restauration visuelle de la case si la requête échoue.

Les champs de référence (`user_id`, `post_id`, `album_id`) sont générés à partir
de `resources.py`. Le navigateur charge les options correspondantes au lieu de
dupliquer une liste de choix dans chaque formulaire.

## 7. Rapport utilisateur

### Terminal

L'option 8 demande un identifiant et affiche dans le terminal :

- le nom et l'email ;
- le nombre de posts ;
- le nombre de commentaires ;
- le post le plus commenté ;
- le nombre de commentaires ;
- le nombre d'égalités éventuelles.

### Web

La route `/users/:id/report` transforme ces mêmes résultats en page visuelle :

- cartes de statistiques ;
- titre du post le plus commenté ;
- lien vers ce post ;
- indication d'une égalité ;
- barres de comparaison du nombre de commentaires par post ;
- liens vers chaque post.

Le calcul reste dans `UserReport` et non dans Angular. Les deux interfaces
affichent donc le même résultat métier.

## 8. Création et modification

### Terminal

Les champs sont demandés un par un. Les erreurs sont traitées immédiatement :

- identifiant non numérique ou négatif ;
- champ obligatoire vide ;
- email ou URL incorrect ;
- auteur ou parent inexistant ;
- confirmation de suppression invalide.

L'utilisateur corrige la valeur avant que l'appel réseau ne parte.

### Web

`EntityForm` génère les formulaires à partir de `resources.py`. Il choisit le
contrôle selon le type :

- texte pour un nom ou un titre ;
- zone multiligne pour un corps ;
- email pour un email ;
- URL pour une adresse web ;
- téléphone pour le téléphone ;
- liste déroulante pour une référence ;
- case à cocher pour un booléen.

Le formulaire affiche l'erreur sous le champ concerné. Le backend reste
indispensable : un utilisateur peut appeler l'API sans navigateur, et le
serveur doit alors appliquer les mêmes règles.

Les mises à jour web sont partielles avec `PATCH`. Si aucun champ ne change,
aucune requête inutile n'est envoyée. Pour un élément créé localement, le front
met à jour sa copie locale sans appeler un endpoint inexistant.

## 9. Téléphones et différence avec les données API

Les nouvelles créations et modifications doivent respecter le format français :

```text
01 23 45 67 89
01-23-45-67-89
06.12.34.56.78
```

La règle exige dix chiffres, commence par `0`, et autorise seulement les
séparateurs entre les groupes. Les formats internationaux, les lettres et les
extensions sont refusés.

JSONPlaceholder contient pourtant des données existantes comme :

```text
1-770-736-8031 x56442
```

Lors d'une lecture, cette valeur est affichée telle que l'API l'a fournie. Lors
d'une création ou modification, elle est refusée car l'application impose le
format français. Cette différence est volontaire : elle distingue la fidélité
de lecture d'une réponse distante et la validation de nouvelles données.

## 10. Erreurs, chargement et état de l'écran

### Terminal

Le menu capture les erreurs prévues, traduit leur clé et affiche un message
lisible. Une exception inattendue est journalisée et remplacée par un message
neutre. Le programme continue lorsque c'est possible.

### Web

Chaque page peut afficher :

- un état de chargement ;
- une erreur de chargement ;
- une erreur de formulaire ;
- une confirmation de succès ;
- une indication qu'une écriture est simulée.

Les erreurs web sont des objets JSON contenant notamment :

```json
{
  "key": "error_invalid_phone",
  "params": {"value": "01 23 45 67 x9"},
  "field": "phone"
}
```

Angular traduit `key` avec la langue active et associe l'erreur au champ.
Les erreurs réseau et les erreurs HTTP ne produisent donc pas de trace Python
dans le navigateur.

## 11. Traductions

Dans le terminal, `choose_language` sélectionne un fichier dans `locales/`, puis
le menu appelle le traducteur directement.

Dans le web :

1. Angular charge la liste `/api/languages` ;
2. l'utilisateur choisit une langue dans l'en-tête ;
3. Angular demande `/api/translations/{code}` ;
4. le pipe `t` traduit les textes des composants.

Les mêmes fichiers JSON servent aux deux interfaces. Ajouter une langue ne
nécessite pas de modifier les composants Angular ni le menu Python.

## 12. Écritures simulées

Les deux interfaces peuvent afficher un succès après un `POST`, `PUT`, `PATCH`
ou `DELETE`, mais JSONPlaceholder ne conserve pas réellement les changements.

Le terminal affiche un message signalant que l'écriture est simulée. Le web
ajoute temporairement le nouvel élément à sa copie locale et met à jour
l'élément affiché. Après un rechargement complet, l'API distante reprend ses
données originales.

## 13. Tests associés

| Zone | Tests principaux | Ce qui est vérifié |
|---|---|---|
| Coeur HTTP | `test_api.py` | requêtes, paramètres, statuts, timeout, JSON |
| Modèles | `test_models.py` | conversion JSON et rapport |
| Validation | `test_validators.py` | limites et formats, dont téléphone français |
| Ressources | `test_resources.py` | schéma, références et conversion API |
| Terminal | `test_main.py`, `test_menu.py` | menu, saisies, traductions et continuité |
| Web | `test_web_api.py` | routes, codes HTTP, CRUD et fichiers Angular |
| Langues | `test_i18n.py` | clés, paramètres et découverte d'une langue |
| Logs | `test_logging_config.py` | rotation, limites et séparation des fichiers |

Les tests web utilisent FastAPI avec un faux client. Les tests du coeur utilisent
également des sessions HTTP simulées. Ils sont donc rapides et reproductibles,
mais un test manuel reste nécessaire pour vérifier les vrais serveurs et le
navigateur.

## 14. Résumé des différences

| Sujet | Terminal | Web |
|---|---|---|
| Interaction | questions séquentielles | navigation et formulaires |
| Recherche | non | utilisateurs et titres |
| Détails | texte linéaire | pages, liens et onglets |
| Ressources visibles | surtout users/posts/comments/rapport | six ressources et explorateur |
| Modification | surtout `PUT` de post | `PATCH` partiel et édition inline |
| Erreurs | message dans PowerShell | erreur localisée sous le champ |
| Rapport | texte | cartes, liens et graphiques en barres |
| Dépendances | Python | Python + Node.js pour le front |
| Démarrage | `start.ps1 console` | `start.ps1 web` ou `dev` |
| Persistance | simulée | simulée |
