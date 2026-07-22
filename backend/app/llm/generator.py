import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.constraints.engine import ValidationResult, validate_config
from app.constraints.models import DeskConfig
from app.llm.prompts import build_system_prompt
from app.rag.retriever import retrieve_relevant_options

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR.parent / "data"
LOGS_DIR = BACKEND_DIR / "logs"
CHAT_MODEL = "gpt-4o"
MAX_ATTEMPTS = 3

load_dotenv(BACKEND_DIR / ".env")


def _load_catalogue() -> dict:
    with open(DATA_DIR / "catalogue.json", encoding="utf-8") as f:
        return json.load(f)


def _load_contraintes() -> dict:
    with open(DATA_DIR / "contraintes.json", encoding="utf-8") as f:
        return json.load(f)


def _invoke_llm(
    system_prompt: str,
    history: list[dict],
    current_config: Optional[dict],
    message: str,
    correction_note: Optional[str] = None,
) -> DeskConfig:
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    structured_llm = llm.with_structured_output(DeskConfig)

    messages: list[tuple[str, str]] = [("system", system_prompt)]
    for turn in history:
        messages.append((turn["role"], turn["content"]))
    if current_config:
        messages.append(("user", f"Configuration actuelle : {json.dumps(current_config, ensure_ascii=False)}"))
    messages.append(("user", message))
    if correction_note:
        messages.append(("user", correction_note))

    return structured_llm.invoke(messages)


def _log_attempt(entry: dict) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOGS_DIR / "generation_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def generate_valid_config(
    message: str,
    history: Optional[list[dict]] = None,
    current_config: Optional[dict] = None,
    max_attempts: int = MAX_ATTEMPTS,
) -> tuple[DeskConfig, ValidationResult, int]:
    """Génère une config via le LLM puis la fait valider par le moteur de contraintes.
    En cas d'erreurs, réinjecte les erreurs au LLM pour correction (jusqu'à max_attempts).
    """
    catalogue = _load_catalogue()
    contraintes = _load_contraintes()
    rag_results = retrieve_relevant_options(message, k=6)
    system_prompt = build_system_prompt(catalogue, rag_results)

    correction_note: Optional[str] = None
    config: Optional[DeskConfig] = None
    result: Optional[ValidationResult] = None
    attempt = 0

    for attempt in range(1, max_attempts + 1):
        config = _invoke_llm(system_prompt, history or [], current_config, message, correction_note)
        result = validate_config(config.model_dump(), catalogue, contraintes)

        _log_attempt(
            {
                "message": message,
                "attempt": attempt,
                "config": config.model_dump(),
                "valid": result.valid,
                "errors": [asdict(e) for e in result.errors],
                "warnings": [asdict(w) for w in result.warnings],
            }
        )

        if result.valid:
            break

        errors_text = "\n".join(f"- {e.message}" for e in result.errors)
        correction_note = (
            "La configuration générée précédemment ne respecte pas ces règles de compatibilité :\n"
            f"{errors_text}\n"
            "Corrige uniquement les champs en conflit pour respecter ces règles, "
            "en conservant les autres choix déjà faits."
        )

    return config, result, attempt


if __name__ == "__main__":
    import sys

    msg = " ".join(sys.argv[1:]) or (
        "Je veux un bureau motorisé style scandinave, plateau bois clair, "
        "structure blanche, pour deux écrans"
    )
    config, result, attempts = generate_valid_config(msg)
    print(f"Tentatives : {attempts}")
    print(f"Valide : {result.valid}")
    if result.errors:
        print("Erreurs restantes :", [e.message for e in result.errors])
    print(config.model_dump_json(indent=2))
