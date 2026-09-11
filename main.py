from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .data_loader import load_all
from .routers import location, npk, groundwater, recommend, summary

app = FastAPI(title="Bhumisutra API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    load_all()  # load CSVs once, fail fast if datasets are missing/malformed


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(location.router)
app.include_router(npk.router)
app.include_router(groundwater.router)
app.include_router(recommend.router)
app.include_router(summary.router)