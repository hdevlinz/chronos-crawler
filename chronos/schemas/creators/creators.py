from pydantic import BaseModel


class CreatorSchema(BaseModel):
    unique_id: str
