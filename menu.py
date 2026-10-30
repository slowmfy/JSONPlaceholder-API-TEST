"""Menu console : affiche les textes et lit ce que l'utilisateur tape.

Aucun appel HTTP ni texte en dur ici : les données viennent du client
(api_client.py) et les textes du traducteur `t` (i18n.py).

Les fonctions reçoivent input_func (lire une saisie) et output (afficher un texte)
en paramètres. En temps normal, ce sont input et print, les fonctions standard de
Python. Les tests les remplacent pour simuler un utilisateur.
"""
import logging

import config
import validators
from exceptions import AppError, ValidationError
from i18n import Translator

logger = logging.getLogger(__name__)


def one_line(text):
    """Les textes de l'API contiennent des retours à la ligne : on les remplace par des espaces."""
    return text.replace("\n", " ")  # \n représente un retour à la ligne


def ask(prompt, parser, t, input_func=input, output=print):
    """Redemande tant que `parser` lève une ValidationError ; renvoie la valeur validée."""
    while True:  # boucle sans fin : seul le « return » permet d'en sortir
        try:
            return parser(input_func(prompt))
        except ValidationError as exc:
            logger.info("Saisie refusée : %s", exc)
            output(t(exc.key, **exc.params))


def choose_language(languages, input_func=input, output=print, locales_dir=config.LOCALES_DIR):
    """Affiche les langues trouvées dans locales/ et renvoie le code choisi."""
    translators = {code: Translator(code, locales_dir) for code, _ in languages}
    # enumerate numérote les langues à partir de 1. Le nom _ signale une valeur ignorée.
    for number, (_, name) in enumerate(languages, start=1):
        output(f"{number} - {name}")
    # Avant le choix, l'invite est affichée dans toutes les langues disponibles.
    prompt = " / ".join(translators[code]("choose_language") for code, _ in languages) + " : "
    default_t = translators[languages[0][0]]
    choices = {str(number): code for number, (code, _) in enumerate(languages, start=1)}
    choice = ask(prompt, lambda raw: validators.parse_menu_choice(raw, choices), default_t,
                 input_func, output)
    return choices[choice]


class ConsoleMenu:
    """Le menu principal : une méthode par option."""

    def __init__(self, client, t, input_func=input, output=print):
        self.client = client
        self.t = t
        self.input = input_func
        self.out = output
        # Associe chaque numéro à son libellé et à la méthode à exécuter.
        self.actions = {
            "1": ("menu_list_users", self.list_users),
            "2": ("menu_user_details", self.show_user),
            "3": ("menu_user_posts", self.list_user_posts),
            "4": ("menu_post_comments", self.list_post_comments),
            "5": ("menu_create_post", self.create_post),
            "6": ("menu_update_post", self.update_post),
            "7": ("menu_delete_post", self.delete_post),
            "8": ("menu_user_report", self.user_report),
        }

    # ---------- Boucle principale ----------

    def run(self):
        """Affiche le menu et exécute les choix jusqu'à ce que l'utilisateur quitte."""
        logger.info("Démarrage du menu (langue : %s)", self.t.language)
        try:
            while True:
                self.print_menu()
                choice = self.input(self.t("prompt_choice")).strip()
                if choice == "0":
                    break  # sort de la boucle
                if choice not in self.actions:
                    logger.warning("Choix de menu invalide : %r", choice)
                    self.out(self.t("error_invalid_choice", value=choice))
                    continue  # repart au début de la boucle
                self.execute(choice)
        except (KeyboardInterrupt, EOFError):
            logger.info("Interruption par l'utilisateur")
            self.out()
        self.out(self.t("goodbye"))
        logger.info("Arrêt du menu")

    def print_menu(self):
        """Affiche le titre, les options numérotées et l'option 0 pour quitter."""
        self.out()
        self.out(self.t("menu_title"))
        for number, (label_key, _) in self.actions.items():
            self.out(f"{number}. {self.t(label_key)}")
        self.out(f"0. {self.t('menu_quit')}")

    def execute(self, choice):
        """Lance une action ; aucune exception ne remonte jusqu'à l'utilisateur."""
        label_key, action = self.actions[choice]
        logger.info("Menu %s : %s", choice, label_key)
        try:
            action()
        except AppError as exc:  # erreur prévue : message traduit
            logger.error("Échec de %s : %s", label_key, exc)
            self.out(self.t(exc.key, **exc.params))
        except EOFError:
            raise  # fin de la saisie (Ctrl+Z) : run() quitte proprement
        except Exception:  # erreur imprévue : détail dans le journal, message neutre à l'écran
            logger.exception("Erreur inattendue dans %s", label_key)
            self.out(self.t("error_unexpected"))

    # ---------- Saisies ----------

    def ask(self, prompt_key, parser):
        """Pose une question traduite et renvoie la réponse validée."""
        return ask(self.t(prompt_key), parser, self.t, self.input, self.out)

    def ask_id(self, prompt_key):
        """Demande un identifiant valide."""
        return self.ask(prompt_key, validators.parse_positive_id)

    def confirm(self, prompt_key):
        """Pose une question oui/non et renvoie True ou False."""
        yes, no = self.t("answer_yes"), self.t("answer_no")
        prompt = self.t("prompt_confirm", question=self.t(prompt_key), yes=yes, no=no)
        return ask(prompt, lambda raw: validators.parse_yes_no(raw, yes, no), self.t,
                   self.input, self.out)

    # ---------- Affichage ----------

    def print_field(self, label_key, value="", indent=""):
        """Ligne « libellé : valeur », avec la ponctuation de la langue choisie."""
        self.out(indent + self.t("label_value", label=self.t(label_key), value=value).rstrip())

    def print_post(self, post):
        """Affiche un post sur deux lignes : identifiant et titre, puis contenu."""
        self.out(f"  [{post.id}] {post.title}")
        self.out(f"      {one_line(post.body)}")

    def print_simulated(self):
        """Rappelle que JSONPlaceholder n'enregistre rien réellement."""
        self.out(self.t("simulated_write"))

    # ---------- Actions : une méthode pour chaque option du menu ----------

    def list_users(self):
        """Option 1 : liste des utilisateurs."""
        for user in self.client.get_users():
            self.out(f"  [{user.id}] {user.name} - {user.email} - {user.city}")

    def show_user(self):
        """Option 2 : détails d'un utilisateur."""
        user = self.client.get_user(self.ask_id("prompt_user_id"))
        self.print_field("label_name", f"{user.name} (@{user.username})", "  ")
        self.print_field("label_email", user.email, "  ")
        self.print_field("label_phone", user.phone, "  ")
        self.print_field("label_website", user.website, "  ")
        self.print_field("label_address", f"{user.street}, {user.suite}, {user.zipcode} {user.city}", "  ")
        self.print_field("label_company", f"{user.company_name} - {user.company_catchphrase}", "  ")

    def list_user_posts(self):
        """Option 3 : posts d'un utilisateur."""
        user_id = self.ask_id("prompt_user_id")
        # /posts?userId=999 renvoie une liste vide : on vérifie d'abord que l'utilisateur existe.
        self.client.get_user(user_id)
        posts = self.client.get_posts_by_user(user_id)
        if not posts:
            self.out(self.t("no_posts", user_id=user_id))
            return
        for post in posts:
            self.out(f"  [{post.id}] {post.title}")

    def list_post_comments(self):
        """Option 4 : commentaires d'un post."""
        post_id = self.ask_id("prompt_post_id")
        self.client.get_post(post_id)
        comments = self.client.get_comments_by_post(post_id)
        if not comments:
            self.out(self.t("no_comments", post_id=post_id))
            return
        for comment in comments:
            self.out(f"  - {comment.name} ({comment.email})")
            self.out(f"      {one_line(comment.body)}")

    def create_post(self):
        """Option 5 : création d'un post."""
        user_id = self.ask_id("prompt_author_id")
        self.client.get_user(user_id)  # l'auteur doit exister
        title = self.ask("prompt_title", validators.validate_title)
        body = self.ask("prompt_body", validators.validate_body)
        post = self.client.create_post(user_id, title, body)
        self.out(self.t("post_created", post_id=post.id))
        self.print_post(post)
        self.print_simulated()

    def update_post(self):
        """Option 6 : modification d'un post."""
        post_id = self.ask_id("prompt_post_id")
        # PUT sur un id inconnu renvoie 500 : on vérifie d'abord que le post existe.
        current = self.client.get_post(post_id)
        self.out(self.t("current_post"))
        self.print_post(current)
        self.out(self.t("keep_current_hint"))
        # PUT remplace toute la ressource : un champ vide garde l'ancienne valeur.
        title = self.ask("prompt_new_title", validators.validate_optional_title) or current.title
        body = self.ask("prompt_new_body", validators.validate_optional_body) or current.body
        if title == current.title and body == current.body:
            self.out(self.t("no_changes"))
            return
        post = self.client.update_post(post_id, current.user_id, title, body)
        self.out(self.t("post_updated"))
        self.print_post(post)
        self.print_simulated()

    def delete_post(self):
        """Option 7 : suppression d'un post, après confirmation."""
        post_id = self.ask_id("prompt_post_id")
        self.print_post(self.client.get_post(post_id))
        if not self.confirm("confirm_delete"):
            self.out(self.t("delete_cancelled"))
            return
        self.client.delete_post(post_id)
        self.out(self.t("post_deleted", post_id=post_id))
        self.print_simulated()

    def user_report(self):
        """Option 8 : rapport d'un utilisateur."""
        report = self.client.get_user_report(self.ask_id("prompt_user_id"))
        self.print_field("report_user", report.user.name)
        self.print_field("label_email", report.user.email)
        self.print_field("report_post_count", report.post_count)
        self.print_field("report_comment_count", report.comment_count)
        best = report.most_commented()
        if best is None:
            self.out(self.t("no_posts", user_id=report.user.id))
            return
        post, count, ties = best  # répartit les trois valeurs dans trois variables
        self.print_field("report_most_commented")
        self.print_field("report_title", post.title, "  ")
        self.print_field("report_comments", count, "  ")
        if ties > 1:
            self.out(f"  {self.t('report_tie', count=ties)}")
