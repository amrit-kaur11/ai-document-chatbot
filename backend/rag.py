# rag.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ---------------- CONFIG ----------------
CHROMA_PATH = "chroma"
COLLECTION_NAME = "docs"
TOP_K = 3
# ----------------------------------------

client = chromadb.Client(
    Settings(
        persist_directory=CHROMA_PATH,
        anonymized_telemetry=False
    )
)

model = SentenceTransformer("all-MiniLM-L6-v2")


def _get_or_create_collection(name: str):
    try:
        return client.get_or_create_collection(name=name)
    except Exception:
        pass
    try:
        return client.get_collection(name=name)
    except Exception:
        pass
    try:
        return client.create_collection(name=name)
    except Exception as e:
        raise RuntimeError(f"Could not access collection: {e}")


def retrieve(query: str):
    """
    Return a list of document strings most similar to `query`.
    Returns empty list if nothing found or collection missing.
    """
    try:
        collection = _get_or_create_collection(COLLECTION_NAME)
    except Exception:
        return []

    # compute embedding for query
    try:
        query_embedding = model.encode([query]).tolist()
    except Exception:
        return []

    try:
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=TOP_K
        )
    except Exception:
        return []

    # Chroma may return nested lists; normalize to list of strings
    docs = results.get("documents", [[]])
    if isinstance(docs, list) and len(docs) > 0:
        return docs[0]
    return []
