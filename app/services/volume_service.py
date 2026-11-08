
from app.core.docker_client import DockerClient


class VolumeService:

    def __init__(self):
        self.client = DockerClient.get_client()

    def listar(self):

        volumes = self.client.volumes.list()

        return [
            {
                "name": volume.name,
                "driver": volume.attrs.get("Driver"),
                "mountpoint": volume.attrs.get("Mountpoint")
            }
            for volume in volumes
        ]

    def criar(self, data):

        volume = self.client.volumes.create(
            name=data.name,
            driver=data.driver
        )

        return {
            "name": volume.name,
            "message": "Volume criado com sucesso"
        }

    def remover(self, name):

        volume = self.client.volumes.get(name)
        volume.remove(force=False)

        return {
            "message": "Volume removido com sucesso"
        }
