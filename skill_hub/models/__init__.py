"""Models package"""

# Import models
from skill_hub.models.skill import Skill
from skill_hub.models.skill_version import SkillVersion
from skill_hub.models.category import Category

# Configure relationships after both classes are defined
from sqlalchemy.orm import configure_mappers

# Configure mappers to resolve relationships
# This is called lazily when needed, not at import time
def configure_all_mappers():
    """Configure all mappers for the models"""
    configure_mappers()

__all__ = ["Skill", "SkillVersion", "Category", "configure_all_mappers"]
