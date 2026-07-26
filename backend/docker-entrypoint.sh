#!/bin/sh
set -e

if [ -z "$(ls -A /app/backend/chroma_db 2>/dev/null)" ]; then
  echo "Base ChromaDB vide : indexation du catalogue..."
  python -m app.rag.indexer
else
  echo "Base ChromaDB déjà indexée, on la réutilise."
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
