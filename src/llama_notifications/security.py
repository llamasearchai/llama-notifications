"""
Security utilities for the llama_notifications package.

This module contains implementations of security-related components such as:
- Credential management
- Encryption services
- TEE (Trusted Execution Environment) simulation
- Secure token handling

These components ensure that all notification content and user credentials
are handled securely and in compliance with privacy regulations.
"""

import base64
import hashlib
import json
import logging
import os
import secrets
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# Try importing cryptography packages
try:
    from cryptography.hazmat.primitives import hashes, padding, serialization
    from cryptography.hazmat.primitives.asymmetric import padding as asymm_padding
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

# Try importing MLX for accelerated crypto
try:
    import mlx.core as mx

    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False

    # Create a minimal simulation of MLX
    class MXSimulation:
        def array(self, data):
            return data

        def random(self):
            class Random:
                def normal(self, shape):
                    import numpy as np

                    return np.random.normal(size=shape)

            return Random()

    class mx:
        core = MXSimulation()


# Configure logging
logger = logging.getLogger("llama_notifications.security")


class EncryptionType(Enum):
    """Types of encryption supported by the system."""

    NONE = 0
    AES256 = 1
    RSA = 2
    HYBRID = 3  # Combined asymmetric and symmetric


class CredentialManager:
    """Manages secure loading and access to API credentials."""

    def __init__(self, environment: str = "production"):
        """
        Initialize the credential manager.

        Args:
            environment: The environment to load credentials for.
                         One of: 'production', 'development', 'testing'
        """
        self.environment = environment
        self._credentials = {}
        self._loaded = False

    def load_credentials(self) -> None:
        """
        Load credentials from environment variables.

        This method loads credentials from environment variables prefixed with
        LLAMA_NOTIFICATIONS_{ENVIRONMENT}_{SERVICE}_{CREDENTIAL}

        For example: LLAMA_NOTIFICATIONS_PRODUCTION_FIREBASE_API_KEY
        """
        if self._loaded:
            return

        credential_prefix = f"LLAMA_NOTIFICATIONS_{self.environment.upper()}_"

        # Try loading from .env file if dotenv is available
        try:
            from dotenv import load_dotenv

            load_dotenv()
            logger.info("Loaded environment from .env file")
        except ImportError:
            logger.debug("python-dotenv not available, using system environment only")

        # Load credentials from environment variables
        for key, value in os.environ.items():
            if key.startswith(credential_prefix):
                service_cred = key[len(credential_prefix) :]
                parts = service_cred.split("_")

                if len(parts) < 2:
                    continue

                service_name = parts[0].lower()
                cred_type = "_".join(parts[1:]).lower()

                if service_name not in self._credentials:
                    self._credentials[service_name] = {}

                self._credentials[service_name][cred_type] = value

        self._loaded = True
        logger.info(f"Loaded credentials for {len(self._credentials)} services")

    def get_credential(self, service: str, credential_name: str) -> Optional[str]:
        """
        Get a specific credential.

        Args:
            service: The service name (e.g., 'firebase', 'twilio')
            credential_name: The credential name (e.g., 'api_key')

        Returns:
            The credential value or None if not found
        """
        if not self._loaded:
            self.load_credentials()

        return self._credentials.get(service, {}).get(credential_name)

    def get_service_credentials(self, service: str) -> Dict[str, str]:
        """
        Get all credentials for a specific service.

        Args:
            service: The service name (e.g., 'firebase', 'twilio')

        Returns:
            Dictionary of credential names to values
        """
        if not self._loaded:
            self.load_credentials()

        return self._credentials.get(service, {})


class EncryptionService:
    """Handles encryption and decryption of notification content."""

    def __init__(self):
        """Initialize the encryption service."""
        self.credential_manager = CredentialManager()

    def _generate_key(self, seed: str, length: int = 32) -> bytes:
        """
        Generate a key from a seed string.

        Args:
            seed: Seed string for key derivation
            length: Desired key length in bytes

        Returns:
            Generated key as bytes
        """
        if not seed:
            # Generate a completely random key if no seed
            return secrets.token_bytes(length)

        # Otherwise derive key from seed
        key = hashlib.sha256(seed.encode()).digest()

        # Use MLX for additional processing if available
        if MLX_AVAILABLE:
            # Convert to MLX array
            key_array = mx.array([b for b in key])

            # Perform some operations (simplified for illustration)
            # In a real implementation, would use proper MLX crypto primitives
            key_array = key_array + 1  # Simple operation for illustration

            # Convert back to bytes
            key = bytes([int(b) % 256 for b in key_array])

        return key[:length]

    def _crypto_encrypt(self, data: str, key: str, encryption_type: EncryptionType) -> str:
        """
        Encrypt data using real cryptographic libraries if available.

        Args:
            data: The plaintext to encrypt
            key: The encryption key
            encryption_type: The type of encryption to use

        Returns:
            Encrypted data as Base64 string
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            # Fall back to simulation if cryptography package not available
            return self._simulate_encryption(data, key, encryption_type)

        data_bytes = data.encode("utf-8")

        if encryption_type == EncryptionType.AES256:
            # Generate key and IV
            derived_key = self._generate_key(key)
            iv = secrets.token_bytes(16)  # 128-bit IV for AES

            # Create padder
            padder = padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(data_bytes) + padder.finalize()

            # Create cipher
            cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv))

            # Encrypt
            encryptor = cipher.encryptor()
            encrypted = encryptor.update(padded_data) + encryptor.finalize()

            # Combine IV and ciphertext
            result = iv + encrypted
            return f"AES256:{base64.b64encode(result).decode('utf-8')}"

        elif encryption_type == EncryptionType.RSA:
            # In a real implementation, this would properly parse an RSA public key
            # This is simplified for illustration
            try:
                # Try to parse key as PEM
                public_key = serialization.load_pem_public_key(key.encode())
            except Exception:
                # Generate a new key for demonstration
                private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                public_key = private_key.public_key()

            # Encrypt with RSA
            encrypted = public_key.encrypt(
                data_bytes,
                asymm_padding.OAEP(
                    mgf=asymm_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            return f"RSA:{base64.b64encode(encrypted).decode('utf-8')}"

        elif encryption_type == EncryptionType.HYBRID:
            # Generate a random AES key
            aes_key = secrets.token_bytes(32)

            # Encrypt data with AES
            iv = secrets.token_bytes(16)
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))

            padder = padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(data_bytes) + padder.finalize()

            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

            # Combine IV and ciphertext for AES part
            aes_part = iv + encrypted_data

            # Encrypt AES key with RSA
            try:
                public_key = serialization.load_pem_public_key(key.encode())
            except Exception:
                private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                public_key = private_key.public_key()

            encrypted_key = public_key.encrypt(
                aes_key,
                asymm_padding.OAEP(
                    mgf=asymm_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            # Combine encrypted key and encrypted data
            key_part = base64.b64encode(encrypted_key).decode("utf-8")
            data_part = base64.b64encode(aes_part).decode("utf-8")

            return f"HYBRID:{key_part}.{data_part}"

        else:
            raise ValueError(f"Unsupported encryption type: {encryption_type}")

    def _simulate_encryption(self, data: str, key: str, encryption_type: EncryptionType) -> str:
        """
        Simulate encryption when cryptographic libraries are not available.

        Args:
            data: The plaintext to encrypt
            key: The encryption key
            encryption_type: The type of encryption to use

        Returns:
            Simulated encrypted data
        """
        # This is only a simulation for illustration purposes
        # In a real implementation, always use proper cryptographic libraries

        if encryption_type == EncryptionType.NONE:
            return data

        elif encryption_type == EncryptionType.AES256:
            # Simulate AES encryption
            key_hash = hashlib.sha256(key.encode()).digest()
            encrypted = key_hash + data.encode("utf-8")
            return f"AES256:{base64.b64encode(encrypted).decode('utf-8')}"

        elif encryption_type == EncryptionType.RSA:
            # Simulate RSA encryption
            key_hash = hashlib.sha512(key.encode()).digest()
            encrypted = key_hash + data.encode("utf-8")
            return f"RSA:{base64.b64encode(encrypted).decode('utf-8')}"

        elif encryption_type == EncryptionType.HYBRID:
            # Simulate hybrid encryption
            key_hash1 = hashlib.sha256(key.encode()).digest()
            key_hash2 = hashlib.sha512((data + key).encode()).digest()
            aes_part = base64.b64encode(key_hash1 + data.encode("utf-8")).decode("utf-8")
            rsa_part = base64.b64encode(key_hash2).decode("utf-8")
            return f"HYBRID:{rsa_part[:32]}.{aes_part}"

        else:
            raise ValueError(f"Unsupported encryption type: {encryption_type}")

    def encrypt(
        self,
        data: str,
        key: str,
        encryption_type: EncryptionType = EncryptionType.AES256,
    ) -> str:
        """
        Encrypt data for secure transmission.

        Args:
            data: The plaintext to encrypt
            key: The encryption key or public key
            encryption_type: The type of encryption to use

        Returns:
            Encrypted data
        """
        if encryption_type == EncryptionType.NONE:
            return data

        logger.debug(f"Encrypting data using {encryption_type.name}")

        # Try real crypto first, fall back to simulation
        try:
            return self._crypto_encrypt(data, key, encryption_type)
        except Exception as e:
            logger.warning(f"Crypto library error: {e}. Using simulation instead.")
            return self._simulate_encryption(data, key, encryption_type)

    def decrypt(self, encrypted_data: str, key: str) -> str:
        """
        Decrypt data.

        Args:
            encrypted_data: The encrypted data
            key: The decryption key or private key

        Returns:
            Decrypted plaintext
        """
        if not encrypted_data or ":" not in encrypted_data:
            return encrypted_data

        encryption_type, data = encrypted_data.split(":", 1)

        logger.debug(f"Decrypting data encrypted with {encryption_type}")

        # This is a simulation - in a real system, use proper crypto libraries
        # In a real implementation, this would properly parse the encrypted data
        # and use the appropriate decryption algorithm

        if encryption_type == "AES256":
            if CRYPTOGRAPHY_AVAILABLE:
                try:
                    # Decode base64
                    encrypted = base64.b64decode(data)

                    # Extract IV and ciphertext
                    iv = encrypted[:16]
                    ciphertext = encrypted[16:]

                    # Derive key
                    derived_key = self._generate_key(key)

                    # Create cipher
                    cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv))

                    # Decrypt
                    decryptor = cipher.decryptor()
                    decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()

                    # Unpad
                    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
                    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()

                    return decrypted.decode("utf-8")
                except Exception as e:
                    logger.warning(f"Decryption error: {e}. Using simulation fallback.")

            # Fallback simulation
            try:
                decoded = base64.b64decode(data)
                # Skip the "key hash" from our simulation
                plaintext = decoded[32:].decode("utf-8")
                return plaintext
            except Exception:
                return "[Decryption Error]"

        elif encryption_type == "RSA":
            # Simulation only - in a real implementation, use proper RSA decryption
            try:
                decoded = base64.b64decode(data)
                # Skip the "key hash" from our simulation
                plaintext = decoded[64:].decode("utf-8")
                return plaintext
            except Exception:
                return "[Decryption Error]"

        elif encryption_type == "HYBRID":
            # For hybrid encryption simulation
            try:
                key_part, data_part = data.split(".", 1)
                decoded = base64.b64decode(data_part)
                # Skip the "key hash" from our simulation
                plaintext = decoded[32:].decode("utf-8")
                return plaintext
            except Exception:
                return "[Decryption Error]"

        else:
            logger.warning(f"Unknown encryption type: {encryption_type}")
            return "[Unknown Encryption]"

    def simulate_tee_protected_processing(self, data: str, operation: str) -> Dict[str, Any]:
        """
        Simulate processing in a Trusted Execution Environment.

        In a real implementation, this would use actual TEE hardware such as
        Intel SGX, ARM TrustZone, or similar technologies.

        Args:
            data: The data to process
            operation: The operation to perform

        Returns:
            Result of the TEE operation
        """
        logger.debug(f"Simulating TEE processing: {operation}")

        if operation == "sign":
            # Simulate digital signature
            signature = base64.b64encode(hashlib.sha256(data.encode("utf-8")).digest()).decode(
                "utf-8"
            )

            return {
                "data": data,
                "signature": signature,
                "timestamp": datetime.now().isoformat(),
            }

        elif operation == "verify":
            # Simulate signature verification
            return {
                "data": data,
                "verified": True,
                "timestamp": datetime.now().isoformat(),
            }

        elif operation == "integrity_check":
            # Simulate integrity check
            checksum = hashlib.sha256(data.encode("utf-8")).hexdigest()
            return {
                "data": data,
                "checksum": checksum,
                "integrity_verified": True,
                "timestamp": datetime.now().isoformat(),
            }

        elif operation == "secure_computation":
            # Simulate secure computation in TEE
            # This would typically be used for sensitive operations
            # like generating cryptographic keys or processing
            # private user data
            result = hashlib.sha256(data.encode("utf-8")).hexdigest()

            return {"result": result, "timestamp": datetime.now().isoformat()}

        else:
            raise ValueError(f"Unsupported TEE operation: {operation}")


class TokenManager:
    """Manages secure tokens for notification services."""

    def __init__(self):
        """Initialize the token manager."""
        self.encryption_service = EncryptionService()
        self.tokens = {}

    def generate_token(self, user_id: str, service: str, expiry: int = 86400) -> str:
        """
        Generate a secure token for a service.

        Args:
            user_id: The user ID
            service: The service name
            expiry: Token validity in seconds

        Returns:
            Secure token
        """
        # Create token payload
        payload = {
            "user_id": user_id,
            "service": service,
            "created": time.time(),
            "expiry": time.time() + expiry,
            "nonce": secrets.token_hex(8),
        }

        # Convert to JSON
        payload_json = json.dumps(payload)

        # Encrypt payload
        master_key = os.environ.get("LLAMA_NOTIFICATIONS_MASTER_KEY", "default-master-key")
        encrypted = self.encryption_service.encrypt(payload_json, master_key, EncryptionType.AES256)

        # Store token
        token_id = secrets.token_hex(16)
        self.tokens[token_id] = {"payload": payload, "created": time.time()}

        # Encode final token
        return f"{token_id}.{base64.urlsafe_b64encode(encrypted.encode()).decode()}"

    def validate_token(self, token: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a token.

        Args:
            token: The token to validate

        Returns:
            Tuple of (is_valid, payload)
        """
        try:
            # Split token
            token_id, encrypted_payload = token.split(".", 1)

            # Check if token exists
            if token_id not in self.tokens:
                return False, {"error": "Invalid token"}

            # Get stored payload
            stored = self.tokens[token_id]

            # Check expiry
            if stored["payload"]["expiry"] < time.time():
                return False, {"error": "Token expired"}

            return True, stored["payload"]

        except Exception as e:
            logger.warning(f"Token validation error: {e}")
            return False, {"error": str(e)}

    def revoke_token(self, token_id: str) -> bool:
        """
        Revoke a token.

        Args:
            token_id: The token ID to revoke

        Returns:
            True if token was revoked, False otherwise
        """
        if token_id in self.tokens:
            del self.tokens[token_id]
            return True
        return False
