"""Readable click and error logging for the isolated desktop debug mode."""

from datetime import datetime
import traceback
from functools import wraps


_EXPECTED_ACTIONS = (
    (("afficher le mot de passe", "masquer le mot de passe"), "La valeur ne doit apparaître que tant que l'option d'affichage est active ; la masquer doit rétablir les caractères protégés."),
    (("ajouter",), "Un formulaire d'ajout doit s'ouvrir. Rien n'est enregistré avant « Sauvegarder »."),
    (("sauvegarder",), "Les champs doivent être validés, l'élément enregistré dans le coffre temporaire, puis la liste actualisée."),
    (("supprimer",), "Une confirmation doit apparaître avant la suppression du seul élément fictif sélectionné."),
    (("audit",), "L'audit doit afficher le score et les mots de passe faibles, réutilisés ou anciens présents dans les données fictives."),
    (("tous les comptes",), "La liste complète des comptes fictifs doit s'afficher."),
    (("générer", "regénérer"), "Un mot de passe de démonstration doit être créé sans modifier le coffre avant validation."),
    (("copier",), "La copie est volontairement bloquée en mode debug ; le presse-papiers ne doit pas changer."),
    (("exporter",), "Une boîte de dialogue doit proposer l'export chiffré du coffre temporaire."),
    (("importer",), "Une boîte de dialogue et une confirmation doivent précéder le remplacement des seules données temporaires."),
    (("changer le mot de passe",), "Le mot de passe fictif doit être vérifié, les données de test rechiffrées, puis l'application reverrouillée."),
    (("paramètres",), "La fenêtre des paramètres doit s'ouvrir."),
    (("thème",), "L'apparence doit basculer entre les thèmes clair et sombre."),
    (("remplir",), "Le remplissage navigateur est indisponible en mode debug et ne doit transmettre aucun identifiant."),
    (("annuler",), "La fenêtre courante doit se fermer sans enregistrer les champs non validés."),
    (("fermer",), "La fenêtre des paramètres doit se fermer sans modifier le coffre."),
)


def expected_result_for(label: str) -> str:
    """Return a concise French expectation for a clicked control."""
    normalized = label.casefold()
    for keywords, expected in _EXPECTED_ACTIONS:
        if any(keyword in normalized for keyword in keywords):
            return expected
    return "Le contrôle doit effectuer l'action indiquée dans l'interface sans quitter le mode debug."


class DebugConsole:
    """Print each UI click, expected result, and uncaught Tk callback error."""

    def __init__(self, root):
        self.root = root
        self._click_number = 0
        root.bind_all("<Button-1>", self._on_click, add="+")
        root.report_callback_exception = self._report_callback_exception

    @staticmethod
    def _write(message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}", flush=True)

    def startup(self, account_count: int, database_path: str):
        self._write("=== MODE DEBUG VAULTAPP ===")
        self._write("Coffre temporaire isolé ; données fictives ; aucune API ni copie presse-papiers.")
        self._write(f"Comptes fictifs chargés : {account_count}.")
        self._write(f"Base temporaire : {database_path}")
        self._write("Clique dans l'application : chaque clic affiche l'action attendue.")

    def operation_started(self, name: str, expected: str):
        self._write(f"[ACTION] {name}")
        self._write(f"[ATTENDU] {expected}")

    def operation_succeeded(self, name: str):
        self._write(f"[SANS ERREUR] {name} : le traitement est terminé sans exception.")

    def operation_failed(self, name: str, error):
        self._write(f"[ERREUR ACTION] {name} : {type(error).__name__}: {error}")
        self._write("[À VÉRIFIER] Consulte la trace d'erreur qui suit.")

    def handled_error(self, name: str, error):
        self._write(f"[ERREUR GÉRÉE] {name} : {type(error).__name__}: {error}")
        self._write("[À VÉRIFIER] Un message d'erreur doit aussi apparaître dans l'application.")

    def _button_label(self, widget) -> str:
        current = widget
        while current is not None and current is not self.root:
            if "button" in current.__class__.__name__.casefold():
                label = getattr(current, "accessible_name", "")
                if label:
                    return label
                try:
                    label = str(current.cget("text")).strip()
                    if label:
                        return label
                except (AttributeError, KeyError, TypeError):
                    pass
            current = getattr(current, "master", None)
        return widget.__class__.__name__

    def _on_click(self, event):
        label = self._button_label(event.widget)
        self._click_number += 1
        self._write(f"[CLIC {self._click_number:03}] {label}")
        self._write(f"[ATTENDU] {expected_result_for(label)}")
        self.root.after_idle(lambda: self._report_click_result(label))

    def _report_click_result(self, label: str):
        if not self.root.winfo_exists():
            return
        screen = getattr(self.root, "current_screen", None)
        screen_name = screen.__class__.__name__ if screen is not None else "aucun écran"
        try:
            window_name = self.root.focus_get().winfo_toplevel().title()
        except (AttributeError, TypeError):
            window_name = self.root.title()
        self._write(
            f"[APRÈS CLIC] « {label} » traité ; écran : {screen_name} ; "
            f"fenêtre active : {window_name}. Vérifie aussi le message affiché dans l'application."
        )

    def _report_callback_exception(self, exception_type, exception, tb):
        self._write(f"[ERREUR] {exception_type.__name__}: {exception}")
        traceback.print_exception(exception_type, exception, tb)
        self._write("[À VÉRIFIER] L'action a échoué ; consulte la trace ci-dessus.")


def traced_action(name: str, expected: str):
    """Log the start and outcome of a debug-mode UI operation."""
    def decorate(function):
        @wraps(function)
        def wrapped(instance, *args, **kwargs):
            console = getattr(instance, "debug_console", None)
            if console is None:
                return function(instance, *args, **kwargs)

            console.operation_started(name, expected)
            try:
                result = function(instance, *args, **kwargs)
            except Exception as error:
                console.operation_failed(name, error)
                raise
            console.operation_succeeded(name)
            return result
        return wrapped
    return decorate
