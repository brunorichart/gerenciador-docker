
from fastapi import APIRouter, HTTPException, Query
from docker.errors import NotFound, APIError, DockerException

from app.services.container_service import ContainerService
from app.schemas.container import ContainerCreate

router = APIRouter(
    prefix="/containers",
    tags=["Containers"]
)


def get_service():
    try:
        return ContainerService()
    except Exception as error:
        raise HTTPException(status_code=503, detail=str(error))


def execute(operation):
    try:
        return operation()
    except NotFound:
        raise HTTPException(
            status_code=404,
            detail="Container não encontrado"
        )
    except APIError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )
    except DockerException as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )


@router.get("/")
def listar_containers(all: bool = True):

    service = get_service()
    return execute(lambda: service.listar(all))


@router.get("/{container_id}")
def buscar_container(container_id: str):

    service = get_service()
    return execute(lambda: service.buscar(container_id))


@router.post("/", status_code=201)
def criar_container(data: ContainerCreate):

    service = get_service()
    return execute(lambda: service.criar(data))


@router.post("/{container_id}/start")
def iniciar_container(container_id: str):

    service = get_service()
    return execute(lambda: service.iniciar(container_id))


@router.post("/{container_id}/stop")
def parar_container(container_id: str):

    service = get_service()
    return execute(lambda: service.parar(container_id))


@router.post("/{container_id}/restart")
def reiniciar_container(container_id: str):

    service = get_service()
    return execute(lambda: service.reiniciar(container_id))


@router.delete("/{container_id}")
def remover_container(container_id: str):

    service = get_service()
    return execute(lambda: service.remover(container_id))


@router.get("/{container_id}/logs")
def consultar_logs(
    container_id: str,
    tail: int = Query(default=100, ge=1, le=10000)
):

    service = get_service()
    return execute(lambda: service.logs(container_id, tail))


@router.get("/{container_id}/stats")
def consultar_estatisticas(container_id: str):

    service = get_service()
    return execute(lambda: service.estatisticas(container_id))
