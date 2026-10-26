import requests

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
        try:
            response = requests.request(
                method, url, params=params, json=payload, timeout=self.timeout
            )
        except requests.exceptions.Timeout:
            raise APIError("Le serveur met trop de temps à répondre.")
        except requests.exceptions.ConnectionError:
            raise APIError("Connexion impossible. Vérifiez votre accès Internet.")

        if response.status_code == 404:
            raise APIError(f"Ressource introuvable ({method} {endpoint}).")
        if not response.ok:
            raise APIError(f"Erreur HTTP {response.status_code} ({method} {endpoint}).")

        try:
            return response.json()
        except ValueError:
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
    
