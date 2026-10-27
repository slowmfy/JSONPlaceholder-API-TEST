from api import APIError, JSONPlaceholderClient

client = JSONPlaceholderClient()


# ---------- Saisies validées ----------

def demander_entier(message):
    """Redemande tant que la saisie n'est pas un entier positif."""
    while True:
        saisie = input(message).strip()
        if saisie.isdigit() and int(saisie) > 0:
            return int(saisie)
        print("Veuillez saisir un entier positif.")


def demander_texte(message, vide_autorise=False):
    """Redemande tant que la saisie est vide (sauf si vide_autorise)."""
    while True:
        saisie = input(message).strip()
        if saisie or vide_autorise:
            return saisie
        print("Ce champ ne peut pas être vide.")


def demander_confirmation(message):
    """Renvoie True pour 'o', False pour 'n'."""
    while True:
        saisie = input(f"{message} (o/n) : ").strip().lower()
        if saisie in ("o", "n"):
            return saisie == "o"
        print("Répondez par 'o' ou 'n'.")


def sur_une_ligne(texte):
    """Les textes de l'API contiennent des retours à la ligne : on les remplace par des espaces."""
    return texte.replace("\n", " ")


def afficher_post(post):
    print(f"  [{post['id']}] {post['title']}")
    print(f"      {sur_une_ligne(post['body'])}")


# ---------- Fonctionnalités ----------

def lister_utilisateurs():
    for user in client.get_users():
        print(f"  [{user['id']}] {user['name']} - {user['email']} - {user['address']['city']}")


def afficher_utilisateur():
    user_id = demander_entier("ID de l'utilisateur : ")
    user = client.get_user(user_id)  # 404 -> APIError
    adresse = user["address"]
    print(f"  Nom        : {user['name']} (@{user['username']})")
    print(f"  Email      : {user['email']}")
    print(f"  Téléphone  : {user['phone']}")
    print(f"  Site web   : {user['website']}")
    print(f"  Adresse    : {adresse['street']}, {adresse['suite']}, {adresse['zipcode']} {adresse['city']}")
    print(f"  Entreprise : {user['company']['name']} - {user['company']['catchPhrase']}")


def lister_posts_utilisateur():
    user_id = demander_entier("ID de l'utilisateur : ")
    posts = client.get_posts_by_user(user_id)
    # Un userId inexistant renvoie 200 avec une liste vide, pas une erreur.
    if not posts:
        print(f"Aucun post pour l'utilisateur {user_id}.")
        return
    for post in posts:
        print(f"  [{post['id']}] {post['title']}")


def afficher_commentaires_post():
    post_id = demander_entier("ID du post : ")
    comments = client.get_comments_by_post(post_id)
    if not comments:
        print(f"Aucun commentaire pour le post {post_id}.")
        return
    for comment in comments:
        print(f"  - {comment['name']}")
        print(f"      {sur_une_ligne(comment['body'])}")


def creer_post():
    user_id = demander_entier("ID de l'auteur : ")
    client.get_user(user_id)  # vérifie que l'auteur existe
    title = demander_texte("Titre : ")
    body = demander_texte("Contenu : ")
    post = client.create_post(user_id, title, body)
    print("Réponse de l'API :")
    print(post)
    # Les écritures sont simulées : le post n'existe pas vraiment sur le serveur.
    try:
        client.get_post(post["id"])
    except APIError:
        print(f"Attention : l'API est simulée, le post {post['id']} n'a pas été enregistré.")


def mettre_a_jour_post():
    post_id = demander_entier("ID du post : ")
    # On vérifie d'abord que le post existe (PUT sur un id inconnu renvoie 500).
    actuel = client.get_post(post_id)
    print("Post actuel :")
    afficher_post(actuel)
    print("Laissez vide pour conserver la valeur actuelle.")
    # PUT remplace toute la ressource : on renvoie l'ancienne valeur si le champ est vide.
    title = demander_texte("Nouveau titre : ", vide_autorise=True) or actuel["title"]
    body = demander_texte("Nouveau contenu : ", vide_autorise=True) or actuel["body"]
    if title == actuel["title"] and body == actuel["body"]:
        print("Aucune modification.")
        return
    post = client.update_post(post_id, actuel["userId"], title, body)
    print("Post mis à jour :")
    afficher_post(post)
    print("(Modification simulée : rien n'est enregistré sur le serveur.)")


def supprimer_post():
    post_id = demander_entier("ID du post : ")
    afficher_post(client.get_post(post_id))
    if not demander_confirmation("Confirmer la suppression ?"):
        print("Suppression annulée.")
        return
    client.delete_post(post_id)  # réponse : {} avec un code 200
    print(f"Post {post_id} supprimé.")
    print("(Suppression simulée : rien n'est enregistré sur le serveur.)")


MENU = {
    "1": ("Lister les utilisateurs", lister_utilisateurs),
    "2": ("Afficher les détails d'un utilisateur", afficher_utilisateur),
    "3": ("Lister les posts d'un utilisateur", lister_posts_utilisateur),
    "4": ("Afficher les commentaires d'un post", afficher_commentaires_post),
    "5": ("Créer un post", creer_post),
    "6": ("Mettre à jour un post", mettre_a_jour_post),
    "7": ("Supprimer un post", supprimer_post),
}


def main():
    try:
        while True:
            print("\n===== JSONPlaceholder =====")
            for numero, (libelle, _) in MENU.items():
                print(f"{numero}. {libelle}")
            print("0. Quitter")

            choix = input("Votre choix : ").strip()
            if choix == "0":
                break
            if choix not in MENU:
                print("Choix invalide.")
                continue

            _, action = MENU[choix]
            try:
                action()
            except APIError as e:
                print(f"Erreur : {e}")
    except KeyboardInterrupt:
        print()
    print("Au revoir !")


if __name__ == "__main__":
    main()

