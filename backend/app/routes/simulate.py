from fastapi import APIRouter
from pydantic import BaseModel
from app.services.engine import recommend_next_action, simulate_futures

router = APIRouter()

class Request(BaseModel):
    profile: str
    decision: str
    context: dict = {}


class NextActionRequest(BaseModel):
    profile: str
    context: dict

@router.post("/simulate")
def simulate(req: Request):
    return simulate_futures(req.decision, req.profile, req.context)


@router.post("/next-action")
def next_action(req: NextActionRequest):
    return recommend_next_action(req.profile, req.context)
