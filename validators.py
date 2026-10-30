"""Contrôle des saisies utilisateur, effectué avant tout appel à l'API.

Les fonctions reçoivent la valeur brute saisie (texte de la console ou valeur
JSON envoyée par l'interface web) et renvoient la valeur nettoyée, ou déclenchent
une ValidationError portant la clé du message à afficher.

Un nom qui commence par _ indique, par convention, un élément interne à ce
fichier : les autres fichiers n'ont pas à l'utiliser.

re.compile prépare une « expression régulière » : un modèle qui décrit à quoi doit
ressembler un texte. Dans un modèle :
    [abc]   un caractère parmi a, b, c
    a-z     les lettres de a à z
    \\d      un chiffre
    +       une fois ou plus
    *       zéro fois ou plus
    ?       facultatif
    {2,63}  de 2 à 63 fois
    ( )     groupe
    |       ou
    \\.      un vrai point (seul, le point signifie « n'importe quel caractère »)
"""
import re
from urllib.parse import urlsplit

import config
from exceptions import ValidationError

# Un entier avec un signe facultatif. re.ASCII limite \d aux chiffres 0 à 9.
_INTEGER = re.compile(r"[+-]?\d+", re.ASCII)

# Avant le @ : caractères autorisés par la RFC 5322, séparés par des points isolés.
_EMAIL_ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
_EMAIL_LOCAL = re.compile(rf"{_EMAIL_ATOM}(\.{_EMAIL_ATOM})*")
# Après le @ : étiquettes de 63 caractères au plus, sans tiret au début ni à la fin,
# puis une extension en lettres (xn--... pour une extension accentuée).
_EMAIL_LABEL = r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?"
_EMAIL_DOMAIN = re.compile(rf"({_EMAIL_LABEL}\.)+([a-z]{{2,63}}|xn--{_EMAIL_LABEL})", re.IGNORECASE | re.ASCII)
_PHONE = re.compile(r"0[1-9](?:[ .-]?[0-9]{2}){4}", re.ASCII)


def _as_text(raw):
    """Texte nettoyé ; None (absence de valeur) devient "" et tout autre type est refusé."""
    if raw is None:
        return ""
    if isinstance(raw, bool) or not isinstance(raw, (str, int)):
        raise ValidationError("error_invalid_input")
    return str(raw).strip()  # strip retire les espaces au début et à la fin


def parse_positive_id(raw, max_value=config.MAX_ID):
    """Identifiant : obligatoire, entier, strictement positif et raisonnable."""
    text = _as_text(raw)
    if not text:
        raise ValidationError("error_required")
    if not _INTEGER.fullmatch(text):  # fullmatch : tout le texte doit suivre le modèle
        raise ValidationError("error_not_integer", value=text)
    digits = text.lstrip("+-").lstrip("0")  # retire le signe et les zéros de tête
    if text.startswith("-") or not digits:
        raise ValidationError("error_not_positive", value=text)
    # La longueur est comparée d'abord : int() refuse les nombres de plus de 4300 chiffres.
    if len(digits) > len(str(max_value)) or int(digits) > max_value:
        raise ValidationError("error_id_too_large", max=max_value)
    return int(digits)  # int convertit le texte en nombre entier


def require_text(raw, max_length=None):
    """Champ obligatoire : non vide après suppression des espaces, longueur limitée."""
    text = _as_text(raw)
    if not text:
        raise ValidationError("error_required")
    if max_length is not None and len(text) > max_length:  # len : longueur du texte
        raise ValidationError("error_too_long", max=max_length, length=len(text))
    return text


def optional_text(raw, max_length=None):
    """Champ facultatif : renvoie None s'il est vide, sinon le texte validé."""
    text = _as_text(raw)
    if not text:
        return None
    return require_text(text, max_length)


# Les fonctions suivantes appliquent la limite de longueur propre à chaque champ.

def validate_title(raw):
    return require_text(raw, config.MAX_TITLE_LENGTH)


def validate_body(raw):
    return require_text(raw, config.MAX_BODY_LENGTH)


def validate_name(raw):
    return require_text(raw, config.MAX_NAME_LENGTH)


def validate_optional_title(raw):
    return optional_text(raw, config.MAX_TITLE_LENGTH)


def validate_optional_body(raw):
    return optional_text(raw, config.MAX_BODY_LENGTH)


def validate_optional_name(raw):
    return optional_text(raw, config.MAX_NAME_LENGTH)


def validate_phone(raw):
    """Numéro français facultatif : 10 chiffres, avec séparateurs de groupes facultatifs."""
    text = optional_text(raw, config.MAX_PHONE_LENGTH)
    if text is not None and (not _PHONE.fullmatch(text) or not any(char.isdigit() for char in text)):
        raise ValidationError("error_invalid_phone", value=text)
    return text


def _domain_to_ascii(domain):
    """Domaine accentué (société.fr) -> forme ASCII xn-- ; "" si la conversion échoue."""
    try:
        return domain.encode("idna").decode("ascii")
    except UnicodeError:
        return ""


def _is_email(text):
    """Renvoie True si le texte a la forme d'une adresse email."""
    # rpartition coupe au dernier @ et renvoie : avant, le @ lui-même, après.
    local, at, domain = text.rpartition("@")
    return bool(
        at  # un @ a bien été trouvé
        and len(local) <= config.MAX_EMAIL_LOCAL_LENGTH
        and _EMAIL_LOCAL.fullmatch(local)
        and _EMAIL_DOMAIN.fullmatch(_domain_to_ascii(domain))
    )


def validate_email(raw):
    """Format d'une adresse email (RFC 5321 et 5322).

    Seul le format est contrôlé : prouver que l'adresse existe demanderait
    d'y envoyer un message de confirmation.
    """
    text = require_text(raw, config.MAX_EMAIL_LENGTH)
    if not _is_email(text):
        raise ValidationError("error_invalid_email", value=text)
    return text


def _is_web_url(text):
    """Renvoie True si le texte est une adresse http ou https complète."""
    # any : vrai si au moins un caractère du texte est un espace.
    if any(char.isspace() for char in text):
        return False
    try:
        parts = urlsplit(text)  # découpe l'adresse : protocole, domaine, port...
        return parts.scheme in ("http", "https") and bool(parts.hostname) and parts.port != 0
    except ValueError:  # crochet non fermé, port non numérique...
        return False


def validate_url(raw):
    """Adresse web complète : http(s)://domaine/..."""
    text = require_text(raw, config.MAX_URL_LENGTH)
    if not _is_web_url(text):
        raise ValidationError("error_invalid_url", value=text)
    return text


def parse_bool(raw):
    """Booléen (vrai ou faux) : true/false en JSON ou en texte ; absent vaut false."""
    if raw is None or isinstance(raw, bool):
        return bool(raw)
    text = _as_text(raw).lower()  # lower met le texte en minuscules
    if text in ("true", "1"):
        return True
    if text in ("false", "0"):
        return False
    raise ValidationError("error_not_boolean", value=text)


def parse_yes_no(raw, yes, no):
    """Réponse oui/non ; `yes` et `no` viennent du fichier de langue (o/n, y/n...)."""
    text = _as_text(raw).lower()
    if text == yes.lower():
        return True
    if text == no.lower():
        return False
    raise ValidationError("error_yes_no", yes=yes, no=no)


def parse_menu_choice(raw, choices):
    """Choix de menu : doit faire partie des options proposées."""
    text = _as_text(raw)
    if text not in choices:
        raise ValidationError("error_invalid_choice", value=text)
    return text
