
from fastapi import APIRouter, HTTPException
from docker.errors import NotFound, APIError, DockerException

from app.services.network_service import NetworkService
from app.schemas.network import NetworkCreate

router = APIRouter(
    prefix="/networks",
    tags=["Networks"]
)


def execute(operation):
    try:
        return operation()
    except NotFound:
        raise HTTPException(status_code=404, detail="Rede não encontrada")
    except APIError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except DockerException as error:
        raise HTTPException(status_code=503, detail=str(error))


@router.get("/")
def listar_redes():

    service = NetworkService()
    return execute(service.listar)


@router.post("/", status_code=201)
def criar_rede(data: NetworkCreate):

    service = NetworkService()
    return execute(lambda: service.criar(data))


@router.delete("/{network_id}")
def remover_rede(network_id: str):

    service = NetworkService()
    return execute(lambda: service.remover(network_id))
