import json
from fastapi import APIRouter
from app.common.schemas import APIResponse

router = APIRouter(prefix="/api/disaster-types", tags=["Disaster Types"])

@router.get("", response_model=APIResponse[list])
def get_types():
    with open("data/disaster_types.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"data": data}
