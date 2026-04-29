from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import models, skills, chat

app = FastAPI(title="lj_claw Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.get("/api/health")
def health():
    return {"status": "ok"}
