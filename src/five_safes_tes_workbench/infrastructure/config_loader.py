from pathlib import Path
from ..models.config_dataclass import FILE_KEY_MAP


class ValidateConfigLoader:
    """
    Loads and parses a workbench configuration file.

    Reads a KEY=VALUE formatted text file, validates its structure,
    and maps file keys to model field names using FILE_KEY_MAP.

    Supported file format:
    ----------------------
        - KEY=VALUE pairs (one per line)
        - Lines starting with '#' are treated as comments
        - Empty lines are ignored
        - Whitespace around keys and values is stripped
    """

    def __init__(self, config_path: str) -> None:
        """
        Initialize the loader with a file path
        """
        self._path = config_path

    def load(self) -> dict[str, str | list[str]]:
        """
        Load, validate, and parse the configuration file.

        Returns:
        ---------
            Dictionary with model field names as keys
            and their corresponding values.

        Raises:
        --------
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a regular file
                        or contains invalid formatting.
        """

        path = Path(self._path)
        self._validate_path(path)
        
        raw_data = self._parse_file(path)
        return self._map_keys(raw_data)
    
    
    def _parse_file(self, path: Path) -> dict[str, str]:
        """
        Parse the configuration file into raw key-value pairs.

        Reads each line, skips comments and empty lines,
        validates format, and extracts KEY=VALUE pairs.
        
        Attributes:
        -----------
            path (Path): The path to the configuration file.
        
        Returns:
        --------
            Dictionary of raw key-value pairs from the file.
        """

        data: dict[str, str] = {}

        with open(path, "r") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()

                # Skip empty lines and comments
                if not self._validate_line(line, line_number):
                    continue

                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                if not key:
                    raise ValueError(
                        f"Empty key at line {line_number}: '{line}'"
                    )

                data[key] = value

        return data


    def _map_keys(self, raw_data: dict[str, str]) -> dict[str, str | list[str]]:
        """
        Map raw file keys to model field names.

        Uses FILE_KEY_MAP to translate file keys (e.g., "5STES_PROJECT")
        to model field names (e.g., "project").

        Special handling:
            - 'tres' field: comma-separated string → list of strings

        Attributes:
        -----------
            raw_data (dict): Raw key-value pairs from the file.

        Returns:
        --------
            Dictionary with model field names as keys and their values.
        """

        mapped: dict[str, str | list[str]] = {}

        for file_key, field_name in FILE_KEY_MAP.items():
            if file_key in raw_data:
                value = raw_data[file_key]

                # Special handling: convert comma-separated to list
                if field_name == "tres":
                    mapped[field_name] = [
                        item.strip() for item in value.split(",")
                    ]
                else:
                    mapped[field_name] = value

        # Warn about unknown keys
        unknown_keys = set(raw_data.keys()) - set(FILE_KEY_MAP.keys())
        if unknown_keys:
            print(f"Unknown keys in config file (ignored): {', '.join(unknown_keys)}")

        return mapped
    
    # ------ Validation Helpers ------

    def _validate_path(self, path: Path) -> None:
        """
        Validate that the configuration file 
        exists and is a regular file.
        """
        if not path.exists():
            raise FileNotFoundError(
                f"Configuration file not found at: {self._path}"
            )
        
        if not path.is_file():
            raise ValueError(
                f"Configuration path is not a file: {self._path}"
            )
        
        
    def _validate_line(self, line: str, line_number: int) -> bool:
        """
        Validate a single line from the configuration file.
        
        Returns:
            True if the line should be processed.
            False if the line should be skipped (empty or comment).

        Raises:
            ValueError: If the line is not empty/comment
                        but doesn't contain '='.
        """
        
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            return False

        if "=" not in line:
            raise ValueError(
                f"Invalid format at line {line_number}: '{line}'. "
                f"Expected KEY=VALUE format."
            )

        return True
            
    