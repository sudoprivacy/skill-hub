from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

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
        return cls(
            name=form_data.get("name", ""),
            display_name=form_data.get("display_name", ""),
            version=form_data.get("version", ""),
            category=form_data.get("category"),
            description=form_data.get("description"),
            core_features=form_data.get("core_features"),
            applicable_scenarios=form_data.get("applicable_scenarios"),
            categories=form_data.getlist("categories") if hasattr(form_data, "getlist") else form_data.get("categories"),
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
