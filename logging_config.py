"""Mise en place des journaux (logs), commune au menu console et à l'API web.

Un journal est un fichier où l'application note ce qu'elle fait, pour comprendre
un problème après coup. L'utilisateur ne le voit pas à l'écran.

La règle qui empêche ces fichiers de saturer le disque est décrite dans config.py.
"""
# logging est le module standard de Python pour écrire des journaux.
# RotatingFileHandler écrit dans un fichier et l'archive quand il devient trop gros.
import logging
from logging.handlers import RotatingFileHandler

import config


# « def » crée une fonction : un bloc de code réutilisable qui reçoit des valeurs
# entre parenthèses et renvoie un résultat avec « return ». Python utilise le
# décalage du texte (l'indentation) pour savoir ce qui fait partie du bloc.
def create_log_handler(log_file):
    """Crée l'objet chargé d'écrire dans `log_file`, avec rotation automatique.

    Si le fichier ne peut pas être ouvert (droits insuffisants, par exemple), les
    messages sont simplement ignorés : un journal indisponible ne doit jamais
    empêcher l'application de fonctionner.
    """
    # try / except : on essaie le bloc « try » ; si l'erreur OSError (problème de
    # fichier) survient, Python exécute le bloc « except » au lieu de s'arrêter.
    try:
        handler = RotatingFileHandler(
            log_file,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding="utf-8",  # conserve les accents
        )
    except OSError:
        handler = logging.NullHandler()  # NullHandler ignore tout ce qu'il reçoit
    handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    return handler


# log_file=config.LOG_FILE est une valeur par défaut : elle s'applique si
# l'appelant ne précise pas de fichier.
def configure_logging(log_file=config.LOG_FILE):
    """Envoie les messages de toute l'application vers `log_file`.

    La console et l'API web écrivent chacune dans leur fichier : sous Windows, un
    fichier ouvert par un autre programme ne peut pas être archivé.
    """
    # Une erreur d'écriture dans le journal ne doit pas s'afficher à l'utilisateur.
    logging.raiseExceptions = False
    logging.basicConfig(level=config.LOG_LEVEL, handlers=[create_log_handler(log_file)])
    # urllib3, utilisé par requests, écrirait trop de détails techniques.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
