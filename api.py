import logging

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://jsonplaceholder.typicode.com"
TIMEOUT = 5


class APIError(Exception):
    """Custom exception for API errors."""
    pass


class JSONPlaceholderClient:

    def __init__(self, base_url=BASE_URL, timeout=TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout

    def _request(self, method, endpoint, params=None, payload=None):
        url = f"{self.base_url}{endpoint}"
        logger.debug("%s %s params=%s payload=%s", method, url, params, payload)
        try:
            response = requests.request(
                method, url, params=params, json=payload, timeout=self.timeout
            )
        except requests.exceptions.Timeout:
            logger.error("Timeout après %ss : %s %s", self.timeout, method, url)
            raise APIError("Le serveur met trop de temps à répondre.")
        except requests.exceptions.ConnectionError as e:
            logger.error("Erreur de connexion : %s %s (%s)", method, url, e)
            raise APIError("Connexion impossible. Vérifiez votre accès Internet.")

        logger.info("%s %s -> %s (%.2fs)", method, endpoint, response.status_code,
                    response.elapsed.total_seconds())

        if response.status_code == 404:
            logger.warning("Ressource introuvable : %s %s", method, endpoint)
            raise APIError(f"Ressource introuvable ({method} {endpoint}).")
        if not response.ok:
            logger.error("Erreur HTTP %s : %s %s", response.status_code, method, endpoint)
            raise APIError(f"Erreur HTTP {response.status_code} ({method} {endpoint}).")

        try:
            return response.json()
        except ValueError:
            logger.error("Réponse non JSON : %s %s -> %r", method, endpoint, response.text[:200])
            raise APIError("La réponse du serveur n'est pas un JSON valide.")

    def get_users(self):
        return self._request("GET", "/users")

    def get_user(self, user_id):
        return self._request("GET", f"/users/{user_id}")

    def get_post(self, post_id):
        return self._request("GET", f"/posts/{post_id}")

    def get_posts_by_user(self, user_id):
        return self._request("GET", "/posts", params={"userId": user_id})

    def get_comments_by_post(self, post_id):
        return self._request("GET", "/comments", params={"postId": post_id})

    def create_post(self, user_id, title, body):
        return self._request("POST", "/posts", payload={"userId": user_id, "title": title, "body": body})

    def update_post(self, post_id, user_id, title, body):
        return self._request("PUT", f"/posts/{post_id}", payload={"id": post_id, "userId": user_id, "title": title, "body": body})

    def delete_post(self, post_id):
        return self._request("DELETE", f"/posts/{post_id}")
    
