"""Tests de api_client.py : traitement des réponses JSON et gestion des erreurs.

Le vrai client est utilisé, mais la connexion est remplacée par la fausse session de
conftest.py. Trois écritures reviennent souvent :
- session.request.return_value = ...   réponse renvoyée par la fausse API ;
- session.request.side_effect = ...    erreur à déclencher, ou liste de réponses
                                       successives (une par appel) ;
- session.request.call_args            requête que le client a réellement envoyée.
"""
import pytest
import requests

from conftest import USER_JSON, comment_json, make_response, post_json
from exceptions import (
    APIConnectionError,
    APITimeoutError,
    HTTPStatusError,
    InvalidResponseError,
    ResourceNotFoundError,
    ValidationError,
)
from models import Post, User


# ---------- Traitement des réponses JSON ----------

def test_get_users_returns_user_objects(client, session):
    """La liste JSON devient une liste d'objets User, avec une requête GET /users correcte.

    Pourquoi : c'est le trajet complet d'une lecture, de la requête envoyée à l'objet reçu.
    """
    # Préparation : la fausse API renverra un utilisateur.
    session.request.return_value = make_response(data=[USER_JSON])

    # Action.
    users = client.get_users()

    # Vérification : le résultat, puis la requête envoyée.
    assert users == [User.from_dict(USER_JSON)]
    session.request.assert_called_once_with(
        "GET", "https://api.test/users", params=None, json=None, timeout=3
    )


def test_get_posts_by_user_sends_query_parameter(client, session):
    """Les posts d'un utilisateur sont demandés avec le filtre ?userId=1.

    Pourquoi : sans ce paramètre, l'API renverrait les 100 posts de tout le monde.
    """
    session.request.return_value = make_response(data=[post_json(1), post_json(2)])

    posts = client.get_posts_by_user(1)

    assert [post.id for post in posts] == [1, 2]
    assert session.request.call_args.kwargs["params"] == {"userId": 1}


def test_get_comments_by_post(client, session):
    """Les commentaires d'un post sont demandés avec le filtre ?postId=3.

    Pourquoi : c'est l'option 4 du menu ; le nom postId diffère de user_id et de userId.
    """
    session.request.return_value = make_response(data=[comment_json(1, 3)])

    comments = client.get_comments_by_post(3)

    assert comments[0].post_id == 3
    assert session.request.call_args.kwargs["params"] == {"postId": 3}


def test_create_post_sends_payload_and_parses_response(client, session):
    """La création envoie un POST avec les noms attendus par l'API et lit le post renvoyé.

    Pourquoi : l'application dit user_id, l'API attend userId. Une erreur ici ferait perdre l'auteur.
    """
    session.request.return_value = make_response(
        status=201, data={"userId": 1, "title": "T", "body": "B", "id": 101}
    )

    post = client.create_post(1, "T", "B")

    assert post == Post(id=101, user_id=1, title="T", body="B")
    args, kwargs = session.request.call_args
    assert args == ("POST", "https://api.test/posts")
    assert kwargs["json"] == {"userId": 1, "title": "T", "body": "B"}


def test_update_post_replaces_the_whole_post_with_put(client, session):
    """La mise à jour envoie un PUT contenant tous les champs du post.

    Pourquoi : PUT remplace tout l'élément, donc un champ oublié serait perdu.
    """
    session.request.return_value = make_response(data=post_json(1))

    post = client.update_post(1, 1, "T", "B")

    assert post.id == 1
    args, kwargs = session.request.call_args
    assert args == ("PUT", "https://api.test/posts/1")
    assert kwargs["json"] == {"id": 1, "userId": 1, "title": "T", "body": "B"}


def test_delete_post(client, session):
    """La suppression envoie un DELETE sur le bon post.

    Pourquoi : c'est l'appel réel de l'option 7 du menu ; une erreur d'adresse viserait un autre post.
    """
    session.request.return_value = make_response(data={})

    client.delete_post(5)

    assert session.request.call_args.args == ("DELETE", "https://api.test/posts/5")


def test_comments_for_posts_uses_a_single_call(client, session):
    """Les commentaires de plusieurs posts sont récupérés en un seul appel.

    Pourquoi : c'est l'optimisation du rapport, qui évite un appel par post.
    """
    session.request.return_value = make_response(data=[comment_json(1, 1), comment_json(2, 2)])

    comments = client.get_comments_for_posts([1, 2])

    assert len(comments) == 2
    session.request.assert_called_once()
    assert session.request.call_args.kwargs["params"] == {"postId": [1, 2]}


def test_comments_for_no_posts_does_not_call_api(client, session):
    """Sans post, aucune requête n'est envoyée.

    Pourquoi : sans filtre, l'API renverrait les 500 commentaires de tous les posts.
    """
    assert client.get_comments_for_posts([]) == []
    session.request.assert_not_called()


def test_user_report_combines_three_calls(client, session):
    """Le rapport rassemble l'utilisateur, ses posts et leurs commentaires en 3 appels.

    Pourquoi : c'est la fonctionnalité demandée par le brief. Les calculs sont testés dans test_models.py.
    """
    # Une liste dans side_effect : une réponse différente pour chaque appel, dans l'ordre.
    session.request.side_effect = [
        make_response(data=USER_JSON),
        make_response(data=[post_json(1), post_json(2)]),
        make_response(data=[comment_json(1, 1), comment_json(2, 2), comment_json(3, 2)]),
    ]

    report = client.get_user_report(1)

    assert report.user.name == "Leanne Graham"
    assert report.post_count == 2
    assert report.comment_count == 3
    post, count, ties = report.most_commented()
    assert (post.id, count, ties) == (2, 2, 1)


# ---------- Gestion des erreurs ----------

def test_timeout_raises_api_timeout_error(client, session):
    """Si l'API met trop de temps à répondre, l'erreur prévue indique le délai.

    Pourquoi : l'exception technique de requests ne doit jamais atteindre l'utilisateur.
    """
    session.request.side_effect = requests.exceptions.Timeout()

    with pytest.raises(APITimeoutError) as error:
        client.get_users()
    assert error.value.params == {"seconds": 3}


def test_connection_error_raises_api_connection_error(client, session):
    """Sans connexion, le client déclenche l'erreur prévue.

    Pourquoi : la coupure réseau est la panne la plus courante.
    """
    session.request.side_effect = requests.exceptions.ConnectionError()

    with pytest.raises(APIConnectionError):
        client.get_users()


@pytest.mark.parametrize("method, key", [("get_user", "user_not_found"), ("get_post", "post_not_found")])
def test_unknown_item_raises_not_found(client, session, method, key):
    """Un 404 devient une erreur « introuvable » propre à la ressource, avec son identifiant.

    Pourquoi : le message doit dire « Utilisateur 999 introuvable », pas seulement « erreur 404 ».
    """
    session.request.return_value = make_response(status=404, data={})

    with pytest.raises(ResourceNotFoundError) as error:
        getattr(client, method)(999)  # getattr retrouve la méthode à partir de son nom
    assert error.value.key == key
    assert error.value.params == {"id": 999}


def test_server_error_raises_http_status_error(client, session):
    """Un code 500 devient une erreur qui porte ce code.

    Pourquoi : JSONPlaceholder renvoie réellement 500 pour un PUT sur un post inconnu.
    """
    session.request.return_value = make_response(status=500)

    with pytest.raises(HTTPStatusError) as error:
        client.update_post(999, 1, "T", "B")
    assert error.value.params == {"status": 500}


def test_non_json_response_raises_invalid_response(client, session):
    """Une réponse qui n'est pas du JSON déclenche l'erreur prévue.

    Pourquoi : un serveur en panne renvoie souvent une page HTML au lieu de JSON.
    """
    session.request.return_value = make_response(invalid_json=True)

    with pytest.raises(InvalidResponseError):
        client.get_users()


def test_object_instead_of_list_raises_invalid_response(client, session):
    """Un objet reçu à la place d'une liste est détecté.

    Pourquoi : parcourir cet objet comme une liste provoquerait une erreur technique.
    """
    session.request.return_value = make_response(data={"error": "oops"})

    with pytest.raises(InvalidResponseError):
        client.get_users()


def test_missing_field_raises_invalid_response(client, session):
    """Un JSON auquel il manque un champ obligatoire est détecté.

    Pourquoi : le problème est signalé tout de suite, pas plus tard pendant l'affichage.
    """
    session.request.return_value = make_response(data={"id": 1, "name": "Sans email"})

    with pytest.raises(InvalidResponseError):
        client.get_user(1)


# ---------- Opérations génériques ----------

def test_list_items_translates_filters(client, session):
    """Les filtres de l'application sont convertis au format de l'API.

    Pourquoi : user_id doit devenir userId, et True doit devenir "true" en minuscules.
    """
    session.request.return_value = make_response(data=[{"id": 1, "userId": 2, "title": "T", "completed": True}])

    todos = client.list_items("todos", {"user_id": 2, "completed": True})

    assert todos[0].completed is True
    assert session.request.call_args.kwargs["params"] == {"userId": 2, "completed": "true"}


def test_unknown_filter_is_rejected_before_any_call(client, session):
    """Un filtre inconnu est refusé sans contacter l'API.

    Pourquoi : le brief exige que les saisies soient contrôlées avant tout appel.
    """
    with pytest.raises(ValidationError) as error:
        client.list_items("posts", {"inconnu": "1"})
    assert error.value.key == "error_unknown_filter"
    session.request.assert_not_called()


def test_patch_checks_existence_then_patches(client, session):
    """La modification lit d'abord l'élément, puis envoie un PATCH.

    Pourquoi : JSONPlaceholder répond 200 à un PATCH sur un élément inconnu.
    """
    session.request.side_effect = [
        make_response(data={"id": 3, "userId": 1, "title": "Album"}),
        make_response(data={"id": 3, "userId": 1, "title": "Nouveau"}),
    ]

    album = client.patch_item("albums", 3, {"title": "Nouveau"})

    assert album.title == "Nouveau"
    assert session.request.call_args_list[0].args == ("GET", "https://api.test/albums/3")
    patch_call = session.request.call_args_list[1]  # le 2e appel, le 1er ayant l'indice 0
    assert patch_call.args == ("PATCH", "https://api.test/albums/3")
    assert patch_call.kwargs["json"] == {"title": "Nouveau"}


def test_delete_item_checks_existence_then_deletes(client, session):
    """La suppression lit d'abord l'élément, puis envoie un DELETE.

    Pourquoi : un élément qui existe doit réellement être supprimé après la vérification.
    """
    session.request.side_effect = [make_response(data=post_json(1)), make_response(data={})]

    client.delete_item("posts", 1)

    assert session.request.call_args_list[1].args == ("DELETE", "https://api.test/posts/1")


def test_delete_unknown_item_is_not_sent(client, session):
    """Supprimer un élément inconnu donne « introuvable », sans envoyer de DELETE.

    Pourquoi : JSONPlaceholder répondrait 200 à DELETE /photos/9999 : la vérification préalable évite ce piège.
    """
    session.request.return_value = make_response(status=404, data={})

    with pytest.raises(ResourceNotFoundError) as error:
        client.delete_item("photos", 9999)
    assert (error.value.key, error.value.params) == ("photo_not_found", {"id": 9999})
    assert session.request.call_count == 1  # seule la lecture a été envoyée


# ---------- Explorateur d'API ----------

def test_send_returns_raw_status_and_body(client, session):
    """L'explorateur reçoit le code et le contenu tels quels, même pour un 404.

    Pourquoi : son rôle est de montrer la vraie réponse, sans la transformer en erreur.
    """
    session.request.return_value = make_response(status=404, data={})

    result = client.send("GET", "/posts/999")

    assert (result["status"], result["body"]) == (404, {})
    assert isinstance(result["elapsed_ms"], int)


def test_send_returns_text_when_the_response_is_not_json(client, session):
    """Une réponse qui n'est pas du JSON est renvoyée sous forme de texte.

    Pourquoi : l'explorateur doit tout afficher, sans planter sur une page HTML.
    """
    session.request.return_value = make_response(invalid_json=True)

    assert client.send("GET", "/posts")["body"] == "<html>"
