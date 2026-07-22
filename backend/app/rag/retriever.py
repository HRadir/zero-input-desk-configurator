from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from app.rag.indexer import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL

_store: Chroma | None = None


def _get_store() -> Chroma:
    global _store
    if _store is None:
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        _store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DIR),
        )
    return _store


def retrieve_relevant_options(query: str, k: int = 5) -> list[dict]:
    store = _get_store()
    results = store.similarity_search_with_score(query, k=k)
    return [
        {
            "categorie": doc.metadata["categorie"],
            "id": doc.metadata["id"],
            "description": doc.page_content,
            "score": score,
        }
        for doc, score in results
    ]


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or "plateau bois clair scandinave"
    print(f"Requête : {query!r}\n")
    for r in retrieve_relevant_options(query):
        print(f"[{r['score']:.3f}] ({r['categorie']}) {r['id']}: {r['description']}")
