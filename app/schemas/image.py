
from pydantic import BaseModel, Field


class ImagePull(BaseModel):

    name: str = Field(
        min_length=1,
        description="Nome da imagem"
    )
