from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ValidationIssue:
    rule_id: str
    message: str
    champ: Optional[str] = None


@dataclass
class ValidationResult:
    valid: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)


def _find_by_id(items: list[dict[str, Any]], item_id: Optional[str]) -> Optional[dict[str, Any]]:
    return next((item for item in items if item["id"] == item_id), None)


def validate_config(
    config: dict[str, Any], catalogue: dict[str, Any], contraintes: dict[str, Any]
) -> ValidationResult:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    finition = _find_by_id(catalogue["finitions"], config.get("finition_id"))
    plateau = _find_by_id(catalogue["plateaux"], config.get("plateau_id"))
    structure = _find_by_id(catalogue["structures"], config.get("structure_id"))

    if finition is None:
        errors.append(
            ValidationIssue("reference_inconnue", f"Finition inconnue: {config.get('finition_id')}", "finition_id")
        )
    if plateau is None:
        errors.append(
            ValidationIssue("reference_inconnue", f"Plateau inconnu: {config.get('plateau_id')}", "plateau_id")
        )
    if structure is None:
        errors.append(
            ValidationIssue("reference_inconnue", f"Structure inconnue: {config.get('structure_id')}", "structure_id")
        )

    # Sans plateau/structure valides, les règles métier ci-dessous n'ont pas de sens à évaluer.
    if plateau is None or structure is None:
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    largeur = config.get("largeur_choisie_cm")
    nombre_ecrans = config.get("nombre_ecrans")
    accessoires_ids: list[str] = config.get("accessoires", [])
    style_demande = config.get("style_demande")

    if largeur not in plateau["largeurs_disponibles_cm"]:
        errors.append(
            ValidationIssue(
                "largeur_indisponible",
                f"Largeur {largeur}cm non disponible pour '{plateau['id']}' "
                f"(options: {plateau['largeurs_disponibles_cm']})",
                "largeur_choisie_cm",
            )
        )

    accessoires: list[dict[str, Any]] = []
    for accessoire_id in accessoires_ids:
        acc = _find_by_id(catalogue["accessoires"], accessoire_id)
        if acc is None:
            errors.append(
                ValidationIssue("reference_inconnue", f"Accessoire inconnu: {accessoire_id}", "accessoires")
            )
        else:
            accessoires.append(acc)

    for regle in contraintes["regles"]:
        rtype = regle["type"]
        target = errors if regle["severite"] == "erreur" else warnings

        if rtype == "largeur_min_ecrans":
            seuil = regle["seuils"].get(str(nombre_ecrans))
            if seuil is not None and largeur is not None and largeur < seuil:
                target.append(
                    ValidationIssue(
                        regle["id"],
                        f"{nombre_ecrans} écran(s) nécessite(nt) une largeur ≥ {seuil}cm (actuel: {largeur}cm)",
                        "largeur_choisie_cm",
                    )
                )

        elif rtype == "moteur_min_largeur":
            if (
                largeur is not None
                and largeur >= regle["largeur_seuil_cm"]
                and structure["moteur"] != regle["moteur_requis"]
            ):
                target.append(
                    ValidationIssue(
                        regle["id"],
                        f"Largeur ≥ {regle['largeur_seuil_cm']}cm nécessite un moteur "
                        f"{regle['moteur_requis']} (actuel: {structure['moteur']})",
                        "structure_id",
                    )
                )

        elif rtype == "largeur_max_structure":
            if largeur is not None and largeur > structure["largeur_max_compatible_cm"]:
                target.append(
                    ValidationIssue(
                        regle["id"],
                        f"Largeur {largeur}cm dépasse la largeur max compatible de la structure "
                        f"({structure['largeur_max_compatible_cm']}cm)",
                        "largeur_choisie_cm",
                    )
                )

        elif rtype == "accessoire_prerequis_dimension":
            if regle["accessoire_id"] in accessoires_ids:
                dimension = regle["dimension"]
                valeur = plateau.get(dimension) if dimension in plateau else config.get(dimension)
                if valeur is None or valeur < regle["valeur_min"]:
                    target.append(
                        ValidationIssue(
                            regle["id"],
                            f"'{regle['accessoire_id']}' nécessite {dimension} ≥ {regle['valeur_min']} "
                            f"(actuel: {valeur})",
                            "accessoires",
                        )
                    )

        elif rtype == "accessoire_prerequis_accessoire":
            if regle["accessoire_id"] in accessoires_ids and regle["accessoire_requis_id"] not in accessoires_ids:
                target.append(
                    ValidationIssue(
                        regle["id"],
                        f"'{regle['accessoire_id']}' nécessite '{regle['accessoire_requis_id']}' "
                        "dans la configuration",
                        "accessoires",
                    )
                )

        elif rtype == "coherence_accessoire_ecrans":
            bras_count = sum(2 if a["id"] == "bras_ecran_double" else 1 for a in accessoires if a["type"] == "bras_ecran")
            if nombre_ecrans is not None and bras_count != nombre_ecrans:
                target.append(
                    ValidationIssue(
                        regle["id"],
                        f"{bras_count} bras écran configuré(s) pour {nombre_ecrans} écran(s) déclaré(s)",
                        "accessoires",
                    )
                )

        elif rtype == "coherence_style":
            if style_demande:
                tags = set(structure["style_tags"]) | set(plateau["style_tags"])
                if finition is not None:
                    tags |= set(finition["style_tags"])
                if style_demande not in tags:
                    target.append(
                        ValidationIssue(
                            regle["id"],
                            f"Le style '{style_demande}' n'est pas cohérent avec la finition/plateau/structure choisis",
                        )
                    )

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
