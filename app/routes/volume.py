
from fastapi import APIRouter, HTTPException
from docker.errors import NotFound, APIError, DockerException

from app.services.volume_service import VolumeService
from app.schemas.volume import VolumeCreate

router = APIRouter(
    prefix="/volumes",
    tags=["Volumes"]
)


def execute(operation):
    try:
        return operation()
    except NotFound:
        raise HTTPException(status_code=404, detail="Volume não encontrado")
    except APIError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except DockerException as error:
        raise HTTPException(status_code=503, detail=str(error))


@router.get("/")
def listar_volumes():

    service = VolumeService()
    return execute(service.listar)


@router.post("/", status_code=201)
def criar_volume(data: VolumeCreate):

    service = VolumeService()
    return execute(lambda: service.criar(data))


@router.delete("/{name}")
def remover_volume(name: str):

    service = VolumeService()
    return execute(lambda: service.remover(name))
