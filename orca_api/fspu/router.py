from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class PlanRequest(BaseModel):
    task_description: str
    requirements: Optional[List[str]] = []

@router.post("/fspu/plan")
async def create_plan(req: PlanRequest):
    # Logic: Select provider with 'reason_codes'
    # Mock selection
    selected_provider = "local-stub"
    reason = "lowest_latency"
    
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
