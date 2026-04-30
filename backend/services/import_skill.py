import os
import shutil
import urllib.request
import zipfile
import tarfile
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

SKILLS_DIR = Path(__file__).parent.parent / "skills"
IMPORTS_FILE = Path(__file__).parent.parent / "data" / "skill_imports.json"


class SkillImportService:
    def __init__(self):
        self.skills_dir = SKILLS_DIR
        self.skills_dir.mkdir(exist_ok=True)

    def _load_imports(self) -> List[Dict[str, Any]]:
        if not IMPORTS_FILE.exists():
            return []
        try:
            return json.loads(IMPORTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_imports(self, imports: List[Dict[str, Any]]):
        IMPORTS_FILE.write_text(json.dumps(imports, ensure_ascii=False, indent=2), encoding="utf-8")

    def _is_skill_dir(self, path: Path) -> bool:
        return (path / "SKILL.md").exists() or (path / "skill.json").exists()

    def _scan_skills_in_dir(self, source_path: Path) -> List[Path]:
        skills = []
        for item in source_path.iterdir():
            if item.is_dir() and self._is_skill_dir(item):
                skills.append(item)
        return skills

    def _generate_skill_id(self, skill_name: str) -> str:
        import re
        name = re.sub(r'[^a-zA-Z0-9\-_ ]', '', skill_name)
        return name.lower().replace("-", "_").replace(" ", "_")

    def _register_skill_to_json(self, skill_name: str, skill_path: Path) -> str:
        import re
        from config import load_json, save_json

        skill_id = self._generate_skill_id(skill_name)
        display_name = skill_name
        skill_md = skill_path / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
            if match:
                display_name = match.group(1).strip()

        data = load_json("skills.json")
        if any(s["id"] == skill_id for s in data.get("skills", [])):
            return skill_id

        data.setdefault("skills", []).append({
            "id": skill_id,
            "name": display_name,
            "enabled": True,  # 默认启用
            "config": {}
        })
        save_json("skills.json", data)
        return skill_id

    def _deregister_skill_from_json(self, skill_id: str):
        from config import load_json, save_json
        data = load_json("skills.json")
        data["skills"] = [s for s in data.get("skills", []) if s["id"] != skill_id]
        save_json("skills.json", data)

    def is_url(self, source: str) -> bool:
        return source.startswith(("http://", "https://", "git+"))

    def import_skill(self, source: str) -> dict:
        """Import skills from a directory path or URL."""
        if self.is_url(source):
            return self._import_from_url(source)
        else:
            return self._import_from_directory(source)

    def _import_from_directory(self, source: str) -> dict:
        """Import all skills from a local directory path."""
        if not os.path.exists(source):
            return {"success": False, "error": f"路径不存在: {source}"}

        source_path = Path(source).resolve()
        if not source_path.is_dir():
            return {"success": False, "error": "不是有效的目录"}

        # 检查是否已导入过
        imports = self._load_imports()
        if any(imp.get("source") == source for imp in imports):
            return {"success": False, "error": "该路径已导入"}

        # 扫描目录下的所有 skills
        skill_dirs = self._scan_skills_in_dir(source_path)
        if not skill_dirs:
            return {"success": False, "error": "目录下没有找到有效的 skills"}

        imported = []
        failed = []
        skill_ids = []

        for skill_dir in skill_dirs:
            skill_name = skill_dir.name
            dest = self.skills_dir / skill_name

            if dest.exists():
                failed.append(f"{skill_name} (已存在)")
                continue

            try:
                is_external = not str(skill_dir).startswith(str(source_path.parent.parent))
                if is_external:
                    try:
                        os.symlink(skill_dir, dest)
                    except OSError:
                        shutil.copytree(skill_dir, dest)
                else:
                    shutil.copytree(skill_dir, dest)

                skill_id = self._register_skill_to_json(skill_name, dest)
                skill_ids.append(skill_id)
                imported.append(skill_name)
            except Exception as e:
                failed.append(f"{skill_name} ({str(e)})")

        if not imported and failed:
            return {"success": False, "error": f"导入失败: {', '.join(failed)}"}

        # 记录导入来源
        imports.append({
            "source": source,
            "type": "directory",
            "skills": skill_ids,
            "skill_names": imported
        })
        self._save_imports(imports)

        return {
            "success": True,
            "name": f"{len(imported)} 个 skills",
            "type": "directory",
            "imported": imported,
            "failed": failed if failed else None,
            "source": source
        }

    def _import_from_url(self, url: str) -> dict:
        filename = url.split("/")[-1]
        tmp_file = f"/tmp/{filename}"

        try:
            urllib.request.urlretrieve(url, tmp_file)
            skill_name = filename.replace(".zip", "").replace(".tar.gz", "").replace(".tgz", "").replace(".skill", "")
            dest = self.skills_dir / skill_name

            if dest.exists():
                os.remove(tmp_file)
                return {"success": False, "error": f"Skill '{skill_name}' 已存在"}

            if filename.endswith(".zip"):
                with zipfile.ZipFile(tmp_file, 'r') as z:
                    z.extractall(dest)
            else:
                with tarfile.open(tmp_file, 'r:gz') as t:
                    t.extractall(dest)

            os.remove(tmp_file)

            if not self._is_skill_dir(dest):
                shutil.rmtree(dest)
                return {"success": False, "error": "压缩包内没有有效的 skill"}

            skill_id = self._register_skill_to_json(skill_name, dest)

            # 记录
            imports = self._load_imports()
            imports.append({
                "source": url,
                "type": "download",
                "skills": [skill_id],
                "skill_names": [skill_name]
            })
            self._save_imports(imports)

            return {"success": True, "name": skill_name, "type": "download", "source": url}
        except Exception as e:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            return {"success": False, "error": str(e)}

    def unimport_skill(self, source: str) -> dict:
        """Remove all skills imported from a source path/URL."""
        imports = self._load_imports()
        record = None
        for i, imp in enumerate(imports):
            if imp.get("source") == source:
                record = imports.pop(i)
                break

        if not record:
            return {"success": False, "error": "导入记录不存在"}

        self._save_imports(imports)

        removed = []
        for skill_id in record.get("skills", []):
            self._deregister_skill_from_json(skill_id)
            removed.append(skill_id)

        # 清理 skills 目录下的 symlink/文件夹
        for skill_name in record.get("skill_names", []):
            skill_path = self.skills_dir / skill_name
            if skill_path.exists() or skill_path.is_symlink():
                if skill_path.is_symlink():
                    os.unlink(skill_path)
                elif skill_path.is_dir():
                    shutil.rmtree(skill_path)

        return {"success": True, "removed": removed}

    def list_import_sources(self) -> List[Dict[str, Any]]:
        """List all import sources with their managed skills."""
        imports = self._load_imports()
        return [
            {
                "source": imp.get("source"),
                "type": imp.get("type"),
                "skills": [{"id": sid, "name": name} for sid, name in zip(imp.get("skills", []), imp.get("skill_names", []))]
            }
            for imp in imports
        ]