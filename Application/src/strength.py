"""
Analyse de la force des mots de passe — VaultApp V2.

Utilise zxcvbn (bibliothèque Dropbox) pour une analyse réaliste :
score 0 = trivial (mot du dictionnaire, "123456"...)
score 4 = très robuste (années à cracker même offline)

Fallback simple si zxcvbn n'est pas disponible.
"""

try:
    from zxcvbn import zxcvbn as _zxcvbn
    ZXCVBN_AVAILABLE = True
except ImportError:
    ZXCVBN_AVAILABLE = False


# ── Niveaux de force ──────────────────────────────────────────
STRENGTH_LEVELS = [
    {"score": 0, "label": "Très faible", "color": "#ef4444"},
    {"score": 1, "label": "Faible",      "color": "#f97316"},
    {"score": 2, "label": "Moyen",       "color": "#eab308"},
    {"score": 3, "label": "Fort",        "color": "#22c55e"},
    {"score": 4, "label": "Excellent",   "color": "#10b981"},
]

# Traductions des suggestions zxcvbn (EN → FR)
_SUGGESTIONS_FR = {
    "Use a few words, avoid common phrases":
        "Utilise plusieurs mots, évite les phrases courantes",
    "No need for symbols, digits, or uppercase letters":
        "Pas besoin d'ajouter des symboles à tout prix",
    "Add another word or two. Uncommon words are better.":
        "Ajoute un mot supplémentaire. Les mots rares sont meilleurs.",
    "Straight rows of keys are easy to guess":
        "Les suites de touches clavier sont faciles à deviner",
    "Short keyboard patterns are easy to guess":
        "Les suites courtes au clavier sont faciles à deviner",
    "Use a longer keyboard pattern with more turns":
        "Utilise une suite plus longue avec des changements de direction",
    "Repeats like \"aaa\" are easy to guess":
        "Les répétitions comme « aaa » sont faciles à deviner",
    "Repeats like \"abcabc\" are only slightly harder to guess than \"abc\"":
        "Les répétitions comme « abcabc » ne sont guère mieux que « abc »",
    "Avoid repeated words and characters":
        "Évite les répétitions de mots et de caractères",
    "Sequences like abc or 6543 are easy to guess":
        "Les suites comme abc ou 6543 sont faciles à deviner",
    "Avoid sequences":
        "Évite les suites logiques",
    "Recent years are easy to guess":
        "Les années récentes sont faciles à deviner",
    "Avoid recent years":
        "Évite les années récentes",
    "Avoid years that are associated with you":
        "Évite les années qui te concernent",
    "Dates are often easy to guess":
        "Les dates sont souvent faciles à deviner",
    "Avoid dates and years that are associated with you":
        "Évite les dates et années qui te concernent",
    "This is a top-10 common password":
        "C'est l'un des 10 mots de passe les plus courants",
    "This is a top-100 common password":
        "C'est l'un des 100 mots de passe les plus courants",
    "This is a very common password":
        "C'est un mot de passe très courant",
    "This is similar to a commonly used password":
        "C'est similaire à un mot de passe très utilisé",
    "A word by itself is easy to guess":
        "Un seul mot est facile à deviner",
    "Names and surnames by themselves are easy to guess":
        "Les prénoms et noms seuls sont faciles à deviner",
    "Common names and surnames are easy to guess":
        "Les prénoms et noms courants sont faciles à deviner",
    "Capitalization doesn't help very much":
        "La majuscule initiale n'aide pas vraiment",
    "All-uppercase is almost as easy to guess as all-lowercase":
        "Tout en majuscules est presque aussi facile à deviner qu'en minuscules",
    "Reversed words aren't much harder to guess":
        "Les mots à l'envers ne sont pas beaucoup plus difficiles à deviner",
    "Predictable substitutions like '@' instead of 'a' don't help very much":
        "Les substitutions évidentes (@ pour a) n'aident pas vraiment",
}

_CRACK_TIMES_FR = {
    "less than a second": "moins d'une seconde",
    "seconds": "quelques secondes",
    "minutes": "quelques minutes",
    "hours": "quelques heures",
    "days": "quelques jours",
    "months": "quelques mois",
    "years": "quelques années",
    "centuries": "des siècles",
}


def _translate_crack_time(raw: str) -> str:
    for en, fr in _CRACK_TIMES_FR.items():
        if en in raw:
            return fr
    return raw


def analyze_password(password: str) -> dict:
    """
    Analyse la force d'un mot de passe.

    Returns:
        dict avec :
            score      : int 0-4 (-1 si vide)
            label      : str  "Faible" / "Moyen" / …
            color      : str  couleur hex
            fraction   : float 0.0-1.0 (pour la barre)
            suggestions: list[str]
            crack_time : str  estimation de crack offline
    """
    if not password:
        return {
            "score": -1, "label": "", "color": "#6b7280",
            "fraction": 0.0, "suggestions": [], "crack_time": "",
        }

    if ZXCVBN_AVAILABLE:
        result = _zxcvbn(password)
        score = result["score"]
        level = STRENGTH_LEVELS[score]
        raw_suggestions = result["feedback"].get("suggestions", [])
        suggestions = [_SUGGESTIONS_FR.get(s, s) for s in raw_suggestions]
        raw_time = result["crack_times_display"].get(
            "offline_slow_hashing_1e4_per_second", ""
        )
        crack_time = _translate_crack_time(raw_time)
    else:
        score = _simple_score(password)
        level = STRENGTH_LEVELS[score]
        suggestions = []
        crack_time = ""

    return {
        "score": score,
        "label": level["label"],
        "color": level["color"],
        "fraction": (score + 1) / 5,
        "suggestions": suggestions,
        "crack_time": crack_time,
    }


def is_weak(password: str) -> bool:
    """True si le mot de passe est trop faible (score ≤ 1)."""
    if not password:
        return False
    return analyze_password(password)["score"] <= 1


def _simple_score(password: str) -> int:
    """Heuristique de secours si zxcvbn n'est pas dispo."""
    score = 0.0
    if len(password) >= 8:  score += 1
    if len(password) >= 12: score += 1
    if any(c.isupper() for c in password): score += 0.5
    if any(c.isdigit() for c in password): score += 0.5
    if any(c in r"!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password): score += 1
    return min(4, int(score))


def calculate_vault_score(
    accounts, last_changed_dates: dict, password_scores: dict = None
) -> int:
    """
    Calcule le score global de santé du coffre (0 à 100%).
    Chaque compte vaut 10 points maximum :
    - Force (zxcvbn score) : score 4 = 5pts, 3 = 4pts, 2 = 2pts, 0-1 = 0pts
    - Unicité : unique = 3pts, réutilisé = 0pts
    - Fraîcheur : récent = 2pts, obsolète = 0pts
    """
    from datetime import datetime, timezone, timedelta

    total_accounts = len(accounts)
    if total_accounts == 0:
        return 100

    # 1. Identifier les doublons
    password_groups = {}
    for acc in accounts:
        pwd = acc.password
        if pwd:
            password_groups.setdefault(pwd, []).append(acc.id)

    reused_account_ids = set()
    for pwd, ids in password_groups.items():
        if len(ids) > 1:
            reused_account_ids.update(ids)

    # 2. Identifier les obsolètes (> 180 jours)
    now_naive_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    six_months_ago = now_naive_utc - timedelta(days=180)

    def parse_sqlite_timestamp(dt_str: str) -> datetime:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                continue
        return datetime.now()

    obsolete_account_ids = set()
    for acc in accounts:
        changed_str = last_changed_dates.get(acc.id) or acc.created_at
        if changed_str:
            changed_dt = parse_sqlite_timestamp(changed_str)
            if changed_dt < six_months_ago:
                obsolete_account_ids.add(acc.id)

    # 3. Calculer les points
    total_points = 0
    for acc in accounts:
        pwd = acc.password
        if not pwd:
            total_points += 10 # Pas de mot de passe = pas de vulnérabilité
            continue

        acc_pts = 0

        # Force
        f_score = (
            password_scores[acc.id]
            if password_scores is not None and acc.id in password_scores
            else analyze_password(pwd)["score"]
        )
        if f_score == 4:
            acc_pts += 5
        elif f_score == 3:
            acc_pts += 4
        elif f_score == 2:
            acc_pts += 2

        # Unicité
        if acc.id not in reused_account_ids:
            acc_pts += 3

        # Fraîcheur
        if acc.id not in obsolete_account_ids:
            acc_pts += 2

        total_points += acc_pts

    return int((total_points / (total_accounts * 10)) * 100)
