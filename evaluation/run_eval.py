"""Harnais d'exécution RQ3.

Exécute le jeu de test data/jeu_de_test_evaluation.json contre le pipeline réel
(app.llm.generator.generate_valid_config), en appel Python direct — pas via l'API
HTTP (cf. protocole : c'est la logique du pipeline qui est évaluée, pas la couche API).

Ne calcule aucune métrique : logue uniquement les résultats bruts dans
evaluation/eval_log.jsonl pour validation manuelle avant analyse.
"""

import json
import sys
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.llm import generator as generator_module  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent
TESTSET_PATH = ROOT_DIR / "data" / "jeu_de_test_evaluation.json"
LOG_PATH = EVAL_DIR / "eval_log.jsonl"


@contextmanager
def _capture_pipeline():
    """Intercepte retrieve_relevant_options, _invoke_llm et validate_config tels
    qu'importés/définis dans generator.py, pour observer chaque tentative de la
    boucle interne de generate_valid_config() sans réimplémenter cette boucle.

    generate_valid_config() appelle _invoke_llm() puis validate_config() une fois
    par itération, toujours dans cet ordre, avant de décider de continuer ou de
    s'arrêter (cf. generator.py:83-108) — donc le N-ième appel intercepté de
    chaque correspond exactement à la N-ième tentative.
    """
    captured = {"rag_results": [], "invocations": [], "validations": []}

    original_retrieve = generator_module.retrieve_relevant_options
    original_invoke = generator_module._invoke_llm
    original_validate = generator_module.validate_config

    def retrieve_wrapper(query, k=5):
        results = original_retrieve(query, k=k)
        captured["rag_results"] = results
        return results

    def invoke_wrapper(system_prompt, history, current_config, message, correction_note=None):
        generation = original_invoke(system_prompt, history, current_config, message, correction_note)
        captured["invocations"].append({"correction_note_recue": correction_note, "generation": generation})
        return generation

    def validate_wrapper(config, catalogue, contraintes):
        result = original_validate(config, catalogue, contraintes)
        captured["validations"].append(result)
        return result

    generator_module.retrieve_relevant_options = retrieve_wrapper
    generator_module._invoke_llm = invoke_wrapper
    generator_module.validate_config = validate_wrapper
    try:
        yield captured
    finally:
        generator_module.retrieve_relevant_options = original_retrieve
        generator_module._invoke_llm = original_invoke
        generator_module.validate_config = original_validate


def run_single(message: str, history=None, current_config=None) -> dict:
    with _capture_pipeline() as captured:
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
        for i, (inv, val) in enumerate(zip(captured["invocations"], captured["validations"]), start=1)
    ]

    return {
        "message": message,
        "rag_results": captured["rag_results"],
        "tentatives": tentatives,
        "config": config.model_dump(),
        "llm_message": llm_message,
        "validation": asdict(result),
        "attempts": attempts,
    }


def _append_log(entry: dict) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_mono_tour(requetes: list[dict]) -> None:
    for req in requetes:
        print(f"[mono-tour] #{req['id']} : {req['requete']}")
        result = run_single(req["requete"])
        _append_log({"id": req["id"], "type": "mono_tour", "categorie": req["categorie"], **result})
        print(f"    -> valide={result['validation']['valid']} tentatives={result['attempts']}")


def run_multi_tours(scenario: dict) -> None:
    history: list[dict] = []
    current_config = None
    for tour in scenario["tours"]:
        print(f"[multi-tours] #{tour['id']} : {tour['message']}")
        result = run_single(tour["message"], history=history, current_config=current_config)
        _append_log({"id": tour["id"], "type": "multi_tours", **result})
        print(f"    -> valide={result['validation']['valid']} tentatives={result['attempts']}")

        history.append({"role": "user", "content": tour["message"]})
        history.append({"role": "assistant", "content": result["llm_message"]})
        current_config = result["config"]


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()  # une seule passe : fichier repartant de zéro à chaque exécution

    with open(TESTSET_PATH, encoding="utf-8") as f:
        testset = json.load(f)

    run_mono_tour(testset["requetes_mono_tour"])
    run_multi_tours(testset["scenario_multi_tours"])

    print(f"\nTerminé : {LOG_PATH}")


if __name__ == "__main__":
    main()
