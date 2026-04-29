from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import load_json, save_json

router = APIRouter()

class ModelConfig(BaseModel):
    id: str
    name: str
    provider: str
    api_key: str
    api_base: str
    enabled: bool = True

class SetActiveRequest(BaseModel):
    model_id: str

@router.get("/")
def list_models():
    data = load_json("models.json")
    return data

@router.post("/")
def add_model(model: ModelConfig):
    data = load_json("models.json")
    if any(m["id"] == model.id for m in data.get("models", [])):
        raise HTTPException(status_code=400, detail="Model already exists")
    data.setdefault("models", []).append(model.model_dump())
    if data.get("active_model") is None:
        data["active_model"] = model.id
    save_json("models.json", data)
    return {"success": True}

@router.put("/{model_id}")
def update_model(model_id: str, model: ModelConfig):
    data = load_json("models.json")
    for i, m in enumerate(data.get("models", [])):
        if m["id"] == model_id:
            data["models"][i] = model.model_dump()
            save_json("models.json", data)
            return {"success": True}
    raise HTTPException(status_code=404, detail="Model not found")

@router.delete("/{model_id}")
def delete_model(model_id: str):
    data = load_json("models.json")
    data["models"] = [m for m in data.get("models", []) if m["id"] != model_id]
    if data.get("active_model") == model_id:
        data["active_model"] = data["models"][0]["id"] if data["models"] else None
    save_json("models.json", data)
    return {"success": True}

@router.put("/{model_id}/active")
def set_active_model(model_id: str):
    data = load_json("models.json")
    if not any(m["id"] == model_id for m in data.get("models", [])):
        raise HTTPException(status_code=404, detail="Model not found")
    data["active_model"] = model_id
    save_json("models.json", data)
    return {"success": True}
