from typing import Optional

class MapParsingError(Exception):
    """Raised when an error occurs during parsing or validaton of the map file."""
    def __init__(self, message: str, line_num: Optional[int] = None) -> None:
        if line_num is not None:
            super().__init__(f"line {line_num}: {message}")
        else:
            super().__init__(message)
