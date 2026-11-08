
from fastapi import APIRouter, HTTPException
from docker.errors import NotFound, APIError, DockerException

from app.services.image_service import ImageService
from app.schemas.image import ImagePull

router = APIRouter(
    prefix="/images",
    tags=["Images"]
)


def execute(operation):
    try:
        return operation()
    except NotFound:
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    except APIError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except DockerException as error:
        raise HTTPException(status_code=503, detail=str(error))


@router.get("/")
def listar_imagens():

    service = ImageService()
    return execute(service.listar)


@router.post("/pull")
def baixar_imagem(data: ImagePull):

    service = ImageService()
    return execute(lambda: service.baixar(data.name))


@router.delete("/{image_id}")
def remover_imagem(image_id: str):

    service = ImageService()
    return execute(lambda: service.remover(image_id))
