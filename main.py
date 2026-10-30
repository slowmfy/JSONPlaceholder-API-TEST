"""Point d'entrée du menu console : c'est le fichier lancé par « python main.py ».

Il prépare les journaux, fait choisir la langue, puis démarre le menu.
"""
import logging
import sys

import config
from api_client import JsonPlaceholderClient
from i18n import Translator, available_languages
from logging_config import configure_logging
from menu import ConsoleMenu, choose_language

# Objet qui écrit dans le journal. __name__ est le nom du fichier : chaque ligne
# du journal indique ainsi de quel fichier elle vient.
logger = logging.getLogger(__name__)


def main():
    """Enchaîne les étapes de démarrage de l'application console."""
    configure_logging()
    logger.info("Démarrage de l'application")

    languages = available_languages()
    if not languages:
        # Aucune traduction disponible : seul message qui ne peut pas être traduit.
        logger.critical("Aucun fichier de langue valide dans %s", config.LOCALES_DIR)
        sys.exit(f"No locale file found in {config.LOCALES_DIR}")  # arrête le programme

    # Ctrl+C (KeyboardInterrupt) ou la fin de la saisie (EOFError) doivent quitter
    # proprement, sans afficher d'erreur technique.
    try:
        language = choose_language(languages)
    except (KeyboardInterrupt, EOFError):
        logger.info("Arrêt avant le choix de la langue")
        print()
        return
    logger.info("Langue choisie : %s", language)

    # Crée le client HTTP et le traducteur, les donne au menu, puis lance le menu.
    ConsoleMenu(JsonPlaceholderClient(), Translator(language)).run()
    logger.info("Arrêt de l'application")


# Vrai seulement quand ce fichier est lancé directement. Les tests peuvent ainsi
# l'importer sans démarrer le menu.
if __name__ == "__main__":
    main()
