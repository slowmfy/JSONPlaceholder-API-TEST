# Cas de tests manuels

**Prérequis communs** : environnement installé (voir README), connexion Internet active, application lancée avec `python main.py`, langue **1 - Français** choisie (sauf mention contraire). Les données de référence sont celles de JSONPlaceholder : 10 utilisateurs (id 1 à 10), 100 posts (id 1 à 100), 5 commentaires par post.

## Synthèse

| ID | Titre | Catégorie | Résultat obtenu | Statut |
|---|---|---|---|---|
| TC001 | Lister les utilisateurs | Nominal | | |
| TC002 | Afficher un utilisateur existant | Nominal | | |
| TC003 | Afficher un utilisateur inexistant | Ressource inexistante | | |
| TC004 | Créer un post valide | Nominal | | |
| TC005 | Créer un post avec un identifiant invalide | Validation | | |
| TC006 | Créer un post pour un auteur inexistant | Cohérence | | |
| TC007 | Créer un post avec un titre vide | Validation | | |
| TC008 | Créer un post avec un titre trop long | Validation | | |
| TC009 | Lister les posts d'un utilisateur | Nominal | | |
| TC010 | Afficher les commentaires d'un post | Nominal | | |
| TC011 | Afficher les commentaires d'un post inexistant | Ressource inexistante | | |
| TC012 | Mettre à jour le contenu d'un post | Nominal | | |
| TC013 | Mettre à jour un post sans modification | Cas limite | | |
| TC014 | Mettre à jour un post inexistant | Ressource inexistante | | |
| TC015 | Supprimer un post après confirmation | Nominal | | |
| TC016 | Annuler une suppression | Cas limite | | |
| TC017 | Rapport d'un utilisateur existant | Nominal | | |
| TC018 | Rapport d'un utilisateur inexistant | Ressource inexistante | | |
| TC019 | Identifiant nul ou négatif | Validation | | |
| TC020 | Choix de menu invalide | Validation | | |
| TC021 | Utiliser l'application en anglais | Multilingue | | |
| TC022 | Ajouter une troisième langue | Multilingue | | |
| TC023 | API inaccessible | Erreur réseau | | |
| TC024 | Timeout réseau | Erreur réseau | | |
| TC025 | Quitter avec Ctrl+C | Robustesse | | |
| TC026 | Vérifier la journalisation | Logging | | |
| TC027 | Créer un utilisateur avec un email invalide | Web, validation | | |
| TC028 | Créer un utilisateur avec un email valide | Web, nominal | | |
| TC029 | Ajouter un commentaire avec un email invalide | Web, validation | | |
| TC030 | Supprimer un post depuis la liste | Web, nominal | | |
| TC031 | Enregistrer sans modification | Web, cas limite | | |
| TC032 | Vider un champ facultatif | Web, cas limite | | |
| TC033 | Cocher une tâche | Web, nominal | | |
| TC034 | Utiliser l'explorateur d'API | Web, nominal | | |
| TC035 | Refuser une lettre dans un téléphone | Web, validation | | |
| TC036 | Vérifier la rotation des journaux | Logging | | |

---

### TC001 - Lister les utilisateurs
- **Objectif** : vérifier l'affichage de la liste des utilisateurs.
- **Données** : aucune.
- **Étapes** : 1. Saisir `1`.
- **Résultat attendu** : 10 lignes au format `[id] Nom - email - ville`, la première étant `[1] Leanne Graham - Sincere@april.biz - Gwenborough`. Le menu s'affiche de nouveau.

### TC002 - Afficher un utilisateur existant
- **Objectif** : vérifier l'affichage des détails d'un utilisateur.
- **Données** : identifiant `1`.
- **Étapes** : 1. Saisir `2`. 2. Saisir `1`.
- **Résultat attendu** : nom `Leanne Graham (@Bret)`, email `Sincere@april.biz`, téléphone, site web, adresse complète et entreprise `Romaguera-Crona` sont affichés.

### TC003 - Afficher un utilisateur inexistant
- **Objectif** : vérifier la gestion d'une ressource absente (404).
- **Données** : identifiant `999`.
- **Étapes** : 1. Saisir `2`. 2. Saisir `999`.
- **Résultat attendu** : message `Utilisateur 999 introuvable.`, aucune trace Python, retour au menu.

### TC004 - Créer un post valide
- **Objectif** : vérifier la création d'un post.
- **Données** : auteur `1`, titre `Mon titre`, contenu `Mon contenu`.
- **Étapes** : 1. Saisir `5`. 2. Saisir `1`. 3. Saisir le titre. 4. Saisir le contenu.
- **Résultat attendu** : `Post créé (id 101) :` suivi du post `[101] Mon titre` et de la mention indiquant que l'opération est simulée.

### TC005 - Créer un post avec un identifiant invalide
- **Objectif** : vérifier qu'un identifiant non numérique est refusé avant l'appel à l'API.
- **Données** : identifiant `abc`, puis `1`.
- **Étapes** : 1. Saisir `5`. 2. Saisir `abc`. 3. Saisir `1` et terminer la création.
- **Résultat attendu** : après `abc`, message `« abc » n'est pas un nombre entier.` et la question est reposée. Dans `app.log`, aucune requête HTTP n'apparaît pour `abc`.

### TC006 - Créer un post pour un auteur inexistant
- **Objectif** : vérifier la cohérence des données (l'auteur doit exister).
- **Données** : identifiant `11`.
- **Étapes** : 1. Saisir `5`. 2. Saisir `11`.
- **Résultat attendu** : message `Utilisateur 11 introuvable.` ; le titre et le contenu ne sont pas demandés ; aucun `POST` dans `app.log`.

### TC007 - Créer un post avec un titre vide
- **Objectif** : vérifier le contrôle des champs obligatoires.
- **Données** : auteur `1`, titre composé uniquement d'espaces, puis `Titre`.
- **Étapes** : 1. Saisir `5`, puis `1`. 2. Saisir quelques espaces comme titre. 3. Saisir `Titre`.
- **Résultat attendu** : message `Ce champ est obligatoire.` puis la question `Titre :` est reposée.

### TC008 - Créer un post avec un titre trop long
- **Objectif** : vérifier la limite de longueur des champs.
- **Données** : auteur `1`, titre de 201 caractères.
- **Étapes** : 1. Saisir `5`, puis `1`. 2. Coller un titre de 201 caractères.
- **Résultat attendu** : message `Texte trop long (201 caractères, maximum 200).` et la question est reposée.

### TC009 - Lister les posts d'un utilisateur
- **Objectif** : vérifier le filtrage des posts par utilisateur.
- **Données** : identifiant `1`.
- **Étapes** : 1. Saisir `3`. 2. Saisir `1`.
- **Résultat attendu** : 10 posts (id 1 à 10) au format `[id] titre`.

### TC010 - Afficher les commentaires d'un post
- **Objectif** : vérifier l'affichage des commentaires.
- **Données** : identifiant de post `1`.
- **Étapes** : 1. Saisir `4`. 2. Saisir `1`.
- **Résultat attendu** : 5 commentaires avec titre, email de l'auteur (le premier : `Eliseo@gardner.biz`) et texte sur une ligne.

### TC011 - Afficher les commentaires d'un post inexistant
- **Objectif** : vérifier qu'un post inexistant est signalé (et non affiché comme « sans commentaire »).
- **Données** : identifiant de post `101`.
- **Étapes** : 1. Saisir `4`. 2. Saisir `101`.
- **Résultat attendu** : message `Post 101 introuvable.`

### TC012 - Mettre à jour le contenu d'un post
- **Objectif** : vérifier la mise à jour partielle (le titre est conservé).
- **Données** : post `1`, titre laissé vide, contenu `Nouveau contenu`.
- **Étapes** : 1. Saisir `6`. 2. Saisir `1`. 3. Valider le titre vide. 4. Saisir le nouveau contenu.
- **Résultat attendu** : le post actuel est affiché, puis `Post mis à jour :` avec le titre d'origine et le nouveau contenu, et la mention « simulée ».

### TC013 - Mettre à jour un post sans modification
- **Objectif** : vérifier qu'aucune requête n'est envoyée si rien ne change.
- **Données** : post `1`, titre et contenu laissés vides.
- **Étapes** : 1. Saisir `6`. 2. Saisir `1`. 3. Valider deux champs vides.
- **Résultat attendu** : message `Aucune modification.` ; aucun `PUT` dans `app.log`.

### TC014 - Mettre à jour un post inexistant
- **Objectif** : vérifier qu'on ne déclenche pas l'erreur 500 de l'API.
- **Données** : post `500`.
- **Étapes** : 1. Saisir `6`. 2. Saisir `500`.
- **Résultat attendu** : message `Post 500 introuvable.` ; les nouveaux champs ne sont pas demandés.

### TC015 - Supprimer un post après confirmation
- **Objectif** : vérifier la suppression.
- **Données** : post `5`, réponse `o`.
- **Étapes** : 1. Saisir `7`. 2. Saisir `5`. 3. Répondre `o`.
- **Résultat attendu** : le post est affiché, puis `Post 5 supprimé.` et la mention « simulée » ; un `DELETE /posts/5 -> 200` figure dans `app.log`.

### TC016 - Annuler une suppression
- **Objectif** : vérifier la confirmation et le contrôle de la réponse.
- **Données** : post `5`, réponses `peut-être` puis `n`.
- **Étapes** : 1. Saisir `7`, puis `5`. 2. Répondre `peut-être`. 3. Répondre `n`.
- **Résultat attendu** : `Répondez par « o » ou « n ».` puis `Suppression annulée.` ; aucun `DELETE` dans `app.log`.

### TC017 - Rapport d'un utilisateur existant
- **Objectif** : vérifier la synthèse utilisateur.
- **Données** : identifiant `1`.
- **Étapes** : 1. Saisir `8`. 2. Saisir `1`.
- **Résultat attendu** : `Utilisateur : Leanne Graham`, `Email : Sincere@april.biz`, `Nombre de posts : 10`, `Nombre total de commentaires : 50`, post le plus commenté `sunt aut facere repellat…` avec `Commentaires : 5`, et la mention `(10 posts sont à égalité, le premier est affiché.)`. Dans `app.log`, 3 requêtes GET seulement.

### TC018 - Rapport d'un utilisateur inexistant
- **Objectif** : vérifier la gestion d'erreur dans un traitement à plusieurs appels.
- **Données** : identifiant `42`.
- **Étapes** : 1. Saisir `8`. 2. Saisir `42`.
- **Résultat attendu** : message `Utilisateur 42 introuvable.` ; les posts et commentaires ne sont pas demandés à l'API.

### TC019 - Identifiant nul ou négatif
- **Objectif** : vérifier le contrôle « identifiant positif ».
- **Données** : `0`, puis `-3`, puis `1`.
- **Étapes** : 1. Saisir `2`. 2. Saisir successivement `0`, `-3`, `1`.
- **Résultat attendu** : deux fois `L'identifiant doit être strictement positif.`, puis l'utilisateur 1 s'affiche.

### TC020 - Choix de menu invalide
- **Objectif** : vérifier la robustesse du menu.
- **Données** : `9`, puis `abc`, puis une saisie vide.
- **Étapes** : 1. Saisir chaque valeur au menu principal.
- **Résultat attendu** : `Choix invalide : « … ».` à chaque fois, le menu est réaffiché.

### TC021 - Utiliser l'application en anglais
- **Objectif** : vérifier que tous les textes proviennent du fichier de langue.
- **Données** : langue `2`, utilisateur `999`.
- **Étapes** : 1. Au démarrage, saisir `2`. 2. Parcourir le menu, saisir `2` puis `999`. 3. Saisir `0`.
- **Résultat attendu** : menu, invites et messages en anglais (`User 999 not found.`, `Goodbye!`) ; aucun texte français. La confirmation de suppression attend `y/n`.

### TC022 - Ajouter une troisième langue
- **Objectif** : vérifier qu'une langue s'ajoute sans modifier le code.
- **Données** : copie de `locales/en.json` en `locales/es.json` avec `"language_name": "Español"` et `"choose_language": "Elija un idioma"`.
- **Étapes** : 1. Créer le fichier. 2. Lancer `python main.py`.
- **Résultat attendu** : le choix `3 - Español` est proposé et l'invite contient `Elija un idioma`. Le choisir lance l'application avec ce fichier. (Supprimer `es.json` après le test.)

### TC023 - API inaccessible
- **Objectif** : vérifier le comportement sans réseau.
- **Données** : connexion Internet désactivée (Wi-Fi coupé).
- **Étapes** : 1. Couper le réseau. 2. Saisir `1`. 3. Rétablir le réseau et saisir `1`.
- **Résultat attendu** : étape 2 : `API inaccessible. Vérifiez votre connexion Internet.`, l'application continue. Étape 3 : la liste s'affiche normalement.

### TC024 - Timeout réseau
- **Objectif** : vérifier la gestion d'un serveur trop lent.
- **Données** : `TIMEOUT = 0.001` dans `config.py`.
- **Étapes** : 1. Modifier `config.py`. 2. Lancer l'application et saisir `1`. 3. Remettre `TIMEOUT = 5`.
- **Résultat attendu** : `Le serveur n'a pas répondu dans le délai imparti (0.001 s).` ; le menu reste utilisable.

### TC025 - Quitter avec Ctrl+C
- **Objectif** : vérifier l'arrêt propre.
- **Données** : aucune.
- **Étapes** : 1. Au menu, ou pendant une saisie d'identifiant, appuyer sur `Ctrl+C`.
- **Résultat attendu** : `Au revoir !` s'affiche, sans trace `KeyboardInterrupt`.

### TC026 - Vérifier la journalisation
- **Objectif** : vérifier que les actions et erreurs sont tracées.
- **Données** : scénario TC004 puis TC003.
- **Étapes** : 1. Réaliser TC004 et TC003. 2. Ouvrir `app.log`.
- **Résultat attendu** : lignes horodatées contenant `Création dans posts`, `POST /posts -> 201`, `Ressource introuvable : GET /users/999` (WARNING) et `Échec de menu_user_details` (ERROR).

---

Les cas suivants concernent l'interface web. **Prérequis** : application lancée avec `.\start.ps1`, page ouverte sur http://127.0.0.1:8000, langue Français.

### TC027 - Créer un utilisateur avec un email invalide
- **Objectif** : vérifier que les adresses mal formées sont refusées.
- **Données** : nom `Ada`, nom d'utilisateur `ada`, puis successivement les emails `a@b..fr`, `a@-b.fr`, `.a@b.fr`, `a..b@c.fr`, `a@b.c`.
- **Étapes** : 1. Page Utilisateurs, cliquer sur `Ajouter`. 2. Remplir le formulaire. 3. Cliquer sur `Créer` pour chaque email.
- **Résultat attendu** : à chaque essai, le champ Email passe en rouge avec le message `Adresse email invalide : « … ». Format attendu : prenom.nom@exemple.fr` ; aucun utilisateur n'est créé.

### TC028 - Créer un utilisateur avec un email valide
- **Objectif** : vérifier qu'une adresse correcte est acceptée.
- **Données** : nom `Ada`, nom d'utilisateur `ada`, email `ada.lovelace+test@exemple.co.uk`.
- **Étapes** : 1. Page Utilisateurs, cliquer sur `Ajouter`. 2. Remplir le formulaire. 3. Cliquer sur `Créer`.
- **Résultat attendu** : message `Utilisateur 11 créé.` suivi de la mention « simulée » ; l'utilisateur apparaît en haut de la liste.

### TC029 - Ajouter un commentaire avec un email invalide
- **Objectif** : vérifier que la même règle s'applique aux commentaires.
- **Données** : post `1`, nom `Nom`, email `a@b..fr`, contenu `Texte`.
- **Étapes** : 1. Ouvrir le post 1. 2. Dans Commentaires, cliquer sur `Ajouter`. 3. Remplir le formulaire et cliquer sur `Créer`.
- **Résultat attendu** : message d'erreur sous le champ Email ; le commentaire n'est pas ajouté.

### TC030 - Supprimer un post depuis la liste
- **Objectif** : vérifier la suppression avec confirmation.
- **Données** : post `1`.
- **Étapes** : 1. Page Posts, cliquer sur `Supprimer` sur la première ligne. 2. Cliquer sur `Annuler`. 3. Cliquer de nouveau sur `Supprimer`, puis confirmer.
- **Résultat attendu** : `Annuler` ne supprime rien ; après confirmation, le message `Post 1 supprimé.` s'affiche et la ligne disparaît. Le post revient au rechargement de la page, car l'écriture est simulée.

### TC031 - Enregistrer sans modification
- **Objectif** : vérifier qu'aucune requête inutile n'est envoyée.
- **Données** : post `4`.
- **Étapes** : 1. Ouvrir le post 4. 2. Cliquer sur `Modifier`, puis `Enregistrer` sans rien changer.
- **Résultat attendu** : message `Aucune modification.`, sans mention « simulée » ; aucun `PATCH` dans `web.log`.

### TC032 - Vider un champ facultatif
- **Objectif** : vérifier qu'un champ facultatif peut être effacé.
- **Données** : utilisateur `2`.
- **Étapes** : 1. Ouvrir la fiche de l'utilisateur 2. 2. Cliquer sur `Modifier`. 3. Effacer le téléphone et enregistrer.
- **Résultat attendu** : message `Utilisateur 2 modifié.` ; le téléphone est vide sur la fiche.

### TC033 - Cocher une tâche
- **Objectif** : vérifier la modification rapide d'une tâche.
- **Données** : tâche `1`.
- **Étapes** : 1. Page Tâches, cocher la première tâche.
- **Résultat attendu** : message `Tâche 1 modifiée.`, le titre apparaît barré.

### TC034 - Utiliser l'explorateur d'API
- **Objectif** : vérifier l'accès aux routes sans écran dédié et le contrôle du chemin.
- **Données** : exemple `GET /users/1/todos`, puis chemin `/articles`.
- **Étapes** : 1. Page Explorateur API, cliquer sur l'exemple. 2. Cliquer sur `Envoyer`. 3. Saisir `/articles` et cliquer sur `Envoyer`.
- **Résultat attendu** : étape 2 : statut 200, durée, JSON et commande `curl`. Étape 3 : message `Chemin non reconnu`, champ Chemin en rouge, aucune requête envoyée à JSONPlaceholder.

### TC035 - Refuser une lettre dans un téléphone

- **Objectif** : empêcher l'enregistrement d'une lettre dans un numéro.
- **Données** : `01 23 45 67 89`, puis `010-692-6593 x09125`.
- **Étapes** : ouvrir la modification d'un utilisateur, saisir le numéro, puis enregistrer.
- **Résultat attendu** : le numéro français est accepté ; le numéro contenant une lettre est refusé avec une erreur sur le champ Téléphone.

---

Le dernier cas revient au menu console. Il modifie un réglage le temps du test : pensez à le restaurer à la fin.

### TC036 - Vérifier la rotation des journaux
- **Objectif** : vérifier que les journaux ne peuvent pas saturer le disque.
- **Données** : `LOG_MAX_BYTES = 500` dans `config.py`, au lieu de `1_000_000`.
- **Étapes** : 1. Modifier `config.py`. 2. Lancer `python main.py`, choisir `1`, puis lancer l'option `1` une dizaine de fois et quitter avec `0`. 3. Dans PowerShell, exécuter `Get-ChildItem app.log*`. 4. Remettre `LOG_MAX_BYTES = 1_000_000`.
- **Résultat attendu** : `app.log` et au plus 3 archives (`app.log.1` à `app.log.3`), chacun faisant moins de 500 octets. `app.log` contient les messages les plus récents.
