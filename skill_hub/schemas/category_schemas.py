from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

@dataclass
class CategoryCreateRequest:
    name: str
    display_name: str
    order_index: Optional[int] = 0
    icon_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CategoryCreateRequest":
        return cls(
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            order_index=data.get("order_index", 0),
            icon_url=data.get("icon_url"),
        )

    def validate(self) -> Tuple[bool, Optional[str]]:
        if not self.name:
            return False, "name is required"
        if not self.display_name:
            return False, "display_name is required"
        return True, None

    def to_category_data(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "order_index": self.order_index,
            "icon_url": self.icon_url,
        }

@dataclass
class CategoryUpdateRequest:
    name: Optional[str] = None
    display_name: Optional[str] = None
    order_index: Optional[int] = None
    icon_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CategoryUpdateRequest":
        return cls(
            name=data.get("name"),
            display_name=data.get("display_name"),
            order_index=data.get("order_index"),
            icon_url=data.get("icon_url"),
        )

    def validate(self) -> Tuple[bool, Optional[str]]:
        # at least one field should be present to update
        if self.name is None and self.display_name is None and self.order_index is None and self.icon_url is None:
            return False, "at least one field is required to update"
        return True, None

    def to_update_data(self) -> Dict[str, Any]:
        data = {}
        if self.name is not None:
            data["name"] = self.name
        if self.display_name is not None:
            data["display_name"] = self.display_name
        if self.order_index is not None:
            data["order_index"] = self.order_index
        if self.icon_url is not None:
            data["icon_url"] = self.icon_url
        return data
