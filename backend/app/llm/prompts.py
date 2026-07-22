SYSTEM_PROMPT_TEMPLATE = """Tu es l'assistant d'un configurateur de bureaux électriques assis/debout motorisés, en contexte B2B.

Ton rôle : à partir de la demande du client (en langage naturel, potentiellement en plusieurs tours de dialogue), produire une configuration structurée en choisissant EXCLUSIVEMENT parmi les identifiants du catalogue ci-dessous. N'invente jamais un identifiant qui n'existe pas dans cette liste.

{catalogue_ids}

Options du catalogue les plus pertinentes pour cette demande (issues d'une recherche sémantique dans le catalogue) :
{rag_context}

Si une configuration actuelle est fournie dans la conversation, modifie-la selon la nouvelle demande du client plutôt que de repartir de zéro — conserve les champs non mentionnés par le client dans son dernier message.

Réponds uniquement en remplissant les champs de la configuration structurée demandée, sans texte libre additionnel."""


def build_catalogue_ids_summary(catalogue: dict) -> str:
    lines = [
        "Finitions disponibles (id : nom) : "
        + ", ".join(f"{f['id']} ({f['nom']})" for f in catalogue["finitions"]),
        "Plateaux disponibles (id : nom, largeurs en cm, profondeur en cm) : "
        + ", ".join(
            f"{p['id']} ({p['nom']}, largeurs {p['largeurs_disponibles_cm']}, profondeur {p['profondeur_cm']}cm)"
            for p in catalogue["plateaux"]
        ),
        "Structures disponibles (id : nom, moteur, largeur max compatible) : "
        + ", ".join(
            f"{s['id']} ({s['nom']}, moteur {s['moteur']}, largeur max {s['largeur_max_compatible_cm']}cm)"
            for s in catalogue["structures"]
        ),
        "Accessoires disponibles (id : nom) : "
        + ", ".join(f"{a['id']} ({a['nom']})" for a in catalogue["accessoires"]),
    ]
    return "\n".join(lines)


def build_system_prompt(catalogue: dict, rag_results: list[dict]) -> str:
    rag_context = "\n".join(f"- ({r['categorie']}) {r['description']}" for r in rag_results) or "(aucune)"
    return SYSTEM_PROMPT_TEMPLATE.format(
        catalogue_ids=build_catalogue_ids_summary(catalogue),
        rag_context=rag_context,
    )
