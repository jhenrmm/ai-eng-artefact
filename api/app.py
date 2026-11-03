from threading import Lock

from fastapi import FastAPI, HTTPException, Path

from config import PDF_PATH
from schemas import ChatRequest, ChatResponse, ConversationResponse
from service.database import (
    ConversationNotFoundError,
    DatabaseError,
    get_history,
    save_exchange,
)
from service.ingestion import ingest
from service.ollama import OllamaError
from service.rag import answer


app = FastAPI(
    title="Empório da Música",
    description="Customer service agent for Empório da Música.",
)

_index = None
_index_lock = Lock()


def get_index():
    global _index
    if _index is None:
        with _index_lock:
            if _index is None:
                _index = ingest(PDF_PATH)
    return _index


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def send_message(req: ChatRequest):
    try:
        history = (
            get_history(req.conversation_id)
            if req.conversation_id is not None
            else []
        )
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if history is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    chunks, vector_store = get_index()

    try:
        reply = answer(req.message, chunks, vector_store, history=history)
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        conversation_id = save_exchange(
            req.conversation_id,
            req.message,
            reply,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        ) from exc
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatResponse(
        conversation_id=conversation_id,
        message=reply,
    )


@app.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(conversation_id: int = Path(ge=1)):
    try:
        history = get_history(conversation_id)
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if history is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return ConversationResponse(
        conversation_id=conversation_id,
        messages=history,
    )
