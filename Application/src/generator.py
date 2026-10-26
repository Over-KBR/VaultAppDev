"""
Générateur de mots de passe sécurisé — VaultApp V2.

Utilise le module secrets (cryptographiquement sûr) pour générer
des mots de passe selon les critères choisis par l'utilisateur.
"""

import secrets
import string


# Jeux de caractères
CHARS_UPPERCASE  = string.ascii_uppercase          # A-Z
CHARS_LOWERCASE  = string.ascii_lowercase          # a-z
CHARS_DIGITS     = string.digits                   # 0-9
CHARS_SYMBOLS    = "!@#$%^&*()-_=+[]{}|;:,.<>?"   # symboles courants


def generate_password(
    length: int = 16,
    use_uppercase: bool = True,
    use_lowercase: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    """
    Génère un mot de passe aléatoire cryptographiquement sûr.

    Garantit qu'au moins 1 caractère de chaque groupe activé
    est présent dans le résultat.

    Args:
        length       : longueur totale (min 4, max 128)
        use_uppercase: inclure des majuscules
        use_lowercase: inclure des minuscules
        use_digits   : inclure des chiffres
        use_symbols  : inclure des symboles

    Returns:
        Le mot de passe généré (str).

    Raises:
        ValueError si aucun groupe n'est sélectionné.
    """
    length = max(4, min(128, length))

    # Construire le pool et la liste des "obligatoires"
    pool = ""
    required = []

    if use_uppercase:
        pool += CHARS_UPPERCASE
        required.append(secrets.choice(CHARS_UPPERCASE))
    if use_lowercase:
        pool += CHARS_LOWERCASE
        required.append(secrets.choice(CHARS_LOWERCASE))
    if use_digits:
        pool += CHARS_DIGITS
        required.append(secrets.choice(CHARS_DIGITS))
    if use_symbols:
        pool += CHARS_SYMBOLS
        required.append(secrets.choice(CHARS_SYMBOLS))

    if not pool:
        raise ValueError("Au moins un groupe de caractères doit être sélectionné.")

    # Compléter avec des caractères aléatoires du pool
    remaining_count = length - len(required)
    remaining = [secrets.choice(pool) for _ in range(remaining_count)]

    # Mélanger tout pour éviter que les obligatoires soient toujours en début
    all_chars = required + remaining
    # Utiliser Fisher-Yates via secrets pour rester cryptographiquement sûr
    for i in range(len(all_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        all_chars[i], all_chars[j] = all_chars[j], all_chars[i]

    return "".join(all_chars)


def estimate_entropy(password: str) -> float:
    """
    Estime l'entropie en bits du mot de passe (approximation).
    H = L × log2(pool_size)
    """
    import math
    pool = 0
    if any(c in CHARS_LOWERCASE  for c in password): pool += len(CHARS_LOWERCASE)
    if any(c in CHARS_UPPERCASE  for c in password): pool += len(CHARS_UPPERCASE)
    if any(c in CHARS_DIGITS     for c in password): pool += len(CHARS_DIGITS)
    if any(c in CHARS_SYMBOLS    for c in password): pool += len(CHARS_SYMBOLS)
    if pool == 0:
        return 0.0
    return len(password) * math.log2(pool)
