"""
Module de chiffrement pour VaultApp.

Comment ça marche (en simple) :
1. Tu tapes ton mot de passe maître
2. On le passe dans un "mixeur" (PBKDF2) avec un sel aléatoire
   → Ça produit une clé de 256 bits (la clé AES)
3. Cette clé sert à chiffrer/déchiffrer tes mots de passe
4. Sans la clé (= sans ton mot de passe maître), impossible de lire les données

Termes techniques :
- Salt : données aléatoires ajoutées au mot de passe avant le hachage
         (empêche les attaques par dictionnaire)
- PBKDF2 : algorithme qui transforme un mot de passe en clé, très lentement
           (600 000 tours → empêche le brute-force)
- AES-256-GCM : chiffrement symétrique de niveau militaire avec vérification
                 d'intégrité (personne ne peut modifier les données chiffrées)
- Nonce/IV : nombre aléatoire utilisé une seule fois pour chaque chiffrement
             (deux chiffrements du même texte donnent des résultats différents)
"""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


# Nombre d'itérations pour PBKDF2
# Plus c'est élevé, plus c'est lent à cracker (mais aussi à déverrouiller)
# 600 000 est la recommandation OWASP 2023
PBKDF2_ITERATIONS = 600_000

# Taille du sel en octets (16 octets = 128 bits)
SALT_SIZE = 16

# Taille de la clé AES en octets (32 octets = 256 bits)
KEY_SIZE = 32

# Taille du nonce pour AES-GCM (12 octets = 96 bits, standard recommandé)
NONCE_SIZE = 12


def generate_salt() -> bytes:
    """Génère un sel aléatoire cryptographiquement sûr."""
    return os.urandom(SALT_SIZE)


def derive_key(master_password: str, salt: bytes) -> bytes:
    """
    Transforme le mot de passe maître en clé AES-256.
    
    C'est comme un mixeur ultra-puissant :
    mot de passe + sel → 600 000 tours de mixage → clé de 256 bits
    
    Args:
        master_password: Le mot de passe maître tapé par l'utilisateur
        salt: Le sel aléatoire (stocké dans la base de données)
    
    Returns:
        La clé AES de 32 octets (256 bits)
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(master_password.encode('utf-8'))


def create_verification_hash(master_password: str, salt: bytes) -> str:
    """
    Crée un hash pour vérifier le mot de passe maître aux prochains lancements.
    
    On ne stocke JAMAIS le mot de passe en clair. On stocke juste un hash
    qui permet de vérifier si le mot de passe tapé est le bon.
    
    On utilise un sel différent pour le hash de vérification (dérivé du sel principal)
    pour séparer la clé de chiffrement du hash de vérification.
    """
    # On dérive un sel spécifique pour la vérification
    verification_salt = hashlib.sha256(salt + b"verification").digest()[:SALT_SIZE]
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=verification_salt,
        iterations=PBKDF2_ITERATIONS,
    )
    verification_key = kdf.derive(master_password.encode('utf-8'))
    return base64.b64encode(verification_key).decode('utf-8')


def verify_master_password(master_password: str, salt: bytes, stored_hash: str) -> bool:
    """
    Vérifie si le mot de passe maître est correct.
    
    Compare le hash du mot de passe tapé avec le hash stocké.
    """
    computed_hash = create_verification_hash(master_password, salt)
    # Comparaison en temps constant (empêche les attaques par timing)
    return hashlib.sha256(computed_hash.encode()).digest() == hashlib.sha256(stored_hash.encode()).digest()


def encrypt(plaintext: str, key: bytes) -> str:
    """
    Chiffre un texte avec AES-256-GCM.
    
    Le résultat est encodé en base64 pour pouvoir être stocké dans SQLite.
    Format : base64(nonce + données_chiffrées)
    
    Args:
        plaintext: Le texte à chiffrer (ex: un mot de passe)
        key: La clé AES-256 (32 octets)
    
    Returns:
        Le texte chiffré encodé en base64
    """
    if not plaintext:
        return ""
    
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    
    # On colle le nonce devant les données chiffrées et on encode en base64
    return base64.b64encode(nonce + ciphertext).decode('utf-8')


def decrypt(encrypted_text: str, key: bytes) -> str:
    """
    Déchiffre un texte chiffré avec AES-256-GCM.
    
    Args:
        encrypted_text: Le texte chiffré en base64
        key: La clé AES-256 (32 octets)
    
    Returns:
        Le texte en clair
    """
    if not encrypted_text:
        return ""
    
    raw = base64.b64decode(encrypted_text.encode('utf-8'))
    
    # Les 12 premiers octets = nonce, le reste = données chiffrées
    nonce = raw[:NONCE_SIZE]
    ciphertext = raw[NONCE_SIZE:]
    
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    
    return plaintext.decode('utf-8')
