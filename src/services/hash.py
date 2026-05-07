import hashlib

import bcrypt


def _prehash(password: str) -> bytes:
    """Reduce a password to a fixed-length byte string via SHA-256.

    bcrypt silently truncates inputs longer than 72 bytes; pre-hashing prevents that.

    Args:
        password: Plain-text password string.

    Returns:
        SHA-256 hex digest encoded to bytes.
    """
    return hashlib.sha256(password.encode()).hexdigest().encode()


class Hash:
    """Password hashing and verification using bcrypt with SHA-256 pre-hashing."""

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Check whether a plain-text password matches a stored bcrypt hash.

        Args:
            plain_password: The raw password supplied by the user.
            hashed_password: The bcrypt hash stored in the database.

        Returns:
            ``True`` if the password matches, ``False`` otherwise.
        """
        return bcrypt.checkpw(_prehash(plain_password), hashed_password.encode())

    def get_password_hash(self, password: str) -> str:
        """Hash a plain-text password using bcrypt.

        Args:
            password: The raw password to hash.

        Returns:
            A bcrypt hash string suitable for database storage.
        """
        return bcrypt.hashpw(_prehash(password), bcrypt.gensalt()).decode()
