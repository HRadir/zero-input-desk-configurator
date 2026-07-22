# Schéma des données — catalogue.json / contraintes.json

Contexte : le modèle 3D (`desk.glb`, cf. `frontend/public/models/MODEL_NOTES.md`) est un mesh fusionné à un seul matériau. La couleur est donc découplée en une entité `finitions` indépendante (teinte globale appliquée à tout le bureau), tandis que `plateaux` et `structures` portent les spécifications commerciales (dimensions, moteur, prix) sans couleur propre.

## catalogue.json

```
{
  "finitions":   [ { id, nom, couleur_hex, style_tags[] } ],
  "plateaux":    [ { id, nom, materiau, largeurs_disponibles_cm[], profondeur_cm, prix_eur, style_tags[] } ],
  "structures":  [ { id, nom, moteur: "double"|"triple", hauteur_min_cm, hauteur_max_cm,
                     charge_max_kg, largeur_max_compatible_cm, prix_eur, style_tags[] } ],
  "accessoires": [ { id, nom, type, prix_eur, rendu_3d: bool, prerequis: {} } ],
  "styles":      [ "scandinave", "industriel", "minimaliste", "moderne", "classique" ]
}
```

- `rendu_3d: false` sur tous les accessoires actuellement : le GLB source n'a aucun mesh dédié pour ces éléments (cf. MODEL_NOTES.md) ; ils existent dans la config et le récapitulatif texte, pas dans la scène 3D.
- `prerequis` d'un accessoire peut contenir : `profondeur_plateau_min_cm`, `largeur_plateau_min_cm`, ou `accessoire_requis` (id d'un autre accessoire nécessaire).

## contraintes.json

```
{
  "regles": [ { id, type, description, severite: "erreur"|"avertissement", ...params spécifiques au type } ]
}
```

Types de règles implémentés (cf. `contraintes.json` pour les paramètres exacts de chacune) :

| type | vérifie |
|---|---|
| `largeur_min_ecrans` | largeur du plateau ≥ seuil selon nombre d'écrans (`seuils` : nombre_ecrans → cm) |
| `moteur_min_largeur` | si largeur ≥ `largeur_seuil_cm`, `structure.moteur == moteur_requis` |
| `largeur_max_structure` | largeur choisie ≤ `structure.largeur_max_compatible_cm` |
| `accessoire_prerequis_dimension` | si l'accessoire est présent, une dimension du plateau/config respecte `valeur_min` |
| `accessoire_prerequis_accessoire` | si l'accessoire est présent, un autre accessoire (`accessoire_requis_id`) doit l'être aussi |
| `coherence_accessoire_ecrans` | nombre de bras écran (somme simple+double, double comptant pour 2) == nombre d'écrans déclaré |
| `coherence_style` | (avertissement uniquement) finition/plateau/structure partagent un tag de style avec celui demandé |

## DeskConfig attendu (JSON généré par le LLM, structure Pydantic en Phase 3)

```
{
  "finition_id": "finition_chene_clair",
  "plateau_id": "plateau_standard",
  "largeur_choisie_cm": 140,
  "structure_id": "structure_double_moteur",
  "nombre_ecrans": 2,
  "accessoires": ["bras_ecran_double", "passe_cable"],
  "style_demande": "scandinave"
}
```

`largeur_choisie_cm` doit être une valeur présente dans `largeurs_disponibles_cm` du plateau sélectionné (vérifié par validation Pydantic, pas par le moteur de contraintes métier).
