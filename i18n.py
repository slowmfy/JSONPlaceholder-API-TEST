"""Traductions : les textes affichés sont lus dans locales/<code>.json.

i18n est l'abréviation d'« internationalisation » (i + 18 lettres + n).

Les langues ne sont pas listées dans le code : tout fichier JSON valide du
dossier locales/ est proposé au démarrage. Ajouter une langue revient donc à
ajouter un fichier.
"""
import json
import logging

import config

logger = logging.getLogger(__name__)

# Clé qui contient, dans chaque fichier de langue, le nom à afficher (« Français »).
LANGUAGE_NAME_KEY = "language_name"


def load_messages(code, locales_dir=config.LOCALES_DIR):
    """Charge le fichier de langue ; renvoie {} (dictionnaire vide) s'il est absent ou invalide.

    Un dictionnaire associe des clés à des valeurs : {"goodbye": "Au revoir !"}.
    """
    # Un f-string, f"...", remplace ce qui est entre accolades par sa valeur.
    path = locales_dir / f"{code}.json"
    try:
        # utf-8-sig : accepte aussi les fichiers enregistrés avec un BOM (Bloc-notes, PowerShell).
        # « with » garantit que le fichier est refermé, même en cas d'erreur.
        with open(path, encoding="utf-8-sig") as file:
            messages = json.load(file)
    except (OSError, ValueError) as exc:
        logger.error("Fichier de langue illisible %s : %s", path, exc)
        return {}
    # Un fichier JSON peut contenir autre chose qu'un dictionnaire, comme [1, 2].
    if not isinstance(messages, dict):
        logger.error("Fichier de langue mal formé (objet JSON attendu) : %s", path)
        return {}
    return messages


def available_languages(locales_dir=config.LOCALES_DIR, default=config.DEFAULT_LANGUAGE):
    """Renvoie [(code, nom affiché), ...], la langue par défaut en premier."""
    languages = []  # liste vide, remplie par la boucle
    # « for » répète le bloc pour chaque fichier .json trouvé dans le dossier.
    for path in sorted(locales_dir.glob("*.json")):
        messages = load_messages(path.stem, locales_dir)  # path.stem : nom sans l'extension
        if messages:
            languages.append((path.stem, messages.get(LANGUAGE_NAME_KEY, path.stem)))
    # Trie selon « est-ce une autre langue que celle par défaut ? » : False passe avant True.
    # « lambda » crée une petite fonction sans nom, ici utilisée comme critère de tri.
    languages.sort(key=lambda language: language[0] != default)
    return languages


class Translator:
    """Fournit les textes d'une langue, avec repli sur la langue par défaut.

    Une clé absente de la langue choisie est cherchée dans la langue par
    défaut, puis la clé elle-même est affichée : une traduction incomplète ne
    fait jamais planter l'application.
    """

    def __init__(self, language=config.DEFAULT_LANGUAGE, locales_dir=config.LOCALES_DIR,
                 default=config.DEFAULT_LANGUAGE):
        self.language = language
        self.messages = load_messages(language, locales_dir)
        self.fallback = self.messages if language == default else load_messages(default, locales_dir)

    # __call__ permet d'utiliser l'objet comme une fonction : t("goodbye").
    def __call__(self, key, **params):
        """Renvoie le texte de `key` en y plaçant les paramètres : t("user_not_found", id=7)."""
        text = self.messages.get(key)  # .get renvoie None si la clé n'existe pas
        if text is None:
            text = self.fallback.get(key)
            if text is None:
                logger.warning("Clé de traduction absente : %s", key)
                return key
            logger.warning("Clé %s absente en '%s', langue par défaut utilisée", key, self.language)
        try:
            # Remplace {id} dans le texte par la valeur du paramètre id.
            return text.format(**params)
        except (KeyError, IndexError, ValueError) as exc:
            logger.warning("Paramètres invalides pour la clé %s : %s", key, exc)
            return text
