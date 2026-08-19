"""Harnais de jugement repete RQ3 - axe 3, 15 repetitions par requete.

Reprend le protocole de run_judge.py (Claude Sonnet 5 comme juge, tool use
force, memes 3 dimensions : couverture, absence_invention, transparence),
mais applique aux 240 repetitions deja generees par run_eval_repeated.py
(axe 2) dans eval_log_repeated.jsonl, plutot qu'a une seule execution par
requete.

Ne calcule aucune moyenne : logue uniquement les jugements bruts dans
evaluation/judge_log_repeated.jsonl. Fichiers existants (eval_log.jsonl,
judge_log.jsonl, eval_log_repeated.jsonl) non modifies.
"""

import json
import sys
import time
from pathlib import Path

import anthropic

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR))

from run_judge import JUDGE_MODEL, judge_entry  # noqa: E402

EVAL_LOG_REPEATED_PATH = EVAL_DIR / "eval_log_repeated.jsonl"
JUDGE_LOG_REPEATED_PATH = EVAL_DIR / "judge_log_repeated.jsonl"

MAX_RATE_LIMIT_RETRIES = 8
RATE_LIMIT_BASE_DELAY_S = 5.0


def _load_eval_entries() -> list[dict]:
    entries = []
    with open(EVAL_LOG_REPEATED_PATH, encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line))
    return entries


def _judge_with_retry(client: anthropic.Anthropic, entry_for_judge: dict) -> dict:
    delay = RATE_LIMIT_BASE_DELAY_S
    for attempt in range(1, MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return judge_entry(client, entry_for_judge)
        except anthropic.RateLimitError as exc:
            if attempt == MAX_RATE_LIMIT_RETRIES:
                raise
            print(f"    (rate limit, tentative {attempt}/{MAX_RATE_LIMIT_RETRIES}, pause {delay:.0f}s : {exc})")
            time.sleep(delay)
            delay *= 1.5
    raise AssertionError("unreachable")


def _append_log(entry: dict) -> None:
    with open(JUDGE_LOG_REPEATED_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _load_done_ids() -> set:
    if not JUDGE_LOG_REPEATED_PATH.exists():
        return set()
    done = set()
    with open(JUDGE_LOG_REPEATED_PATH, encoding="utf-8") as f:
        for line in f:
            done.add(json.loads(line)["id"])
    return done


def main() -> None:
    done_ids = _load_done_ids()
    if done_ids:
        print(f"Reprise : {len(done_ids)} requete(s) deja loguee(s) ({sorted(done_ids)}), non re-executees.")

    client = anthropic.Anthropic()
    eval_entries = _load_eval_entries()

    for eval_entry in eval_entries:
        if eval_entry["id"] in done_ids:
            print(f"[juge] #{eval_entry['id']} deja loguee, on saute")
            continue

        print(f"[juge] #{eval_entry['id']} ({eval_entry['type']}) : {eval_entry['message']}")
        judgments = []
        for rep in eval_entry["repetitions"]:
            entry_for_judge = {
                "message": eval_entry["message"],
                "config": rep["config"],
                "llm_message": rep["llm_message"],
            }
            judgment = _judge_with_retry(client, entry_for_judge)
            judgments.append(
                {
                    "repetition": rep["repetition"],
                    "config": rep["config"],
                    "llm_message": rep["llm_message"],
                    "judgment": judgment,
                }
            )
            print(
                f"    rep {rep['repetition']}/15 -> couverture={judgment['couverture']} "
                f"absence_invention={judgment['absence_invention']} transparence={judgment['transparence']}"
            )

        _append_log(
            {
                "id": eval_entry["id"],
                "type": eval_entry["type"],
                "message": eval_entry["message"],
                "judge_model": JUDGE_MODEL,
                "judgments": judgments,
            }
        )

    print(f"\nTermine : {JUDGE_LOG_REPEATED_PATH}")


if __name__ == "__main__":
    main()
