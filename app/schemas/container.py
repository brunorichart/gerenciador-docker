
from pydantic import BaseModel, Field
from typing import Literal, Optional


class VolumeMount(BaseModel):

    kind: Literal["volume", "bind"] = "volume"
    source: str = Field(min_length=1, description="Nome do volume ou pasta no computador")
    target: str = Field(min_length=1, pattern=r"^/", description="Pasta de destino dentro do container")
    read_only: bool = False
    copy_initial_data: bool = False


class ContainerCommand(BaseModel):

    command: str = Field(min_length=1, max_length=4096)
    shell: Literal["/bin/sh", "/bin/bash", "cmd.exe"] = "/bin/sh"


class PackageInstall(BaseModel):

    tools: list[Literal[
        "ping",
        "vim",
        "curl",
        "ssh-client",
        "ssh-server",
        "wget",
        "git",
        "process-tools",
        "dns-tools"
    ]] = Field(min_length=1, max_length=9)


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

    volume: Optional[VolumeMount] = None

    detach: bool = True

    restart_policy: Optional[str] = "no"


class ContainerResponse(BaseModel):

    id: str
    name: str
    image: str
    status: str
