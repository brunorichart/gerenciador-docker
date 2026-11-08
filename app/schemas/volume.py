
from pydantic import BaseModel, Field


class VolumeCreate(BaseModel):

    name: str = Field(min_length=1)
    driver: str = "local"
