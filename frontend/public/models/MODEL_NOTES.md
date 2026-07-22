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

## Emplacement du fichier

`frontend/public/models/desk.glb` (14.3 Mo, format GLB binaire)
