import json
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR.parent / "data"
CHROMA_DIR = BACKEND_DIR / "chroma_db"
COLLECTION_NAME = "catalogue_bureau"
EMBEDDING_MODEL = "text-embedding-3-small"

load_dotenv(BACKEND_DIR / ".env")


def _load_catalogue() -> dict:
    with open(DATA_DIR / "catalogue.json", encoding="utf-8") as f:
        return json.load(f)


def _finition_to_text(item: dict) -> str:
    styles = ", ".join(item["style_tags"])
    return f"Finition '{item['nom']}' (couleur {item['couleur_hex']}). Styles associés : {styles}."


def _plateau_to_text(item: dict) -> str:
    largeurs = ", ".join(str(l) for l in item["largeurs_disponibles_cm"])
    styles = ", ".join(item["style_tags"])
    return (
        f"Plateau '{item['nom']}', matériau {item['materiau']}, profondeur {item['profondeur_cm']}cm, "
        f"largeurs disponibles : {largeurs} cm. Prix {item['prix_eur']}€. Styles associés : {styles}."
    )


def _structure_to_text(item: dict) -> str:
    styles = ", ".join(item["style_tags"])
    return (
        f"Structure '{item['nom']}', moteur {item['moteur']}, hauteur réglable de "
        f"{item['hauteur_min_cm']}cm à {item['hauteur_max_cm']}cm, charge max {item['charge_max_kg']}kg, "
        f"largeur max compatible {item['largeur_max_compatible_cm']}cm. Prix {item['prix_eur']}€. "
        f"Styles associés : {styles}."
    )


def _accessoire_to_text(item: dict) -> str:
    return f"Accessoire '{item['nom']}' (type {item['type']}). Prix {item['prix_eur']}€."


def build_documents(catalogue: dict) -> list[Document]:
    documents: list[Document] = []
    for item in catalogue["finitions"]:
        documents.append(Document(page_content=_finition_to_text(item), metadata={"categorie": "finition", "id": item["id"]}))
    for item in catalogue["plateaux"]:
        documents.append(Document(page_content=_plateau_to_text(item), metadata={"categorie": "plateau", "id": item["id"]}))
    for item in catalogue["structures"]:
        documents.append(Document(page_content=_structure_to_text(item), metadata={"categorie": "structure", "id": item["id"]}))
    for item in catalogue["accessoires"]:
        documents.append(Document(page_content=_accessoire_to_text(item), metadata={"categorie": "accessoire", "id": item["id"]}))
    return documents


def index_catalogue() -> Chroma:
    catalogue = _load_catalogue()
    documents = build_documents(catalogue)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # Idempotent : on repart d'une collection vide à chaque exécution, pour ne pas
    # accumuler des doublons quand le script est relancé après une modif du catalogue.
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION_NAME)

    return Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
    )


if __name__ == "__main__":
    store = index_catalogue()
    print(f"Indexé {store._collection.count()} documents dans la collection '{COLLECTION_NAME}' ({CHROMA_DIR})")
