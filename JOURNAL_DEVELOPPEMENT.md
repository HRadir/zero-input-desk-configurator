# Journal de développement — "Zero Input" : configurateur conversationnel de bureau assis/debout

Document de travail destiné à nourrir le chapitre "Expérimentation" / "Implémentation" du mémoire. Il retrace, de façon précise et chronologique, l'ensemble du développement mené avec l'assistance de Claude Code (Anthropic), les choix techniques effectués et pourquoi, les difficultés réellement rencontrées, et une analyse de ce qui a nécessité — ou non — un apport significatif de l'IA par rapport à ce qu'un développeur junior aurait pu produire seul.

---

## 1. Objectif du projet et rappel du pipeline

Le système répond à la problématique du mémoire : à partir d'un besoin exprimé en langage naturel par un client B2B ("Je veux un bureau motorisé style scandinave, plateau bois clair, structure blanche, pour deux écrans"), générer automatiquement une configuration produit valide, visualisée en temps réel sur un modèle 3D, via un dialogue multi-tours.

Pipeline retenu :

```
Langage naturel (chat)
   → Recherche sémantique (RAG, ChromaDB) dans le catalogue produit
   → Génération d'une configuration structurée (GPT-4o, sortie contrainte à un schéma Pydantic)
   → Validation déterministe par un moteur de contraintes métier
   → Boucle de correction automatique si invalide (ré-injection des erreurs au LLM)
   → Mise à jour en temps réel du viewer 3D (React Three Fiber)
```

Ce pipeline hybride — génération probabiliste (LLM) encadrée par une validation déterministe (moteur de règles) — est le cœur de la contribution technique du mémoire : il permet d'obtenir une fiabilité proche de 100 % sur la validité métier des configurations produites, malgré le caractère intrinsèquement non déterministe d'un LLM.

---

## 2. Stack technique retenue et justification

| Choix | Alternative envisagée | Pourquoi ce choix |
|---|---|---|
| **FastAPI** (backend) | Flask, Django REST | Asynchrone nativement, validation automatique des requêtes via Pydantic, documentation OpenAPI générée sans effort — adapté à une API qui expose surtout des endpoints JSON simples. |
| **LangChain** (orchestration LLM) | Appels directs à l'API OpenAI (SDK `openai` brut) | Fournit `with_structured_output()`, qui force une réponse LLM à respecter un schéma Pydantic exact sans avoir à parser/réparer manuellement du JSON en texte libre — voir section 6 pour le détail de la difficulté que ça évite. |
| **ChromaDB** (base vectorielle) | Pinecone, Weaviate, FAISS brut | Base vectorielle locale, embarquée (pas de service externe à gérer), largement suffisante pour un catalogue de 16 entrées, et compatible avec les métriques d'évaluation RAGAS prévues en Phase 12. |
| **OpenAI GPT-4o** (génération + embeddings) | Anthropic Claude | Choix initial du sujet de mémoire. Une bascule vers Claude a été envisagée en cours de projet (section 5, épisode "Claude vs OpenAI") mais abandonnée : Anthropic ne propose aucune API d'embeddings propriétaire, ce qui aurait imposé une architecture hybride (Claude pour la génération + un fournisseur tiers pour les embeddings). Le surcoût de complexité n'était pas justifié par le gain, d'autant que le sujet du mémoire nommait déjà explicitement GPT-4o. |
| **React + Three.js + React Three Fiber (R3F) + drei** (viewer 3D) | Three.js vanilla, Babylon.js | R3F permet de décrire une scène 3D de façon déclarative avec des composants React (cohérent avec le reste du frontend) ; `drei` fournit des abstractions prêtes à l'emploi (`useGLTF`, `Bounds`, `ContactShadows`, `Environment`) qui évitent de réécrire à la main la gestion du chargement GLTF, du cadrage caméra, etc. |
| **Zustand** (état global frontend) | Redux, Context API | Bibliothèque minimaliste à base de hooks, largement suffisante pour trois stores indépendants (config du bureau, catalogue, historique de chat) sans le boilerplate de Redux. |
| **Pydantic** (modèles de données backend) | dataclasses brutes + validation manuelle | Utilisé à la fois pour la validation structurelle (types, bornes) et directement comme schéma cible de la sortie structurée du LLM (`with_structured_output`) — un seul modèle sert les deux usages. |
| **Docker / docker-compose** | Lancement manuel des deux serveurs | Permet un lancement en une commande pour la démo/soutenance, indépendant de l'environnement Python/Node local de la machine de démonstration. |

---

## 3. Déroulé chronologique détaillé

### Phase 0 — Scaffolding
Création de l'arborescence (`frontend/`, `backend/`, `data/`, `evaluation/`), initialisation Git, environnement virtuel Python (`venv`) avec toutes les dépendances, projet Vite + React + Three.js + R3F + Zustand côté frontend. Vérification que les deux serveurs démarrent (`/health` côté backend, page par défaut Vite côté frontend).

*Incident mineur* : un dossier fantôme `backend/backend/` a été créé par erreur — un `cd backend` exécuté dans une commande précédente avait laissé le répertoire de travail du shell positionné dans `backend/`, si bien qu'une commande `mkdir` ultérieure (censée créer `backend/app/rag/`, `backend/app/llm/`, `backend/app/schemas/`) a créé ces dossiers imbriqués une seconde fois sous `backend/backend/`. Repéré et corrigé avant le premier commit (`git add -A -n` en mode simulation avait révélé l'anomalie).

### Phase 1 — Acquisition et inspection du modèle 3D
Sur suggestion pertinente de l'utilisateur, l'ordre initial du plan a été inversé : plutôt que de concevoir le catalogue produit puis d'adapter le rendu 3D au modèle disponible, le modèle 3D (`desk.glb`, FurniMesh) a été téléchargé et inspecté **avant** la conception du catalogue, pour que le catalogue soit dimensionné en connaissance de cause.

L'inspection technique (script Python utilisant la bibliothèque `pygltflib` pour parser directement le format binaire GLB) a révélé une contrainte structurante pour tout le reste du projet :
- **1 seul mesh, 1 seul matériau**, piloté par une texture bakée (bois + métal peints ensemble dans la même image) — aucune séparation plateau/structure.
- **0 animation, 0 skin** — aucun rig pour simuler le mouvement assis/debout.
- **Aucun mesh dédié aux accessoires** (bras écran, passe-câble...).

Ces trois constats ont directement déterminé les choix suivants, assumés comme limitations documentées (`frontend/public/models/MODEL_NOTES.md`) :
1. La couleur ne peut être qu'une teinte globale (`material.color.set()`, une opération de multiplication qui ne peut qu'assombrir une texture existante, jamais l'éclaircir) — d'où le choix de découpler la couleur en un concept de "finition" globale dans le catalogue, plutôt que des couleurs indépendantes plateau/structure.
2. Le mouvement assis/debout est simulé par une translation Y programmée de tout l'objet, pas un vrai télescopage des pieds.
3. Les accessoires ne sont pas rendus en 3D en v1 (config/texte uniquement).

### Phase 2 — Modèle de données
`data/catalogue.json` (5 finitions, 3 plateaux, 2 structures, 6 accessoires, 5 styles) et `data/contraintes.json` (8 règles de compatibilité) conçus directement à la lumière de la Phase 1.

### Phase 3 — Moteur de contraintes
`backend/app/constraints/engine.py` : plutôt que d'écrire une fonction de validation par règle métier codée en dur, les règles sont **données** (JSON) et interprétées par un dispatcher générique basé sur un champ `type` (ex. `largeur_min_ecrans`, `moteur_min_largeur`, `accessoire_prerequis_dimension`...). Ce choix d'architecture data-driven rend l'ajout d'une nouvelle règle métier possible sans toucher au code applicatif principal (juste une entrée JSON + une branche de dispatch). 10 tests unitaires (`pytest`), un par règle plus un scénario valide de bout en bout et un cas de référence catalogue inconnue — 10/10 dès la première exécution.

### Phase 4 — Squelette API FastAPI
`/health`, `GET /catalogue`, `POST /config/validate`. CORS restreint à l'origine du serveur de dev Vite.

### Phase 5 — Viewer 3D statique
Composant `DeskViewer.jsx` : `Canvas` R3F, `useGLTF` pour charger `desk.glb`, `OrbitControls`, et surtout le composant `Bounds` de `drei` qui recadre automatiquement la caméra sur l'objet chargé — utile car la taille réelle du modèle (en unités "monde") n'était pas connue à l'avance. Un premier rendu montrait une vue de face plate et peu engageante ; corrigé en changeant la position initiale de la caméra (`Bounds` conserve la direction de vue et ne fait qu'ajuster la distance, donc partir d'une position en légère plongée donne une perspective 3/4 plus lisible).

### Phase 6 — Rendu piloté par la configuration
Store Zustand `useConfigStore`. La teinte de finition est appliquée en **clonant** la scène et les matériaux (`scene.clone(true)` puis `material.clone()`) avant de les modifier — point important : `useGLTF` met en cache et partage l'objet scène chargé entre toutes les instances du composant (y compris entre rechargements à chaud en développement) ; muter directement le matériau du cache aurait corrompu l'affichage pour toute réutilisation ultérieure du modèle. La hauteur assis/debout est animée par interpolation (`useFrame`, lerp) plutôt qu'un changement instantané. Un panneau de debug (sélecteurs manuels) permet de tester le rendu indépendamment du chat, qui n'existe pas encore à ce stade.

### Phase 7 — Indexation RAG
`backend/app/rag/indexer.py` : chaque entrée du catalogue est transformée en description textuelle puis embeddée (`OpenAIEmbeddings`, `text-embedding-3-small`) et stockée dans une collection ChromaDB persistante. Le script est rendu **idempotent** : à chaque exécution, la collection existante est supprimée puis recréée, pour éviter d'accumuler des doublons d'embeddings si le script est relancé plusieurs fois (un piège facile à ne pas anticiper).

### Phase 8 — Génération LLM
`backend/app/llm/generator.py` : `ChatOpenAI(...).with_structured_output(DeskConfig)` force le LLM à renvoyer un objet conforme au schéma Pydantic `DeskConfig`, sans avoir à demander "réponds en JSON" en texte libre puis à parser/réparer la réponse à la main. Le prompt système liste explicitement les identifiants réels du catalogue (pour limiter les hallucinations d'ID) et injecte les résultats de la recherche RAG. Testé dès le premier appel avec la phrase d'exemple du mémoire : configuration cohérente et déjà valide.

### Phase 9 — Boucle de validation/correction
Après génération, la configuration est validée par le moteur de contraintes (Phase 3). En cas d'échec, les messages d'erreur précis sont réinjectés comme instruction de correction au LLM (jusqu'à 3 tentatives), chaque tentative étant journalisée (`backend/logs/generation_log.jsonl`) — cette matière brute est prévue pour l'évaluation RAGAS de la Phase 12. Ce mécanisme a été validé en conditions réelles : une demande de correction ("finalement 3 écrans" sans ajuster la largeur ni les accessoires) a généré une configuration invalide en 1er essai, corrigée automatiquement en cascade (plateau plus large, structure triple moteur, nombre de bras écran ajusté) au 2e essai.

### Phase 10 — Interface de chat
Store `useChatStore` (historique, appel `/chat/generate`, correspondance entre les champs `snake_case` de l'API et `camelCase` du store frontend) et composant `ChatPanel` (historique, saisie, indicateur de chargement, récapitulatif de configuration, bouton de validation finale). Testé de bout en bout via un scénario scripté à deux tours de dialogue, avec captures d'écran automatiques à chaque étape.

### Phase 11 — Robustesse
Gestion d'erreurs de bout en bout : les exceptions lors de l'appel LLM (timeout, quota, réseau) sont interceptées côté FastAPI et renvoyées en HTTP 502 avec un message clair (plutôt qu'un 500 brut avec trace Python complète) ; un `ErrorBoundary` React entoure spécifiquement le viewer 3D pour afficher un message propre si le modèle GLB ne charge pas, plutôt qu'un écran blanc. Vérification à froid : arrêt complet des deux serveurs, redémarrage strict selon les instructions du `README.md`, rejeu du scénario complet — comportement identique, tests toujours au vert.

### Extensions au-delà du plan initial

**Dockerisation.** `docker-compose.yml` (service `backend` FastAPI, service `frontend` build React servi par nginx), volume nommé persistant pour ChromaDB, script d'entrée (`docker-entrypoint.sh`) qui n'indexe le catalogue que si le volume est vide (idempotence au premier démarrage). Testé de bout en bout, y compris un redémarrage du conteneur backend pour confirmer que l'index n'est pas recalculé inutilement.

**Champ `message` du LLM.** Un vrai problème d'expérience utilisateur a été identifié par l'utilisateur : le LLM était structurellement incapable de signaler qu'une partie d'une demande était impossible (ex. "des autocollants oranges sur le bureau") — `with_structured_output(DeskConfig)` ne laissait aucun canal d'expression en dehors des champs de configuration eux-mêmes, et le message affiché dans le chat était de toute façon une chaîne codée en dur côté frontend. Corrigé en introduisant un modèle `GenerationResult` englobant `config` et un champ `message` en langage naturel, avec instruction explicite dans le prompt système de signaler toute demande sans équivalent catalogue plutôt que de l'ignorer silencieusement. Vérifié avec une demande volontairement impossible : le LLM signale correctement la limitation.

**Mise à l'échelle 3D largeur/plateau, limitation de la structure.** Il a été constaté que changer la largeur, le plateau ou la structure dans le panneau de debug n'avait strictement aucun effet visuel — seuls la teinte et le mode assis/debout avaient été câblés en Phase 6. Corrigé pour la largeur et la profondeur du plateau via une mise à l'échelle **relative** du mesh (facteur = valeur choisie / valeur de référence par défaut, le modèle n'ayant pas de cotes réelles connues en cm). Pour la structure (moteur double/triple), le choix a été de **ne pas inventer d'effet visuel arbitraire** — le mesh fusionné ne modélise pas de pieds/moteur séparés, donc rien d'honnête ne peut être affiché — et de documenter cette limitation plutôt que de la masquer.

**Ajout d'un modèle d'écran 3D.** Second asset externe (Sketchfab, licence CC Attribution, auteur "Annelida"), correctement structuré (2 meshes séparés écran/pied, contrairement au bureau) et exprimé en unités métriques réelles — contrairement au bureau, dont les unités ne correspondent à aucune mesure connue. La combinaison des deux dans une même scène a nécessité un calage empirique (échelle et position ajustées par essais successifs et captures d'écran) plutôt qu'un calcul de conversion d'unités, puisqu'aucune conversion fiable n'existe entre les deux référentiels. Un problème signalé par l'utilisateur (le pied de l'écran visuellement enfoncé dans le plateau) a été corrigé en ajoutant une marge de dégagement explicite, vérifiée par calcul géométrique exact plutôt que par capture d'écran (les tentatives de changement d'angle de caméra via automatisation de navigateur se sont révélées peu concluantes, une manipulation ayant même fait basculer la caméra sous le bureau par erreur).

**Hygiène Git/GitHub.** Sur demande explicite de l'utilisateur, toute mention de "Claude" a été retirée de l'historique Git — vérification a montré qu'elle n'existait que dans le message de commit (`Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`), jamais dans l'identité auteur/committeur. Réécriture des 5 commits via `git filter-branch --msg-filter` (l'usage de `rebase -i` étant exclu), suivie d'un `push --force` (confirmé explicitement avant exécution). Une seconde réécriture a raccourci et traduit tous les messages en anglais, sur une demande de style ultérieure. Un affichage résiduel de "Claude" dans la page "Contributors" de GitHub après coup a été diagnostiqué (sans certitude absolue) comme un effet de cache côté GitHub (le graphe de contributeurs n'est pas recalculé en temps réel après une réécriture d'historique), et non comme une trace réelle dans les données Git elles-mêmes — confirmé par une recherche exhaustive (`git log --all`) ne faisant apparaître aucune occurrence.

---

## 4. Difficultés techniques réellement rencontrées (synthèse transversale)

Cette section répond spécifiquement à la question "quelles parties ont posé le plus de problème".

1. **La contrainte du modèle 3D fusionné (Phase 1)** — la découverte que le GLB n'a qu'un seul matériau et aucun rig a été la contrainte la plus structurante du projet : elle a forcé une refonte du schéma de catalogue (finition globale plutôt que couleurs séparées) et impose encore aujourd'hui des limitations assumées (structure sans représentation visuelle).
2. **Confusions d'environnement Windows/PowerShell** — le répertoire de travail de PowerShell a changé de façon inattendue à plusieurs reprises entre deux commandes, provoquant des erreurs "module introuvable" lors du lancement d'`uvicorn` avec des chemins relatifs erronés ; nécessité de revérifier systématiquement `Get-Location` et de préférer des chemins absolus.
3. **Processus serveurs orphelins** — plusieurs instances de `npm run dev` sont restées actives sur le port 5173 (et ses variantes IPv4/IPv6) d'une session à l'autre, provoquant un repli silencieux de Vite sur le port 5174 pendant qu'un test automatisé continuait de cibler l'ancien port 5173 (donc l'ancien code) — source d'une confusion de débogage significative, résolue en identifiant les processus via `netstat`/`Get-Process` avant de les arrêter.
4. **Collision de sélecteur CSS dans les tests automatisés** — l'indicateur de chargement du chat partageait la même classe CSS (`chat-message-assistant`) que les vrais messages de l'assistant, faisant qu'un test automatisé considérait par erreur qu'une réponse était arrivée alors que seul l'indicateur de chargement était présent.
5. **Bascule OpenAI/Claude** — une hésitation sur le fournisseur LLM a nécessité de vérifier qu'Anthropic ne propose pas d'API d'embeddings, information déterminante pour trancher rapidement en faveur du statu quo (OpenAI de bout en bout).
6. **Disponibilité de Docker Desktop** — le démon Docker n'était pas démarré au moment de construire les images, nécessitant une coordination (attente active) avant de pouvoir lancer les builds.
7. **Réécriture d'historique Git** — une opération avancée et rarement pratiquée (`filter-branch` avec un script de filtrage de message, nettoyage des références de sauvegarde, `push --force`), à mener avec prudence (confirmation explicite avant toute opération destructive, vérification exhaustive avant et après).
8. **Réconciliation d'échelle entre deux assets 3D hétérogènes** — combiner le bureau (unités arbitraires non calibrées) et l'écran (unités métriques réelles) dans une même scène ne pouvait pas se résoudre par un calcul : il a fallu procéder par ajustements empiriques successifs, avec des captures d'écran comme seul outil de vérification (et un outil de vérification lui-même limité, cf. point suivant).
9. **Fiabilité des vérifications visuelles automatisées** — les tentatives de changer l'angle de caméra par automatisation de souris (`OrbitControls`) pour vérifier visuellement un contact objet/surface se sont révélées peu fiables (une tentative a fait passer la caméra sous le bureau) ; la vérification finale s'est appuyée sur un calcul géométrique exact plutôt que sur l'image rendue.
10. **Environnement de développement éphémère** — les outils d'inspection créés en cours de session (environnement Python dédié à l'inspection de fichiers GLB, installation de Playwright pour les tests visuels) étaient stockés dans un répertoire temporaire propre à la session et ont dû être recréés à plusieurs reprises d'une session de travail à l'autre.

---

## 5. Parties du code les plus complexes — ce qui aurait été difficile pour un développeur junior sans assistance IA

Cette section évalue, module par module, ce qui représente une réelle difficulté conceptuelle (pas seulement du volume de code) et où l'assistance de l'IA a le plus apporté par rapport à ce qu'un développeur junior aurait probablement produit seul.

### 5.1 La boucle génération ↔ validation ↔ correction (`backend/app/llm/generator.py`, Phases 8-9)
**C'est la partie la plus complexe du projet, et la plus directement liée à la contribution du mémoire.** Un développeur junior confronté au problème "faire produire du JSON valide par un LLM" se tourne spontanément vers une des deux approches suivantes, toutes deux fragiles :
- demander "réponds uniquement en JSON" dans le prompt, puis parser la réponse texte avec `json.loads()` entouré d'un `try/except` — cassant dès que le LLM ajoute la moindre phrase d'accompagnement ou une virgule superflue ;
- écrire des expressions régulières pour extraire les champs un par un — fragile, illisible, impossible à maintenir dès que le schéma évolue.

L'usage de `with_structured_output()` de LangChain (qui s'appuie sur le "tool calling"/"function calling" natif du modèle) pour garantir un JSON conforme à un schéma Pydantic est une technique qu'un junior ne connaît généralement pas d'emblée. Au-delà de l'outil, la conception de la **boucle de correction** — combiner un composant génératif (non fiable à 100 %) avec un moteur déterministe (la source de vérité), en ré-injectant les erreurs précises comme instruction de correction ciblée plutôt que de tout régénérer à l'aveugle — est un choix d'architecture qui ne relève pas d'un simple assemblage de bibliothèques : c'est une décision de conception qui répond directement à la problématique de fiabilité du mémoire.

### 5.2 L'ajout tardif du champ `message` (Phase "extensions")
Moins visible techniquement, mais révélateur : un junior aurait probablement laissé le schéma de sortie du LLM strictement identique au besoin métier (`DeskConfig`), sans anticiper qu'un modèle contraint à ce schéma perd toute possibilité d'exprimer une limitation. Identifier ce manque, puis le corriger sans casser la contrainte de schéma existante (en enveloppant `DeskConfig` dans un modèle englobant plutôt qu'en ajoutant des champs optionnels epars) est une subtilité de conception de schéma/prompt qui demande de comprendre *simultanément* le fonctionnement du structured output et les attentes UX.

### 5.3 La gestion du cache de scène GLTF (`frontend/src/components/DeskViewer.jsx`, Phase 6)
Le bug potentiel ici est insidieux et non local : `useGLTF` (drei) met en cache l'objet `scene` chargé et le **partage** entre toutes les instances du composant qui l'utilisent, y compris entre rechargements à chaud. Un junior qui applique directement `material.color.set()` sur cet objet partagé sans le cloner d'abord (`scene.clone(true)` + `material.clone()` par mesh) introduit un bug qui ne se manifeste pas immédiatement dans les tests simples, mais corrompt le rendu dès qu'un deuxième composant réutilise le même modèle ou après un rechargement à chaud en développement — un piège classique de la programmation avec des ressources partagées, difficile à diagnostiquer a posteriori.

### 5.4 La réconciliation d'échelle entre deux modèles 3D hétérogènes (Phase "ajout écran")
Il n'existe pas de solution "correcte" à ce problème au sens d'une formule à appliquer : le bureau n'a pas d'unité réelle connue, l'écran si. Un junior chercherait probablement une conversion d'unités qui n'existe pas, ou abandonnerait l'intégration faute de repère. La solution retenue — accepter l'absence de conversion fiable et procéder par calibration empirique itérative, documentée comme telle plutôt que présentée comme un calcul exact — est une décision méthodologique autant qu'un choix technique, qui vaut la peine d'être explicitée dans le mémoire comme une limitation assumée et justifiée.

### 5.5 Le moteur de contraintes data-driven (`backend/app/constraints/engine.py`, Phase 3)
Complexité modérée mais réelle : un junior aurait très probablement écrit une fonction de validation par règle métier, codée en dur (`if nombre_ecrans == 2 and largeur < 140: erreur`, dispersé dans le code). Le choix de faire des règles des **données** (JSON) interprétées par un dispatcher générique sur un champ `type` est un pattern de conception ("moteur de règles") qui demande un peu de recul architectural, même s'il reste d'un niveau de difficulté inférieur aux points 5.1 à 5.4.

### 5.6 L'orchestration Docker et l'idempotence de l'indexation
Concevoir un `docker-entrypoint.sh` qui indexe le catalogue uniquement si le volume ChromaDB est vide (plutôt que systématiquement à chaque démarrage) demande de comprendre la distinction entre l'image (reconstruite à chaque `--build`) et le volume (persistant entre redémarrages) — une distinction Docker qu'un junior maîtrise rarement sans l'avoir déjà pratiquée.

### 5.7 La réécriture d'historique Git (`git filter-branch`)
Compétence rarement enseignée et rarement pratiquée même par des développeurs expérimentés : réécrire le message de plusieurs commits déjà poussés, gérer les références de sauvegarde (`refs/original/*`), et pousser en force en toute sécurité (vérifier au préalable que le dépôt distant est bien vide de tout historique conflictuel) sont des opérations qu'un junior effectuerait rarement sans casser quelque chose — le risque d'erreur destructive y est élevé.

### 5.8 Ce qui, à l'inverse, relevait d'un niveau junior/intermédiaire
Par souci d'exhaustivité et d'honnêteté : le scaffolding (Phase 0), les endpoints FastAPI simples (Phase 4), le viewer 3D statique sans logique de configuration (Phase 5), le store Zustand de base (Phase 6 pour sa partie état, hors le piège du cache GLTF), et l'interface de chat React (Phase 10, hors la boucle d'appel API) sont d'une complexité raisonnable pour un développeur junior encadré — l'assistance IA y a surtout apporté un gain de **vitesse d'exécution**, pas une résolution de difficulté conceptuelle.

---

## 6. Limitations assumées (à citer explicitement dans le mémoire)

1. **Couleur** : teinte globale multiplicative sur l'ensemble du bureau (pas de séparation plateau/structure) — le grain de la texture de base reste visible sous la teinte, et une teinte claire ne peut pas éclaircir une texture sombre (limite mathématique de la multiplication de couleurs).
2. **Hauteur assis/debout** : translation verticale simulée de l'objet entier, pas de télescopage réel des pieds (absence de rig dans le fichier source).
3. **Accessoires** (bras écran, passe-câble, dock USB, panneau acoustique, support laptop) : aucune représentation 3D, gérés uniquement au niveau de la configuration et du texte.
4. **Structure (moteur double/triple, charge max)** : aucune représentation visuelle possible, absence assumée plutôt que simulation arbitraire.
5. **Largeur/profondeur du plateau** : approximées par une mise à l'échelle relative du mesh (facteur par rapport à une configuration de référence), pas une conversion d'unités réelles — le modèle source n'a pas de cotes en centimètres fiables.
6. **Écran 3D** : échelle et position calées empiriquement, pas de conversion d'unités exacte entre le bureau et l'écran (deux assets aux conventions d'unités différentes).
7. **Licences des assets 3D** : `desk.glb` (FurniMesh) sans licence explicitement précisée sur la fiche produit — à vérifier avant citation dans le mémoire ; `monitor.glb` (Sketchfab) sous licence CC Attribution, nécessitant de créditer l'auteur "Annelida".

---

## 7. Reste à faire (non couvert par ce journal)

- **Phase 12 — Évaluation RAGAS** : jeu de requêtes de test, calcul des métriques (faithfulness, context precision/recall, answer relevancy), plus des métriques personnalisées (taux de configuration valide dès la première génération, nombre moyen d'itérations de correction) exploitant `backend/logs/generation_log.jsonl`.
- **Phase 13 — Finitions pour la soutenance** : nettoyage du panneau de debug, captures/vidéo de démonstration, vérification finale des builds.
- Amélioration potentielle (non engagée) : séparation des matériaux plateau/structure dans Blender (Solution B évoquée dès la Phase 1, jamais mise en œuvre faute de nécessité) ; représentation 3D des accessoires via des assets dédiés, sur le même principe que l'ajout de l'écran.

---

## 8. Réflexion : rôle de l'assistance IA dans le développement

Ce projet étant lui-même un mémoire sur la génération automatique assistée par IA, il est pertinent d'expliciter où l'assistance de Claude Code a le plus concrètement apporté de valeur par rapport à un développement "junior seul" :

- **Accélération pure** sur les tâches de scaffolding, d'écriture de tests, de composants React standards — un gain de vitesse, pas de résolution de difficulté conceptuelle propre.
- **Connaissance d'outils et de patterns spécifiques** peu enseignés (sortie structurée LangChain, `git filter-branch`, orchestration Docker avec volume persistant et idempotence) — un junior aurait dû chercher/apprendre ces techniques, avec un risque d'erreur plus élevé en cours de route (en particulier sur les opérations Git destructives).
- **Diagnostic systématique de problèmes d'environnement** (ports occupés, processus orphelins, démon Docker non démarré, cache GitHub) — appuyé sur l'exécution réelle de commandes de vérification (`netstat`, `Get-Process`, `git log --all`) plutôt que sur des suppositions, réduisant le temps perdu en hypothèses non vérifiées.
- **Ce qui est resté du ressort de l'utilisateur, à chaque étape** : les décisions d'architecture structurantes (inversion de l'ordre des phases après l'inspection du GLB, choix du fournisseur LLM, périmètre de ce qui devait être visuellement représenté ou assumé comme limitation, style des messages de commit, exigence de confidentialité sur la mention de l'IA dans l'historique Git) ont systématiquement été posées comme des choix explicites à valider, jamais décidées unilatéralement par l'IA — cohérent avec le rôle d'assistant technique plutôt que de décideur produit.

Ce dernier point mérite d'être noté explicitement dans le mémoire : l'assistance IA a été la plus efficace non pas en remplaçant le jugement du développeur, mais en réduisant le coût d'exploration des options techniques (recherche, mise en œuvre, vérification) une fois la décision prise par l'utilisateur.
