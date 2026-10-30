"""Erreurs propres à l'application.

Une exception est un signal d'erreur. Le mot « raise » la déclenche : le programme
quitte alors ce qu'il faisait et remonte jusqu'à un bloc « except » qui sait la
traiter. Sans ce bloc, le programme s'arrêterait avec un message technique.

Chaque exception porte une clé de traduction (et ses paramètres) plutôt qu'un
texte : c'est l'interface qui l'affiche dans la langue choisie par l'utilisateur.

Une classe est un modèle d'objet. « class B(A) » crée B à partir de A : B hérite
de tout ce que A sait faire. Toutes les classes ci-dessous descendent de AppError :

    AppError
    ├── ValidationError            saisie refusée
    └── APIError                   problème avec l'API
        ├── APIConnectionError     API inaccessible
        ├── APITimeoutError        pas de réponse à temps
        ├── ResourceNotFoundError  élément inexistant (404)
        ├── HTTPStatusError        autre code d'erreur HTTP
        └── InvalidResponseError   réponse illisible
"""


class AppError(Exception):
    """Erreur prévue, affichable à l'utilisateur sous forme de message traduit."""

    key = "error_unexpected"  # clé utilisée quand aucune n'est précisée

    # __init__ s'exécute automatiquement quand on crée l'objet. « self » désigne
    # l'objet en cours de création. **params récupère tous les paramètres nommés
    # supplémentaires : AppError("user_not_found", id=7) donne params == {"id": 7}.
    def __init__(self, key=None, field=None, **params):
        self.key = key or self.key  # « or » : la clé reçue, sinon celle de la classe
        self.field = field  # champ de formulaire en faute, s'il y en a un
        self.params = params
        # super() appelle le __init__ de la classe parente (Exception).
        super().__init__(f"{self.key} {params}" if params else self.key)


class ValidationError(AppError):
    """Saisie utilisateur invalide, détectée avant tout appel à l'API."""

    key = "error_invalid_input"


class APIError(AppError):
    """Erreur lors d'un échange avec l'API."""

    key = "error_api"


class APIConnectionError(APIError):
    """L'API ne peut pas être jointe (pas de réseau, serveur arrêté...)."""

    key = "error_connection"


class APITimeoutError(APIError):
    """L'API n'a pas répondu dans le délai fixé par config.TIMEOUT."""

    key = "error_timeout"


class ResourceNotFoundError(APIError):
    """L'élément demandé n'existe pas (code HTTP 404)."""

    key = "error_not_found"


class HTTPStatusError(APIError):
    """L'API a répondu avec un code d'erreur autre que 404 (500, par exemple)."""

    key = "error_http"


class InvalidResponseError(APIError):
    """Réponse illisible (pas du JSON) ou dont la structure n'est pas celle attendue."""

    key = "error_invalid_response"
