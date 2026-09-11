"""Genuine trend analysis on the real GWL_Cleaned.csv observations.

Rule (per spec): GWL_mbgl = metres BELOW ground level, so an INCREASING
value over time means the water table is getting deeper -> Depleting.
A DECREASING value means the water table is rising -> Improving.

Only 2021-2023 exist in the uploaded data. 2024 and 2025 are explicitly
reported as unavailable - never predicted or guessed.
"""
import numpy as np
import pandas as pd
from typing import Dict

from .data_loader import get_gwl
from .location_matcher import match_district

DEPLETE_THRESHOLD = 0.10   # mbgl/year increase to call it "Depleting"
IMPROVE_THRESHOLD = -0.10  # mbgl/year decrease to call it "Improving"
KNOWN_YEARS = [2021, 2022, 2023]
FUTURE_YEARS = [2024, 2025]


def get_groundwater_status(state: str, district: str) -> Dict:
    gwl = get_gwl()
    state_df = gwl[gwl["State"].str.upper() == state.strip().upper()]
    candidates = sorted(state_df["District"].unique().tolist())
    matched = match_district(district, candidates)

    if matched is None:
        return {
            "matched_district": None,
            "status": "Insufficient Data",
            "current_level_mbgl": None,
            "slope_mbgl_per_year": None,
            "history": [
                {"year": y, "value": None, "available": False} for y in KNOWN_YEARS
            ]
            + [{"year": y, "value": None, "available": False} for y in FUTURE_YEARS],
            "insufficient_data": True,
        }

    district_df = state_df[state_df["District"] == matched]

    # Duplicate observations within a year are aggregated by mean - this is
    # the documented aggregation method required by the spec.
    yearly = (
        district_df[district_df["Year"].isin(KNOWN_YEARS)]
        .groupby("Year")["GWL_mbgl"]
        .mean()
        .to_dict()
    )

    history = []
    for y in KNOWN_YEARS:
        val = yearly.get(y)
        history.append(
            {"year": y, "value": round(float(val), 2) if val is not None else None,
             "available": val is not None}
        )
    for y in FUTURE_YEARS:
        history.append({"year": y, "value": None, "available": False})

    known_points = [(y, v["value"]) for y, v in zip(KNOWN_YEARS, [h for h in history[:3]])]
    known_points = [(y, v) for y, v in [(h["year"], h["value"]) for h in history[:3]] if v is not None]

    if len(known_points) < 2:
        status = "Insufficient Data"
        slope = None
        insufficient = True
        current_level = known_points[0][1] if known_points else None
    else:
        years = np.array([p[0] for p in known_points], dtype=float)
        values = np.array([p[1] for p in known_points], dtype=float)
        slope = float(np.polyfit(years, values, 1)[0])
        if slope > DEPLETE_THRESHOLD:
            status = "Depleting"
        elif slope < IMPROVE_THRESHOLD:
            status = "Improving"
        else:
            status = "Stable"
        insufficient = False
        current_level = known_points[-1][1]  # most recent available year

    return {
        "matched_district": matched,
        "status": status,
        "current_level_mbgl": round(current_level, 2) if current_level is not None else None,
        "slope_mbgl_per_year": round(slope, 3) if slope is not None else None,
        "history": history,
        "insufficient_data": insufficient,
    }