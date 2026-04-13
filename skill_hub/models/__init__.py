"""Models package"""

# Import models
from skill_hub.models.skill import Skill
from skill_hub.models.skill_version import SkillVersion
from skill_hub.models.category import Category
from skill_hub.models.assistant import Assistant

# Configure relationships after both classes are defined
from sqlalchemy.orm import configure_mappers

# Configure mappers to resolve relationships
# This is called lazily when needed, not at import time
def configure_all_mappers():
    """Configure all mappers for the models"""
    configure_mappers()

__all__ = ["Skill", "SkillVersion", "Category", "Assistant", "configure_all_mappers"]
