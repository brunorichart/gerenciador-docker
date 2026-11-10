from fastapi import APIRouter

from app.services.machine_service import get_machine_info

router = APIRouter(
    prefix="/machine",
    tags=["Machine"]
)


@router.get("/")
def consultar_maquina():

    return get_machine_info()