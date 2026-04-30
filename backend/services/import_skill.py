import os
import shutil
import urllib.request
import zipfile
import tarfile
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

SKILLS_DIR = Path(__file__).parent.parent / "skills"


class SkillImportService:
    def __init__(self):
        self.skills_dir = SKILLS_DIR
        self.skills_dir.mkdir(exist_ok=True)

    def is_url(self, source: str) -> bool:
        return source.startswith(("http://", "https://", "git+"))

    def is_local_absolute(self, source: str) -> bool:
        return os.path.isabs(source)

    def is_within_project(self, path: str) -> bool:
        project_root = Path(__file__).parent.parent.parent.resolve()
        return Path(path).resolve().is_relative_to(project_root)

    def import_skill(self, source: str) -> dict:
        """
        Import skill(s) from source (URL or local path).
        Returns: { "success": bool, "name": str, "type": str, "path": str, "error": str }
        If source is a directory containing multiple skills, imports all.
        """
        if self.is_url(source):
            return self._import_from_url(source)
        elif self.is_local_absolute(source):
            return self._import_from_local(source)
        else:
            return {"success": False, "error": "Invalid source: must be URL or absolute path"}

    def _is_skill_dir(self, path: Path) -> bool:
        """Check if a directory is a valid skill (has SKILL.md or skill.json)."""
        return (path / "SKILL.md").exists() or (path / "skill.json").exists()

    def _scan_skills_dir(self, source_path: Path) -> List[Path]:
        """Scan a directory for valid skill subdirectories."""
        skills = []
        for item in source_path.iterdir():
            if item.is_dir() and self._is_skill_dir(item):
                skills.append(item)
        return skills

    def _register_to_json(self, skill_name: str, skill_path: Path) -> str:
        """Register imported skill to skills.json. Returns the skill id."""
        from config import load_json, save_json

        # Try to read SKILL.md for id and name
        skill_id = skill_name.lower().replace("-", "_").replace(" ", "_")
        display_name = skill_name
        skill_md = skill_path / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
            if match:
                display_name = match.group(1).strip()

        data = load_json("skills.json")
        # Check if already registered
        if any(s["id"] == skill_id for s in data.get("skills", [])):
            return skill_id  # Already registered

        data.setdefault("skills", []).append({
            "id": skill_id,
            "name": display_name,
            "enabled": False,
            "config": {}
        })
        save_json("skills.json", data)
        return skill_id

    def _import_from_url(self, url: str) -> dict:
        """Download and import a skill from URL (.skill, .zip, or git repo)."""
        if url.startswith("git+"):
            return self._import_from_git(url)

        if url.endswith(".skill"):
            return self._import_skill_package(url)
        elif url.endswith((".zip", ".tar.gz", ".tgz")):
            return self._extract_archive(url)
        else:
            return self._import_skill_package(url)

    def _import_from_git(self, git_url: str) -> dict:
        """Clone a git repository as a skill."""
        repo_url = git_url.replace("git+", "")
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        dest = self.skills_dir / repo_name

        if dest.exists():
            return {"success": False, "error": f"Skill '{repo_name}' already exists"}

        try:
            os.system(f"git clone --depth 1 {repo_url} {dest}")
            if dest.exists():
                self._register_to_json(repo_name, dest)
                return {"success": True, "name": repo_name, "type": "clone", "path": str(dest)}
            else:
                return {"success": False, "error": "Git clone failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _import_skill_package(self, url: str) -> dict:
        """Download a .skill package and extract it."""
        parts = url.rstrip("/").split("/")
        filename = parts[-1]
        skill_name = filename.replace(".skill", "").replace(".zip", "")
        tmp_file = f"/tmp/{filename}"

        try:
            urllib.request.urlretrieve(url, tmp_file)
            dest = self.skills_dir / skill_name
            if dest.exists():
                return {"success": False, "error": f"Skill '{skill_name}' already exists"}

            with zipfile.ZipFile(tmp_file, 'r') as z:
                z.extractall(dest)

            os.remove(tmp_file)
            self._register_to_json(skill_name, dest)
            return {"success": True, "name": skill_name, "type": "download", "path": str(dest)}
        except Exception as e:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            return {"success": False, "error": str(e)}

    def _extract_archive(self, url: str) -> dict:
        """Extract a zip/tar.gz archive."""
        filename = url.split("/")[-1]
        tmp_file = f"/tmp/{filename}"

        try:
            urllib.request.urlretrieve(url, tmp_file)
            skill_name = filename.replace(".zip", "").replace(".tar.gz", "").replace(".tgz", "")
            dest = self.skills_dir / skill_name

            if dest.exists():
                return {"success": False, "error": f"Skill '{skill_name}' already exists"}

            if filename.endswith(".zip"):
                with zipfile.ZipFile(tmp_file, 'r') as z:
                    z.extractall(dest)
            else:
                with tarfile.open(tmp_file, 'r:gz') as t:
                    t.extractall(dest)

            os.remove(tmp_file)
            self._register_to_json(skill_name, dest)
            return {"success": True, "name": skill_name, "type": "download", "path": str(dest)}
        except Exception as e:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            return {"success": False, "error": str(e)}

    def _import_from_local(self, source: str) -> dict:
        """Import from a local path (symlink or copy). Can be a single skill or a directory of skills."""
        if not os.path.exists(source):
            return {"success": False, "error": f"Path does not exist: {source}"}

        source_path = Path(source).resolve()

        # If it's a single skill directory
        if source_path.is_dir() and self._is_skill_dir(source_path):
            return self._import_single_skill(source_path)

        # If it's a directory containing multiple skills
        if source_path.is_dir():
            return self._import_skills_directory(source_path)

        return {"success": False, "error": "Source is not a valid skill directory"}

    def _import_single_skill(self, source_path: Path) -> dict:
        """Import a single skill directory."""
        skill_name = source_path.name
        dest = self.skills_dir / skill_name

        if dest.exists():
            return {"success": False, "error": f"Skill '{skill_name}' already exists"}

        if self.is_within_project(str(source_path)):
            shutil.copytree(source_path, dest)
            import_type = "copy"
        else:
            try:
                os.symlink(source_path, dest)
                import_type = "symlink"
            except OSError:
                shutil.copytree(source_path, dest)
                import_type = "copy"

        self._register_to_json(skill_name, dest)
        return {"success": True, "name": skill_name, "type": import_type, "path": str(dest)}

    def _import_skills_directory(self, source_path: Path) -> dict:
        """Import all skills from a directory."""
        skill_dirs = self._scan_skills_dir(source_path)
        if not skill_dirs:
            return {"success": False, "error": "No valid skills found in directory"}

        imported = []
        failed = []

        for skill_dir in skill_dirs:
            skill_name = skill_dir.name
            dest = self.skills_dir / skill_name

            if dest.exists():
                failed.append(f"{skill_name} (already exists)")
                continue

            try:
                if self.is_within_project(str(skill_dir)):
                    shutil.copytree(skill_dir, dest)
                    import_type = "copy"
                else:
                    try:
                        os.symlink(skill_dir, dest)
                        import_type = "symlink"
                    except OSError:
                        shutil.copytree(skill_dir, dest)
                        import_type = "copy"

                self._register_to_json(skill_name, dest)
                imported.append(skill_name)
            except Exception as e:
                failed.append(f"{skill_name} ({str(e)})")

        if not imported and failed:
            return {"success": False, "error": f"Import failed: {', '.join(failed)}"}

        return {
            "success": True,
            "name": f"{len(imported)} skill(s)",
            "type": "batch",
            "imported": imported,
            "failed": failed if failed else None,
            "path": str(self.skills_dir)
        }

    def list_imported_skills(self) -> List[Dict[str, Any]]:
        """List all imported skills (both local and symlinks)."""
        skills = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() or item.is_symlink():
                link_target = os.readlink(item) if item.is_symlink() else None
                skills.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "symlink" if link_target else "local"
                })
        return skills