"""Pydantic request/response models shared across routers."""
from typing import List, Optional
from pydantic import BaseModel, Field


class LocationRequest(BaseModel):
    state: str
    district: str
    area: Optional[str] = None


class NPKInfo(BaseModel):
    state: str
    district: str
    matched_district: str
    n: float
    p: float
    k: float
    is_state_average: bool = Field(
        description="True if exact district had no NPK record and a state-level average was used"
    )


class YearValue(BaseModel):
    year: int
    value: Optional[float]  # None when unavailable
    available: bool


class GroundwaterInfo(BaseModel):
    state: str
    district: str
    matched_district: str
    status: str  # "Depleting" | "Stable" | "Improving" | "Insufficient Data"
    current_level_mbgl: Optional[float]
    slope_mbgl_per_year: Optional[float]
    history: List[YearValue]
    insufficient_data: bool = False


class WeatherInput(BaseModel):
    temperature_c: float
    humidity_pct: float
    rainfall_mm_per_day: float


class RecommendRequest(BaseModel):
    state: str
    district: str
    weather: WeatherInput


class CropRecommendation(BaseModel):
    crop: str
    suitability_score: float          # 0-100, location-specific
    dataset_baseline_score: float     # 0-100, generic crop archetype score from crop_rec.csv
    water_demand: str                 # Low / Moderate / High
    water_demand_is_estimated: bool
    groundwater_risk: str             # Low / Moderate / High
    final_score: float                # 0-100, ranking score after GW adjustment
    reason_codes: List[str]


class RecommendResponse(BaseModel):
    location: LocationRequest
    npk: NPKInfo
    groundwater: GroundwaterInfo
    weather: WeatherInput
    recommendations: List[CropRecommendation]


class SummaryRequest(BaseModel):
    farmer_or_group_name: Optional[str] = None
    recommend: RecommendResponse