import json
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.constraints.engine import validate_config
from app.constraints.models import DeskConfig
from app.llm.generator import generate_valid_config
from app.schemas.chat import ChatRequest

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

app = FastAPI(title="Zero Input API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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


@app.post("/chat/generate")
def chat_generate(payload: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in payload.history]
    try:
        config, result, attempts = generate_valid_config(
            payload.message, history=history, current_config=payload.current_config
        )
    except Exception as exc:
        # Frontière système : erreurs réseau/API OpenAI (timeout, rate limit, clé invalide...).
        # On renvoie une erreur propre plutôt qu'un 500 brut avec traceback.
        raise HTTPException(
            status_code=502,
            detail=f"Impossible de générer la configuration (appel au LLM échoué) : {exc}",
        ) from exc
    return {
        "config": config.model_dump(),
        "validation": asdict(result),
        "attempts": attempts,
    }
