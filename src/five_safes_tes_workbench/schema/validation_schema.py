from pathlib import Path

import yaml
from pydantic import BaseModel

from .auth_schema import AuthValidationModel
from .config_schema import ConfigValidationModel


class WorkbenchValidationModel(BaseModel):
    """
    Combined Pydantic Model that composes both
    infrastructure config and auth config validation.

    Attributes:
    -----------
    - config: Infrastructure configuration (TES, MinIO, project).
    - auth: Authentication configuration (token or keycloak).
    """

    config: ConfigValidationModel
    auth: AuthValidationModel

    @classmethod
    def from_yaml(cls, config_path: str) -> "WorkbenchValidationModel":
        """
        Load and validate config from a YAML file.

        Args:
            config_path: Path to the YAML config file.

        Returns:
            Validated WorkbenchValidationModel instance.

        Raises:
            FileNotFoundError: If file doesn't exist.
            pydantic.ValidationError: If validation fails.
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls.model_validate(data)
