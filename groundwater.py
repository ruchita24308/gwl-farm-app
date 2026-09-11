from fastapi import APIRouter
from ..schemas import GroundwaterInfo
from ..groundwater_model import get_groundwater_status

router = APIRouter(prefix="/api/groundwater", tags=["groundwater"])


@router.get("/{state}/{district}", response_model=GroundwaterInfo)
def read_groundwater(state: str, district: str):
    data = get_groundwater_status(state, district)
    return GroundwaterInfo(
        state=state,
        district=district,
        matched_district=data["matched_district"] or "Not Found",
        status=data["status"],
        current_level_mbgl=data["current_level_mbgl"],
        slope_mbgl_per_year=data["slope_mbgl_per_year"],
        history=data["history"],
        insufficient_data=data["insufficient_data"],
    )