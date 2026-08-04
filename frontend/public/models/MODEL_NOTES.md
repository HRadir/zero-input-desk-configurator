# Notes techniques — desk.glb

Source : FurniMesh, "A Modern Electric Standing Desk" (T821ZW)
https://furnimesh.com/library/tables/desk/a-modern-electric-standing-desk-featuring-a-t821zw/

Licence d'usage non précisée sur la fiche produit — à vérifier dans les conditions générales de FurniMesh avant citation/diffusion dans le mémoire.

## Structure du fichier (inspectée via pygltflib)

- **Scène** : 1 nœud racine `world` → 1 enfant `geometry_0`
- **Nodes** : 2 seulement (`world`, `geometry_0`) — aucune hiérarchie (pas de nœuds séparés "plateau"/"pieds")
- **Meshes** : 1 seul mesh (`geometry_0`), 1 seule primitive
- **Matériaux** : 1 seul matériau, sans nom
  - `baseColorFactor = [1, 1, 1, 1]` (blanc neutre = pas de teinte appliquée par défaut)
  - `baseColorTexture` : une texture PNG bakée (probablement bois + métal peints ensemble dans une même image)
  - `metallicRoughnessTexture` : une seconde texture PNG
  - `metallicFactor = 1.0`, `roughnessFactor = 1.0` (ces facteurs multiplient la texture correspondante)
  - pas de normalTexture / occlusionTexture / emissiveTexture
- **Animations** : 0
- **Skins** : 0
- **Triangles** : 296 813 / **Vertices** : 178 470 (cf. fiche FurniMesh)

## Implications actées avec l'utilisateur

1. **Couleur (v1 — Solution A retenue)** : le modèle étant un mesh unique avec un seul matériau piloté par une texture bakée, on applique une teinte globale via `material.color.set(hexColor)` (multiplie `baseColorFactor`), ce qui module toute la texture (plateau + structure) d'un coup. Le rendu sera approximatif (le grain de bois/texture de base reste visible sous la teinte) — **limitation à documenter explicitement dans le mémoire**.
   - Le catalogue v1 (Phase 2) proposera donc des "finitions" globales plutôt que des couleurs indépendantes plateau/structure.
2. **Amélioration future (Solution B, prévue mais pas bloquante pour la suite)** : Blender est installé chez l'utilisateur. Étape ultérieure possible : ouvrir `desk.glb` dans Blender, séparer la géométrie plateau/structure en 2 matériaux distincts (par sélection de faces + assignation), réexporter en GLB. Permettrait un vrai catalogue plateau/structure indépendant. Non fait à ce stade pour ne pas bloquer l'avancement du pipeline NL→config→3D.
3. **Hauteur assis/debout (0 animation dans le fichier)** : simulée côté code par une **translation Y programmée** du nœud racine (`world`) entre une position "assis" et une position "debout", interpolée dans le temps (`useFrame` en R3F). Tout le bureau monte en bloc (pas de télescopage visuel des pieds) — limitation acceptée, cohérente avec l'absence de rig dans le fichier source.
4. **Accessoires** (bras écran, passe-câble, etc.) : aucun mesh dédié dans le fichier — le catalogue ne pourra pas afficher ces options comme des sous-meshes activables/désactivables du GLB natif. Ils seront soit omis du rendu 3D (présents seulement dans la config/texte), soit représentés plus tard par des primitives géométriques simples ajoutées par code (hors GLB). Décision de scope : **omis du rendu 3D en v1**, gérés uniquement au niveau de la config JSON et du récapitulatif texte.
5. **Largeur du plateau et profondeur du plateau (Phase 6, complété a posteriori)** : le mesh unique n'ayant pas de cotes réelles connues en cm, la largeur choisie (`largeurChoisieCm`) et la profondeur du plateau sélectionné (`profondeur_cm` du catalogue) sont approximées par une **mise à l'échelle relative** du mesh entier sur les axes X (largeur) et Z (profondeur), avec la configuration par défaut (140cm / 70cm) comme référence (facteur 1). Ce n'est donc pas une conversion cm → unités du monde 3D fidèle, juste une variation visuelle proportionnelle et honnête du volume du bureau.
6. **Structure (moteur double/triple, charge max)** : **aucune représentation visuelle**. Ces attributs n'ont pas d'équivalent géométrique dans un mesh fusionné sans pieds/moteur modélisés séparément — la couleur étant déjà réservée à la finition, il n'y a rien de honnête à afficher pour distinguer les structures entre elles. Limitation assumée, à citer explicitement dans le chapitre limites du mémoire plutôt que de simuler un effet visuel arbitraire.

## Emplacement du fichier

`frontend/public/models/desk.glb` (14.3 Mo, format GLB binaire)

---

# Notes techniques — monitor.glb

Source : Sketchfab, "PC Monitor 27 inch" par Annelida
https://sketchfab.com/3d-models/pc-monitor-27-inch-06fb18eec19245d4811c4c3c8c7ea567

**Licence : CC Attribution.** Usage commercial autorisé, mais attribution obligatoire à l'auteur "Annelida" — **à citer explicitement dans les remerciements/annexes du mémoire**.

## Structure du fichier (inspectée via pygltflib)

- **Nodes** : 7, hiérarchie propre (`Screen` → `Screen_Display_0`, `Main_low` → `Main_low_Base_0`)
- **Meshes** : 2, chacun avec son propre matériau (`Display` pour l'écran, `Base` pour le pied/châssis) — contrairement au bureau, la géométrie est déjà séparée par partie
- **Animations** : 0
- **Triangles** : ~6 400 / **Vertices** : ~3 300
- **Unités** : cotes réelles en mètres (bounding box mesuré : écran ~0,71m × 0,40m, ensemble avec pied ~0,72m × 0,51m × 0,18m) — contrairement à `desk.glb`, ce fichier respecte la convention glTF standard (1 unité = 1 mètre)

## Intégration (Phase — ajout écrans à l'écran 3D)

Le bureau (`desk.glb`) est en unités arbitraires non calibrées (cf. section précédente), alors que `monitor.glb` est en vraies unités métriques. Combiner les deux dans une seule scène Three.js sans ajustement ferait apparaître l'écran disproportionné (trop grand) par rapport au bureau. En l'absence d'une cote fiable pour le bureau, l'échelle et la position de l'écran (`MONITOR_SCALE`, `MONITOR_Y_OFFSET`, `MONITOR_Z_OFFSET` dans `DeskViewer.jsx`) sont **calées empiriquement par capture d'écran**, pas calculées à partir d'une conversion d'unités exacte — cohérent avec l'approche déjà retenue pour la largeur/profondeur du plateau.

- Un écran est instancié par unité de `nombre_ecrans` (1 à 3), positionné le long de l'axe X du plateau, avec un espacement qui suit le facteur d'échelle de la largeur du bureau (`scaleX`) pour rester cohérent si le plateau change de largeur.
- Le groupe des écrans partage la même translation verticale (assis/debout) que le bureau, pour bouger avec lui.
- Au-delà de 3 écrans, la disposition n'est pas prévue (le catalogue plafonne `nombre_ecrans` à 3).

## Emplacement du fichier

`frontend/public/models/monitor.glb` (9,6 Mo, format GLB binaire)
