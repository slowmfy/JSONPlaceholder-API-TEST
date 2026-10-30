"""Description des ressources de JSONPlaceholder.

Une « ressource » est un type de données de l'API : users, posts, comments, albums,
photos, todos. La table RESOURCES, en bas de ce fichier, décrit chacune une seule
fois : son modèle, ses champs modifiables (avec leur validateur) et ses filtres.

Le client HTTP, l'API web et les formulaires de l'interface Angular s'appuient
tous sur cette table : ajouter un champ ou une ressource se fait ici.

Vocabulaire des noms :
- snake_case (user_id) : convention de Python, utilisée dans l'application ;
- camelCase (userId) : convention du JSON renvoyé par JSONPlaceholder.
"""
from collections.abc import Callable
from dataclasses import dataclass

import validators
from exceptions import ResourceNotFoundError, ValidationError
from models import Album, Comment, Photo, Post, Todo, User


# frozen=True interdit de modifier l'objet après sa création.
@dataclass(frozen=True)
class Field:
    """Un champ d'une ressource."""

    name: str          # nom dans l'application (snake_case)
    api_name: str      # nom dans le JSON de JSONPlaceholder (camelCase)
    kind: str          # type de saisie : text, textarea, email, url, bool, ref
    parse: Callable    # validateur (validators.py)
    required: bool = True
    ref: str | None = None  # ressource référencée quand kind == "ref"

    def describe(self):
        """Description envoyée à l'interface web pour générer les formulaires."""
        return {"name": self.name, "kind": self.kind, "required": self.required, "ref": self.ref}


@dataclass(frozen=True)
class Resource:
    """Une ressource de l'API et les opérations qui ne dépendent que de sa description."""

    name: str          # segment d'URL : /posts
    singular: str      # préfixe des clés de traduction : post_not_found
    model: type
    fields: tuple
    filters: tuple = ()  # champs utilisables en filtre : /posts?userId=1

    @property
    def not_found_key(self):
        return f"{self.singular}_not_found"

    def field(self, name):
        """Renvoie le champ nommé `name`."""
        return next(field for field in self.fields if field.name == name)

    # @staticmethod : fonction rangée dans la classe, qui n'a pas besoin de « self ».
    @staticmethod
    def _parse(field, raw):
        """Applique le validateur du champ ; une erreur indique le champ en faute."""
        try:
            return field.parse(raw)
        except ValidationError as exc:
            exc.field = field.name
            raise  # relance la même erreur, désormais complétée

    def validate(self, data, partial=False):
        """Valide les champs reçus ; `partial` (PATCH) n'exige que les champs présents.

        Les champs inconnus sont ignorés.
        """
        values = {}
        for field in self.fields:
            if partial and field.name not in data:
                continue  # passe directement au champ suivant
            value = self._parse(field, data.get(field.name))
            if value is not None:
                values[field.name] = value
            elif partial:
                values[field.name] = ""  # champ facultatif vidé : à effacer aussi côté API
        if partial and not values:
            raise ValidationError("error_nothing_to_update")
        return values

    def to_api(self, values):
        """Valeurs validées -> corps JSON de JSONPlaceholder (noms en camelCase)."""
        return {field.api_name: values[field.name] for field in self.fields if field.name in values}

    def parse_filters(self, filters):
        """Valide les filtres reçus ; un filtre inconnu est refusé."""
        values = {}
        # .items() parcourt un dictionnaire par paires (clé, valeur).
        for name, raw in filters.items():
            if name not in self.filters:
                raise ValidationError("error_unknown_filter", field=name, value=name)
            values[name] = self._parse(self.field(name), raw)
        return values

    def api_filters(self, filters):
        """Filtres de l'application -> paramètres d'URL de JSONPlaceholder."""
        params = {}
        for name, value in self.parse_filters(filters).items():
            # JSONPlaceholder attend true/false en minuscules.
            params[self.field(name).api_name] = str(value).lower() if isinstance(value, bool) else value
        return params

    def describe(self):
        """Description de la ressource envoyée à l'interface web."""
        return {
            "name": self.name,
            "fields": [field.describe() for field in self.fields],
            "filters": list(self.filters),
        }


def _ref(name, api_name, resource):
    """Crée un champ qui désigne un élément d'une autre ressource (l'auteur d'un post...)."""
    return Field(name, api_name, "ref", validators.parse_positive_id, ref=resource)


# La table : un dictionnaire {nom: Resource}, où chaque ligne Field décrit un champ.
RESOURCES = {resource.name: resource for resource in (
    Resource("users", "user", User, (
        Field("name", "name", "text", validators.validate_name),
        Field("username", "username", "text", validators.validate_name),
        Field("email", "email", "email", validators.validate_email),
        Field("phone", "phone", "phone", validators.validate_phone, required=False),
        Field("website", "website", "text", validators.validate_optional_name, required=False),
    )),
    Resource("posts", "post", Post, (
        _ref("user_id", "userId", "users"),
        Field("title", "title", "text", validators.validate_title),
        Field("body", "body", "textarea", validators.validate_body),
    ), filters=("user_id",)),
    Resource("comments", "comment", Comment, (
        _ref("post_id", "postId", "posts"),
        Field("name", "name", "text", validators.validate_title),
        Field("email", "email", "email", validators.validate_email),
        Field("body", "body", "textarea", validators.validate_body),
    ), filters=("post_id",)),
    Resource("albums", "album", Album, (
        _ref("user_id", "userId", "users"),
        Field("title", "title", "text", validators.validate_title),
    ), filters=("user_id",)),
    Resource("photos", "photo", Photo, (
        _ref("album_id", "albumId", "albums"),
        Field("title", "title", "text", validators.validate_title),
        Field("url", "url", "url", validators.validate_url),
        Field("thumbnail_url", "thumbnailUrl", "url", validators.validate_url),
    ), filters=("album_id",)),
    Resource("todos", "todo", Todo, (
        _ref("user_id", "userId", "users"),
        Field("title", "title", "text", validators.validate_title),
        Field("completed", "completed", "bool", validators.parse_bool, required=False),
    ), filters=("user_id", "completed")),
)}


def get_resource(name):
    """Renvoie la ressource `name`, ou signale qu'elle n'existe pas."""
    try:
        return RESOURCES[name]
    except KeyError:
        raise ResourceNotFoundError(resource=f"/{name}") from None
