"""Objets de l'application, construits à partir des réponses JSON de l'API.

L'API renvoie du JSON, lu en Python sous forme de dictionnaires. Ce fichier les
transforme en objets clairs : on écrit post.title plutôt que data["title"], et
une réponse incomplète est détectée ici, pas au milieu d'un affichage.

@dataclass est un « décorateur » : placé au-dessus d'une classe, il lui ajoute des
fonctions. Il écrit lui-même le __init__ à partir de la liste des champs
(nom: type). Une valeur après le = rend le champ facultatif.

@classmethod indique une fonction appelée sur la classe et non sur un objet :
Post.from_dict(data) construit un Post à partir d'un dictionnaire.
"""
import logging
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field

from exceptions import InvalidResponseError

logger = logging.getLogger(__name__)


# Permet d'écrire « with _parsing(...): » : le code du bloc s'exécute à l'endroit
# du yield. Toute erreur de lecture y est interceptée, au même endroit pour tous
# les modèles, au lieu de répéter ce try / except dans chacun.
@contextmanager
def _parsing(model, data):
    """Transforme un champ manquant ou mal typé en InvalidResponseError."""
    try:
        yield
    except (KeyError, TypeError, AttributeError) as exc:
        logger.error("JSON inattendu pour %s : %r (%s)", model, data, exc)
        raise InvalidResponseError() from exc


def _field(data, name, expected):
    """Lit un champ obligatoire et vérifie son type JSON."""
    value = data[name]
    if type(value) is not expected:
        raise TypeError(f"{name} doit être de type {expected.__name__}")
    return value


def _optional_field(data, name, expected, default=""):
    """Lit un champ facultatif et vérifie son type lorsqu'il est présent."""
    if name not in data or data[name] is None:
        return default
    return _field(data, name, expected)


@dataclass
class User:
    """Un utilisateur. L'adresse et l'entreprise sont aplaties en champs simples."""

    id: int
    name: str
    username: str
    email: str
    phone: str = ""
    website: str = ""
    street: str = ""
    suite: str = ""
    zipcode: str = ""
    city: str = ""
    company_name: str = ""
    company_catchphrase: str = ""

    @classmethod
    def from_dict(cls, data):
        # data["id"] exige le champ ; data.get("phone", "") le remplace par "" s'il manque.
        with _parsing("User", data):
            address = data.get("address") or {}
            company = data.get("company") or {}
            return cls(
                id=_field(data, "id", int),
                name=_field(data, "name", str),
                username=_field(data, "username", str),
                email=_field(data, "email", str),
                phone=_optional_field(data, "phone", str),
                website=_optional_field(data, "website", str),
                street=_optional_field(address, "street", str),
                suite=_optional_field(address, "suite", str),
                zipcode=_optional_field(address, "zipcode", str),
                city=_optional_field(address, "city", str),
                company_name=_optional_field(company, "name", str),
                company_catchphrase=_optional_field(company, "catchPhrase", str),
            )


@dataclass
class Post:
    """Un article publié par un utilisateur."""

    id: int
    user_id: int
    title: str
    body: str

    @classmethod
    def from_dict(cls, data):
        with _parsing("Post", data):
            return cls(
                id=_field(data, "id", int),
                user_id=_field(data, "userId", int),
                title=_field(data, "title", str),
                body=_field(data, "body", str),
            )


@dataclass
class Comment:
    """Un commentaire sur un post."""

    id: int
    post_id: int
    name: str
    email: str
    body: str

    @classmethod
    def from_dict(cls, data):
        with _parsing("Comment", data):
            return cls(
                id=_field(data, "id", int),
                post_id=_field(data, "postId", int),
                name=_field(data, "name", str),
                email=_field(data, "email", str),
                body=_field(data, "body", str),
            )


@dataclass
class Album:
    """Un album photo d'un utilisateur."""

    id: int
    user_id: int
    title: str

    @classmethod
    def from_dict(cls, data):
        with _parsing("Album", data):
            return cls(
                id=_field(data, "id", int),
                user_id=_field(data, "userId", int),
                title=_field(data, "title", str),
            )


@dataclass
class Photo:
    """Une photo d'un album."""

    id: int
    album_id: int
    title: str
    url: str
    thumbnail_url: str

    @classmethod
    def from_dict(cls, data):
        with _parsing("Photo", data):
            return cls(
                id=_field(data, "id", int),
                album_id=_field(data, "albumId", int),
                title=_field(data, "title", str),
                url=_field(data, "url", str),
                thumbnail_url=_field(data, "thumbnailUrl", str),
            )


@dataclass
class Todo:
    """Une tâche à faire d'un utilisateur."""

    id: int
    user_id: int
    title: str
    completed: bool

    @classmethod
    def from_dict(cls, data):
        with _parsing("Todo", data):
            return cls(
                id=_field(data, "id", int),
                user_id=_field(data, "userId", int),
                title=_field(data, "title", str),
                completed=_field(data, "completed", bool),
            )


@dataclass
class UserReport:
    """Synthèse d'un utilisateur : ses posts et les commentaires reçus."""

    user: User
    posts: list
    comments: list = field(default_factory=list)  # liste vide par défaut

    # @property permet de lire le résultat comme un champ : report.post_count, sans ().
    @property
    def post_count(self):
        return len(self.posts)

    @property
    def comment_count(self):
        # Seuls les commentaires des posts de l'utilisateur sont comptés.
        post_ids = {post.id for post in self.posts}  # ensemble des identifiants
        return sum(1 for comment in self.comments if comment.post_id in post_ids)

    def comments_per_post(self):
        """Nombre de commentaires par post, y compris les posts sans commentaire."""
        # Counter compte les valeurs : combien de commentaires pour chaque post_id.
        counts = Counter(comment.post_id for comment in self.comments)
        # Construit un dictionnaire {id du post: nombre de commentaires}.
        return {post.id: counts.get(post.id, 0) for post in self.posts}

    def most_commented(self):
        """Renvoie (post, nombre de commentaires, nombre de posts à égalité), ou None sans post.

        En cas d'égalité, le premier post (dans l'ordre de l'API) est retenu.
        """
        if not self.posts:
            return None
        counts = self.comments_per_post()
        best = max(self.posts, key=lambda post: counts[post.id])
        best_count = counts[best.id]
        ties = sum(1 for count in counts.values() if count == best_count)
        return best, best_count, ties
