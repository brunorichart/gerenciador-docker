
from pydantic import BaseModel, Field
from typing import Optional


class ContainerCreate(BaseModel):

    image: str = Field(
        min_length=1,
        description="Nome da imagem Docker"
    )

    name: str = Field(
        min_length=1,
        description="Nome do container"
    )

    ports: Optional[dict[str, int]] = None

    environment: Optional[dict[str, str]] = None

    detach: bool = True

    restart_policy: Optional[str] = "no"


class ContainerResponse(BaseModel):

    id: str
    name: str
    image: str
    status: str
