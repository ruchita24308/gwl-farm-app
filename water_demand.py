"""Relative crop water-demand reference table.

IMPORTANT: none of the uploaded datasets contain a water-demand field, so
this table is a small, explicitly-labeled standard agronomic reference
(commonly used categorisation of *relative* irrigation water requirement),
NOT a value derived from crop_rec.csv, and NOT a claim of exact litres.
Crops not present in this table default to 'Moderate' and are flagged as
estimated so the UI can say so honestly.
"""
from typing import Tuple

_WATER_DEMAND = {
    # Low water demand - drought tolerant pulses / hardy trees
    "chickpea": "Low",
    "lentil": "Low",
    "blackgram": "Low",
    "mothbeans": "Low",
    "mungbean": "Low",
    "pigeonpeas": "Low",
    "mango": "Low",
    "pomegranate": "Low",
    # Moderate water demand
    "cotton": "Moderate",
    "maize": "Moderate",
    "coffee": "Moderate",
    "grapes": "Moderate",
    "orange": "Moderate",
    "apple": "Moderate",
    "kidneybeans": "Moderate",
    # High water demand - wetland / heavy-irrigation crops
    "rice": "High",
    "banana": "High",
    "jute": "High",
    "coconut": "High",
    "papaya": "High",
    "watermelon": "High",
    "muskmelon": "High",
}


def get_water_demand(crop: str) -> Tuple[str, bool]:
    """Returns (category, is_estimated_default)."""
    crop = crop.strip().lower()
    if crop in _WATER_DEMAND:
        return _WATER_DEMAND[crop], False
    return "Moderate", True