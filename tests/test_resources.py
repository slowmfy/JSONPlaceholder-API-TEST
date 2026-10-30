"""Tests de resources.py : validation des champs et conversion vers le JSON de l'API."""
import pytest

from exceptions import ResourceNotFoundError, ValidationError
from i18n import load_messages
from resources import RESOURCES, get_resource


# ---------- Validation complète (création) ----------

def test_validate_returns_clean_values():
    """Les valeurs reçues sont nettoyées et converties : "3" devient 3, les espaces disparaissent.

    Pourquoi : l'API doit recevoir des données propres, quelle que soit l'interface d'origine.
    """
    values = RESOURCES["posts"].validate({"user_id": "3", "title": "  T  ", "body": "B"})
    assert values == {"user_id": 3, "title": "T", "body": "B"}


def test_validate_reports_the_faulty_field():
    """Une erreur indique quel champ est en faute.

    Pourquoi : l'interface web affiche le message à côté du bon champ, ici l'adresse de la photo.
    """
    with pytest.raises(ValidationError) as error:
        RESOURCES["photos"].validate({"album_id": 1, "title": "T", "url": "ftp://x", "thumbnail_url": "https://x.fr"})
    assert (error.value.key, error.value.field) == ("error_invalid_url", "url")


def test_optional_fields_are_dropped_when_empty():
    """Un champ facultatif vide n'est pas envoyé à la création.

    Pourquoi : envoyer un téléphone vide serait inutile.
    """
    values = RESOURCES["users"].validate({"name": "A", "username": "a", "email": "a@b.fr", "phone": "  "})
    assert values == {"name": "A", "username": "a", "email": "a@b.fr"}


def test_todo_completed_defaults_to_false():
    """Une tâche créée sans préciser son état n'est pas terminée.

    Pourquoi : c'est le sens attendu d'une nouvelle tâche.
    """
    assert RESOURCES["todos"].validate({"user_id": 1, "title": "T"})["completed"] is False


# ---------- Validation partielle (modification) ----------

def test_partial_validation_only_checks_given_fields():
    """En modification, seuls les champs envoyés sont contrôlés.

    Pourquoi : changer un titre ne doit pas obliger à renvoyer l'auteur et le contenu.
    """
    assert RESOURCES["posts"].validate({"title": "Nouveau"}, partial=True) == {"title": "Nouveau"}


def test_partial_validation_still_rejects_empty_values():
    """Un champ obligatoire envoyé vide reste refusé en modification.

    Pourquoi : on ne doit pas pouvoir effacer le titre d'un post.
    """
    with pytest.raises(ValidationError) as error:
        RESOURCES["posts"].validate({"title": ""}, partial=True)
    assert error.value.field == "title"


def test_partial_validation_can_clear_an_optional_field():
    """Un champ facultatif peut être vidé en modification.

    Pourquoi : ce défaut existait : effacer un téléphone dans le formulaire n'avait aucun effet.
    """
    assert RESOURCES["users"].validate({"phone": "  "}, partial=True) == {"phone": ""}


# ---------- Conversions et filtres ----------

def test_to_api_uses_camel_case_names():
    """Les noms de l'application sont convertis vers ceux de l'API.

    Pourquoi : JSONPlaceholder attend thumbnailUrl et non thumbnail_url.
    """
    api = RESOURCES["photos"].to_api({"album_id": 1, "title": "T", "url": "u", "thumbnail_url": "t"})
    assert api == {"albumId": 1, "title": "T", "url": "u", "thumbnailUrl": "t"}


def test_filters_are_validated_then_converted():
    """Les filtres sont d'abord validés, puis traduits au format de l'adresse de l'API.

    Pourquoi : l'application travaille avec le nombre 2 et le booléen True, l'API attend userId=2 et completed=true.
    """
    filters = {"user_id": "2", "completed": "true"}

    assert RESOURCES["todos"].parse_filters(filters) == {"user_id": 2, "completed": True}
    assert RESOURCES["todos"].api_filters(filters) == {"userId": 2, "completed": "true"}


@pytest.mark.parametrize("filters, key, field", [
    ({"title": "x"}, "error_unknown_filter", "title"),
    ({"user_id": "abc"}, "error_not_integer", "user_id"),
    ({"completed": "peut-être"}, "error_not_boolean", "completed"),
])
def test_invalid_filters(filters, key, field):
    """Un filtre inconnu ou de mauvais type est refusé, en nommant le filtre en cause.

    Pourquoi : un filtre invalide doit être arrêté avant d'atteindre l'API.
    """
    with pytest.raises(ValidationError) as error:
        RESOURCES["todos"].api_filters(filters)
    assert (error.value.key, error.value.field) == (key, field)


# ---------- Cohérence de la table ----------

def test_unknown_resource():
    """Demander une ressource qui n'existe pas déclenche l'erreur prévue.

    Pourquoi : /api/articles doit répondre « introuvable », pas provoquer une erreur technique.
    """
    with pytest.raises(ResourceNotFoundError):
        get_resource("articles")


def test_every_field_matches_the_model_and_the_api():
    """Chaque champ de la table correspond bien au modèle Python et au nom utilisé par l'API.

    Pourquoi : une faute de frappe dans la table ferait perdre un champ sans provoquer d'erreur.
    Le test fabrique un JSON à partir de la table, puis vérifie que le modèle retrouve chaque valeur.
    """
    for resource in RESOURCES.values():
        api_json = {"id": 1}
        for field in resource.fields:
            if field.kind == "bool":
                value = True
            elif field.kind == "ref":
                value = 1
            else:
                value = field.name
            api_json[field.api_name] = value

        item = resource.model.from_dict(api_json)

        for field in resource.fields:
            # getattr lit le champ de l'objet à partir de son nom.
            assert getattr(item, field.name) == api_json[field.api_name]
            assert field.kind != "ref" or field.ref in RESOURCES  # la cible d'une référence existe
        assert set(resource.filters) <= {field.name for field in resource.fields}


def test_every_resource_has_translated_messages():
    """Chaque ressource a ses messages et ses libellés dans le fichier de langue.

    Pourquoi : ajouter une ressource sans ses traductions afficherait des clés brutes à l'écran.
    """
    messages = load_messages("fr")
    for resource in RESOURCES.values():
        keys = [resource.not_found_key, f"res_{resource.name}"]
        keys += [f"{action}_{resource.singular}" for action in ("created", "updated", "deleted")]
        keys += [f"field_{field.name}" for field in resource.fields]
        assert not [key for key in keys if key not in messages]
