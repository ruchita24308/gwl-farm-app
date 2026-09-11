"""Loads and caches the three datasets exactly once at process startup.
No synthetic values are ever generated here - only real dataset content."""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

_cache = {}


def _load_crop_rec() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "crop_rec.csv")
    df = pd.read_csv(path)
    df["crop"] = df["crop"].str.strip().str.lower()
    return df


def _load_npk() -> pd.DataFrame:
    """final_npk.csv may be a genuine CSV or (as uploaded) an .xlsx saved with
    a .csv extension. We detect the real format and parse accordingly - no
    values are fabricated either way."""
    path = os.path.join(DATA_DIR, "final_npk.csv")
    with open(path, "rb") as f:
        head = f.read(4)
    if head[:2] == b"PK":  # zip/xlsx signature
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df["State"] = df["State"].astype(str).str.strip()
    df["District"] = df["District"].astype(str).str.strip()
    for col in ("N", "P", "K"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["N", "P", "K"])


def _load_gwl() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "gwl_cleaned.csv")
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df["State"] = df["State"].astype(str).str.strip()
    df["District"] = df["District"].astype(str).str.strip()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["GWL_mbgl"] = pd.to_numeric(df["GWL_mbgl"], errors="coerce")
    return df.dropna(subset=["Year", "GWL_mbgl"])


def load_all():
    if not _cache:
        _cache["crop_rec"] = _load_crop_rec()
        _cache["npk"] = _load_npk()
        _cache["gwl"] = _load_gwl()
    return _cache


def get_crop_rec() -> pd.DataFrame:
    return load_all()["crop_rec"]


def get_npk() -> pd.DataFrame:
    return load_all()["npk"]


def get_gwl() -> pd.DataFrame:
    return load_all()["gwl"]