
from fastapi import APIRouter, HTTPException
from docker.errors import NotFound, APIError, DockerException

from app.services.network_service import NetworkService
from app.schemas.network import NetworkConnect, NetworkCreate, NetworkPing

router = APIRouter(
    prefix="/networks",
    tags=["Networks"]
)


def execute(operation):
    try:
        return operation()
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
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


@router.get("/host-addresses")
def listar_enderecos_da_maquina():

    service = NetworkService()
    return execute(service.host_addresses)


@router.post("/", status_code=201)
def criar_rede(data: NetworkCreate):

    service = NetworkService()
    return execute(lambda: service.criar(data))


@router.post("/{network_id}/connect")
def conectar_container(network_id: str, data: NetworkConnect):

    service = NetworkService()
    return execute(lambda: service.conectar(network_id, data.container_id))


@router.post("/{network_id}/ping")
def testar_ping(network_id: str, data: NetworkPing):

    service = NetworkService()
    return execute(lambda: service.ping(network_id, data.source_container_id, data.target))


@router.delete("/{network_id}/containers/{container_id}")
def desconectar_container(network_id: str, container_id: str):

    service = NetworkService()
    return execute(lambda: service.desconectar(network_id, container_id))


@router.delete("/{network_id}")
def remover_rede(network_id: str):

    service = NetworkService()
    return execute(lambda: service.remover(network_id))
