from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import models_router, skills_router, chat_router
from services.weather import WeatherService, CITY_LIST_FILE

app = FastAPI(title="lj_claw Agent", redirect_slashes=False)

# Download city list on startup if not exists
weather_service = WeatherService()
if not CITY_LIST_FILE.exists():
    weather_service.download_city_list()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models_router, prefix="/api/models", tags=["models"])
app.include_router(skills_router, prefix="/api/skills", tags=["skills"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

@app.get("/api/health")
def health():
    return {"status": "ok"}
