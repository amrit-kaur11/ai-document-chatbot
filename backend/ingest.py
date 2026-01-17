# ingest.py
import requests
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os

# ---------------- CONFIG ----------------
CHROMA_PATH = "chroma"
COLLECTION_NAME = "docs"
CHUNK_SIZE = 700
# ----------------------------------------

# Chromadb client (persist folder)
client = chromadb.Client(
    Settings(
        persist_directory=CHROMA_PATH,
        anonymized_telemetry=False
    )
)

# SentenceTransformer (kept global so model is loaded once)
# If startup is slow, consider lazy-loading inside ingest()
model = SentenceTransformer("all-MiniLM-L6-v2")


def download_google_doc(url: str) -> str:
    # Expects a standard google docs share link with /d/<id>/
    try:
        doc_id = url.split("/d/")[1].split("/")[0]
    except Exception:
        raise ValueError("Invalid Google Doc URL format.")

    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"

    response = requests.get(export_url, timeout=15)
    if response.status_code != 200:
        raise ValueError("Google Doc must be public and accessible. (status_code=%s)" % response.status_code)

    return response.text


def chunk_text(text: str):
    words = text.split()
    chunks = []
    for i in range(0, len(words), CHUNK_SIZE):
        chunks.append(" ".join(words[i:i + CHUNK_SIZE]))
    return chunks


def _get_or_create_collection(name: str):
    # Try various common chromadb APIs for compatibility across versions
    try:
        return client.get_or_create_collection(name=name)
    except Exception:
        pass

    try:
        # older/newer variants
        return client.get_collection(name=name)
    except Exception:
        pass

    try:
        return client.create_collection(name=name)
    except Exception as e:
        raise RuntimeError(f"Could not get or create collection: {e}")


def ingest(url: str):
    """
    Ingest a public Google Doc URL into Chroma collection.
    Returns number of chunks added (int).
    Raises ValueError for user-facing problems (bad URL / not public).
    Raises other Exceptions for unexpected failures.
    """

    # Download and chunk first (so we fail early before touching DB)
    text = download_google_doc(url)
    chunks = chunk_text(text)
    if len(chunks) == 0:
        raise ValueError("Document contains no text.")

    # Reset / delete old collection if present (safe reset)
    try:
        # Try client API variants
        if hasattr(client, "delete_collection"):
            client.delete_collection(name=COLLECTION_NAME)
        elif hasattr(client, "reset"):
            # older api fallback (no-op usually)
            client.reset()
        else:
            # delete persist folder as last resort (careful)
            if os.path.exists(CHROMA_PATH):
                # do not delete automatically; let user decide in worst-case
                pass
    except Exception:
        # ignore deletion failures; we'll try to get/create a fresh collection
        pass

    # get/create collection in a compatible way
    collection = _get_or_create_collection(COLLECTION_NAME)

    # Compute embeddings
    # model.encode returns numpy arrays - convert to list for chroma
    embeddings = model.encode(chunks).tolist()
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    # Add to collection
    try:
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids
        )
    except Exception as e:
        raise RuntimeError(f"Failed to add documents to collection: {e}")

    return len(chunks)
