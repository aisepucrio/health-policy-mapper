import re
from dataclasses import dataclass, field
from typing import Dict, Any

class InvalidColumnNameError(ValueError):
    """Custom exception for invalid column names."""
    pass

@dataclass(frozen=True)
class Column:
    """
    Value Object representing a extraction column.

    Garantees that 'name' is a valid identifier (letters, digits, underscores, and not starting with a digit).
    and 'description' is a string. (not exceeding 300 characters).
    """

    name: str = field()
    description: str = field(default="")

    def __post_init__(self):

        # Pre-process the name: remove special characters and normalize
        processed_name = self.name.lower()

        # Replace common separators with underscores
        processed_name = processed_name.replace(" ", "_")
        processed_name = processed_name.replace("-", "_")
        processed_name = processed_name.replace("+", "_")

        # Remove quotes and other special characters
        processed_name = processed_name.replace("'", "")
        processed_name = processed_name.replace('"', "")
        processed_name = processed_name.replace("(", "")
        processed_name = processed_name.replace(")", "")
        processed_name = processed_name.replace("&", "_and_")
        processed_name = processed_name.replace("/", "_")
        processed_name = processed_name.replace("\\", "_")

        # Validate the name and description
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', processed_name):
            raise InvalidColumnNameError(f"Invalid column name: {processed_name}. Must start with a letter or underscore and contain only letters, digits, and underscores.")

        object.__setattr__(self, 'name', processed_name)

        # Ensure description is a string and does not exceed 300 characters
        if not isinstance(self.description, str) or len(self.description) > 300:
            raise ValueError("Description must be a string not exceeding 300 characters.")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Column object to a dictionary.

        :return: Dictionary representation of the Column.
        """
        return {
            "name": self.name,
            "description": self.description
        }
