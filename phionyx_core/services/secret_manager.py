"""
Secret Manager — v4 §6
=========================

Vault-first secret management with env var fallback.
Abstracts secret access for all modules.
"""

import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class SecretManager:
    """
    Secret management with Vault integration and env var fallback.

    Resolution order:
    1. HashiCorp Vault (if configured)
    2. Environment variables
    3. Default value (if provided)
    """

    def __init__(
        self,
        vault_url: Optional[str] = None,
        vault_token: Optional[str] = None,
        vault_mount: str = "secret",
    ):
        """
        Initialize secret manager.

        Args:
            vault_url: HashiCorp Vault URL (e.g., https://vault.example.com)
            vault_token: Vault authentication token
            vault_mount: Vault secret mount path
        """
        self._vault_url = vault_url or os.environ.get("VAULT_ADDR")
        self._vault_token = vault_token or os.environ.get("VAULT_TOKEN")
        self._vault_mount = vault_mount
        self._vault_client = None
        self._cache: Dict[str, str] = {}

        if self._vault_url and self._vault_token:
            self._init_vault()

    def _init_vault(self) -> None:
        """Initialize Vault client if available."""
        try:
            import hvac
            self._vault_client = hvac.Client(
                url=self._vault_url,
                token=self._vault_token,
            )
            if self._vault_client.is_authenticated():
                logger.info(f"Vault connected: {self._vault_url}")
            else:
                logger.warning("Vault authentication failed — using env fallback")
                self._vault_client = None
        except ImportError:
            logger.info("hvac package not available — using env fallback only")
        except Exception as e:
            logger.warning(f"Vault init failed: {e} — using env fallback")

    def get_secret(
        self,
        key: str,
        default: Optional[str] = None,
        vault_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get a secret value.

        Args:
            key: Secret key name
            default: Default value if not found
            vault_path: Optional Vault path (default: data/{key})

        Returns:
            Secret value or default
        """
        # Check cache
        if key in self._cache:
            return self._cache[key]

        # Try Vault
        if self._vault_client:
            try:
                path = vault_path or f"data/{key}"
                response = self._vault_client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=self._vault_mount,
                )
                value = response["data"]["data"].get(key)
                if value:
                    self._cache[key] = value
                    return value
            except Exception as e:
                logger.debug(f"Vault read failed for {key}: {e}")

        # Fallback to env var
        env_value = os.environ.get(key)
        if env_value:
            self._cache[key] = env_value
            return env_value

        return default

    def clear_cache(self) -> None:
        """Clear cached secrets."""
        self._cache.clear()

    @property
    def is_vault_connected(self) -> bool:
        """Check if Vault is connected."""
        return self._vault_client is not None
