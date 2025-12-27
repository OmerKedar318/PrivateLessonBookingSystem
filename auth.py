import hashlib
import os


def hash_password(password):
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + hashed.hex()  # store both


def verify_password(raw_password, stored_hash):
    salt_hex, hash_hex = stored_hash.split(":")
    salt = bytes.fromhex(salt_hex)
    stored = bytes.fromhex(hash_hex)
    new_hash = hashlib.pbkdf2_hmac("sha256", raw_password.encode(), salt, 100000)
    return new_hash == stored
