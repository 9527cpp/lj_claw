from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import load_json, save_json
from services.import_skill import SkillImportService

router = APIRouter()
import_service = SkillImportService()

class SkillConfig(BaseModel):
    id: str
    name: str
    enabled: bool = True
    config: dict = {}

class ImportRequest(BaseModel):
    source: str  # URL or local absolute path

@router.get("/")
def list_skills():
    data = load_json("skills.json")
    return data

@router.post("/import")
async def import_skill(request: ImportRequest):
    """Import a skill from URL (cloud) or local path (symlink or copy)."""
    result = import_service.import_skill(request.source)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Import failed"))
    return result

@router.get("/imported")
def list_imported_skills():
    """List all locally imported/skilled skills."""
    return {"skills": import_service.list_imported_skills()}

@router.get("/import-sources")
def list_import_sources():
    """List all import sources (paths/URLs) with their managed skills."""
    return {"sources": import_service.list_import_sources()}

@router.delete("/import")
async def unimport_skill(source: str):
    """Remove an imported skill source and all its skills from management."""
    result = import_service.unimport_skill(source)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unimport failed"))
    return result

@router.put("/{skill_id}")
def update_skill(skill_id: str, skill: SkillConfig):
    data = load_json("skills.json")
    for i, s in enumerate(data.get("skills", [])):
        if s["id"] == skill_id:
            data["skills"][i] = skill.model_dump()
            save_json("skills.json", data)
            return {"success": True}
    raise HTTPException(status_code=404, detail="Skill not found")

@router.put("/{skill_id}/enabled")
def toggle_skill(skill_id: str, enabled: bool):
    data = load_json("skills.json")
    for i, s in enumerate(data.get("skills", [])):
        if s["id"] == skill_id:
            data["skills"][i]["enabled"] = enabled
            save_json("skills.json", data)
            return {"success": True}
    raise HTTPException(status_code=404, detail="Skill not found")
