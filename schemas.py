from pydantic import BaseModel, Field

from config import CHAT_MAX_MESSAGE_CHARS


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=CHAT_MAX_MESSAGE_CHARS)
    conversation_id: int | None = Field(default=None, ge=1)


class ChatResponse(BaseModel):
    conversation_id: int
    message: str

