"""Lets the mobile app check whether a GPS-detected state/district actually
resolves against our datasets, before requesting recommendations."""
from fastapi import APIRouter
from ..schemas import LocationRequest
from ..data_loader import get_npk, get_gwl
from ..location_matcher import match_district

router = APIRouter(prefix="/api/location", tags=["location"])


@router.post("/match")
def match_location(payload: LocationRequest):
    gwl = get_gwl()
    npk = get_npk()

    gwl_candidates = gwl[gwl["State"].str.upper() == payload.state.upper()]["District"].unique().tolist()
    npk_candidates = npk[npk["State"].str.upper() == payload.state.upper()]["District"].unique().tolist()

    gwl_match = match_district(payload.district, gwl_candidates)
    npk_match = match_district(payload.district, npk_candidates)

    return {
        "state": payload.state,
        "district": payload.district,
        "groundwater_data_found": gwl_match is not None,
        "matched_groundwater_district": gwl_match,
        "exact_npk_data_found": npk_match is not None,
        "matched_npk_district": npk_match,
    }