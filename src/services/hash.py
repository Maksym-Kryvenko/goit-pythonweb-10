import hashlib

import bcrypt


def _prehash(password: str) -> bytes:
    # SHA-256 reduces any password to 32 bytes so bcrypt never silently truncates
    return hashlib.sha256(password.encode()).hexdigest().encode()


class Hash:
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(_prehash(plain_password), hashed_password.encode())

    def get_password_hash(self, password: str) -> str:
        return bcrypt.hashpw(_prehash(password), bcrypt.gensalt()).decode()
