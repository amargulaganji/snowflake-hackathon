from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import members, agent, documents, studio, admin

app = FastAPI(title="Clinical Copilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(members.router)
app.include_router(agent.router)
app.include_router(documents.router)
app.include_router(studio.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
