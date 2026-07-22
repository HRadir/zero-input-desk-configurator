# Zero Input — Configurateur conversationnel de bureau assis/debout

Mémoire de Master : génération automatique de configurations personnalisées à partir de besoins client exprimés en langage naturel, appliquée à un configurateur B2B de bureau électrique assis/debout.

Pipeline : langage naturel → recherche RAG dans le catalogue (ChromaDB) → génération d'une configuration structurée (GPT-4o) → validation/correction par un moteur de contraintes → mise à jour en temps réel d'un viewer 3D (React Three Fiber).

## Prérequis

- Python 3.11+
- Node.js 20+
- Une clé API OpenAI avec facturation activée (https://platform.openai.com/api-keys)

## Structure du projet

```
backend/     FastAPI + LangChain + ChromaDB (API, moteur de contraintes, RAG, LLM)
frontend/    React + Three.js + React Three Fiber (viewer 3D + chat)
data/        catalogue.json, contraintes.json, SCHEMA.md
evaluation/  scripts d'évaluation RAGAS (Phase 12)
```

## Installation initiale

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env
# éditer .env et renseigner OPENAI_API_KEY
```

Indexer le catalogue dans ChromaDB (à refaire à chaque modification de `data/catalogue.json`) :

```powershell
venv\Scripts\python.exe -m app.rag.indexer
```

### Frontend

```powershell
cd frontend
npm install
```

Le modèle 3D (`desk.glb`, non versionné car volumineux) doit être placé dans `frontend/public/models/desk.glb` — voir `frontend/public/models/MODEL_NOTES.md` pour son origine et ses limitations connues.

Optionnel : `copy .env.example .env` si le backend ne tourne pas sur `http://localhost:8000`.

## Lancer le projet

Deux terminaux, depuis la racine du projet :

**Backend** (port 8000) :

```powershell
backend\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --port 8000
```

**Frontend** (port 5173) :

```powershell
cd frontend
npm run dev
```

Ouvrir `http://localhost:5173`.

## Tests

```powershell
cd backend
venv\Scripts\python.exe -m pytest tests -v
```

## Limitations connues

Le modèle 3D source est un mesh fusionné à un seul matériau (pas de séparation plateau/structure, pas de rig d'animation) — voir `frontend/public/models/MODEL_NOTES.md` pour le détail des choix de simplification (teinte globale, translation verticale simulée, accessoires non rendus en 3D).
