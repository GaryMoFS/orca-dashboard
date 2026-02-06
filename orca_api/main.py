from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ORCA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from orca_api.fspu import router as fspu_router
app.include_router(fspu_router.router, prefix="/api", tags=["fspu"])

@app.get("/")
async def root():
    return {"message": "ORCA API Root"}
