"""Tests de web_api.py : réponses JSON, validation et traduction des erreurs en codes HTTP.

Le serveur n'est pas réellement lancé. TestClient envoie des requêtes directement à
l'application, comme le ferait le navigateur, et renvoie la réponse.

Rappel des codes : 200 réussite, 201 créé, 404 introuvable, 405 méthode non autorisée,
422 saisie invalide, 500 erreur interne, 502 API inaccessible, 504 délai dépassé.
"""
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import config
from api_client import JsonPlaceholderClient
from conftest import USER_JSON, comment_json, post_json
from exceptions import APIConnectionError, APITimeoutError, HTTPStatusError, ResourceNotFoundError
from models import Comment, Post, Todo, User, UserReport
from web_api import app, get_client


@pytest.fixture
def fake_client():
    """Remplace le client HTTP de l'application par un Mock, le temps d'un test.

    Le code placé après yield s'exécute à la fin du test : il retire le remplacement.
    """
    fake = Mock()
    app.dependency_overrides[get_client] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


@pytest.fixture
def http():
    """Faux navigateur. raise_server_exceptions=False : voir la vraie réponse d'erreur."""
    return TestClient(app, raise_server_exceptions=False)


# ---------- Langues et schéma ----------

def test_languages_lists_locale_files(http):
    """La liste des langues vient du dossier locales/, avec le français en premier.

    Pourquoi : c'est elle qui remplit le sélecteur de langue de l'interface.
    """
    languages = http.get("/api/languages").json()
    assert languages[0] == {"code": "fr", "name": "Français"}
    assert {"code": "en", "name": "English"} in languages


def test_translations_of_a_language(http):
    """Les textes d'une langue sont envoyés à l'interface.

    Pourquoi : l'interface Angular affiche ses textes à partir de cette réponse.
    """
    assert http.get("/api/translations/en").json()["goodbye"] == "Goodbye!"


def test_translations_of_unknown_language_is_404(http):
    """Demander une langue inexistante répond 404 avec une clé d'erreur.

    Pourquoi : le code de langue vient de l'adresse, et peut donc être n'importe quoi.
    """
    response = http.get("/api/translations/xx")
    assert response.status_code == 404
    assert response.json()["key"] == "error_not_found"


def test_schema_describes_every_resource(http):
    """Le schéma décrit les 6 ressources et leurs champs.

    Pourquoi : les formulaires Angular sont générés à partir de cette description.
    """
    schema = http.get("/api/schema").json()
    assert set(schema) == {"users", "posts", "comments", "albums", "photos", "todos"}
    assert {"name": "user_id", "kind": "ref", "required": True, "ref": "users"} in schema["posts"]["fields"]
    assert schema["todos"]["filters"] == ["user_id", "completed"]


# ---------- Lecture ----------

def test_get_item_returns_json(http, fake_client):
    """GET /api/users/1 renvoie l'élément en JSON.

    Pourquoi : c'est le cas normal, et il vérifie aussi l'appel transmis au client.
    """
    # Préparation : le faux client renverra un utilisateur.
    fake_client.get_item.return_value = User.from_dict(USER_JSON)

    # Action : le faux navigateur fait la requête.
    response = http.get("/api/users/1")

    # Vérification : la réponse HTTP, puis l'appel reçu par le client.
    assert response.status_code == 200
    assert response.json()["company_name"] == "Romaguera-Crona"
    fake_client.get_item.assert_called_once_with("users", 1)


def test_unknown_resource_is_404(http, fake_client):
    """Une ressource inconnue répond 404, en lecture comme en suppression, sans appeler le client.

    Pourquoi : seules les 6 ressources décrites sont accessibles.
    """
    assert http.get("/api/articles/1").status_code == 404
    assert http.delete("/api/articles/1").status_code == 404
    fake_client.get_item.assert_not_called()
    fake_client.delete_item.assert_not_called()


@pytest.mark.parametrize("raw, key", [("abc", "error_not_integer"), ("0", "error_not_positive")])
def test_invalid_id_is_rejected_before_api_call(http, fake_client, raw, key):
    """Un identifiant invalide dans l'adresse répond 422 sans appeler le client.

    Pourquoi : la validation est la même que dans le menu console, et elle passe avant l'appel.
    """
    response = http.get(f"/api/users/{raw}")

    assert response.status_code == 422
    assert (response.json()["key"], response.json()["field"]) == (key, "id")
    fake_client.get_item.assert_not_called()


def test_list_with_filter_checks_parent_exists(http, fake_client):
    """Une liste filtrée vérifie que le parent existe, puis renvoie les éléments.

    Pourquoi : JSONPlaceholder répond par une liste vide si l'utilisateur n'existe pas.
    """
    fake_client.list_items.return_value = [Todo(1, 2, "T", True)]

    response = http.get("/api/todos?user_id=2&completed=true")

    assert response.json() == [{"id": 1, "user_id": 2, "title": "T", "completed": True}]
    fake_client.get_item.assert_called_once_with("users", 2)
    fake_client.list_items.assert_called_once_with("todos", {"user_id": 2, "completed": True})


def test_list_with_unknown_parent_is_404(http, fake_client):
    """Filtrer sur un utilisateur inconnu répond 404 au lieu d'une liste vide.

    Pourquoi : une liste vide laisserait croire que l'utilisateur existe sans rien avoir publié.
    """
    fake_client.get_item.side_effect = ResourceNotFoundError("user_not_found", id=99)

    response = http.get("/api/posts?user_id=99")

    assert response.status_code == 404
    assert response.json()["params"] == {"id": 99}
    fake_client.list_items.assert_not_called()


def test_invalid_filter_is_rejected_before_any_api_call(http, fake_client):
    """Un filtre invalide est refusé avant la moindre requête, en nommant le filtre.

    Pourquoi : ce défaut existait : le parent était vérifié sur l'API avant le contrôle des filtres.
    """
    response = http.get("/api/todos?user_id=1&completed=peut-etre")

    assert response.json()["key"] == "error_not_boolean"
    assert response.json()["field"] == "completed"
    fake_client.get_item.assert_not_called()


@pytest.mark.parametrize("name", ["resource", "inconnu"])
def test_unknown_filter_with_the_real_client(http, name):
    """Un filtre inconnu est refusé par le vrai client, avec le format d'erreur habituel.

    Pourquoi : un Mock accepte tout : ce test a besoin du vrai client. C'est ainsi qu'a été
    trouvé le défaut de ?resource=1, qui provoquait une erreur 500.
    """
    session = Mock()
    app.dependency_overrides[get_client] = lambda: JsonPlaceholderClient(session=session)

    response = http.get(f"/api/posts?{name}=1")
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json() == {"key": "error_unknown_filter", "params": {"value": name}, "field": name}
    session.request.assert_not_called()


# ---------- Traduction des erreurs en codes HTTP ----------

@pytest.mark.parametrize("error, status, key", [
    (ResourceNotFoundError("user_not_found", id=9), 404, "user_not_found"),
    (APITimeoutError(seconds=5), 504, "error_timeout"),
    (APIConnectionError(), 502, "error_connection"),
    (HTTPStatusError(status=500), 502, "error_http"),
    (ZeroDivisionError(), 500, "error_unexpected"),
])
def test_errors_are_mapped_to_status_and_key(http, fake_client, error, status, key):
    """Chaque type d'erreur donne le bon code HTTP et une clé traduisible, sans trace Python.

    Pourquoi : l'interface s'appuie sur la clé pour afficher le message dans la bonne langue.
    """
    fake_client.get_item.side_effect = error

    response = http.get("/api/users/9")

    assert response.status_code == status
    assert response.json()["key"] == key
    assert "Traceback" not in response.text


def test_method_not_allowed_uses_the_error_format(http):
    """Une méthode HTTP non prévue répond avec le format d'erreur habituel.

    Pourquoi : ce défaut existait : la 405 de FastAPI n'avait pas ce format, donc pas de message traduit.
    """
    response = http.put("/api/users")

    assert response.status_code == 405
    assert response.json() == {"key": "error_http", "params": {"status": 405}, "field": None}


def test_malformed_json_body(http, fake_client):
    """Un corps de requête qui n'est pas du JSON répond 422 avec une clé d'erreur.

    Pourquoi : l'API web peut être appelée par autre chose que le formulaire Angular.
    """
    response = http.post("/api/posts", content="{ pas du json", headers={"Content-Type": "application/json"})

    assert response.status_code == 422
    assert response.json()["key"] == "error_invalid_input"


@pytest.mark.parametrize("path", ["/api", "/api/inconnu/1/2/3"])
def test_unknown_api_routes_are_json_404(http, path):
    """Une adresse /api inconnue répond en JSON, et non par la page Angular.

    Pourquoi : ce défaut existait : /api renvoyait du HTML, illisible pour le code qui attend du JSON.
    """
    response = http.get(path)
    assert response.status_code == 404
    assert response.json()["key"] == "error_not_found"


# ---------- Écriture ----------

def test_create_validates_each_field(http, fake_client):
    """Un champ invalide répond 422 en indiquant le champ, sans rien créer.

    Pourquoi : c'est grâce à `field` que le message s'affiche sous le bon champ du formulaire.
    """
    response = http.post("/api/posts", json={"user_id": 1, "title": "   ", "body": "B"})

    assert response.status_code == 422
    assert response.json() == {"key": "error_required", "params": {}, "field": "title"}
    fake_client.create_item.assert_not_called()


@pytest.mark.parametrize("resource, data", [
    ("users", {"name": "A", "username": "a"}),
    ("comments", {"post_id": 1, "name": "N", "body": "B"}),
])
def test_create_rejects_invalid_email(http, fake_client, resource, data):
    """Les deux ressources qui ont un email le contrôlent, sans rien créer.

    Pourquoi : les règles sont testées dans test_validators.py ; ici, on vérifie que
    la validation est bien branchée sur ces deux formulaires.
    """
    response = http.post(f"/api/{resource}", json={**data, "email": "a@b..fr"})

    assert response.status_code == 422
    assert (response.json()["key"], response.json()["field"]) == ("error_invalid_email", "email")
    fake_client.create_item.assert_not_called()


def test_create_checks_reference_and_creates(http, fake_client):
    """Une création valide vérifie l'auteur, nettoie les valeurs et ignore les champs inconnus.

    Pourquoi : c'est le cas normal, et il couvre chaque étape avant l'envoi.
    """
    fake_client.create_item.return_value = Post(101, 1, "T", "B")

    response = http.post("/api/posts", json={"user_id": "1", "title": " T ", "body": "B", "extra": "ignoré"})

    assert response.status_code == 201
    assert response.json() == {"item": {"id": 101, "user_id": 1, "title": "T", "body": "B"}, "simulated": True}
    fake_client.get_item.assert_called_once_with("users", 1)
    fake_client.create_item.assert_called_once_with("posts", {"user_id": 1, "title": "T", "body": "B"})


def test_unknown_reference_names_the_field(http, fake_client):
    """Un auteur inconnu répond 404 en désignant le champ user_id, sans rien créer.

    Pourquoi : le message doit s'afficher sous le champ « auteur » du formulaire.
    """
    fake_client.get_item.side_effect = ResourceNotFoundError("user_not_found", id=99)

    response = http.post("/api/posts", json={"user_id": 99, "title": "T", "body": "B"})

    assert response.status_code == 404
    assert response.json()["field"] == "user_id"
    fake_client.create_item.assert_not_called()


def test_patch_sends_only_given_fields(http, fake_client):
    """PATCH ne transmet que les champs reçus.

    Pourquoi : cocher une tâche ne doit pas renvoyer son titre.
    """
    fake_client.patch_item.return_value = Todo(1, 1, "T", True)

    response = http.patch("/api/todos/1", json={"completed": True})

    assert response.json()["item"]["completed"] is True
    assert response.json()["simulated"] is True
    fake_client.patch_item.assert_called_once_with("todos", 1, {"completed": True})


def test_patch_checks_references(http, fake_client):
    """Modifier l'auteur d'un post vers un utilisateur inconnu est refusé.

    Pourquoi : la modification suit la même règle que la création, sinon un post pourrait
    se retrouver sans auteur valide.
    """
    fake_client.get_item.side_effect = ResourceNotFoundError("user_not_found", id=99)

    response = http.patch("/api/posts/1", json={"user_id": 99})

    assert response.status_code == 404
    assert response.json()["field"] == "user_id"
    fake_client.patch_item.assert_not_called()


def test_patch_can_clear_an_optional_field(http, fake_client):
    """PATCH peut vider un champ facultatif.

    Pourquoi : vider le téléphone doit réellement partir vers l'API.
    """
    fake_client.patch_item.return_value = User(1, "A", "a", "a@b.fr")

    response = http.patch("/api/users/1", json={"phone": ""})

    assert response.status_code == 200
    fake_client.patch_item.assert_called_once_with("users", 1, {"phone": ""})


def test_patch_without_fields_is_rejected(http, fake_client):
    """Un PATCH sans aucun champ utile est refusé.

    Pourquoi : il n'y a rien à modifier : mieux vaut le dire que simuler une réussite.
    """
    response = http.patch("/api/posts/1", json={})

    assert response.json()["key"] == "error_nothing_to_update"
    fake_client.patch_item.assert_not_called()


def test_delete(http, fake_client):
    """DELETE confirme la suppression et précise qu'elle est simulée.

    Pourquoi : l'interface utilise cette mention pour prévenir l'utilisateur.
    """
    response = http.delete("/api/albums/3")

    assert response.json() == {"deleted": 3, "simulated": True}
    fake_client.delete_item.assert_called_once_with("albums", 3)


# ---------- Rapport ----------

def test_report(http, fake_client):
    """Le rapport est converti en JSON, avec les totaux et le détail par post.

    Pourquoi : les calculs ont lieu dans models.py ; ici, on vérifie ce que reçoit la page.
    """
    posts = [Post.from_dict(post_json(1)), Post.from_dict(post_json(2))]
    comments = [Comment.from_dict(comment_json(i, 2)) for i in range(3)]
    fake_client.get_user_report.return_value = UserReport(User.from_dict(USER_JSON), posts, comments)

    data = http.get("/api/users/1/report").json()

    assert data["user"]["name"] == "Leanne Graham"
    assert (data["post_count"], data["comment_count"]) == (2, 3)
    best = data["most_commented"]
    assert (best["post"]["id"], best["comments"], best["ties"]) == (2, 3, 1)
    assert [(entry["post"]["id"], entry["comments"]) for entry in data["posts"]] == [(1, 0), (2, 3)]


def test_report_of_a_user_without_posts(http, fake_client):
    """Le rapport d'un utilisateur sans post répond normalement, avec des champs vides.

    Pourquoi : sans post, il n'y a pas de post le plus commenté à convertir en JSON.
    """
    fake_client.get_user_report.return_value = UserReport(User.from_dict(USER_JSON), [], [])

    data = http.get("/api/users/1/report").json()

    assert data["most_commented"] is None
    assert data["posts"] == []


# ---------- Explorateur d'API ----------

def test_explorer_forwards_request(http, fake_client):
    """L'explorateur transmet méthode, adresse et filtres, et retire le corps d'un GET.

    Pourquoi : la méthode écrite en minuscules et le filtre dans l'adresse doivent être compris.
    """
    fake_client.send.return_value = {"status": 200, "elapsed_ms": 12, "body": []}

    response = http.post("/api/explorer", json={"method": "get", "path": "/users/1/todos?completed=true&title=",
                                                "body": {"ignoré": "pour un GET"}})

    assert response.json()["status"] == 200
    fake_client.send.assert_called_once_with("GET", "/users/1/todos", params=[("completed", "true"), ("title", "")],
                                             payload=None)


@pytest.mark.parametrize("method, payload", [
    ("POST", {"a": 1}),
    ("PUT", {"a": 1}),
    ("PATCH", {"a": 1}),
    ("DELETE", None),      # une suppression n'a pas de corps
])
def test_explorer_accepts_every_write_method(http, fake_client, method, payload):
    """Les méthodes d'écriture sont acceptées, et le corps n'est transmis qu'à celles qui l'utilisent.

    Pourquoi : l'explorateur doit donner accès à toutes les méthodes de l'API.
    """
    fake_client.send.return_value = {"status": 200, "elapsed_ms": 12, "body": {}}

    http.post("/api/explorer", json={"method": method, "path": "/posts/1", "body": {"a": 1}})

    fake_client.send.assert_called_once_with(method, "/posts/1", params=None, payload=payload)


@pytest.mark.parametrize("payload, key, field", [
    ({"method": "TRACE", "path": "/posts"}, "error_invalid_method", "method"),
    ({"method": "GET", "path": "https://evil.example/posts"}, "error_invalid_path", "path"),
    ({"method": "GET", "path": "//evil.example/posts"}, "error_invalid_path", "path"),
    ({"method": "GET", "path": "/../admin"}, "error_invalid_path", "path"),
    ({"method": "GET", "path": "/articles"}, "error_invalid_path", "path"),
])
def test_explorer_rejects_invalid_requests(http, fake_client, payload, key, field):
    """Les méthodes inconnues et les adresses hors JSONPlaceholder sont refusées.

    Pourquoi : sécurité : sans cela, le serveur pourrait être utilisé pour appeler n'importe quel site.
    """
    response = http.post("/api/explorer", json=payload)

    assert response.status_code == 422
    assert (response.json()["key"], response.json()["field"]) == (key, field)
    fake_client.send.assert_not_called()


# ---------- Service de l'interface Angular ----------

@pytest.fixture
def frontend_dir(tmp_path, monkeypatch):
    """Crée un faux site compilé, ainsi qu'un fichier secret placé en dehors de celui-ci."""
    build = tmp_path / "build"
    build.mkdir()
    (build / "index.html").write_text("page angular", encoding="utf-8")
    (build / "main.js").write_text("code", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("secret", encoding="utf-8")
    monkeypatch.setattr(config, "FRONTEND_DIR", build)
    return build


def test_static_file_is_served(http, frontend_dir):
    """Un fichier du site compilé est renvoyé tel quel.

    Pourquoi : sans cela, le navigateur ne recevrait pas le code de l'interface.
    """
    assert http.get("/main.js").text == "code"


def test_angular_routes_fall_back_to_index(http, frontend_dir):
    """Une adresse de l'interface renvoie la page Angular.

    Pourquoi : recharger /users/1/report doit afficher le site, pas une erreur 404.
    """
    assert http.get("/users/1/report").text == "page angular"
    assert http.get("/").text == "page angular"


@pytest.mark.parametrize("path", ["/..%2Fsecret.txt", "/%2E%2E/secret.txt", "/..%5Csecret.txt"])
def test_files_outside_the_build_are_never_served(http, frontend_dir, path):
    """Une adresse piégée avec ../ ne donne jamais accès aux fichiers hors du site.

    Pourquoi : sécurité : sans ce contrôle, on pourrait lire n'importe quel fichier du PC.
    """
    assert "secret" not in http.get(path).text


def test_real_client_is_used_by_default():
    """Sans remplacement, l'API web utilise le vrai client HTTP.

    Pourquoi : tous les autres tests remplacent ce client. Celui-ci est le seul à prouver
    qu'en temps normal, l'API web a bien un client pour travailler.
    """
    assert isinstance(get_client(), JsonPlaceholderClient)


def test_missing_frontend_build_shows_a_readable_message(http, tmp_path, monkeypatch):
    """Si l'interface n'est pas compilée, un message explique quoi faire.

    Pourquoi : une erreur 404 sèche ne dirait pas à l'utilisateur de lancer npm run build.
    """
    monkeypatch.setattr(config, "FRONTEND_DIR", tmp_path)

    response = http.get("/users")

    assert response.status_code == 404
    assert "npm run build" in response.text
