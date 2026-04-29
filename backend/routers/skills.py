from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import load_json, save_json

router = APIRouter()

class SkillConfig(BaseModel):
    id: str
    name: str
    enabled: bool = True
    config: dict = {}

@router.get("/")
def list_skills():
    data = load_json("skills.json")
    return data

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
