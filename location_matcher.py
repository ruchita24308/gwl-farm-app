"""Fuzzy-matches a GPS/reverse-geocoded district name against the district
spellings actually present in each dataset (they differ between files,
e.g. 'Hanumakonda' vs 'HANAMKONDA')."""
import difflib
import re
from typing import List, Optional


def normalize(name: str) -> str:
    name = name.upper().strip()
    name = re.sub(r"[^A-Z ]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def match_district(query: str, candidates: List[str]) -> Optional[str]:
    """Returns the best-matching candidate district name, or None if nothing
    is close enough. Tries exact match, then substring containment, then
    fuzzy string similarity, in that order of confidence."""
    if not query or not candidates:
        return None

    q_norm = normalize(query)
    norm_map = {normalize(c): c for c in candidates}

    # 1. exact normalized match
    if q_norm in norm_map:
        return norm_map[q_norm]

    # 2. substring containment either direction (handles
    #    "Bhadradri Kothagudem" <-> "BHADRADRI")
    for norm_c, original in norm_map.items():
        if q_norm in norm_c or norm_c in q_norm:
            return original

    # 3. fuzzy match (handles "Jagitial" <-> "JAGITYAL")
    close = difflib.get_close_matches(q_norm, list(norm_map.keys()), n=1, cutoff=0.6)
    if close:
        return norm_map[close[0]]

    return None