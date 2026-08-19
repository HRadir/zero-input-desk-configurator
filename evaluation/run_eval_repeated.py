"""Harnais de repetition RQ3 - axe 2 (validite), 15 repetitions par requete.

Repete l'execution du pipeline reel (generate_valid_config) 15 fois par
requete du jeu de test, pour mesurer un taux de succes plutot qu'un resultat
unique par requete. Reprend le protocole de run_eval.py (appel Python
direct, pas d'API HTTP), mais ne capture pas le retrieval : il est
deterministe (embedding -> ChromaDB) et deja mesure une fois dans
eval_log.jsonl, donc hors perimetre de cette repetition.

Ne calcule aucune metrique : logue uniquement les resultats bruts dans
evaluation/eval_log_repeated.jsonl pour validation manuelle avant analyse.
Fichiers existants (eval_log.jsonl, judge_log.jsonl) non modifies.
"""

import json
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

import openai

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.llm import generator as generator_module  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent
TESTSET_PATH = ROOT_DIR / "data" / "jeu_de_test_evaluation.json"
LOG_PATH = EVAL_DIR / "eval_log_repeated.jsonl"

N_REPETITIONS = 15
MAX_RATE_LIMIT_RETRIES = 8
RATE_LIMIT_BASE_DELAY_S = 5.0


@contextmanager
def _capture_attempts():
    """Intercepte _invoke_llm et validate_config (tels qu'importes dans
    generator.py) pour reconstruire le detail de chaque tentative, sans
    dupliquer la boucle reelle de generate_valid_config(). Ne capture PAS
    retrieve_relevant_options ici (cf. docstring du module).
    """
    invocations = []
    validations = []

    original_invoke = generator_module._invoke_llm
    original_validate = generator_module.validate_config

    def invoke_wrapper(system_prompt, history, current_config, message, correction_note=None):
        generation = original_invoke(system_prompt, history, current_config, message, correction_note)
        invocations.append({"correction_note_recue": correction_note, "generation": generation})
        return generation

    def validate_wrapper(config, catalogue, contraintes):
        result = original_validate(config, catalogue, contraintes)
        validations.append(result)
        return result

    generator_module._invoke_llm = invoke_wrapper
    generator_module.validate_config = validate_wrapper
    try:
        yield invocations, validations
    finally:
        generator_module._invoke_llm = original_invoke
        generator_module.validate_config = original_validate


def run_single(message: str, history=None, current_config=None) -> dict:
    with _capture_attempts() as (invocations, validations):
        config, llm_message, result, attempts = generator_module.generate_valid_config(
            message, history=history, current_config=current_config
        )

    tentatives = [
        {
            "tentative": i,
            "correction_note_recue": inv["correction_note_recue"],
            "config": inv["generation"].config.model_dump(),
            "llm_message": inv["generation"].message,
            "validation": asdict(val),
        }
        for i, (inv, val) in enumerate(zip(invocations, validations), start=1)
    ]

    return {
        "tentatives": tentatives,
        "config": config.model_dump(),
        "llm_message": llm_message,
        "validation": asdict(result),
        "attempts": attempts,
    }


def run_single_with_retry(message: str, history=None, current_config=None) -> dict:
    """run_single() avec retry/backoff sur les erreurs de rate limit OpenAI
    (429, plafond de tokens/minute) — attendues sur un volume de 240
    executions sequentielles, pas une anomalie a laisser planter le run."""
    delay = RATE_LIMIT_BASE_DELAY_S
    for attempt in range(1, MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return run_single(message, history=history, current_config=current_config)
        except openai.RateLimitError as exc:
            if attempt == MAX_RATE_LIMIT_RETRIES:
                raise
            print(f"    (rate limit, tentative {attempt}/{MAX_RATE_LIMIT_RETRIES}, pause {delay:.0f}s : {exc})")
            time.sleep(delay)
            delay *= 1.5
    raise AssertionError("unreachable")


def _append_log(entry: dict) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _load_done_ids() -> set:
    if not LOG_PATH.exists():
        return set()
    done = set()
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            done.add(json.loads(line)["id"])
    return done


def run_mono_tour_repeated(requetes: list[dict], done_ids: set) -> None:
    for req in requetes:
        if req["id"] in done_ids:
            print(f"[mono-tour] #{req['id']} deja loguee, on saute")
            continue
        print(f"[mono-tour] #{req['id']} : {req['requete']}")
        repetitions = []
        for rep in range(1, N_REPETITIONS + 1):
            result = run_single_with_retry(req["requete"])
            repetitions.append({"repetition": rep, **result})
            print(
                f"    rep {rep}/{N_REPETITIONS} -> valide={result['validation']['valid']} "
                f"tentatives={result['attempts']}"
            )
        _append_log(
            {
                "id": req["id"],
                "type": "mono_tour",
                "categorie": req["categorie"],
                "message": req["requete"],
                "repetitions": repetitions,
            }
        )


def run_multi_tours_repeated(scenario: dict, done_ids: set) -> None:
    tours = scenario["tours"]
    if all(t["id"] in done_ids for t in tours):
        print("[multi-tours] deja loguee, on saute")
        return

    entries_by_id = {
        t["id"]: {"id": t["id"], "type": "multi_tours", "message": t["message"], "repetitions": []}
        for t in tours
    }

    for rep in range(1, N_REPETITIONS + 1):
        print(f"[multi-tours] repetition {rep}/{N_REPETITIONS}")
        history: list[dict] = []
        current_config = None
        for tour in tours:
            print(f"    #{tour['id']} : {tour['message']}")
            result = run_single_with_retry(tour["message"], history=history, current_config=current_config)
            entries_by_id[tour["id"]]["repetitions"].append({"repetition": rep, **result})
            print(f"        -> valide={result['validation']['valid']} tentatives={result['attempts']}")

            history.append({"role": "user", "content": tour["message"]})
            history.append({"role": "assistant", "content": result["llm_message"]})
            current_config = result["config"]

    for tour in tours:
        _append_log(entries_by_id[tour["id"]])


def main() -> None:
    done_ids = _load_done_ids()
    if done_ids:
        print(f"Reprise : {len(done_ids)} requete(s) deja loguee(s) ({sorted(done_ids)}), non re-executees.")

    with open(TESTSET_PATH, encoding="utf-8") as f:
        testset = json.load(f)

    run_mono_tour_repeated(testset["requetes_mono_tour"], done_ids)
    run_multi_tours_repeated(testset["scenario_multi_tours"], done_ids)

    print(f"\nTermine : {LOG_PATH}")


if __name__ == "__main__":
    main()
