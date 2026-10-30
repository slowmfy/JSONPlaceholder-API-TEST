"""Tests de menu.py : scénarios complets du menu console, sans clavier ni réseau.

Le client HTTP est remplacé par un Mock et l'utilisateur par une liste de saisies :
["2", "1", "0"] revient à taper 2 (option), 1 (identifiant), 0 (quitter).
"""
from unittest.mock import Mock

import pytest

from conftest import USER_JSON, comment_json, post_json
from exceptions import APIConnectionError, ResourceNotFoundError
from i18n import Translator, available_languages
from menu import ConsoleMenu, choose_language
from models import Comment, Post, User, UserReport


def run_menu(client, inputs, language="fr", prompts=None):
    """Lance le menu avec des saisies simulées et renvoie tout ce qui a été affiché.

    prompts : liste facultative qui reçoit les questions posées à l'utilisateur.
    """
    printed = []
    answers = iter(inputs)  # iter permet de prendre les saisies une à une avec next

    def fake_input(prompt):
        """Remplace input() : renvoie la saisie suivante de la liste."""
        if prompts is not None:
            prompts.append(prompt)
        try:
            return next(answers)
        except StopIteration:
            raise EOFError from None  # comme input() quand l'entrée est fermée

    menu = ConsoleMenu(client, Translator(language), input_func=fake_input,
                       output=lambda *args: printed.append(" ".join(map(str, args))))
    menu.run()
    return "\n".join(printed)


def post():
    """Fabrique le post n°1."""
    return Post.from_dict(post_json(1))


def report():
    """Fabrique un rapport : un utilisateur, un post, un commentaire."""
    return UserReport(User.from_dict(USER_JSON), [post()], [Comment.from_dict(comment_json(1, 1))])


# ---------- Robustesse : aucune exception ne doit atteindre l'utilisateur ----------

def test_api_error_shows_translated_message_and_continues():
    """Si l'API est injoignable, un message traduit s'affiche et le menu continue.

    Pourquoi : une panne réseau ne doit pas fermer l'application.
    """
    # Préparation : tout appel à get_users déclenchera une erreur de connexion.
    client = Mock()
    client.get_users.side_effect = APIConnectionError()

    # Action : l'utilisateur choisit l'option 1, puis quitte.
    output = run_menu(client, ["1", "0"])

    # Vérification : message d'erreur, puis menu toujours utilisable jusqu'à la sortie.
    assert "API inaccessible" in output
    assert "Au revoir" in output


def test_unexpected_exception_is_not_shown_to_user():
    """Un bug imprévu donne un message neutre, sans détail technique.

    Pourquoi : c'est l'exigence du brief : aucune exception Python à l'écran.
    """
    client = Mock()
    client.get_users.side_effect = ZeroDivisionError("boom")

    output = run_menu(client, ["1", "0"], language="en")

    assert "unexpected error" in output
    assert "ZeroDivisionError" not in output and "Traceback" not in output


def test_invalid_id_is_asked_again_before_calling_api():
    """Un identifiant invalide est redemandé ; l'API n'est appelée qu'avec une valeur correcte.

    Pourquoi : deux choses à la fois : le menu boucle, et rien d'invalide ne part vers l'API.
    """
    client = Mock()
    client.get_user.side_effect = ResourceNotFoundError("user_not_found", id=999)

    output = run_menu(client, ["2", "abc", "-1", "999", "0"])

    assert "n'est pas un nombre entier" in output
    assert "strictement positif" in output
    assert "Utilisateur 999 introuvable." in output
    client.get_user.assert_called_once_with(999)


def test_menu_shows_every_option():
    """Le menu affiche son titre, ses options et le moyen de quitter.

    Pourquoi : sans cet affichage, l'utilisateur ne saurait pas quoi taper.
    """
    output = run_menu(Mock(), ["0"])

    assert "===== JSONPlaceholder =====" in output
    assert "1. Lister les utilisateurs" in output
    assert "8. Rapport utilisateur" in output
    assert "0. Quitter" in output


def test_invalid_menu_choice_is_refused():
    """Un numéro d'option inexistant affiche un message d'erreur.

    Pourquoi : une faute de frappe ne doit rien lancer et le menu doit se réafficher.
    """
    assert "Choix invalide : « 9 »." in run_menu(Mock(), ["9", "0"])


@pytest.mark.parametrize("inputs", [[], ["2"]], ids=["au-menu", "pendant-une-question"])
def test_end_of_input_quits_cleanly(inputs):
    """La fin de la saisie (Ctrl+Z) quitte proprement, même au milieu d'une question.

    Pourquoi : ce défaut existait : Ctrl+Z pendant une question affichait « erreur inattendue ».
    """
    output = run_menu(Mock(), inputs)

    assert "Au revoir" in output
    assert "inattendue" not in output


def test_ctrl_c_quits_cleanly():
    """Ctrl+C pendant une action quitte proprement.

    Pourquoi : c'est le moyen normal d'interrompre un programme en console.
    """
    client = Mock()
    client.get_users.side_effect = KeyboardInterrupt

    output = run_menu(client, ["1"])

    assert "Au revoir" in output
    assert "KeyboardInterrupt" not in output


# ---------- Langue ----------

@pytest.mark.parametrize("answer, expected", [("1", "fr"), ("2", "en")])
def test_choose_language(answer, expected):
    """Les langues sont numérotées, un mauvais numéro est redemandé, et le bon code est renvoyé.

    Pourquoi : la saisie 9 est donnée en premier pour vérifier que la question est reposée. La
    langue n'étant pas encore choisie, la question est posée dans toutes les langues.
    """
    answers = iter(["9", answer])
    printed = []
    prompts = []

    def fake_input(prompt):
        prompts.append(prompt)
        return next(answers)

    code = choose_language(available_languages(), input_func=fake_input, output=printed.append)

    assert code == expected
    assert printed[:2] == ["1 - Français", "2 - English"]
    assert "Choix invalide : « 9 »." in printed  # message dans la langue par défaut
    assert "Choisissez une langue / Choose a language : " in prompts


def test_report_uses_the_punctuation_of_the_language():
    """Le français met un espace avant les deux-points, l'anglais non.

    Pourquoi : ce défaut existait : la ponctuation était écrite dans le code au lieu des traductions.
    """
    client = Mock()
    client.get_user_report.return_value = report()

    assert "Nombre de posts : 1" in run_menu(client, ["8", "1", "0"], language="fr")
    english = run_menu(client, ["8", "1", "0"], language="en")
    assert "Number of posts: 1" in english and " : " not in english


def test_confirmation_prompt_is_translated():
    """La question de confirmation est entièrement traduite, réponses comprises.

    Pourquoi : en anglais, la question doit proposer y/n et non o/n.
    """
    client = Mock()
    prompts = []

    run_menu(client, ["7", "1", "n", "0"], language="en", prompts=prompts)

    assert "Confirm deletion? (y/n): " in prompts


# ---------- Options de lecture (1 à 4) ----------

def test_list_users():
    """L'option 1 affiche l'identifiant, le nom, l'email et la ville.

    Pourquoi : ce sont les informations demandées par le brief.
    """
    client = Mock()
    client.get_users.return_value = [User.from_dict(USER_JSON)]

    output = run_menu(client, ["1", "0"])

    assert "[1] Leanne Graham - Sincere@april.biz - Gwenborough" in output


def test_show_user_displays_every_detail():
    """L'option 2 affiche toutes les informations de l'utilisateur.

    Pourquoi : les données imbriquées (adresse, entreprise) doivent arriver jusqu'à l'écran.
    """
    client = Mock()
    client.get_user.return_value = User.from_dict(USER_JSON)

    output = run_menu(client, ["2", "1", "0"])

    assert "Nom : Leanne Graham (@Bret)" in output
    assert "Email : Sincere@april.biz" in output
    assert "Téléphone : 1-770-736-8031 x56442" in output
    assert "Site web : hildegard.org" in output
    assert "Adresse : Kulas Light, Apt. 556, 92998-3874 Gwenborough" in output
    assert "Entreprise : Romaguera-Crona - Multi-layered client-server neural-net" in output


def test_list_user_posts():
    """L'option 3 affiche les posts de l'utilisateur.

    Pourquoi : c'est le cas normal de cette option.
    """
    client = Mock()
    client.get_posts_by_user.return_value = [post()]

    assert "[1] Titre 1" in run_menu(client, ["3", "1", "0"])


def test_list_user_posts_of_a_user_without_posts():
    """Un utilisateur sans post donne un message clair, pas un écran vide.

    Pourquoi : l'utilisateur doit comprendre que la liste est vraiment vide.
    """
    client = Mock()
    client.get_posts_by_user.return_value = []

    assert "Aucun post pour l'utilisateur 7." in run_menu(client, ["3", "7", "0"])


def test_list_user_posts_checks_that_the_user_exists():
    """Un utilisateur inconnu est signalé, et ses posts ne sont pas demandés.

    Pourquoi : /posts?userId=999 renvoie une liste vide, ce qui serait trompeur.
    """
    client = Mock()
    client.get_user.side_effect = ResourceNotFoundError("user_not_found", id=99)

    assert "Utilisateur 99 introuvable." in run_menu(client, ["3", "99", "0"])
    client.get_posts_by_user.assert_not_called()


def test_list_post_comments_on_a_single_line():
    """L'option 4 affiche l'auteur, l'email, et le commentaire sur une seule ligne.

    Pourquoi : les textes de l'API contiennent des retours à la ligne qui casseraient l'affichage.
    """
    client = Mock()
    client.get_comments_by_post.return_value = [Comment(1, 1, "Nom", "a@b.fr", "ligne 1\nligne 2")]

    output = run_menu(client, ["4", "1", "0"])

    assert "- Nom (a@b.fr)" in output
    assert "ligne 1 ligne 2" in output


def test_list_post_comments_checks_that_the_post_exists():
    """Un post inconnu est signalé, et ses commentaires ne sont pas demandés.

    Pourquoi : /comments?postId=999 renvoie une liste vide, ce qui serait trompeur.
    """
    client = Mock()
    client.get_post.side_effect = ResourceNotFoundError("post_not_found", id=999)

    assert "Post 999 introuvable." in run_menu(client, ["4", "999", "0"])
    client.get_comments_by_post.assert_not_called()


def test_list_comments_of_a_post_without_comments():
    """Un post sans commentaire donne un message clair.

    Pourquoi : même raison que pour un utilisateur sans post.
    """
    client = Mock()
    client.get_comments_by_post.return_value = []

    assert "Aucun commentaire pour le post 3." in run_menu(client, ["4", "3", "0"])


# ---------- Options d'écriture (5 à 7) ----------

def test_create_post_asks_again_until_fields_are_valid():
    """L'option 5 redemande chaque champ invalide, puis crée le post et rappelle que c'est simulé.

    Pourquoi : c'est le scénario le plus complet : identifiant faux, titre vide, contenu trop long.
    """
    client = Mock()
    client.create_post.return_value = Post(101, 1, "Titre", "Contenu")

    output = run_menu(client, ["5", "abc", "1", "   ", "Titre", "x" * 2001, "Contenu", "0"])

    assert "Ce champ est obligatoire." in output
    assert "Texte trop long (2001 caractères, maximum 2000)." in output
    assert "Post créé (id 101) :" in output
    assert "[101] Titre" in output
    assert "      Contenu" in output
    assert "rien n'est enregistré" in output
    client.create_post.assert_called_once_with(1, "Titre", "Contenu")


def test_create_post_stops_when_the_author_does_not_exist():
    """Si l'auteur n'existe pas, le post n'est pas créé.

    Pourquoi : un post ne doit pas être rattaché à un utilisateur inconnu.
    """
    client = Mock()
    client.get_user.side_effect = ResourceNotFoundError("user_not_found", id=11)

    assert "Utilisateur 11 introuvable." in run_menu(client, ["5", "11", "0"])
    client.create_post.assert_not_called()


def test_update_post_keeps_empty_fields():
    """L'option 6 montre le post, garde l'ancienne valeur d'un champ vide et rappelle que c'est simulé.

    Pourquoi : PUT remplace tout, donc le titre actuel doit être renvoyé pour ne pas le perdre.
    """
    client = Mock()
    client.get_post.return_value = post()
    client.update_post.return_value = Post(1, 1, "Titre 1", "Nouveau")

    output = run_menu(client, ["6", "1", "", "Nouveau", "0"])

    assert "Post actuel :" in output
    assert "[1] Titre 1" in output
    assert "conserver la valeur actuelle" in output
    assert "Post mis à jour :" in output
    assert "      Nouveau" in output
    assert "rien n'est enregistré" in output
    client.update_post.assert_called_once_with(1, 1, "Titre 1", "Nouveau")


def test_update_post_without_change_sends_nothing():
    """Sans changement, rien n'est envoyé et l'utilisateur en est informé.

    Pourquoi : une requête inutile afficherait une fausse réussite.
    """
    client = Mock()
    client.get_post.return_value = post()

    assert "Aucune modification." in run_menu(client, ["6", "1", "", "", "0"])
    client.update_post.assert_not_called()


def test_delete_post_after_confirmation():
    """L'option 7 montre le post, le supprime quand l'utilisateur confirme et rappelle que c'est simulé.

    Pourquoi : c'est le cas normal, et montrer le post évite de supprimer le mauvais.
    """
    client = Mock()
    client.get_post.return_value = post()

    output = run_menu(client, ["7", "1", "o", "0"])

    assert "[1] Titre 1" in output
    assert "Post 1 supprimé." in output
    assert "rien n'est enregistré" in output
    client.delete_post.assert_called_once_with(1)


def test_delete_can_be_cancelled():
    """Une réponse invalide est redemandée, et répondre non annule la suppression.

    Pourquoi : c'est une action destructrice : elle ne doit partir que sur un oui clair.
    """
    client = Mock()

    output = run_menu(client, ["7", "1", "peut-être", "n", "0"])

    assert "Répondez par" in output
    assert "Suppression annulée." in output
    client.delete_post.assert_not_called()


# ---------- Rapport (option 8) ----------

def test_report_of_a_user_with_comments():
    """L'option 8 affiche l'utilisateur, les totaux et le post le plus commenté.

    Pourquoi : c'est la présentation attendue du rapport. Avec un seul post, pas d'égalité à signaler.
    """
    client = Mock()
    client.get_user_report.return_value = report()

    output = run_menu(client, ["8", "1", "0"])

    assert "Utilisateur : Leanne Graham" in output
    assert "Email : Sincere@april.biz" in output
    assert "Nombre total de commentaires : 1" in output
    assert "Post le plus commenté :" in output
    assert "  Titre : Titre 1" in output
    assert "  Commentaires : 1" in output
    assert "à égalité" not in output


def test_report_signals_a_tie():
    """Quand plusieurs posts sont à égalité, le rapport le signale.

    Pourquoi : sans cette mention, l'utilisateur croirait qu'un post se démarque des autres.
    """
    client = Mock()
    posts = [Post.from_dict(post_json(1)), Post.from_dict(post_json(2))]
    client.get_user_report.return_value = UserReport(User.from_dict(USER_JSON), posts, [])

    assert "(2 posts sont à égalité, le premier est affiché.)" in run_menu(client, ["8", "1", "0"])


def test_report_of_a_user_without_posts():
    """Un utilisateur sans post a un rapport sans ligne « post le plus commenté ».

    Pourquoi : il n'y a rien à afficher, et le code ne doit pas tenter de lire un post absent.
    """
    client = Mock()
    client.get_user_report.return_value = UserReport(User.from_dict(USER_JSON), [], [])

    output = run_menu(client, ["8", "1", "0"])

    assert "Aucun post pour l'utilisateur 1." in output
    assert "Post le plus commenté" not in output
