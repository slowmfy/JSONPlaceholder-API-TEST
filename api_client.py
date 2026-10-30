"""Client HTTP : seul fichier de l'application qui communique avec l'API.

HTTP est le protocole du web. Le client envoie une requête composée d'une méthode
et d'une adresse, et le serveur renvoie un code et des données :
    GET     lire
    POST    créer
    PUT     remplacer entièrement
    PATCH   modifier en partie
    DELETE  supprimer

Codes de réponse courants : 200 réussite, 201 créé, 404 introuvable, 500 erreur
du serveur. requests est la bibliothèque Python utilisée pour envoyer ces requêtes.
"""
import logging
import time

import requests

import config
from exceptions import (
    APIConnectionError,
    APITimeoutError,
    HTTPStatusError,
    InvalidResponseError,
    ResourceNotFoundError,
)
from models import Comment, Post, UserReport
from resources import get_resource

logger = logging.getLogger(__name__)


class JsonPlaceholderClient:
    """Regroupe tous les appels à l'API JSONPlaceholder.

    Les méthodes renvoient des objets de models.py et lèvent une APIError
    (ou une sous-classe) en cas de problème : l'appelant n'a jamais à manipuler
    `requests` ni le JSON brut.

    Les opérations génériques (list_items, get_item, create_item, patch_item,
    delete_item) fonctionnent pour toutes les ressources décrites dans
    resources.py : users, posts, comments, albums, photos, todos.
    """

    def __init__(self, base_url=config.BASE_URL, timeout=config.TIMEOUT, session=None):
        # rstrip retire le / final éventuel, pour ne pas obtenir // dans les adresses.
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # Une session réutilise la connexion TCP entre les appels. Les tests en
        # fournissent une fausse pour ne jamais appeler le vrai réseau.
        self.session = session or requests.Session()

    # Le _ en tête indique une méthode interne à cette classe.
    def _send(self, method, endpoint, params=None, payload=None):
        """Envoie la requête ; les erreurs réseau deviennent des APIError."""
        url = f"{self.base_url}{endpoint}"
        logger.debug("%s %s params=%s payload=%s", method, url, params, payload)
        try:
            return self.session.request(method, url, params=params, json=payload, timeout=self.timeout)
        except requests.exceptions.Timeout as exc:
            logger.error("Timeout après %ss : %s %s", self.timeout, method, url)
            # « from exc » conserve la cause d'origine pour le diagnostic.
            raise APITimeoutError(seconds=self.timeout) from exc
        except requests.exceptions.RequestException as exc:
            logger.error("API inaccessible : %s %s (%s)", method, url, exc)
            raise APIConnectionError() from exc

    def _request(self, method, endpoint, params=None, payload=None):
        """Envoie la requête, contrôle la réponse et renvoie son JSON décodé.

        Toutes les erreurs HTTP sont gérées ici, une seule fois pour toute l'application.
        """
        response = self._send(method, endpoint, params, payload)
        logger.info("%s %s -> %s", method, endpoint, response.status_code)

        if response.status_code == 404:
            logger.warning("Ressource introuvable : %s %s", method, endpoint)
            raise ResourceNotFoundError(resource=endpoint)
        if not response.ok:  # response.ok est faux pour un code d'erreur (400 et plus)
            logger.error("Erreur HTTP %s : %s %s", response.status_code, method, endpoint)
            raise HTTPStatusError(status=response.status_code)

        try:
            return response.json()
        except ValueError as exc:
            logger.error("Réponse non JSON : %s %s -> %r", method, endpoint, response.text[:200])
            raise InvalidResponseError() from exc

    def _request_list(self, endpoint, model, params=None):
        """Demande une liste et transforme chaque élément en objet `model`."""
        data = self._request("GET", endpoint, params=params)
        if not isinstance(data, list):
            logger.error("Liste attendue pour %s, reçu : %r", endpoint, data)
            raise InvalidResponseError()
        # Construit une nouvelle liste en appliquant from_dict à chaque élément.
        return [model.from_dict(item) for item in data]

    # ---------- Opérations génériques ----------

    def list_items(self, resource, filters=None):
        """GET /<resource>, avec filtres facultatifs ({"user_id": 1} -> ?userId=1)."""
        res = get_resource(resource)
        params = res.api_filters(filters or {})
        logger.info("Récupération de la liste %s %s", resource, params or "")
        return self._request_list(f"/{resource}", res.model, params=params or None)

    def get_item(self, resource, item_id):
        """GET /<resource>/<id> : un élément précis."""
        res = get_resource(resource)
        logger.info("Récupération de %s %s", resource, item_id)
        try:
            data = self._request("GET", f"/{resource}/{item_id}")
        except ResourceNotFoundError:
            # Remplace l'erreur générale par un message propre à la ressource.
            raise ResourceNotFoundError(res.not_found_key, id=item_id) from None
        return res.model.from_dict(data)

    def create_item(self, resource, values):
        """POST /<resource> ; `values` a déjà été validé (Resource.validate)."""
        res = get_resource(resource)
        logger.info("Création dans %s : %s", resource, values)
        item = res.model.from_dict(self._request("POST", f"/{resource}", payload=res.to_api(values)))
        logger.info("Élément %s créé avec l'id %s", resource, item.id)
        return item

    def patch_item(self, resource, item_id, values):
        """PATCH /<resource>/<id> : modification partielle."""
        res = get_resource(resource)
        # PATCH sur un id inconnu renvoie 200 : on vérifie d'abord qu'il existe.
        self.get_item(resource, item_id)
        logger.info("Modification de %s %s : %s", resource, item_id, values)
        data = self._request("PATCH", f"/{resource}/{item_id}", payload=res.to_api(values))
        return res.model.from_dict(data)

    def delete_item(self, resource, item_id):
        """DELETE /<resource>/<id>."""
        # DELETE sur un id inconnu renvoie aussi 200 : même vérification.
        self.get_item(resource, item_id)
        logger.info("Suppression de %s %s", resource, item_id)
        self._request("DELETE", f"/{resource}/{item_id}")

    def send(self, method, endpoint, params=None, payload=None):
        """Requête brute (explorateur d'API) : statut et corps renvoyés sans interprétation."""
        logger.info("Explorateur : %s %s params=%s", method, endpoint, params)
        start = time.perf_counter()  # chronomètre
        response = self._send(method, endpoint, params, payload)
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        try:
            body = response.json()
        except ValueError:
            body = response.text
        return {"status": response.status_code, "elapsed_ms": elapsed_ms, "body": body}

    # ---------- Raccourcis utilisés par le menu console ----------

    def get_users(self):
        return self.list_items("users")

    def get_user(self, user_id):
        return self.get_item("users", user_id)

    def get_post(self, post_id):
        return self.get_item("posts", post_id)

    def get_posts_by_user(self, user_id):
        return self.list_items("posts", {"user_id": user_id})

    def get_comments_by_post(self, post_id):
        return self.list_items("comments", {"post_id": post_id})

    def get_comments_for_posts(self, post_ids):
        """Commentaires de plusieurs posts en un seul appel (?postId=1&postId=2...)."""
        if not post_ids:
            return []
        logger.info("Récupération des commentaires des posts %s", post_ids)
        return self._request_list("/comments", Comment, params={"postId": list(post_ids)})

    def get_user_report(self, user_id):
        """Rassemble l'utilisateur, ses posts et leurs commentaires."""
        logger.info("Génération du rapport de l'utilisateur %s", user_id)
        user = self.get_user(user_id)
        posts = self.get_posts_by_user(user_id)
        comments = self.get_comments_for_posts([post.id for post in posts])
        return UserReport(user=user, posts=posts, comments=comments)

    def create_post(self, user_id, title, body):
        return self.create_item("posts", {"user_id": user_id, "title": title, "body": body})

    def update_post(self, post_id, user_id, title, body):
        """PUT : remplace tout le post (l'appelant fournit tous les champs)."""
        logger.info("Modification du post %s", post_id)
        data = self._request(
            "PUT",
            f"/posts/{post_id}",
            payload={"id": post_id, "userId": user_id, "title": title, "body": body},
        )
        return Post.from_dict(data)

    def delete_post(self, post_id):
        logger.info("Suppression du post %s", post_id)
        self._request("DELETE", f"/posts/{post_id}")
