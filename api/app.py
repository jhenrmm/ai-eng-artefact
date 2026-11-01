from threading import Lock

from fastapi import FastAPI, HTTPException

from config import PDF_PATH
from schemas import ChatRequest, ChatResponse
from service.ingestion import ingest
from service.ollama import OllamaError
from service.rag import answer

app = FastAPI(
    title="Empório da Música",
    description="Customer service agent for Empório da Música.",
)

_index = None
_index_lock = Lock()

_conversations: dict[int, list[dict]] = {}
_conversations_lock = Lock()
_next_conversation_id = 1


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
    global _next_conversation_id

    chunks, vector_store = get_index()

    with _conversations_lock:
        if req.conversation_id is None:
            conversation_id = _next_conversation_id
            _next_conversation_id += 1
            history = []
        else:
            conversation_id = req.conversation_id
            history = _conversations.get(conversation_id)
            if history is None:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found.",
                )
            history = list(history)

    try:
        reply = answer(req.message, chunks, vector_store, history=history)
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    with _conversations_lock:
        _conversations[conversation_id] = [
            *history,
            {"role": "user", "content": req.message},
            {"role": "assistant", "content": reply},
        ]

    return ChatResponse(
        conversation_id=conversation_id,
        message=reply,
    )
