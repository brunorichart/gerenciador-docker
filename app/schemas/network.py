
from pydantic import BaseModel, Field


class NetworkCreate(BaseModel):

    name: str = Field(min_length=1)
    driver: str = "bridge"


class NetworkConnect(BaseModel):

    container_id: str = Field(min_length=1)


class NetworkPing(BaseModel):

    source_container_id: str = Field(min_length=1)
    target: str = Field(min_length=1, max_length=253)
