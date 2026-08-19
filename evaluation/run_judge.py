"""Harnais de jugement RQ3 — axe 3 (alignement besoin/configuration).

Juge chaque entree de eval_log.jsonl avec Claude Sonnet 5 (modele different
de GPT-4o, qui genere les configurations), via un appel a tool use force
(schema JSON strict, pas de texte libre a parser). Logue dans
evaluation/judge_log.jsonl, sans modifier eval_log.jsonl.

Ne calcule aucune moyenne : logue uniquement les jugements bruts par entree
pour validation manuelle avant analyse.
"""

import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
EVAL_DIR = Path(__file__).resolve().parent
EVAL_LOG_PATH = EVAL_DIR / "eval_log.jsonl"
JUDGE_LOG_PATH = EVAL_DIR / "judge_log.jsonl"

load_dotenv(ROOT_DIR / "backend" / ".env")

JUDGE_MODEL = "claude-sonnet-5"

CATALOGUE_CATEGORIES = ["finitions", "plateaux", "structures", "accessoires", "styles"]

JUDGE_TOOL = {
    "name": "submit_judgment",
    "description": (
        "Soumets l'evaluation de l'alignement entre la demande du client et la "
        "configuration de bureau generee en reponse."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "couverture": {
                "type": "integer",
                "enum": [0, 1, 2],
                "description": (
                    "0 = aucun attribut explicitement demande par le client n'est "
                    "reflete dans la configuration finale. 1 = certains attributs "
                    "demandes sont refletes mais pas tous. 2 = tous les attributs "
                    "explicitement demandes par le client sont refletes dans la "
                    "configuration finale."
                ),
            },
            "couverture_justification": {
                "type": "string",
                "description": "Justification en une phrase, courte.",
            },
            "absence_invention": {
                "type": "integer",
                "enum": [0, 1, 2],
                "description": (
                    "0 = la configuration ajoute quelque chose que le client n'a pas "
                    "demande et qui contredit son intention. 1 = un ou plusieurs "
                    "ajouts discutables, sans contredire clairement l'intention. "
                    "2 = aucun ajout ne contredit l'intention du client. Les ajouts "
                    "necessaires a la validite de la configuration (comme un bras "
                    "ecran ajoute pour correspondre au nombre d'ecrans) ne comptent "
                    "PAS comme une invention a penaliser."
                ),
            },
            "absence_invention_justification": {
                "type": "string",
                "description": "Justification en une phrase, courte.",
            },
            "transparence": {
                "type": "integer",
                "enum": [0, 1, 2],
                "description": (
                    "0 = une partie de la demande du client n'a aucun equivalent "
                    "dans les categories du catalogue fournies, et le message ne le "
                    "signale pas du tout. 1 = signale mais de facon peu claire ou "
                    "incomplete. 2 = soit clairement signale dans le message, soit "
                    "sans objet parce que toute la demande avait un equivalent "
                    "plausible dans le catalogue."
                ),
            },
            "transparence_justification": {
                "type": "string",
                "description": "Justification en une phrase, courte.",
            },
        },
        "required": [
            "couverture",
            "couverture_justification",
            "absence_invention",
            "absence_invention_justification",
            "transparence",
            "transparence_justification",
        ],
        "additionalProperties": False,
    },
}

JUDGE_SYSTEM_PROMPT = """Tu es un juge independant qui evalue, apres coup, si une configuration de bureau assis/debout generee par un autre systeme (GPT-4o) reflete fidelement la demande d'un client exprimee en langage naturel.

Tu ne connais PAS le catalogue complet des produits disponibles : seulement la liste des categories qui existent ({categories}). Utilise cette liste uniquement pour juger si une partie de la demande du client etait plausiblement hors catalogue (par exemple si le client demande un materiau, une decoration ou un accessoire qui ne correspond a aucune de ces categories).

Tu recois pour chaque cas : la requete du client, la configuration finale generee (derniere tentative, apres correction eventuelle), et le message en langage naturel renvoye au client. Evalue trois dimensions independantes en appelant l'outil submit_judgment. Sois strict et honnete : une note de 2 doit correspondre a un alignement reellement complet, pas approximatif."""


def _load_eval_entries() -> list[dict]:
    entries = []
    with open(EVAL_LOG_PATH, encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line))
    return entries


def _build_user_message(entry: dict) -> str:
    return (
        f"Requete du client :\n{entry['message']}\n\n"
        f"Configuration finale generee :\n{json.dumps(entry['config'], ensure_ascii=False, indent=2)}\n\n"
        f"Message renvoye au client :\n{entry['llm_message']}"
    )


def judge_entry(client: anthropic.Anthropic, entry: dict) -> dict:
    system_prompt = JUDGE_SYSTEM_PROMPT.format(categories=", ".join(CATALOGUE_CATEGORIES))
    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=1024,
        system=system_prompt,
        tools=[JUDGE_TOOL],
        tool_choice={"type": "tool", "name": "submit_judgment"},
        messages=[{"role": "user", "content": _build_user_message(entry)}],
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    return tool_use.input


def _append_log(entry: dict) -> None:
    with open(JUDGE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    if JUDGE_LOG_PATH.exists():
        JUDGE_LOG_PATH.unlink()

    client = anthropic.Anthropic()
    entries = _load_eval_entries()

    for entry in entries:
        print(f"[juge] #{entry['id']} ({entry['type']}) : {entry['message']}")
        judgment = judge_entry(client, entry)
        _append_log(
            {
                "id": entry["id"],
                "type": entry["type"],
                "message": entry["message"],
                "config": entry["config"],
                "llm_message": entry["llm_message"],
                "judgment": judgment,
                "judge_model": JUDGE_MODEL,
            }
        )
        print(
            f"    -> couverture={judgment['couverture']} "
            f"absence_invention={judgment['absence_invention']} "
            f"transparence={judgment['transparence']}"
        )

    print(f"\nTermine : {JUDGE_LOG_PATH}")


if __name__ == "__main__":
    main()
