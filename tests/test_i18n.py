"""Tests de i18n.py et des fichiers locales/*.json : traductions et ajout de langues.

tmp_path est une fixture de pytest : un dossier temporaire vide, créé pour le test.
Il permet de fabriquer de faux fichiers de langue sans toucher aux vrais.
"""
import json
import re
from pathlib import Path

import pytest

import config
from i18n import Translator, available_languages, load_messages

PROJECT_DIR = Path(__file__).resolve().parent.parent
LOCALE_FILES = sorted(config.LOCALES_DIR.glob("*.json"))
PLACEHOLDER = re.compile(r"\{(\w+)\}")  # repère les paramètres : {id}, {max}...


def write_locale(directory, code, messages):
    """Crée un faux fichier de langue dans `directory`."""
    (directory / f"{code}.json").write_text(json.dumps(messages), encoding="utf-8")


def used_keys():
    """Clés passées à t(...) ou portées par les exceptions dans le code source."""
    keys = set()
    for path in PROJECT_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        keys |= set(re.findall(r"""\bt\(\s*["'](\w+)["']""", source))
        keys |= set(re.findall(r"""(?:key\s*=\s*|Error\(\s*)["'](\w+)["']""", source))
        keys |= set(re.findall(r"""["']((?:menu|prompt|label|report|confirm)_\w+)["']""", source))
    return keys


def frontend_keys():
    """Clés utilisées par l'interface Angular : 'cle' | t, key: 'cle', label: 'cle'."""
    keys = set()
    sources = PROJECT_DIR.glob("frontend/src/**/*")
    for path in (path for path in sources if path.suffix in (".ts", ".html")):
        source = path.read_text(encoding="utf-8")
        keys |= set(re.findall(r"""'(\w+)'\s*\|\s*t\b""", source))
        keys |= set(re.findall(r"""\b(?:key|label):\s*'(\w+)'""", source))
    return keys


# ---------- Cohérence des fichiers de langue ----------
# ids= donne un nom lisible à chaque cas : le nom du fichier de langue contrôlé.
# Une langue ajoutée dans locales/ est donc testée automatiquement.

@pytest.mark.parametrize("path", LOCALE_FILES, ids=lambda p: p.name)
def test_every_locale_has_the_same_keys_as_default(path):
    """Chaque langue contient exactement les mêmes clés que la langue par défaut.

    Pourquoi : un texte oublié dans une langue s'afficherait en français pour ses utilisateurs.
    """
    reference = load_messages(config.DEFAULT_LANGUAGE)
    messages = load_messages(path.stem)
    assert messages.keys() == reference.keys()


@pytest.mark.parametrize("path", LOCALE_FILES, ids=lambda p: p.name)
def test_every_locale_keeps_the_same_placeholders(path):
    """Chaque traduction garde les mêmes paramètres, comme {id}.

    Pourquoi : un traducteur qui écrit {identifiant} empêcherait d'afficher la valeur.
    """
    reference = load_messages(config.DEFAULT_LANGUAGE)
    messages = load_messages(path.stem)
    for key, text in reference.items():
        assert set(PLACEHOLDER.findall(messages[key])) == set(PLACEHOLDER.findall(text)), key


def test_every_key_used_in_code_exists():
    """Chaque clé utilisée dans le code Python existe dans le fichier de langue.

    Pourquoi : une faute de frappe dans une clé afficherait le nom de la clé à l'écran.
    """
    missing = used_keys() - load_messages(config.DEFAULT_LANGUAGE).keys()
    assert not missing


def test_every_key_used_by_the_web_interface_exists():
    """Chaque clé utilisée par l'interface Angular existe dans le fichier de langue.

    Pourquoi : même risque que pour Python, côté navigateur.
    """
    keys = frontend_keys()
    assert "nav_users" in keys  # vérifie que l'analyse trouve bien les clés
    assert not keys - load_messages(config.DEFAULT_LANGUAGE).keys()


# ---------- Traducteur ----------

def test_translation_with_parameters():
    """Le texte est donné dans la bonne langue, avec la valeur à sa place.

    Pourquoi : c'est la fonction de base du multilingue.
    """
    assert Translator("en")("user_not_found", id=7) == "User 7 not found."
    assert Translator("fr")("user_not_found", id=7) == "Utilisateur 7 introuvable."


def test_missing_key_falls_back_to_default_language(tmp_path):
    """Une clé absente d'une langue est prise dans la langue par défaut.

    Pourquoi : le brief demande qu'une traduction incomplète reste utilisable.
    """
    write_locale(tmp_path, "fr", {"hello": "Bonjour"})
    write_locale(tmp_path, "de", {})
    assert Translator("de", tmp_path, default="fr")("hello") == "Bonjour"


def test_unknown_key_returns_the_key_itself():
    """Une clé qui n'existe nulle part est affichée telle quelle.

    Pourquoi : un texte manquant ne doit pas faire planter l'application.
    """
    assert Translator("fr")("cle_inexistante") == "cle_inexistante"


def test_missing_parameter_does_not_crash():
    """Un paramètre oublié laisse le texte brut, sans erreur.

    Pourquoi : format() planterait sans ce contrôle, à cause d'une simple erreur de programmation.
    """
    assert Translator("fr")("user_not_found") == "Utilisateur {id} introuvable."


# ---------- Découverte des langues ----------

def test_new_language_is_discovered_without_code_change(tmp_path):
    """Un nouveau fichier de langue est détecté, et la langue par défaut reste en premier.

    Pourquoi : c'est l'exigence principale du brief sur le multilingue.
    """
    write_locale(tmp_path, "en", {"language_name": "English"})
    write_locale(tmp_path, "fr", {"language_name": "Français"})
    write_locale(tmp_path, "es", {"language_name": "Español"})

    assert available_languages(tmp_path, default="fr") == [
        ("fr", "Français"), ("en", "English"), ("es", "Español"),
    ]


def test_locale_file_saved_with_a_bom_is_accepted(tmp_path):
    """Un fichier enregistré avec un BOM est lu normalement.

    Pourquoi : le Bloc-notes et PowerShell ajoutent souvent ce marqueur invisible en tête des
    fichiers UTF-8, ce qui rendait le fichier illisible.
    """
    (tmp_path / "es.json").write_text('{"language_name": "Español"}', encoding="utf-8-sig")

    assert available_languages(tmp_path) == [("es", "Español")]


@pytest.mark.parametrize("content", ["{ pas du json", "[1, 2]"])
def test_invalid_locale_file_is_ignored(tmp_path, content):
    """Un fichier de langue cassé est ignoré, et les autres langues restent disponibles.

    Pourquoi : une erreur dans un fichier de traduction ne doit pas empêcher le démarrage.
    """
    write_locale(tmp_path, "fr", {"language_name": "Français"})
    (tmp_path / "xx.json").write_text(content, encoding="utf-8")

    assert available_languages(tmp_path) == [("fr", "Français")]
    assert load_messages("xx", tmp_path) == {}
