from pydantic import BaseModel


class PostCreate(BaseModel):
    id : int 
    title: str
    content: str


