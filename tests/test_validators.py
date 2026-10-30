"""Tests de validators.py : contrôle de ce que l'utilisateur saisit.

Comment lire un test :
- une fonction dont le nom commence par test_ est lancée automatiquement par pytest ;
- `assert condition` fait échouer le test si la condition est fausse ;
- @pytest.mark.parametrize lance le même test une fois par ligne de données ;
- `with pytest.raises(Erreur)` vérifie que le bloc déclenche bien cette erreur.
"""
import pytest

import validators
from exceptions import ValidationError


# ---------- Identifiants ----------

@pytest.mark.parametrize("raw, expected", [
    ("1", 1),
    (" 42 ", 42),    # les espaces autour sont retirés
    ("+7", 7),
    ("007", 7),      # les zéros de tête sont ignorés
    (12, 12),        # l'interface web peut envoyer un vrai nombre
])
def test_valid_ids(raw, expected):
    """Les écritures correctes d'un identifiant donnent le bon nombre.

    Pourquoi : un identifiant valide ne doit jamais être refusé, quelle que soit sa présentation.
    """
    assert validators.parse_positive_id(raw) == expected


@pytest.mark.parametrize("raw, key", [
    ("", "error_required"),
    ("   ", "error_required"),
    (None, "error_required"),
    ("abc", "error_not_integer"),
    ("1.5", "error_not_integer"),
    ("1_000", "error_not_integer"),                       # accepté par int(), refusé ici
    ("١٢", "error_not_integer"),                          # chiffres arabes, même piège
    ("0", "error_not_positive"),
    ("000", "error_not_positive"),
    ("-3", "error_not_positive"),
    pytest.param("-" + "9" * 5000, "error_not_positive", id="negatif-5000-chiffres"),
    ("99999999999", "error_id_too_large"),
    pytest.param("9" * 5000, "error_id_too_large", id="5000-chiffres"),  # int() planterait
])
def test_invalid_ids(raw, key):
    """Chaque identifiant invalide est refusé avec le message qui lui correspond.

    Pourquoi : ces cas ont provoqué de vrais pièges, comme le nombre de 5000 chiffres
    qui faisait planter int(). Le bon message aide l'utilisateur à corriger sa saisie.
    """
    with pytest.raises(ValidationError) as error:
        validators.parse_positive_id(raw)
    assert error.value.key == key  # error.value est l'erreur attrapée


@pytest.mark.parametrize("raw", [True, 1.5, ["1"], {"id": 1}])
def test_non_text_values_are_rejected(raw):
    """Une valeur JSON qui n'est ni un texte ni un entier est refusée comme identifiant.

    Pourquoi : l'interface web envoie du JSON, et en Python True vaut 1. Sans ce
    contrôle, `true` serait pris pour l'identifiant 1.
    """
    with pytest.raises(ValidationError) as error:
        validators.parse_positive_id(raw)
    assert error.value.key == "error_invalid_input"


def test_id_at_the_limit():
    """Le plus grand identifiant autorisé passe ; le suivant est refusé.

    Pourquoi : les erreurs se cachent souvent à la frontière (> au lieu de >=).
    """
    assert validators.parse_positive_id(str(2**31 - 1)) == 2**31 - 1
    with pytest.raises(ValidationError):
        validators.parse_positive_id(str(2**31))


# ---------- Textes ----------

def test_required_text_is_stripped():
    """Les espaces au début et à la fin d'un texte sont retirés.

    Pourquoi : un espace copié-collé par erreur ne doit pas se retrouver dans les données.
    """
    assert validators.require_text("  Bonjour  ") == "Bonjour"


@pytest.mark.parametrize("raw", ["", "   ", None])
def test_required_text_rejects_empty(raw):
    """Un champ obligatoire vide, ou rempli d'espaces, est refusé.

    Pourquoi : un titre composé d'espaces paraît rempli mais ne contient rien.
    """
    with pytest.raises(ValidationError) as error:
        validators.require_text(raw)
    assert error.value.key == "error_required"


def test_title_too_long_is_rejected():
    """Un titre de 200 caractères passe ; à 201, il est refusé et le message donne les deux longueurs.

    Pourquoi : le brief demande de limiter la longueur, et l'utilisateur doit savoir de combien il dépasse.
    """
    assert validators.validate_title("x" * 200) == "x" * 200
    with pytest.raises(ValidationError) as error:
        validators.validate_title("x" * 201)  # "x" * 201 répète x 201 fois
    assert error.value.key == "error_too_long"
    assert error.value.params == {"max": 200, "length": 201}


def test_optional_text():
    """Un champ facultatif vide donne None ; rempli, il est nettoyé et sa longueur contrôlée.

    Pourquoi : dans la mise à jour d'un post, un champ vide signifie « garder l'ancienne valeur ».
    """
    assert validators.validate_optional_title("   ") is None
    assert validators.validate_optional_title(" Nouveau ") == "Nouveau"
    with pytest.raises(ValidationError):
        validators.validate_optional_name("x" * 101)


@pytest.mark.parametrize("raw", [
    "01 23 45 67 89",
    "01-23-45-67-89",
    "06.12.34.56.78",
    "0123456789",
])
def test_valid_phone(raw):
    assert validators.validate_phone(raw) == raw


@pytest.mark.parametrize("raw", [
    "01AB234567",
    "061234567",
    "0012345678",
    "+33123456789",
    "01 23 45 67 8a",
    "telephone",
])
def test_phone_rejects_letters(raw):
    with pytest.raises(ValidationError) as error:
        validators.validate_phone(raw)
    assert error.value.key == "error_invalid_phone"


def test_phone_rejects_more_than_14_characters():
    with pytest.raises(ValidationError) as error:
        validators.validate_phone("01 23 45 67 890")
    assert error.value.key == "error_too_long"


# ---------- Réponses et choix ----------

@pytest.mark.parametrize("raw, expected", [("o", True), ("O", True), (" n ", False)])
def test_yes_no(raw, expected):
    """La réponse oui/non accepte les majuscules et les espaces.

    Pourquoi : la confirmation d'une suppression ne doit pas échouer pour une simple majuscule.
    """
    assert validators.parse_yes_no(raw, "o", "n") is expected


def test_yes_no_rejects_other_answers():
    """Toute autre réponse est refusée, et le message rappelle les deux réponses possibles.

    Pourquoi : une suppression ne doit jamais partir sur une réponse ambiguë.
    """
    with pytest.raises(ValidationError) as error:
        validators.parse_yes_no("oui", "o", "n")
    assert error.value.params == {"yes": "o", "no": "n"}


def test_menu_choice():
    """Un choix proposé est accepté ; un choix absent de la liste est refusé.

    Pourquoi : c'est ce contrôle qui protège le choix de la langue au démarrage.
    """
    assert validators.parse_menu_choice(" 2 ", {"1", "2"}) == "2"
    with pytest.raises(ValidationError):
        validators.parse_menu_choice("3", {"1", "2"})


# ---------- Emails ----------

@pytest.mark.parametrize("raw", [
    "a@b.fr",
    " Prenom.Nom@exemple.com ",
    "Sincere@april.biz",               # adresses réelles de JSONPlaceholder
    "Lucio_Hettinger@annie.ca",
    "prenom.nom+tag@exemple.co.uk",
    "o'neil@exemple.ie",
    "a_b-c@x-y.io",
    "contact@société.fr",              # domaine accentué
    "contact@xn--socit-esab.fr",       # le même, déjà converti par le navigateur
    "x" * 64 + "@b.fr",                # 64 caractères avant le @ : limite autorisée
])
def test_valid_email(raw):
    """Les adresses correctes sont acceptées et renvoyées sans espaces autour.

    Pourquoi : une validation trop stricte bloquerait de vrais utilisateurs, comme
    un nom avec une apostrophe ou un domaine accentué.
    """
    assert validators.validate_email(raw) == raw.strip()


@pytest.mark.parametrize("raw", [
    "ab.fr",                 # pas de @
    "a@b",                   # pas d'extension
    "a b@c.fr",              # espace
    "@b.fr",                 # rien avant le @
    "a@",                    # rien après le @
    "a@b@c.fr",              # deux @
    ".a@b.fr",               # point au début
    "a.@b.fr",               # point à la fin
    "a..b@c.fr",             # deux points de suite
    "a,b@c.fr",              # caractère interdit
    "a(b)@c.fr",
    "josé@exemple.fr",       # accent avant le @
    "a@.fr",                 # étiquette vide
    "a@b..fr",
    "a@b.fr.",               # point final
    "a@-b.fr",               # tiret au début d'une étiquette
    "a@b-.fr",               # tiret à la fin d'une étiquette
    "a@b_c.fr",              # _ interdit dans un domaine
    "a@b.c",                 # extension trop courte
    "a@b.123",               # extension numérique
    "a@[127.0.0.1]",         # adresse IP
    "x" * 65 + "@b.fr",      # plus de 64 caractères avant le @
    "a@" + "b" * 64 + ".fr", # étiquette de plus de 63 caractères
])
def test_invalid_email(raw):
    """Chaque adresse mal formée est refusée.

    Pourquoi : chaque ligne correspond à une règle de la norme. Avant la validation
    actuelle, la plupart de ces adresses étaient acceptées.
    """
    with pytest.raises(ValidationError) as error:
        validators.validate_email(raw)
    assert error.value.key == "error_invalid_email"


def test_email_too_long():
    """Une adresse de plus de 254 caractères est refusée avec le message de longueur.

    Pourquoi : c'est la limite de la norme RFC 5321.
    """
    with pytest.raises(ValidationError) as error:
        validators.validate_email("a@" + "b." * 126 + "fr")
    assert error.value.key == "error_too_long"
    assert error.value.params["max"] == 254


def test_email_is_required():
    """Une adresse vide est signalée comme manquante, et non comme mal formée.

    Pourquoi : « champ obligatoire » est plus clair que « format invalide » pour un champ vide.
    """
    with pytest.raises(ValidationError) as error:
        validators.validate_email("   ")
    assert error.value.key == "error_required"


# ---------- Adresses web et booléens ----------

@pytest.mark.parametrize("raw, valid", [
    ("https://picsum.photos/seed/1/600", True),
    ("http://exemple.fr", True),
    ("https://a.fr:8080/x?y=1", True),
    ("ftp://exemple.fr", False),    # protocole non web
    ("exemple.fr", False),          # pas de protocole
    ("https://", False),            # pas de domaine
    ("http://[", False),            # crochet non fermé : urlsplit lèverait ValueError
    ("https://a b.fr/x", False),    # espace
    ("http://:80", False),          # pas de nom de domaine
    ("http://a.fr:abc/", False),    # port non numérique
    ("http://a.fr:0/", False),      # le port 0 n'existe pas
])
def test_url(raw, valid):
    """Seules les adresses http(s) complètes sont acceptées.

    Pourquoi : ces adresses servent à afficher des images, et `http://[` faisait planter
    l'analyse avant ce contrôle.
    """
    if valid:
        assert validators.validate_url(raw) == raw
    else:
        with pytest.raises(ValidationError):
            validators.validate_url(raw)


@pytest.mark.parametrize("raw, expected", [(True, True), (False, False), (None, False),
                                           ("true", True), ("false", False), ("0", False), (" TRUE ", True)])
def test_parse_bool(raw, expected):
    """Vrai et faux sont compris en JSON comme en texte ; une valeur absente vaut faux.

    Pourquoi : le filtre ?completed=true de l'adresse arrive sous forme de texte.
    """
    assert validators.parse_bool(raw) is expected


@pytest.mark.parametrize("raw", ["oui", 2, [True], ""])
def test_parse_bool_rejects_other_values(raw):
    """Toute autre valeur est refusée, y compris le texte vide.

    Pourquoi : deviner le sens d'une valeur douteuse pourrait changer une tâche sans raison.
    """
    with pytest.raises(ValidationError):
        validators.parse_bool(raw)
