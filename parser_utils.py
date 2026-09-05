import re
from typing import Dict, Optional, Tuple
from pydantic import BaseModel, Field
from src.models import ZoneType

class RawMetadata(BaseModel):
	zone: ZoneType = ZoneType.NORMAL
	color: Optional[str] = None
	max_drones: int = Field(default=1, ge=1)
	max_link_capacity: int = Field(default=1, ge=1)

class MetadataParser:
	@staticmethod
	def extract_and_parse(raw_text: str) -> Tuple[str, RawMetadata]:
		match = re.search(r"\[(.*?)\]", raw_text)
		meta_dict: Dict[str, str] = {}

		if match:
			inside_brackets = match.group(1).strip()
			clean_text = re.sub(r"\[.*?\]", "", raw_text).strip()

			for token in inside_brackets.split():
				if "=" in token:
					k, v = token.split("=", 1)
					meta_dict[k] = v
				else:
					if token in [t.value for t in ZoneType]:
						meta_dict["zone"] = token
					else:
						meta_dict["color"] = token
			return clean_text, RawMetadata(**meta_dict)
		return raw_text.strip(), RawMetadata()
