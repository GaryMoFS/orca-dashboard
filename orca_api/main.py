from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ORCA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8001",
        "http://127.0.0.1:8001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from orca_api.events import router as events_router
app.include_router(events_router.router, prefix="/api", tags=["events"])

from orca_api.fstack import router as fstack_router
app.include_router(fstack_router.router, prefix="/api", tags=["fstack"])

from orca_api.llm_gateway import router as gateway_router
app.include_router(gateway_router.router, prefix="/api", tags=["providers"])

from orca_api.llm import router as llm_router
app.include_router(llm_router.router, prefix="/api", tags=["llm"])

from fastapi.staticfiles import StaticFiles

from orca_api.system import router as system_router
app.include_router(system_router.router, prefix="/api/system", tags=["system"])

from orca_api.files import router as files_router
app.include_router(files_router.router, prefix="/api/files", tags=["files"])

from orca_api.tts import router as tts_router
app.include_router(tts_router.router, prefix="/api/tts", tags=["tts"])

# Mount runs directory for static access (e.g. audio files)
import os
os.makedirs("runs", exist_ok=True)
app.mount("/runs", StaticFiles(directory="runs"), name="runs")

@app.get("/api/health")
async def health_check():
    return {"ok": True}

@app.get("/")
async def root():
    return {"message": "ORCA API Root"}
