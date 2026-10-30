"""Tests de main.py : démarrage, choix de la langue et arrêt.

Ici, input() est le vrai : on remplace plutôt sys.stdin, le « clavier » de Python, par
un texte préparé. Le texte "2\n0\n" revient à taper 2, Entrée, 0, Entrée.
"""
import io
import sys
from unittest.mock import Mock

import pytest

import main


class InterruptedInput(io.StringIO):
    """Faux clavier sur lequel l'utilisateur appuie sur Ctrl+C dès la première lecture."""

    def readline(self, *args):
        raise KeyboardInterrupt


# autouse=True applique cette fixture à tous les tests du fichier.
@pytest.fixture(autouse=True)
def no_log_file(monkeypatch):
    """Empêche les tests d'écrire dans le vrai journal app.log."""
    fake = Mock()
    monkeypatch.setattr(main, "configure_logging", fake)
    return fake


def test_language_choice_opens_the_menu_in_that_language(monkeypatch, capsys, no_log_file):
    """Les journaux sont préparés, puis choisir la langue 2 affiche tout le menu en anglais.

    Pourquoi : c'est le parcours complet du démarrage, avec les vrais fichiers de langue.
    capsys capture ce qui est écrit à l'écran.
    """
    monkeypatch.setattr(sys, "stdin", io.StringIO("2\n0\n"))

    main.main()

    output = capsys.readouterr().out
    assert "1 - Français" in output and "2 - English" in output
    assert "List users" in output and "Goodbye!" in output
    no_log_file.assert_called_once()


def test_ctrl_c_on_the_language_prompt_quits_cleanly(monkeypatch, capsys):
    """Ctrl+C dès la première question quitte sans erreur Python.

    Pourquoi : le brief interdit de montrer une exception Python à l'utilisateur.
    """
    monkeypatch.setattr(sys, "stdin", InterruptedInput())

    main.main()

    assert "Traceback" not in capsys.readouterr().err


def test_missing_locale_files_stop_with_a_clear_message(monkeypatch):
    """Sans aucun fichier de langue, le programme s'arrête avec un message clair.

    Pourquoi : c'est le seul cas où aucune traduction n'est possible, d'où le texte en dur.
    """
    monkeypatch.setattr(main, "available_languages", lambda: [])

    with pytest.raises(SystemExit) as stop:  # SystemExit est déclenché par sys.exit()
        main.main()
    assert "No locale file found" in str(stop.value)
