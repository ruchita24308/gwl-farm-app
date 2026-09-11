from fastapi import APIRouter
from ..schemas import NPKInfo
from ..recommender import get_npk_for_location

router = APIRouter(prefix="/api/npk", tags=["npk"])


@router.get("/{state}/{district}", response_model=NPKInfo)
def read_npk(state: str, district: str):
    data = get_npk_for_location(state, district)
    return NPKInfo(
        state=state,
        district=district,
        matched_district=data["matched_district"] or "State Average",
        n=round(data["n"], 2),
        p=round(data["p"], 2),
        k=round(data["k"], 2),
        is_state_average=data["is_state_average"],
    )