import os
from typing import Any

from pydantic import BaseModel


class BaseConfig(BaseModel):
    model_config = {"extra": "forbid", "validate_assignment": True}

    @classmethod
    def from_env(cls, prefix: str = "") -> "BaseConfig":
        env_data = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                env_data[config_key] = value
        return cls(**env_data)

    def resolve_secrets(self, secret_manager: Any | None = None) -> "BaseConfig":
        return self
