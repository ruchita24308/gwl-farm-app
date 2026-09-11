"""Core scoring/ranking engine. All numbers trace back to a real dataset
value or a documented, disclosed conversion rule - nothing here is random."""
from typing import Dict, List, Tuple

import pandas as pd

from .data_loader import get_crop_rec, get_npk
from .location_matcher import match_district
from .water_demand import get_water_demand

SUITABILITY_WEIGHT = 1 / 6  # N, P, K, temperature, humidity, rainfall - equal weight
GOOD_SIM_THRESHOLD = 0.66

# groundwater status + crop water demand -> (score penalty points 0-100 scale, risk label)
_GW_ADJUSTMENT = {
    ("Depleting", "High"): (35, "High"),
    ("Depleting", "Moderate"): (15, "Moderate"),
    ("Depleting", "Low"): (-5, "Low"),
    ("Stable", "High"): (20, "Moderate"),
    ("Stable", "Moderate"): (10, "Low"),
    ("Stable", "Low"): (0, "Low"),
    ("Improving", "High"): (8, "Moderate"),
    ("Improving", "Moderate"): (3, "Low"),
    ("Improving", "Low"): (0, "Low"),
    # Treat unknown/insufficient groundwater status conservatively, like "Stable"
    ("Insufficient Data", "High"): (20, "Moderate"),
    ("Insufficient Data", "Moderate"): (10, "Low"),
    ("Insufficient Data", "Low"): (0, "Low"),
}


def bin_temperature(temp_c: float) -> int:
    if temp_c < 20:
        return 1
    if temp_c <= 30:
        return 2
    return 3


def bin_humidity(humidity_pct: float) -> int:
    if humidity_pct < 40:
        return 1
    if humidity_pct <= 70:
        return 2
    return 3


def bin_rainfall(rainfall_mm_per_day: float) -> int:
    if rainfall_mm_per_day < 2.5:
        return 1
    if rainfall_mm_per_day <= 7.5:
        return 2
    return 3


def _similarity(actual: float, crop_score: float) -> float:
    """1.0 = perfect match, falls off linearly, floors at 0."""
    return max(0.0, 1.0 - abs(actual - crop_score) / 2.0)


def get_npk_for_location(state: str, district: str) -> Dict:
    npk = get_npk()
    state_df = npk[npk["State"].str.upper() == state.strip().upper()]
    candidates = state_df["District"].tolist()
    matched = match_district(district, candidates)

    if matched is not None:
        row = state_df[state_df["District"] == matched].iloc[0]
        return {
            "matched_district": matched,
            "n": float(row["N"]),
            "p": float(row["P"]),
            "k": float(row["K"]),
            "is_state_average": False,
        }

    # Fallback: district has no NPK record -> use state average (documented)
    if len(state_df) == 0:
        # No state data at all - use a neutral mid-scale value (2.0) and flag it
        return {"matched_district": None, "n": 2.0, "p": 2.0, "k": 2.0, "is_state_average": True}

    return {
        "matched_district": None,
        "n": float(state_df["N"].mean()),
        "p": float(state_df["P"].mean()),
        "k": float(state_df["K"].mean()),
        "is_state_average": True,
    }


def generate_recommendations(
    npk_values: Dict,
    temperature_c: float,
    humidity_pct: float,
    rainfall_mm_per_day: float,
    gw_status: str,
) -> List[Dict]:
    crop_df = get_crop_rec()

    temp_tier = bin_temperature(temperature_c)
    humidity_tier = bin_humidity(humidity_pct)
    rainfall_tier = bin_rainfall(rainfall_mm_per_day)

    results = []
    for _, row in crop_df.iterrows():
        n_sim = _similarity(npk_values["n"], row["n_score"])
        p_sim = _similarity(npk_values["p"], row["p_score"])
        k_sim = _similarity(npk_values["k"], row["k_score"])
        t_sim = _similarity(temp_tier, row["temperature_score"])
        h_sim = _similarity(humidity_tier, row["humidity_score"])
        r_sim = _similarity(rainfall_tier, row["rainfall_score"])

        suitability = (
            (n_sim + p_sim + k_sim + t_sim + h_sim + r_sim) * SUITABILITY_WEIGHT
        ) * 100

        water_demand, is_estimated = get_water_demand(row["crop"])
        penalty, risk_label = _GW_ADJUSTMENT[(gw_status, water_demand)]
        final_score = max(0.0, min(100.0, suitability - penalty))

        reason_codes = []
        if n_sim >= GOOD_SIM_THRESHOLD:
            reason_codes.append("N_GOOD")
        if p_sim >= GOOD_SIM_THRESHOLD:
            reason_codes.append("P_GOOD")
        if k_sim >= GOOD_SIM_THRESHOLD:
            reason_codes.append("K_GOOD")
        if t_sim >= GOOD_SIM_THRESHOLD:
            reason_codes.append("TEMP_GOOD")
        if h_sim >= GOOD_SIM_THRESHOLD:
            reason_codes.append("HUMIDITY_GOOD")
        if r_sim >= GOOD_SIM_THRESHOLD:
            reason_codes.append("RAINFALL_GOOD")
        if water_demand == "Low":
            reason_codes.append("LOW_WATER_ADVANTAGE")
        if water_demand == "High":
            reason_codes.append("HIGH_WATER_CAUTION")
        if gw_status == "Depleting":
            reason_codes.append("GW_DEPLETING_CAUTION")
        elif gw_status == "Improving":
            reason_codes.append("GW_IMPROVING_ADVANTAGE")

        results.append(
            {
                "crop": row["crop"],
                "suitability_score": round(suitability, 1),
                "dataset_baseline_score": round(float(row["overall_weighted_score"]) / 3 * 100, 1),
                "water_demand": water_demand,
                "water_demand_is_estimated": is_estimated,
                "groundwater_risk": risk_label,
                "final_score": round(final_score, 1),
                "reason_codes": reason_codes,
            }
        )

    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results[:5]