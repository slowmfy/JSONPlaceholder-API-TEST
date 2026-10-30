"""Outils partagés par tous les tests.

pytest lit ce fichier automatiquement. Il contient les données d'exemple et les
« fixtures » : des fonctions marquées @pytest.fixture, qui préparent ce dont un test
a besoin. Un test qui écrit `client` dans ses paramètres reçoit l'objet préparé
par la fixture du même nom.

Les vrais appels réseau sont remplacés par des Mock : des objets factices qui
acceptent n'importe quel appel, renvoient ce qu'on leur demande et mémorisent
comment ils ont été utilisés. Les tests sont ainsi rapides et marchent sans Internet.
"""
from unittest.mock import Mock

import pytest

from api_client import JsonPlaceholderClient

# Un utilisateur tel que JSONPlaceholder le renvoie : adresse et entreprise imbriquées.
USER_JSON = {
    "id": 1,
    "name": "Leanne Graham",
    "username": "Bret",
    "email": "Sincere@april.biz",
    "phone": "1-770-736-8031 x56442",
    "website": "hildegard.org",
    "address": {"street": "Kulas Light", "suite": "Apt. 556", "city": "Gwenborough", "zipcode": "92998-3874"},
    "company": {"name": "Romaguera-Crona", "catchPhrase": "Multi-layered client-server neural-net"},
}


def post_json(post_id, user_id=1):
    """Fabrique un post au format JSON de l'API."""
    return {"id": post_id, "userId": user_id, "title": f"Titre {post_id}", "body": f"Contenu\n{post_id}"}


def comment_json(comment_id, post_id):
    """Fabrique un commentaire au format JSON de l'API."""
    return {"id": comment_id, "postId": post_id, "name": "nom", "email": "a@b.c", "body": "texte"}


def make_response(status=200, data=None, invalid_json=False):
    """Fabrique une fausse réponse HTTP avec le code et le contenu voulus.

    invalid_json=True simule une réponse qui n'est pas du JSON (une page HTML).
    """
    response = Mock(status_code=status, ok=200 <= status < 400, text="<html>")
    if invalid_json:
        # side_effect : appeler response.json() déclenchera cette erreur.
        response.json.side_effect = ValueError("not json")
    else:
        # return_value : appeler response.json() renverra ces données.
        response.json.return_value = data
    return response


@pytest.fixture
def session():
    """Fausse session HTTP : remplace la connexion réseau."""
    return Mock()


@pytest.fixture
def client(session):
    """Vrai client HTTP, branché sur la fausse session : seul le réseau est simulé."""
    return JsonPlaceholderClient(base_url="https://api.test", timeout=3, session=session)
