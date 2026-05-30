from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import json

@dataclass
class SkillCreateRequest:
    name: str
    display_name: str
    version: str
    category: Optional[str] = None
    description: Optional[str] = None
    core_features: Optional[str] = None
    applicable_scenarios: Optional[str] = None
    categories: Optional[list] = None
    emoji: Optional[str] = None
    homepage: Optional[str] = None
    changelog: Optional[str] = None
    author_id: Optional[str] = None
    sort_order: Optional[int] = 0
    status: Optional[int] = 0
    tenant_id: Optional[str] = None

    @classmethod
    def from_form_data(cls, form_data: Dict[str, Any]) -> "SkillCreateRequest":
        categories_raw = form_data.getlist("categories") if hasattr(form_data, "getlist") else form_data.get("categories")
        categories_parsed = None
        if categories_raw:
            if isinstance(categories_raw, list):
                if len(categories_raw) == 1 and isinstance(categories_raw[0], str):
                    try:
                        categories_parsed = json.loads(categories_raw[0])
                    except json.JSONDecodeError:
                        categories_parsed = [s.strip() for s in categories_raw[0].split(",") if s.strip()]
                else:
                    categories_parsed = categories_raw
            elif isinstance(categories_raw, str):
                try:
                    categories_parsed = json.loads(categories_raw)
                except json.JSONDecodeError:
                    categories_parsed = [s.strip() for s in categories_raw.split(",") if s.strip()]

        return cls(
            name=form_data.get("name", ""),
            display_name=form_data.get("display_name", ""),
            version=form_data.get("version", ""),
            category=form_data.get("category"),
            description=form_data.get("description"),
            core_features=form_data.get("core_features"),
            applicable_scenarios=form_data.get("applicable_scenarios"),
            categories=categories_parsed,
            emoji=form_data.get("emoji"),
            homepage=form_data.get("homepage"),
            changelog=form_data.get("changelog"),
            author_id=form_data.get("author_id"),
            tenant_id=form_data.get("tenant_id"),
            sort_order=int(form_data.get("sort_order", 0)) if form_data.get("sort_order") else 0,
            status=int(form_data.get("status", 0)) if form_data.get("status") else 0,
        )

    def validate(self) -> Tuple[bool, Optional[str]]:
        if not self.name:
            return False, "name is required"
        if not self.display_name:
            return False, "display_name is required"
        if not self.version:
            return False, "version is required"
        return True, None

    def to_skill_data(self, author_id: str) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "category": self.category,
            "description": self.description,
            "core_features": self.core_features,
            "applicable_scenarios": self.applicable_scenarios,
            "categories": self.categories,
            "emoji": self.emoji,
            "homepage": self.homepage,
            "author_id": author_id or self.author_id,
            "tenant_id": self.tenant_id,
            "sort_order": self.sort_order,
            "status": self.status,
        }

    def to_version_data(self, skill_id: str, source_url: str, checksum: str, readme_content: Optional[str] = None) -> Dict[str, Any]:
        return {
            "skill_id": skill_id,
            "version": self.version,
            "source_url": source_url,
            "checksum": checksum,
            "changelog": self.changelog,
            "readme_content": readme_content
        }

# Alias for tests
AddSkillRequest = SkillCreateRequest


@dataclass
class SkillUpdateRequest:
    name: Optional[str] = None
    display_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    core_features: Optional[str] = None
    applicable_scenarios: Optional[str] = None
    categories: Optional[list] = None
    emoji: Optional[str] = None
    icon: Optional[str] = None
    homepage: Optional[str] = None
    author_id: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[int] = None
    tenant_id: Optional[str] = None
    star_count: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillUpdateRequest":
        def _get_val(key: str, fallback_key: Optional[str] = None):
            value = data.get(key)
            if value is None and fallback_key:
                value = data.get(fallback_key)
            return value if value != "" else None

        def _parse_int(value):
            return int(value) if value is not None else None

        categories_raw = _get_val("categories")
        categories_parsed = None
        if categories_raw is not None:
            if isinstance(categories_raw, list):
                categories_parsed = categories_raw
            elif isinstance(categories_raw, str):
                try:
                    categories_parsed = json.loads(categories_raw)
                except json.JSONDecodeError:
                    categories_parsed = [s.strip() for s in categories_raw.split(",") if s.strip()]

        return cls(
            name=_get_val("name"),
            display_name=_get_val("display_name", "displayName"),
            category=_get_val("category"),
            description=_get_val("description"),
            core_features=_get_val("core_features", "coreFeatures"),
            applicable_scenarios=_get_val("applicable_scenarios", "applicableScenarios"),
            categories=categories_parsed,
            emoji=_get_val("emoji"),
            icon=_get_val("icon"),
            homepage=_get_val("homepage"),
            author_id=_get_val("author_id", "authorId"),
            tenant_id=_get_val("tenant_id", "tenantId"),
            sort_order=_parse_int(_get_val("sort_order", "sortOrder")),
            status=_parse_int(_get_val("status")),
            star_count=_parse_int(_get_val("star_count", "starCount")),
        )

    def validate(self) -> Tuple[bool, Optional[str]]:
        fields = [
            self.name, self.display_name, self.category, self.description,
            self.core_features, self.applicable_scenarios, self.categories,
            self.emoji, self.icon, self.homepage, self.author_id, self.sort_order,
            self.status, self.tenant_id, self.star_count
        ]

        if all(field is None for field in fields):
            return False, "At least one field is required for update"

        if self.name is not None and (not isinstance(self.name, str) or not self.name.strip()):
            return False, "name must be a non-empty string"

        if self.display_name is not None and (
            not isinstance(self.display_name, str) or not self.display_name.strip()
        ):
            return False, "display_name must be a non-empty string"

        return True, None

    def to_update_data(self) -> Dict[str, Any]:
        data = {}

        if self.name is not None:
            data["name"] = self.name.strip()

        if self.display_name is not None:
            data["display_name"] = self.display_name.strip()

        if self.category is not None:
            data["category"] = self.category

        if self.description is not None:
            data["description"] = self.description

        if self.core_features is not None:
            data["core_features"] = self.core_features

        if self.applicable_scenarios is not None:
            data["applicable_scenarios"] = self.applicable_scenarios

        if self.categories is not None:
            data["categories"] = self.categories

        if self.emoji is not None:
            data["emoji"] = self.emoji

        if self.icon is not None:
            data["icon"] = self.icon

        if self.homepage is not None:
            data["homepage"] = self.homepage

        if self.author_id is not None:
            data["author_id"] = self.author_id

        if self.tenant_id is not None:
            data["tenant_id"] = self.tenant_id

        if self.sort_order is not None:
            data["sort_order"] = self.sort_order

        if self.status is not None:
            data["status"] = self.status

        if self.star_count is not None:
            data["star_count"] = self.star_count

        return data
