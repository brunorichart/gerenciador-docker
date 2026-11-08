
from pydantic import BaseModel, Field


class NetworkCreate(BaseModel):

    name: str = Field(min_length=1)
    driver: str = "bridge"
