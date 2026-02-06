from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class PlanRequest(BaseModel):
    task_description: str
    requirements: Optional[List[str]] = []

@router.post("/fspu/plan")
async def create_plan(req: PlanRequest):
    # Logic: Select provider with 'reason_codes' (naive heuristic v1)
    
    # 1. Check if Ollama is available (via internal probe call or logic duplication)
    # Ideally should use a shared service, but for now we duplicate the check for isolation
    from orca_api.llm_gateway.router import check_ollama
    ollama_status = await check_ollama(timeout=0.5)
    
    selected_provider = "local-stub"
    reason = "fallback_stub"
    
    if ollama_status["active"] and ollama_status["models"]:
        selected_provider = "ollama_local"
        reason = "ollama_available"
    elif ollama_status["active"] and not ollama_status["models"]:
        selected_provider = "ollama_local"
        reason = "ollama_no_models"
    
    plan = {
        "status": "planned",
        "provider": selected_provider,
        "reason_code": reason,
        "steps": [
            {"step": 1, "action": "ingest", "target": req.task_description},
            {"step": 2, "action": "process", "details": "via fstack"}
        ]
    }
    
    # Emit event (in real app, this would push to event bus)
    print(f"EVENT: fspu.plan_selected - {plan}")
    
    return plan
