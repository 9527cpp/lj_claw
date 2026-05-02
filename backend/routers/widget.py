from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from config import load_json, save_json
import uuid
from datetime import datetime

router = APIRouter()

class WidgetConfig(BaseModel):
    id: str
    site_name: str
    site_url: str
    api_key: str
    primary_color: str = "#cc785c"
    secondary_color: str = "#a9583e"
    bot_name: str = "AI 客服"
    welcome_message: str = "您好，有什么可以帮您的？"
    input_placeholder: str = "输入消息..."
    enabled: bool = True
    created_at: str = ""
    updated_at: str = ""

def get_widget_data():
    return load_json("widget_sites.json")

def save_widget_data(data):
    save_json("widget_sites.json", data)

def init_widget_data():
    """Initialize widget data structure if not exists."""
    data = get_widget_data()
    if "sites" not in data:
        data = {"sites": []}
        save_widget_data(data)
    return data

@router.get("/sites")
def list_sites():
    """List all registered widget sites."""
    data = init_widget_data()
    return {"sites": data.get("sites", [])}

@router.post("/sites")
def create_site(config: WidgetConfig):
    """Register a new website for widget embedding."""
    data = init_widget_data()
    
    # Check if site already exists
    for site in data.get("sites", []):
        if site["site_url"] == config.site_url:
            raise HTTPException(status_code=400, detail="该网站已注册")
    
    now = datetime.now().isoformat()
    site = {
        "id": str(uuid.uuid4()),
        "site_name": config.site_name,
        "site_url": config.site_url,
        "api_key": str(uuid.uuid4()),  # Generate unique API key
        "primary_color": config.primary_color,
        "secondary_color": config.secondary_color,
        "bot_name": config.bot_name,
        "welcome_message": config.welcome_message,
        "input_placeholder": config.input_placeholder,
        "enabled": config.enabled,
        "created_at": now,
        "updated_at": now
    }
    
    data["sites"].append(site)
    save_widget_data(data)
    
    return {"site": site}

@router.put("/sites/{site_id}")
def update_site(site_id: str, config: WidgetConfig):
    """Update a widget site configuration."""
    data = init_widget_data()
    
    for site in data.get("sites", []):
        if site["id"] == site_id:
            site.update({
                "site_name": config.site_name,
                "site_url": config.site_url,
                "primary_color": config.primary_color,
                "secondary_color": config.secondary_color,
                "bot_name": config.bot_name,
                "welcome_message": config.welcome_message,
                "input_placeholder": config.input_placeholder,
                "enabled": config.enabled,
                "updated_at": datetime.now().isoformat()
            })
            save_widget_data(data)
            return {"site": site}
    
    raise HTTPException(status_code=404, detail="网站不存在")

@router.delete("/sites/{site_id}")
def delete_site(site_id: str):
    """Delete a widget site."""
    data = init_widget_data()
    
    sites = data.get("sites", [])
    for i, site in enumerate(sites):
        if site["id"] == site_id:
            sites.pop(i)
            data["sites"] = sites
            save_widget_data(data)
            return {"success": True}
    
    raise HTTPException(status_code=404, detail="网站不存在")

@router.post("/sites/{site_id}/regenerate-key")
def regenerate_api_key(site_id: str):
    """Regenerate API key for a widget site."""
    data = init_widget_data()
    
    for site in data.get("sites", []):
        if site["id"] == site_id:
            site["api_key"] = str(uuid.uuid4())
            site["updated_at"] = datetime.now().isoformat()
            save_widget_data(data)
            return {"api_key": site["api_key"]}
    
    raise HTTPException(status_code=404, detail="网站不存在")

@router.get("/config")
def get_widget_config_by_domain(domain: str):
    """Get widget config by domain name. Used by embedded widget."""
    data = init_widget_data()
    
    # Extract domain from full URL if needed
    if "://" in domain:
        from urllib.parse import urlparse
        domain = urlparse(domain).netloc
    
    for site in data.get("sites", []):
        if site["enabled"]:
            # Check if site_url contains the domain
            site_domain = site["site_url"]
            if "://" in site_domain:
                from urllib.parse import urlparse
                site_domain = urlparse(site_domain).netloc
            
            if domain == site_domain or domain.endswith("." + site_domain):
                # Return public config (no API key)
                return {
                    "primaryColor": site["primary_color"],
                    "secondaryColor": site["secondary_color"],
                    "botName": site["bot_name"],
                    "welcomeMessage": site["welcome_message"],
                    "inputPlaceholder": site["input_placeholder"]
                }
    
    raise HTTPException(status_code=404, detail="网站未注册或已禁用")