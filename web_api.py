"""API web (FastAPI) : expose l'application à l'interface Angular.

Une « route » associe une adresse et une méthode HTTP à une fonction Python. Le
décorateur @app.get("/api/languages") signifie : quand le navigateur demande
GET /api/languages, exécuter la fonction juste en dessous. FastAPI convertit
ensuite la valeur renvoyée en JSON.

Comme le menu console, ce fichier ne fait qu'adapter : les appels HTTP restent
dans JsonPlaceholderClient, les contrôles dans validators.py / resources.py et
les textes dans locales/. Les erreurs sont renvoyées sous forme de clé de
traduction, que l'interface affiche dans la langue choisie.

Routes (pour chaque ressource : users, posts, comments, albums, photos, todos) :
    GET    /api/<ressource>?user_id=…   liste, filtres facultatifs
    GET    /api/<ressource>/<id>        détail
    POST   /api/<ressource>             création
    PATCH  /api/<ressource>/<id>        modification partielle
    DELETE /api/<ressource>/<id>        suppression
    POST   /api/explorer                requête libre vers JSONPlaceholder

Lancement : python web_api.py  (documentation interactive : /docs)
"""
import logging
import re
from dataclasses import asdict
from typing import Any
from urllib.parse import parse_qsl, urlsplit

import uvicorn
from fastapi import Body, Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

import config
import validators
from api_client import JsonPlaceholderClient
from exceptions import (
    APIConnectionError,
    APITimeoutError,
    AppError,
    ResourceNotFoundError,
    ValidationError,
)
from i18n import Translator, available_languages
from logging_config import configure_logging
from resources import RESOURCES, get_resource

logger = logging.getLogger(__name__)

# L'application web : toutes les routes ci-dessous lui sont rattachées.
app = FastAPI(title="JSONPlaceholder - API web")

_client = JsonPlaceholderClient()


def get_client():
    """Dépendance FastAPI : remplacée par un faux client dans les tests.

    Le paramètre client=Depends(get_client) d'une route demande à FastAPI
    d'appeler cette fonction et de transmettre son résultat à la route.
    """
    return _client


# ---------- Erreurs ----------

# Code HTTP renvoyé pour chaque type d'erreur.
# 422 saisie invalide, 404 introuvable, 504 délai dépassé, 502 API inaccessible.
ERROR_STATUS = [
    (ValidationError, 422),
    (ResourceNotFoundError, 404),
    (APITimeoutError, 504),
    (APIConnectionError, 502),
]


def error_response(status, key, params=None, field=None):
    """Réponse d'erreur JSON, identique pour toutes les erreurs de l'API."""
    return JSONResponse(status_code=status, content={"key": key, "params": params or {}, "field": field})


# @app.exception_handler indique quelle fonction appeler quand une erreur de ce
# type n'a été traitée nulle part dans une route.
@app.exception_handler(AppError)
def handle_app_error(request, exc):
    """Erreur prévue de l'application : clé de traduction et code HTTP adapté."""
    # next prend le premier code dont le type correspond ; 502 si aucun ne convient.
    status = next((code for cls, code in ERROR_STATUS if isinstance(exc, cls)), 502)
    logger.error("%s %s -> %s : %s", request.method, request.url.path, status, exc)
    return error_response(status, exc.key, exc.params, exc.field)


@app.exception_handler(RequestValidationError)
def handle_malformed_request(request, exc):
    """Requête que FastAPI n'a pas pu lire (JSON invalide, par exemple)."""
    logger.warning("Requête mal formée %s : %s", request.url.path, exc.errors())
    return error_response(422, "error_invalid_input")


@app.exception_handler(HTTPException)
def handle_http_exception(request, exc):
    """Erreurs produites par FastAPI lui-même (méthode non autorisée, 405...)."""
    logger.warning("%s %s -> %s", request.method, request.url.path, exc.status_code)
    return error_response(exc.status_code, "error_http", {"status": exc.status_code})


@app.exception_handler(Exception)
def handle_unexpected(request, exc):
    """Dernier filet de sécurité : le détail technique reste dans le journal."""
    logger.exception("Erreur inattendue sur %s %s", request.method, request.url.path)
    return error_response(500, "error_unexpected")


def parse_id(raw):
    """Valide un identifiant reçu dans l'adresse ; une erreur désigne le champ « id »."""
    try:
        return validators.parse_positive_id(raw)
    except ValidationError as exc:
        exc.field = "id"
        raise


def check_references(res, values, client):
    """Les références (auteur, post, album) doivent exister."""
    for field in res.fields:
        if field.kind == "ref" and field.name in values:
            try:
                client.get_item(field.ref, values[field.name])
            except ResourceNotFoundError as exc:
                exc.field = field.name
                raise


# ---------- Langues et description des ressources ----------

@app.get("/api/languages")
def list_languages():
    """Liste des langues disponibles."""
    return [{"code": code, "name": name} for code, name in available_languages()]


# {code} est une partie variable de l'adresse, transmise à la fonction.
@app.get("/api/translations/{code}")
def get_translations(code: str):
    """Tous les textes d'une langue."""
    if code not in dict(available_languages()):
        raise ResourceNotFoundError(resource=f"locales/{code}.json")
    t = Translator(code)
    # Les clés absentes de la langue sont complétées par la langue par défaut.
    return {**t.fallback, **t.messages}


@app.get("/api/schema")
def get_schema():
    """Champs de chaque ressource : l'interface en déduit ses formulaires."""
    return {name: resource.describe() for name, resource in RESOURCES.items()}


# ---------- Rapport utilisateur ----------

@app.get("/api/users/{user_id}/report")
def get_user_report(user_id: str, client=Depends(get_client)):
    """Rapport d'un utilisateur, converti en données JSON pour l'interface."""
    report = client.get_user_report(parse_id(user_id))
    best = report.most_commented()
    counts = report.comments_per_post()
    return {
        "user": asdict(report.user),  # asdict transforme un objet en dictionnaire
        "post_count": report.post_count,
        "comment_count": report.comment_count,
        "most_commented": None if best is None else {
            "post": asdict(best[0]), "comments": best[1], "ties": best[2],
        },
        "posts": [{"post": asdict(post), "comments": counts[post.id]} for post in report.posts],
    }


# ---------- Explorateur d'API ----------

EXPLORER_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
_NAMES = "|".join(RESOURCES)
# /posts, /posts/1, /users/1/posts : les seules routes de JSONPlaceholder.
EXPLORER_PATH = re.compile(rf"/({_NAMES})(/\d+(/({_NAMES}))?)?/?", re.ASCII)


class ExplorerRequest(BaseModel):
    """Forme attendue du JSON envoyé à /api/explorer ; FastAPI la vérifie seul."""

    method: str
    path: str
    body: Any = None


@app.post("/api/explorer")
def explore(request: ExplorerRequest, client=Depends(get_client)):
    """Envoie une requête libre à JSONPlaceholder et renvoie la réponse brute."""
    method = request.method.strip().upper()
    if method not in EXPLORER_METHODS:
        raise ValidationError("error_invalid_method", value=method, field="method")
    parts = urlsplit(request.path.strip())
    # Une URL complète est refusée : seul JSONPlaceholder peut être interrogé.
    if parts.scheme or parts.netloc or not EXPLORER_PATH.fullmatch(parts.path):
        raise ValidationError("error_invalid_path", value=request.path, field="path")
    body = request.body if method in ("POST", "PUT", "PATCH") else None
    return client.send(method, parts.path, params=parse_qsl(parts.query, keep_blank_values=True) or None, payload=body)


# ---------- Opérations génériques sur les ressources ----------

# Ces routes contiennent {resource} : elles fonctionnent pour les 6 ressources et
# doivent rester après les routes plus précises déclarées au-dessus.

@app.get("/api/{resource}")
def list_items(resource: str, request: Request, client=Depends(get_client)):
    """Liste d'une ressource, avec les filtres de l'adresse (?user_id=1)."""
    res = get_resource(resource)
    filters = res.parse_filters(dict(request.query_params))
    # Filtrer sur un parent inexistant renverrait une liste vide : on le signale.
    check_references(res, filters, client)
    return [asdict(item) for item in client.list_items(resource, filters)]


@app.get("/api/{resource}/{item_id}")
def get_item(resource: str, item_id: str, client=Depends(get_client)):
    """Détail d'un élément."""
    get_resource(resource)
    return asdict(client.get_item(resource, parse_id(item_id)))


@app.post("/api/{resource}", status_code=201)
def create_item(resource: str, data: dict = Body(...), client=Depends(get_client)):
    """Création d'un élément ; data est le JSON envoyé par le formulaire."""
    res = get_resource(resource)
    values = res.validate(data)
    check_references(res, values, client)
    return {"item": asdict(client.create_item(resource, values)), "simulated": True}


@app.patch("/api/{resource}/{item_id}")
def patch_item(resource: str, item_id: str, data: dict = Body(...), client=Depends(get_client)):
    """Modification partielle : seuls les champs envoyés sont contrôlés et changés."""
    res = get_resource(resource)
    item_id = parse_id(item_id)
    values = res.validate(data, partial=True)
    check_references(res, values, client)
    return {"item": asdict(client.patch_item(resource, item_id, values)), "simulated": True}


@app.delete("/api/{resource}/{item_id}")
def delete_item(resource: str, item_id: str, client=Depends(get_client)):
    """Suppression d'un élément."""
    get_resource(resource)
    item_id = parse_id(item_id)
    client.delete_item(resource, item_id)
    return {"deleted": item_id, "simulated": True}


# ---------- Interface Angular compilée ----------

@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    """Sert le build Angular ; toute URL inconnue renvoie index.html (routes Angular)."""
    if path == "api" or path.startswith("api/"):
        return error_response(404, "error_not_found", {"resource": f"/{path}"})
    index = config.FRONTEND_DIR / "index.html"
    if not index.is_file():
        return PlainTextResponse(Translator()("error_frontend_missing"), status_code=404)
    file = (config.FRONTEND_DIR / path).resolve()
    # Sécurité : seuls les fichiers situés dans le dossier du build sont servis.
    if path and file.is_file() and file.is_relative_to(config.FRONTEND_DIR.resolve()):
        return FileResponse(file)
    return FileResponse(index)


# Vrai seulement quand ce fichier est lancé directement (python web_api.py).
if __name__ == "__main__":
    configure_logging(config.WEB_LOG_FILE)
    logger.info("Démarrage de l'API web sur http://%s:%s", config.WEB_HOST, config.WEB_PORT)
    # uvicorn affiche ses propres logs (adresse, requêtes) dans la console ;
    # ceux de l'application vont dans web.log.
    uvicorn.run(app, host=config.WEB_HOST, port=config.WEB_PORT)
