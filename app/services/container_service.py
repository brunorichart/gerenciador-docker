
import shutil
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path, PurePosixPath

from app.core.docker_client import DockerClient
from docker.errors import NotFound
from docker.types import Mount


def mapear_portas_publicadas(ports):

    published = []
    for container_port, bindings in (ports or {}).items():
        for binding in bindings or []:
            if binding.get("HostPort"):
                port, protocol = container_port.split("/", 1)
                published.append({
                    "container_port": int(port),
                    "host_port": int(binding["HostPort"]),
                    "protocol": protocol,
                    "host_ip": binding.get("HostIp", "0.0.0.0")
                })
    return published


class ContainerService:

    def __init__(self):
        self.client = DockerClient.get_client()

    def listar(self, all=True):

        containers = self.client.containers.list(all=all)

        return [
            {
                "id": container.short_id,
                "name": container.name,
                "image": container.image.tags,
                "status": container.status,
                "ports": mapear_portas_publicadas(
                    container.attrs.get("NetworkSettings", {}).get("Ports", {})
                )
            }
            for container in containers
        ]

    def buscar(self, container_id):

        container = self.client.containers.get(container_id)

        container.reload()

        return {
            "id": container.id,
            "name": container.name,
            "image": container.image.tags,
            "status": container.status,
            "created": container.attrs.get("Created")
        }

    def criar(self, data):

        mounts = None
        if data.volume:
            if data.volume.kind == "volume":
                try:
                    self.client.volumes.get(data.volume.source)
                except NotFound:
                    self.client.volumes.create(name=data.volume.source)
            elif data.volume.copy_initial_data:
                self._copiar_arquivos_iniciais(data.image, data.volume.target, data.volume.source)

            mounts = [Mount(
                target=data.volume.target,
                source=data.volume.source,
                type=data.volume.kind,
                read_only=data.volume.read_only
            )]

        container = self.client.containers.run(
            image=data.image,
            name=data.name,
            ports=data.ports,
            environment=data.environment,
            mounts=mounts,
            detach=data.detach,
            restart_policy={
                "Name": data.restart_policy
            }
        )

        return {
            "id": container.short_id,
            "name": container.name,
            "status": container.status
        }

    def _copiar_arquivos_iniciais(self, image, target, source):

        host_path = Path(source)
        host_path.mkdir(parents=True, exist_ok=True)
        if not host_path.is_dir():
            raise ValueError("A origem do bind precisa ser uma pasta.")
        if any(host_path.iterdir()):
            return

        source_container = self.client.containers.create(
            image=image,
            command=["/bin/sh", "-c", "true"]
        )
        try:
            archive, _ = source_container.get_archive(target)
            archive_data = BytesIO(b"".join(archive))
            archive_directory = PurePosixPath(target.rstrip("/")).name
            with tempfile.TemporaryDirectory() as temporary_directory:
                with tarfile.open(fileobj=archive_data) as tar:
                    tar.extractall(temporary_directory, filter="data")
                image_path = Path(temporary_directory) / archive_directory
                if not image_path.is_dir():
                    raise ValueError("Não foi possível localizar os arquivos iniciais na imagem.")
                shutil.copytree(image_path, host_path, dirs_exist_ok=True, symlinks=True)
        finally:
            source_container.remove(force=True)

    def executar(self, container_id, data):

        container = self.client.containers.get(container_id)
        if data.shell == "cmd.exe":
            command = [data.shell, "/S", "/C", data.command]
        else:
            command = [data.shell, "-lc", data.command]

        result = container.exec_run(command, demux=True)
        stdout, stderr = result.output or (None, None)
        output = b"".join(part for part in (stdout, stderr) if part)

        return {
            "exit_code": result.exit_code,
            "output": output.decode("utf-8", errors="replace")[-65536:]
        }

    def iniciar(self, container_id):

        container = self.client.containers.get(container_id)
        container.start()

        return {"message": "Container iniciado com sucesso"}

    def parar(self, container_id):

        container = self.client.containers.get(container_id)
        container.stop()

        return {"message": "Container parado com sucesso"}

    def reiniciar(self, container_id):

        container = self.client.containers.get(container_id)
        container.restart()

        return {"message": "Container reiniciado com sucesso"}

    def remover(self, container_id):

        container = self.client.containers.get(container_id)
        container.remove(force=True)

        return {"message": "Container removido com sucesso"}

    def logs(self, container_id, tail=100):

        container = self.client.containers.get(container_id)

        logs = container.logs(
            tail=tail,
            timestamps=True
        )

        return {
            "logs": logs.decode("utf-8", errors="replace")
        }

    def estatisticas(self, container_id):

        container = self.client.containers.get(container_id)

        return container.stats(stream=False)
