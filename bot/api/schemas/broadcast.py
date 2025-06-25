from pydantic import BaseModel


class Broadcast(BaseModel):
    title: str
    message: str
