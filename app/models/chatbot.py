from pydantic import BaseModel


class ChatBot(BaseModel):
    prompt: str
    max_tokens: int = 100