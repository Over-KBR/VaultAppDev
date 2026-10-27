"""
Tests unitaires — Modules crypto, generator, strength.

Ces tests vérifient chaque fonction de façon isolée,
sans base de données ni interface graphique.

Lancer : pytest tests/test_unit.py -v
"""

import pytest


# ══════════════════════════════════════════════════════════════
# CRYPTO
# ══════════════════════════════════════════════════════════════

class TestCrypto:
    """Tests sur le module src/crypto.py."""

    def test_generate_salt_est_aleatoire(self):
        """Deux sels générés doivent être différents."""
        from src.crypto import generate_salt
        s1 = generate_salt()
        s2 = generate_salt()
        assert s1 != s2

    def test_generate_salt_taille(self):
        """Le sel fait bien 16 octets (128 bits)."""
        from src.crypto import generate_salt, SALT_SIZE
        assert len(generate_salt()) == SALT_SIZE

    def test_derive_key_deterministe(self, master_password, salt):
        """La même entrée produit toujours la même clé."""
        from src.crypto import derive_key
        k1 = derive_key(master_password, salt)
        k2 = derive_key(master_password, salt)
        assert k1 == k2

    def test_derive_key_taille(self, encryption_key):
        """La clé fait bien 32 octets (256 bits)."""
        from src.crypto import KEY_SIZE
        assert len(encryption_key) == KEY_SIZE

    def test_derive_key_sel_different_donne_cle_differente(self, master_password):
        """Deux sels différents → deux clés différentes."""
        from src.crypto import generate_salt, derive_key
        k1 = derive_key(master_password, generate_salt())
        k2 = derive_key(master_password, generate_salt())
        assert k1 != k2

    def test_encrypt_decrypt_roundtrip(self, encryption_key):
        """Chiffrer puis déchiffrer redonne le texte original."""
        from src.crypto import encrypt, decrypt
        texte = "MonMotDePasseSecret123!"
        assert decrypt(encrypt(texte, encryption_key), encryption_key) == texte

    def test_encrypt_texte_vide(self, encryption_key):
        """Chiffrer une chaîne vide retourne une chaîne vide."""
        from src.crypto import encrypt, decrypt
        assert encrypt("", encryption_key) == ""
        assert decrypt("", encryption_key) == ""

    def test_encrypt_non_deterministe(self, encryption_key):
        """Deux chiffrements du même texte donnent des résultats différents (nonce aléatoire)."""
        from src.crypto import encrypt
        texte = "MonSecret"
        assert encrypt(texte, encryption_key) != encrypt(texte, encryption_key)

    def test_decrypt_mauvaise_cle_leve_exception(self, encryption_key):
        """Déchiffrer avec la mauvaise clé lève une exception."""
        from src.crypto import encrypt, decrypt, generate_salt, derive_key
        chiffré = encrypt("secret", encryption_key)
        mauvaise_cle = derive_key("MauvaisMotDePasse", generate_salt())
        with pytest.raises(Exception):
            decrypt(chiffré, mauvaise_cle)

    def test_encrypt_caracteres_speciaux(self, encryption_key):
        """Chiffrement de caractères spéciaux, accents, emojis."""
        from src.crypto import encrypt, decrypt
        texte = "Mötörhead_#2024 🔐 àéîõü"
        assert decrypt(encrypt(texte, encryption_key), encryption_key) == texte

    def test_encrypt_long_texte(self, encryption_key):
        """Chiffrement d'un texte très long."""
        from src.crypto import encrypt, decrypt
        texte = "A" * 10_000
        assert decrypt(encrypt(texte, encryption_key), encryption_key) == texte

    def test_verification_hash_correct(self, master_password, salt):
        """Le hash de vérification accepte le bon mot de passe."""
        from src.crypto import create_verification_hash, verify_master_password
        h = create_verification_hash(master_password, salt)
        assert verify_master_password(master_password, salt, h) is True

    def test_verification_hash_incorrect(self, master_password, salt):
        """Le hash de vérification rejette un mauvais mot de passe."""
        from src.crypto import create_verification_hash, verify_master_password
        h = create_verification_hash(master_password, salt)
        assert verify_master_password("MauvaisMotDePasse", salt, h) is False

    def test_verification_hash_non_deterministe_entre_sels(self, master_password):
        """Le même mot de passe avec deux sels différents donne deux hashs différents."""
        from src.crypto import generate_salt, create_verification_hash
        s1, s2 = generate_salt(), generate_salt()
        assert create_verification_hash(master_password, s1) != create_verification_hash(master_password, s2)


# ══════════════════════════════════════════════════════════════
# GENERATOR
# ══════════════════════════════════════════════════════════════

class TestGenerator:
    """Tests sur le module src/generator.py."""

    def test_longueur_par_defaut(self):
        """Le générateur produit la bonne longueur."""
        from src.generator import generate_password
        pwd = generate_password(length=16)
        assert len(pwd) == 16

    @pytest.mark.parametrize("length", [4, 8, 12, 20, 32, 64])
    def test_longueur_parametree(self, length):
        """Le générateur respecte la longueur demandée."""
        from src.generator import generate_password
        pwd = generate_password(length=length)
        assert len(pwd) == length

    def test_longueur_min_clampee(self):
        """Une longueur < 4 est ramenée à 4."""
        from src.generator import generate_password
        pwd = generate_password(length=1)
        assert len(pwd) == 4

    def test_longueur_max_clampee(self):
        """Une longueur > 128 est ramenée à 128."""
        from src.generator import generate_password
        pwd = generate_password(length=999)
        assert len(pwd) == 128

    def test_contient_majuscule(self):
        """Avec use_uppercase=True, le mot de passe contient au moins une majuscule."""
        from src.generator import generate_password
        import string
        pwd = generate_password(length=16, use_uppercase=True, use_lowercase=False,
                                use_digits=False, use_symbols=False)
        assert all(c in string.ascii_uppercase for c in pwd)

    def test_contient_chiffres(self):
        """Avec use_digits=True uniquement, le mot de passe ne contient que des chiffres."""
        from src.generator import generate_password
        import string
        pwd = generate_password(length=16, use_uppercase=False, use_lowercase=False,
                                use_digits=True, use_symbols=False)
        assert all(c in string.digits for c in pwd)

    def test_tous_groupes_actifs_contient_chaque_type(self):
        """Avec tous les groupes activés, le mot de passe contient au moins 1 de chaque."""
        from src.generator import generate_password, CHARS_UPPERCASE, CHARS_LOWERCASE, CHARS_DIGITS, CHARS_SYMBOLS
        pwd = generate_password(length=20, use_uppercase=True, use_lowercase=True,
                                use_digits=True, use_symbols=True)
        assert any(c in CHARS_UPPERCASE for c in pwd)
        assert any(c in CHARS_LOWERCASE for c in pwd)
        assert any(c in CHARS_DIGITS for c in pwd)
        assert any(c in CHARS_SYMBOLS for c in pwd)

    def test_aucun_groupe_leve_valueerror(self):
        """Si aucun groupe n'est sélectionné, une ValueError est levée."""
        from src.generator import generate_password
        with pytest.raises(ValueError):
            generate_password(use_uppercase=False, use_lowercase=False,
                              use_digits=False, use_symbols=False)

    def test_aleatoire(self):
        """Deux appels successifs donnent des résultats différents."""
        from src.generator import generate_password
        assert generate_password(32) != generate_password(32)

    def test_entropie_positive(self):
        """L'entropie d'un mot de passe non vide est > 0."""
        from src.generator import generate_password, estimate_entropy
        pwd = generate_password(16)
        assert estimate_entropy(pwd) > 0

    def test_entropie_vide_est_zero(self):
        """L'entropie d'une chaîne vide est 0."""
        from src.generator import estimate_entropy
        assert estimate_entropy("") == 0.0


# ══════════════════════════════════════════════════════════════
# STRENGTH
# ══════════════════════════════════════════════════════════════

class TestStrength:
    """Tests sur le module src/strength.py."""

    def test_mot_de_passe_vide(self):
        """Un mot de passe vide retourne score -1."""
        from src.strength import analyze_password
        result = analyze_password("")
        assert result["score"] == -1
        assert result["label"] == ""

    def test_mot_de_passe_trivial(self):
        """'123456' doit avoir un score très bas (0 ou 1)."""
        from src.strength import analyze_password
        result = analyze_password("123456")
        assert result["score"] <= 1

    def test_mot_de_passe_fort(self):
        """Un mot de passe long et complexe doit avoir un score élevé (3 ou 4)."""
        from src.strength import analyze_password
        result = analyze_password("Tr0ub4dor&3_SecurePass!")
        assert result["score"] >= 3

    def test_fraction_entre_0_et_1(self):
        """La fraction est toujours entre 0.0 et 1.0."""
        from src.strength import analyze_password
        for pwd in ["", "abc", "Password1!", "Tr0ub4dor&3_Secure!!"]:
            result = analyze_password(pwd)
            assert 0.0 <= result["fraction"] <= 1.0

    def test_champs_presents(self):
        """Tous les champs attendus sont présents dans le résultat."""
        from src.strength import analyze_password
        result = analyze_password("TestPassword123")
        for key in ("score", "label", "color", "fraction", "suggestions", "crack_time"):
            assert key in result

    def test_is_weak_vrai_pour_mdp_trivial(self):
        """is_weak() retourne True pour un mot de passe trivial."""
        from src.strength import is_weak
        assert is_weak("123456") is True
        assert is_weak("password") is True
        assert is_weak("abc") is True

    def test_is_weak_faux_pour_mdp_fort(self):
        """is_weak() retourne False pour un mot de passe fort."""
        from src.strength import is_weak
        assert is_weak("Tr0ub4dor&3_SecurePass!!") is False

    def test_is_weak_faux_pour_vide(self):
        """is_weak() retourne False pour une chaîne vide (pas de fausse alarme)."""
        from src.strength import is_weak
        assert is_weak("") is False

    def test_couleur_est_hex(self):
        """La couleur retournée est un code hexadécimal valide."""
        from src.strength import analyze_password
        import re
        result = analyze_password("TestPassword1!")
        assert re.match(r"^#[0-9a-fA-F]{6}$", result["color"])

    def test_score_croissant_avec_complexite(self):
        """Un mot de passe plus complexe a un score ≥ au moins aussi élevé."""
        from src.strength import analyze_password
        score_simple = analyze_password("abc")["score"]
        score_moyen = analyze_password("Abcdef123")["score"]
        score_fort = analyze_password("Tr0ub4dor&3_Secure!!")["score"]
        assert score_simple <= score_moyen <= score_fort


class TestCalculateVaultScore:
    """Tests sur le calcul du score global de santé du coffre."""

    class DummyAccount:
        def __init__(self, id: int, password: str, created_at: str):
            self.id = id
            self.password = password
            self.created_at = created_at

    def test_coffre_vide_donne_100(self):
        from src.strength import calculate_vault_score
        assert calculate_vault_score([], {}) == 100

    def test_coffre_parfait_donne_100(self):
        from src.strength import calculate_vault_score
        from datetime import datetime, timezone
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        accs = [
            self.DummyAccount(1, "Tr0ub4dor&3_SecurePass!", now_str),
            self.DummyAccount(2, "Another_Super_Secure_Pass_99#", now_str),
        ]
        # 10/10 points pour chaque compte -> 100%
        assert calculate_vault_score(accs, {}) == 100

    def test_score_reutilise_les_analyses_deja_calculees(self, monkeypatch):
        import src.strength as strength
        from datetime import datetime, timezone
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        account = self.DummyAccount(1, "password", now_str)
        monkeypatch.setattr(
            strength,
            "analyze_password",
            lambda _password: pytest.fail(
                "L’analyse de force devrait être réutilisée"
            ),
        )

        assert strength.calculate_vault_score(
            [account], {}, password_scores={1: 4}
        ) == 100

    def test_mot_de_passe_faible_reduit_le_score(self):
        from src.strength import calculate_vault_score
        from datetime import datetime, timezone
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        accs = [
            self.DummyAccount(1, "Tr0ub4dor&3_SecurePass!", now_str), # 10 pts
            self.DummyAccount(2, "123", now_str),                      # Force = 0, Unique = 3, Récent = 2 -> 5 pts
        ]
        # Total = 15 / 20 -> 75%
        assert calculate_vault_score(accs, {}) == 75

    def test_mot_de_passe_double_reduit_le_score(self):
        from src.strength import calculate_vault_score
        from datetime import datetime, timezone
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        accs = [
            self.DummyAccount(1, "Tr0ub4dor&3_SecurePass!", now_str), # Force = 5, Unique = 0 (double), Récent = 2 -> 7 pts
            self.DummyAccount(2, "Tr0ub4dor&3_SecurePass!", now_str), # Force = 5, Unique = 0 (double), Récent = 2 -> 7 pts
        ]
        # Total = 14 / 20 -> 70%
        assert calculate_vault_score(accs, {}) == 70

    def test_mot_de_passe_obsolete_reduit_le_score(self):
        from src.strength import calculate_vault_score
        from datetime import datetime, timezone, timedelta
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        old_str = (datetime.now(timezone.utc) - timedelta(days=200)).strftime("%Y-%m-%d %H:%M:%S")

        accs = [
            self.DummyAccount(1, "Tr0ub4dor&3_SecurePass!", now_str), # 10 pts
            self.DummyAccount(2, "Another_Super_Secure_Pass_99#", old_str), # Force = 5, Unique = 3, Récent = 0 (vieux) -> 8 pts
        ]
        # Total = 18 / 20 -> 90%
        assert calculate_vault_score(accs, {}) == 90


class TestTOTP:
    def test_code_rfc6238_a_59_secondes(self):
        from src.totp import generate_totp_code

        secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        assert generate_totp_code(secret, timestamp=59) == "287082"

    def test_code_garde_ses_zero_initiaux(self, monkeypatch):
        import src.totp as totp

        monkeypatch.setattr(totp.time, "time", lambda: 0)
        assert totp.generate_totp_code(
            "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        ) == "755224"

    def test_normalisation_base32(self):
        from src.totp import normalize_totp_secret

        assert normalize_totp_secret(" gez dgnb vgy3 tqojq gezd gnbv gy3t qojq ") == (
            "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        )

    @pytest.mark.parametrize("secret", ["", "invalid!", "ABC"])
    def test_secret_invalide_refuse(self, secret):
        from src.totp import generate_totp_code

        with pytest.raises(ValueError):
            generate_totp_code(secret)

    def test_duree_restante_dans_la_periode(self):
        from src.totp import seconds_until_next_code

        assert seconds_until_next_code(timestamp=59) == 1
        assert seconds_until_next_code(timestamp=60) == 30
