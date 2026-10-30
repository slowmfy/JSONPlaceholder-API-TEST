"""Tests de logging_config.py : la règle anti-saturation et la solidité du journal."""
import logging

import pytest

import config
from logging_config import configure_logging, create_log_handler


@pytest.fixture
def small_log(tmp_path, monkeypatch):
    """Prépare un journal limité à 300 octets et 2 archives, pour tester en quelques lignes.

    monkeypatch modifie un réglage pendant le test et le restaure ensuite. Le code placé
    après yield s'exécute à la fin du test : ici, il referme le fichier.
    """
    monkeypatch.setattr(config, "LOG_MAX_BYTES", 300)
    monkeypatch.setattr(config, "LOG_BACKUP_COUNT", 2)
    handler = create_log_handler(tmp_path / "test.log")
    logger = logging.getLogger("test_rotation")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)
    yield logger, tmp_path
    logger.removeHandler(handler)
    handler.close()


def test_log_size_stays_limited(small_log):
    """Après 200 messages, il n'y a que 3 fichiers, chacun sous la limite de taille.

    Pourquoi : c'est la règle demandée : quel que soit le nombre de messages, l'espace
    occupé reste borné (fichier en cours + archives).
    """
    logger, folder = small_log

    for number in range(200):
        logger.info("message %s", number)

    files = sorted(folder.iterdir())
    assert [file.name for file in files] == ["test.log", "test.log.1", "test.log.2"]
    assert all(file.stat().st_size <= 300 for file in files)


def test_most_recent_messages_are_kept(small_log):
    """Les messages récents sont conservés, accents compris ; les plus anciens disparaissent.

    Pourquoi : pour comprendre une panne, ce sont les derniers messages qui comptent.
    """
    logger, folder = small_log

    for number in range(200):
        logger.info("créé n°%s.", number)

    newest = (folder / "test.log").read_text(encoding="utf-8")
    assert "[INFO] test_rotation : créé n°199." in newest  # format défini dans config.py
    everything = "".join(file.read_text(encoding="utf-8") for file in folder.iterdir())
    assert "n°0." not in everything


def test_configuration_uses_the_given_file_and_level(tmp_path, monkeypatch):
    """Le journal choisi et le niveau de config.py sont bien appliqués.

    Pourquoi : la console et le web doivent écrire chacun dans leur fichier, et le niveau
    INFO évite d'enregistrer les détails techniques volumineux.
    """
    received = {}  # recevra les réglages transmis à logging.basicConfig
    monkeypatch.setattr(logging, "basicConfig", lambda **options: received.update(options))
    monkeypatch.setattr(logging, "raiseExceptions", True)

    configure_logging(tmp_path / "choisi.log")

    handler = received["handlers"][0]
    handler.close()
    assert received["level"] == "INFO"
    assert handler.baseFilename == str(tmp_path / "choisi.log")
    assert logging.raiseExceptions is False  # une erreur de journal ne s'affiche jamais
    assert logging.getLogger("urllib3").level == logging.WARNING  # bibliothèque trop bavarde


def test_rule_limits_each_log_to_4_mb():
    """Les réglages de config.py limitent chaque journal à 4 Mo, archives comprises.

    Pourquoi : c'est la limite annoncée dans la documentation. Si un réglage la dépasse, ce test
    oblige à faire ce choix consciemment.
    """
    assert config.LOG_MAX_BYTES * (config.LOG_BACKUP_COUNT + 1) <= 4_000_000


def test_console_and_web_use_separate_files():
    """La console et l'API web n'écrivent pas dans le même fichier.

    Pourquoi : sous Windows, un fichier ouvert par un autre programme ne peut pas être
    renommé. Un test réel a montré que le partager perd des messages et des archives.
    """
    assert config.LOG_FILE != config.WEB_LOG_FILE


def test_unwritable_log_file_does_not_stop_the_application(tmp_path):
    """Un journal impossible à ouvrir est remplacé par un objet qui ignore les messages.

    Pourquoi : un fichier verrouillé ne doit ni arrêter l'application ni afficher une
    erreur. Ici, le chemin donné est un dossier, donc impossible à ouvrir comme fichier.
    """
    assert isinstance(create_log_handler(tmp_path), logging.NullHandler)
