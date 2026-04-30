import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

SKILLS_DIR = Path(__file__).parent.parent / "skills"


class SkillLoader:
    """Load and manage skill SKILL.md content."""

    def __init__(self):
        self.skills_dir = SKILLS_DIR
        self._path_cache: dict[str, Path] = {}
        self._md_cache: dict[str, str] = {}

    def _ensure_cache(self):
        """Build path cache by scanning skills directory once."""
        if self._path_cache:
            return
        if not self.skills_dir.exists():
            return
        for item in self.skills_dir.iterdir():
            if item.is_dir():
                skill_id = item.name.lower().replace("-", "_")
                self._path_cache[skill_id] = item

    def get_skill_path(self, skill_id: str) -> Optional[Path]:
        """Get the filesystem path for a skill by its ID."""
        self._ensure_cache()

        # Try exact match first (with underscores)
        if skill_id in self._path_cache:
            return self._path_cache[skill_id]

        # Try with hyphens
        hyphen_id = skill_id.replace("_", "-")
        for cached_id, path in self._path_cache.items():
            if cached_id.replace("_", "-") == hyphen_id:
                return path

        return None

    def load_skill_md(self, skill_id: str) -> Optional[str]:
        """Load SKILL.md content for a skill."""
        # Check memory cache first
        if skill_id in self._md_cache:
            return self._md_cache[skill_id]

        skill_path = self.get_skill_path(skill_id)
        if not skill_path:
            return None

        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            return None

        content = skill_md.read_text(encoding="utf-8")
        self._md_cache[skill_id] = content
        return content

    def build_skill_context(self, skills: List[Dict[str, Any]]) -> str:
        """
        Build a context string from all enabled skills.
        This injects skill instructions into the system prompt.
        """
        if not skills:
            return ""

        context_parts = []
        context_parts.append("\n\n=== AVAILABLE SKILLS ===\n")

        for skill in skills:
            skill_id = skill.get("id")
            skill_name = skill.get("name", skill_id)
            skill_enabled = skill.get("enabled", False)

            if not skill_enabled:
                continue

            skill_md = self.load_skill_md(skill_id)
            if skill_md:
                context_parts.append(f"\n--- Skill: {skill_name} ({skill_id}) ---\n")
                context_parts.append(skill_md)
                context_parts.append(f"\n--- End of {skill_name} ---\n")

        context_parts.append("\n=== END OF SKILLS ===\n")
        return "".join(context_parts)

    def list_available_skills(self) -> List[Dict[str, Any]]:
        """List all skills in the skills directory with their metadata."""
        skills = []
        for item in self.skills_dir.iterdir():
            if not item.is_dir():
                continue
            skill_md = item / "SKILL.md"
            if not skill_md.exists():
                continue

            # Try to extract name from first heading
            name = item.name
            try:
                content = skill_md.read_text(encoding="utf-8")
                import re
                match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
                if match:
                    name = match.group(1).strip()
            except Exception:
                pass

            skills.append({
                "id": item.name.lower().replace("-", "_"),
                "name": name,
                "path": str(item),
                "has_skill_md": True
            })

        return skills