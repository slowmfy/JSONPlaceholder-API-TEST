"""Réglages de l'application, regroupés ici pour être changés à un seul endroit.

Pour lire ce fichier sans connaître Python :
- une ligne qui commence par # est un commentaire : Python l'ignore ;
- le texte entre triples guillemets, comme celui-ci, est une « docstring » :
  la description d'un fichier, d'une classe ou d'une fonction ;
- NOM = valeur crée une variable. Un nom en MAJUSCULES indique, par convention,
  une valeur qui ne change pas pendant que le programme tourne.
"""
# « import » donne accès à du code écrit ailleurs. Path sert à manipuler des
# chemins de fichiers de la même façon sous Windows, Linux et macOS.
from pathlib import Path

# Dossier du projet. __file__ est le chemin de ce fichier et .parent son dossier.
BASE_DIR = Path(__file__).resolve().parent

# ---------- API distante ----------

BASE_URL = "https://jsonplaceholder.typicode.com"
TIMEOUT = 5  # durée d'attente maximale d'une réponse, en secondes

# ---------- Journalisation (logs) ----------

# L'opérateur / assemble des morceaux de chemin : <dossier du projet>/app.log.
LOG_FILE = BASE_DIR / "app.log"      # journal du menu console
WEB_LOG_FILE = BASE_DIR / "web.log"  # journal de l'API web

# Exemple de ligne produite : 2026-10-30 10:55:16 [INFO] api_client : POST /users -> 201
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s : %(message)s"

# Règle contre la saturation du disque :
# 1. seuls les messages INFO, WARNING, ERROR et CRITICAL sont enregistrés (pas DEBUG) ;
# 2. quand un journal atteint LOG_MAX_BYTES, il est archivé (app.log -> app.log.1)
#    et un nouveau fichier vide démarre ;
# 3. seules LOG_BACKUP_COUNT archives sont gardées : la plus ancienne est supprimée.
# Chaque journal occupe donc au plus 4 Mo : 1 Mo en cours + 3 archives de 1 Mo.
LOG_LEVEL = "INFO"
LOG_MAX_BYTES = 1_000_000  # 1 Mo ; le _ ne sert qu'à rendre le nombre lisible
LOG_BACKUP_COUNT = 3

# ---------- Langues ----------

# Chaque fichier <code>.json de ce dossier est une langue disponible.
LOCALES_DIR = BASE_DIR / "locales"
DEFAULT_LANGUAGE = "fr"

# ---------- Interface web (python web_api.py) ----------

WEB_HOST = "127.0.0.1"  # adresse locale : le site n'est accessible que depuis ce PC
WEB_PORT = 8000
# Dossier où Angular dépose le site compilé (cd frontend && npm run build).
FRONTEND_DIR = BASE_DIR / "frontend" / "dist" / "frontend" / "browser"

# ---------- Limites de validation des saisies ----------

MAX_ID = 2**31 - 1            # ** est la puissance : plus grand entier sur 32 bits
MAX_TITLE_LENGTH = 200
MAX_BODY_LENGTH = 2000
MAX_NAME_LENGTH = 100
MAX_URL_LENGTH = 500
MAX_EMAIL_LENGTH = 254        # limite de la norme RFC 5321
MAX_EMAIL_LOCAL_LENGTH = 64   # partie située avant le @
