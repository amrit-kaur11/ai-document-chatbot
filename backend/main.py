# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ingest import ingest
from rag import retrieve
from llm import generate
from memory import get_memory, add_message

app = FastAPI()

# -- CORS: for local dev allow everything (safe to change to specific origins later) --
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # <-- set to specific origins when deploying
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DocRequest(BaseModel):
    url: str

class ChatRequest(BaseModel):
    session_id: str
    question: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
def ingest_doc(data: DocRequest):
    try:
        count = ingest(data.url)
        return {"status": "success", "chunks": count}
    except ValueError as e:
        # Known / expected errors (e.g. "Google Doc must be public")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected server error - return message to frontend
        raise HTTPException(status_code=500, detail=f"Ingest failed: {e}")

@app.post("/chat")
def chat(data: ChatRequest):
    try:
        history = get_memory(data.session_id)
        chunks = retrieve(data.question)

        context = "\n\n".join(chunks)

        prompt = f"""
You are a document-based assistant.
Answer ONLY from the document below.
Always cite sections like [Chunk 2].
If not found, say: "This info isn't in the document."

Document:
{context}

Conversation history:
{history}

Question:
{data.question}
"""

        answer = generate(prompt)

        add_message(data.session_id, "user", data.question)
        add_message(data.session_id, "assistant", answer)

        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")
