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

from orca_api.llm_gateway import router as gateway_router
app.include_router(gateway_router.router, prefix="/api", tags=["providers"])

@app.get("/")
async def root():
    return {"message": "ORCA API Root"}
