# Lire le projet et ses tests sans connaître Python

Ce guide accompagne le code. Il ne faut pas apprendre tout Python avant de le
lire : il suffit de comprendre quelques constructions.

## 1. Les bases utiles

| Écriture | Signification |
|---|---|
| `nom = valeur` | crée une variable |
| `def f(x):` | définit une fonction |
| `class User:` | définit un modèle d'objet |
| `self` | l'objet en cours dans une classe |
| `if`, `for`, `while` | condition ou répétition |
| `return` | renvoie un résultat |
| `raise Erreur()` | signale une erreur |
| `try` / `except` | intercepte une erreur prévue |
| `with ...:` | garantit la libération d'une ressource |
| `@dataclass` | crée automatiquement le constructeur d'une classe de données |
| `@pytest.mark.parametrize` | répète un test avec plusieurs valeurs |
| `assert` | vérifie qu'un résultat est vrai |

Python utilise l'indentation : les lignes décalées sous `def`, `if` ou `for`
appartiennent au bloc. Une docstring entre triples guillemets explique un fichier
ou une fonction.

## 2. Suivre une action

Pour afficher l'utilisateur 1 dans le terminal :

1. `main.py` choisit la langue et crée le menu.
2. `menu.py` lit l'identifiant et demande à `validators.py` de le contrôler.
3. `api_client.py` envoie `GET /users/1`.
4. `models.py` transforme le dictionnaire JSON en `User`.
5. `menu.py` affiche les champs avec les traductions de `locales/`.

Dans le web, Angular envoie la demande à `web_api.py`. Cette API réutilise
exactement les mêmes `resources.py`, `validators.py`, `models.py` et
`api_client.py`. Le navigateur ne contacte donc pas directement JSONPlaceholder.

## 3. Rôle des fichiers Python

- `main.py` : point d'entrée du terminal.
- `menu.py` : questions et affichage ; il ne connaît pas les détails HTTP.
- `api_client.py` : seul module qui parle au réseau.
- `models.py` : objets `User`, `Post`, `Comment`, `Album`, `Photo`, `Todo` et rapport.
- `resources.py` : champs, noms API, filtres et règles d'écriture.
- `validators.py` : règles réutilisables de saisie.
- `web_api.py` : adaptation FastAPI pour Angular.
- `exceptions.py` : erreurs prévues et clés de traduction.
- `i18n.py` et `locales/` : sélection et chargement des langues.
- `logging_config.py` et `config.py` : journaux et paramètres.

## 4. Lire un test pytest

Un test suit généralement :

1. **Préparer** un faux client avec `Mock`.
2. **Exécuter** une fonction.
3. **Vérifier** avec `assert` le résultat et les appels réalisés.

Exemple simplifié :

```python
def test_invalid_phone():
    with pytest.raises(ValidationError):
        validators.validate_phone("01 23 45 67 x9")
```

`pytest.raises` vérifie qu'une erreur est bien déclenchée. Les tests réseau ne
contactent pas Internet : les réponses HTTP sont fabriquées par `conftest.py`.

## 5. Où chercher selon un problème

- Une saisie acceptée à tort : `validators.py` puis `tests/test_validators.py`.
- Un champ absent ou mal nommé : `models.py` et `tests/test_models.py`.
- Une requête ou un statut HTTP : `api_client.py` et `tests/test_api.py`.
- Un message incorrect : `locales/`, `i18n.py` et `tests/test_i18n.py`.
- Un menu qui ne continue pas après une erreur : `menu.py` et `tests/test_menu.py`.
- Un formulaire web ou un code HTTP : `web_api.py`, `frontend/src/app/` et
  `tests/test_web_api.py`.
- Un fichier de log trop gros : `logging_config.py` et `tests/test_logging_config.py`.

## 6. Téléphones : différence entre lecture et écriture

JSONPlaceholder contient parfois un téléphone comme `1-770-736-8031 x56442`.
Cette donnée distante est affichée telle quelle lors d'une lecture, car le client
ne doit pas réécrire la réponse de l'API. En revanche, la création ou la
modification exige le format français `01 23 45 67 89`. C'est pourquoi un ancien
numéro visible peut être différent d'un nouveau numéro accepté.

## 7. Lancer les vérifications

Depuis la racine du dépôt sous Windows :

```powershell
.\start.ps1 test
```

Ou directement :

```powershell
venv\Scripts\python.exe -m pytest -q
```

Pour le terminal :

```powershell
.\start.ps1 console
```

Pour l'application web complète :

```powershell
.\start.ps1 web
```

Le build Angular est lancé automatiquement si nécessaire. Les écritures restent
simulées par JSONPlaceholder : un succès signifie que la requête a été acceptée,
pas que la donnée sera conservée après rechargement.
