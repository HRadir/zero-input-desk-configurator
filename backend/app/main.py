import json
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.constraints.engine import validate_config
from app.constraints.models import DeskConfig

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

app = FastAPI(title="Zero Input API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_json(filename: str) -> dict:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/catalogue")
def get_catalogue():
    return load_json("catalogue.json")


@app.post("/config/validate")
def validate(payload: DeskConfig):
    catalogue = load_json("catalogue.json")
    contraintes = load_json("contraintes.json")
    result = validate_config(payload.model_dump(), catalogue, contraintes)
    return asdict(result)
