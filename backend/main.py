import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import models_router, skills_router, chat_router, ilink_router, widget_router
from services.ilink_bridge import start_bridge, stop_bridge, TOKEN_PATH
from services.weather import WeatherService, CITY_LIST_FILE


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    weather_service = WeatherService()
    if not CITY_LIST_FILE.exists():
        weather_service.download_city_list()

    # Auto-start ilink bridge if token exists
    if TOKEN_PATH.exists():
        try:
            await start_bridge()
            print("[startup] iLink bridge auto-started")
        except Exception as e:
            print(f"[startup] iLink bridge start failed: {e}")
    else:
        print("[startup] No ilink token found, bridge not auto-started (run QR login first)")

    yield

    # Shutdown
    try:
        await stop_bridge()
        print("[shutdown] iLink bridge stopped")
    except Exception:
        pass


app = FastAPI(title="lj_claw Agent", lifespan=lifespan, redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ilink_router)

app.include_router(models_router, prefix="/api/models", tags=["models"])
app.include_router(skills_router, prefix="/api/skills", tags=["skills"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(widget_router, prefix="/api/widget", tags=["widget"])


@app.get("/api/health")
def health():
    return {"status": "ok"}