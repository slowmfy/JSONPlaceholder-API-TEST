"""Tests de models.py : construction des objets et calculs du rapport utilisateur."""
import pytest

from conftest import USER_JSON, comment_json, post_json
from exceptions import InvalidResponseError
from models import Album, Comment, Photo, Post, Todo, User, UserReport


def make_report(comment_post_ids, post_ids=(1, 2, 3)):
    """Fabrique un rapport : un post par identifiant et un commentaire par valeur de la liste.

    make_report([1, 2, 2]) crée les posts 1, 2 et 3, avec un commentaire sur le post 1
    et deux sur le post 2.
    """
    posts = [Post.from_dict(post_json(post_id)) for post_id in post_ids]
    comments = [Comment.from_dict(comment_json(i, post_id)) for i, post_id in enumerate(comment_post_ids)]
    return UserReport(user=User.from_dict(USER_JSON), posts=posts, comments=comments)


# ---------- Construction depuis le JSON ----------

@pytest.mark.parametrize("model, data, expected", [
    (Post, post_json(5, user_id=2), Post(5, 2, "Titre 5", "Contenu\n5")),
    (Todo, {"id": 1, "userId": 2, "title": "T", "completed": True}, Todo(1, 2, "T", True)),
    (Album, {"id": 1, "userId": 2, "title": "T"}, Album(1, 2, "T")),
    (Photo, {"id": 1, "albumId": 2, "title": "T", "url": "u", "thumbnailUrl": "t"}, Photo(1, 2, "T", "u", "t")),
])
def test_from_dict_renames_fields(model, data, expected):
    """Chaque modèle convertit les noms de l'API : userId devient user_id, par exemple.

    Pourquoi : le reste de l'application ne doit dépendre que des noms Python.
    """
    assert model.from_dict(data) == expected


def test_user_flattens_nested_fields():
    """L'adresse et l'entreprise imbriquées deviennent de simples champs de User.

    Pourquoi : on écrit user.city et non data["address"]["city"], et une erreur de chemin
    ferait disparaître la ville ou l'entreprise de l'affichage.
    """
    user = User.from_dict(USER_JSON)

    assert user.city == "Gwenborough"
    assert user.zipcode == "92998-3874"
    assert user.website == "hildegard.org"
    assert user.company_name == "Romaguera-Crona"


def test_user_optional_fields_default_to_empty():
    """Un utilisateur sans adresse ni entreprise reste valide, avec des champs vides.

    Pourquoi : une création de POST /users renvoie seulement les champs envoyés.
    """
    user = User.from_dict({"id": 1, "name": "A", "username": "a", "email": "a@b.c"})
    assert user.city == "" and user.company_name == ""


@pytest.mark.parametrize("data", [None, "texte", {"id": 1}, [1, 2]])
def test_malformed_post_raises_invalid_response(data):
    """Une donnée qui n'a pas la forme d'un post déclenche l'erreur prévue.

    Pourquoi : aucune réponse étrange de l'API ne doit afficher une erreur Python.
    """
    with pytest.raises(InvalidResponseError):
        Post.from_dict(data)


@pytest.mark.parametrize("field, value", [
    ("id", "1"),
    ("userId", 1.5),
    ("title", 123),
    ("body", None),
])
def test_malformed_post_field_type_raises_invalid_response(field, value):
    """Un champ de post mal typé est rejeté avant de devenir un objet métier."""
    data = post_json(1)
    data[field] = value

    with pytest.raises(InvalidResponseError):
        Post.from_dict(data)


def test_malformed_todo_boolean_raises_invalid_response():
    """Une valeur truthy arbitraire ne doit pas être convertie en booléen."""
    with pytest.raises(InvalidResponseError):
        Todo.from_dict({"id": 1, "userId": 2, "title": "T", "completed": "true"})


# ---------- Calculs du rapport ----------

def test_report_counts():
    """Le rapport compte les posts, les commentaires, et les commentaires de chaque post.

    Pourquoi : ces chiffres sont le cœur du rapport utilisateur demandé par le brief.
    """
    report = make_report([1, 2, 2, 3, 3, 3])
    assert report.post_count == 3
    assert report.comment_count == 6
    assert report.comments_per_post() == {1: 1, 2: 2, 3: 3}


def test_most_commented_post():
    """Le post qui a le plus de commentaires est retrouvé, avec son nombre de commentaires.

    Pourquoi : le test place le maximum sur le post 3 pour prouver que le premier n'est pas pris par hasard.
    """
    post, count, ties = make_report([1, 3, 3, 2]).most_commented()
    assert (post.id, count, ties) == (3, 2, 1)


def test_most_commented_tie_keeps_first_post():
    """En cas d'égalité, le premier post est gardé et le nombre d'ex æquo est indiqué.

    Pourquoi : c'est le cas réel de l'API, où chaque post a exactement 5 commentaires.
    """
    post, count, ties = make_report([1, 2, 3]).most_commented()
    assert (post.id, count, ties) == (1, 1, 3)


def test_post_without_comments_is_counted_as_zero():
    """Un post sans commentaire apparaît avec 0, au lieu d'être oublié.

    Pourquoi : sans cela, le calcul du post le plus commenté planterait sur les posts absents.
    """
    report = make_report([2])
    assert report.comments_per_post() == {1: 0, 2: 1, 3: 0}
    assert report.most_commented()[0].id == 2


def test_comments_of_other_posts_are_ignored():
    """Un commentaire lié au post d'un autre utilisateur n'est pas compté.

    Pourquoi : le total doit concerner uniquement les posts de l'utilisateur du rapport.
    """
    assert make_report([1, 99]).comment_count == 1


def test_user_without_posts():
    """Un utilisateur sans post donne des totaux à 0 et aucun post le plus commenté.

    Pourquoi : chercher un maximum dans une liste vide provoquerait une erreur.
    """
    report = make_report([], post_ids=())
    assert report.post_count == 0
    assert report.comment_count == 0
    assert report.most_commented() is None
