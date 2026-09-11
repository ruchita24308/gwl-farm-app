from fastapi import APIRouter
from ..schemas import RecommendRequest, RecommendResponse, NPKInfo, GroundwaterInfo, CropRecommendation
from ..recommender import get_npk_for_location, generate_recommendations
from ..groundwater_model import get_groundwater_status

router = APIRouter(prefix="/api/recommend", tags=["recommend"])


@router.post("", response_model=RecommendResponse)
def recommend(payload: RecommendRequest):
    npk_data = get_npk_for_location(payload.state, payload.district)
    gw_data = get_groundwater_status(payload.state, payload.district)

    recs = generate_recommendations(
        npk_values=npk_data,
        temperature_c=payload.weather.temperature_c,
        humidity_pct=payload.weather.humidity_pct,
        rainfall_mm_per_day=payload.weather.rainfall_mm_per_day,
        gw_status=gw_data["status"],
    )

    return RecommendResponse(
        location={"state": payload.state, "district": payload.district},
        npk=NPKInfo(
            state=payload.state,
            district=payload.district,
            matched_district=npk_data["matched_district"] or "State Average",
            n=round(npk_data["n"], 2),
            p=round(npk_data["p"], 2),
            k=round(npk_data["k"], 2),
            is_state_average=npk_data["is_state_average"],
        ),
        groundwater=GroundwaterInfo(
            state=payload.state,
            district=payload.district,
            matched_district=gw_data["matched_district"] or "Not Found",
            status=gw_data["status"],
            current_level_mbgl=gw_data["current_level_mbgl"],
            slope_mbgl_per_year=gw_data["slope_mbgl_per_year"],
            history=gw_data["history"],
            insufficient_data=gw_data["insufficient_data"],
        ),
        weather=payload.weather,
        recommendations=[CropRecommendation(**r) for r in recs],
    )