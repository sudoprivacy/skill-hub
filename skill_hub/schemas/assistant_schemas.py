from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple

@dataclass
class AssistantCreateRequest:
    name: str
    profession: str
    description: Optional[str] = None
    prompt_file: Optional[str] = None
    avatar: Optional[str] = None
    default_init_prompt: Optional[str] = None
    category_id: Optional[str] = None
    tenant_id: Optional[str] = None
    sort_order: Optional[int] = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssistantCreateRequest":
        # Handle both camelCase from API and snake_case internally
        # Also handle empty strings from multipart/form-data by coercing them to None

        def _get_val(key1, key2=None):
            val = data.get(key1)
            if val is None and key2:
                val = data.get(key2)
            # Return None if the value is an empty string
            return val if val != "" else None

        return cls(
            name=data.get("name", ""),
            profession=data.get("profession", ""),
            description=_get_val("description"),
            prompt_file=_get_val("promptFile", "prompt_file"),
            avatar=_get_val("avatar"),
            default_init_prompt=_get_val("defaultInitPrompt", "default_init_prompt"),
            category_id=_get_val("categoryId", "category_id"),
            tenant_id=_get_val("tenantId", "tenant_id"),
            sort_order=int(_get_val("sortOrder", "sort_order")) if _get_val("sortOrder", "sort_order") is not None else 0
        )
        
    def validate(self) -> Tuple[bool, Optional[str]]:
        if not self.name or not isinstance(self.name, str) or not self.name.strip():
            return False, "name is required and must be a non-empty string"
            
        if not self.profession or not isinstance(self.profession, str) or not self.profession.strip():
            return False, "profession is required and must be a non-empty string"
            
        return True, None
        
    def to_assistant_data(self) -> Dict[str, Any]:
        """Convert validated schema to dictionary matching model fields."""
        data = {
            "name": self.name.strip(),
            "profession": self.profession.strip(),
        }

        if self.description is not None:
            data["description"] = self.description

        if self.prompt_file is not None:
            data["prompt_file"] = self.prompt_file

        if self.avatar is not None:
            data["avatar"] = self.avatar

        if self.default_init_prompt is not None:
            data["default_init_prompt"] = self.default_init_prompt

        if self.category_id is not None:
            data["category_id"] = self.category_id

        if self.tenant_id is not None:
            data["tenant_id"] = self.tenant_id

        if self.sort_order is not None:
            data["sort_order"] = self.sort_order

        return data

@dataclass
class AssistantUpdateRequest:
    name: Optional[str] = None
    profession: Optional[str] = None
    description: Optional[str] = None
    prompt_file: Optional[str] = None
    avatar: Optional[str] = None
    default_init_prompt: Optional[str] = None
    category_id: Optional[str] = None
    tenant_id: Optional[str] = None
    sort_order: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssistantUpdateRequest":
        return cls(
            name=data.get("name"),
            profession=data.get("profession"),
            description=data.get("description"),
            prompt_file=data.get("promptFile") or data.get("prompt_file"),
            avatar=data.get("avatar"),
            default_init_prompt=data.get("defaultInitPrompt") or data.get("default_init_prompt"),
            category_id=data.get("categoryId") or data.get("category_id"),
            tenant_id=data.get("tenantId") or data.get("tenant_id"),
            sort_order=int(data.get("sortOrder")) if data.get("sortOrder") is not None else (int(data.get("sort_order")) if data.get("sort_order") is not None else None)
        )
        
    def validate(self) -> Tuple[bool, Optional[str]]:
        # Ensure at least one field is provided for update
        fields = [
            self.name, self.profession, self.description,
            self.prompt_file, self.avatar, self.default_init_prompt, self.category_id, self.tenant_id, self.sort_order
        ]
        
        if all(field is None for field in fields):
            return False, "At least one field is required for update"
            
        if self.name is not None and (not isinstance(self.name, str) or not self.name.strip()):
            return False, "name must be a non-empty string"
            
        if self.profession is not None and (not isinstance(self.profession, str) or not self.profession.strip()):
            return False, "profession must be a non-empty string"
            
        return True, None
        
    def to_update_data(self) -> Dict[str, Any]:
        """Convert to dictionary with only provided fields."""
        data = {}
        
        if self.name is not None:
            data["name"] = self.name.strip()
            
        if self.profession is not None:
            data["profession"] = self.profession.strip()
            
        if self.description is not None:
            data["description"] = self.description
            
        if self.prompt_file is not None:
            data["prompt_file"] = self.prompt_file
            
        if self.avatar is not None:
            data["avatar"] = self.avatar
            
        if self.default_init_prompt is not None:
            data["default_init_prompt"] = self.default_init_prompt
            
        if self.category_id is not None:
            data["category_id"] = self.category_id

        if self.tenant_id is not None:
            data["tenant_id"] = self.tenant_id

        if self.sort_order is not None:
            data["sort_order"] = self.sort_order

        return data
