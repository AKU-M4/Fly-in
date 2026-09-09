from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from models import ZoneType


class RawMetadata(BaseModel):
    zone: ZoneType = Field(default=ZoneType.NORMAL)
    color: Optional[str] = Field(default="white")
    max_drones: int = Field(default=1, ge=1)
    max_link_capacity: int = Field(default=1, ge=1)


class MetadataParser:
    @staticmethod
    def extract_and_parse(line: str) -> Tuple[str, RawMetadata]:
        open_b = line.find("[")
        close_b = line.rfind("]")

        if open_b == -1 or close_b == -1 or close_b < open_b:
            return line.strip(), RawMetadata()

        clean_line = (line[:open_b] + " " + line[close_b + 1:]).strip()
        raw_meta = line[open_b + 1:close_b].strip()

        meta_kwargs: Dict[str, Any] = {}
        for token in raw_meta.split():
            if "=" in token:
                k, v = token.split("=", 1)
                v = v.strip("\"'")
                if k in ("max_drones", "max_link_capacity"):
                    if v.isdigit():
                        meta_kwargs[k] = int(v)
                elif k == "zone":
                    try:
                        meta_kwargs[k] = ZoneType(v)
                    except ValueError:
                        pass
                else:
                    meta_kwargs[k] = v

        return clean_line, RawMetadata(**meta_kwargs)
