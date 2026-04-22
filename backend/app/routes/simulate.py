from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Request(BaseModel):
    profile: str
    decision: str

@router.post("/simulate")
def simulate(req: Request):
    return {
        "result": f"Simulated futures for: {req.decision} based on {req.profile}"
    }
