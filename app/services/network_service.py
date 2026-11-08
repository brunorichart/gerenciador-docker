
from app.core.docker_client import DockerClient


class NetworkService:

    def __init__(self):
        self.client = DockerClient.get_client()

    def listar(self):

        networks = self.client.networks.list()

        return [
            {
                "id": network.short_id,
                "name": network.name,
                "driver": network.attrs.get("Driver")
            }
            for network in networks
        ]

    def criar(self, data):

        network = self.client.networks.create(
            name=data.name,
            driver=data.driver
        )

        return {
            "id": network.short_id,
            "name": network.name,
            "message": "Rede criada com sucesso"
        }

    def remover(self, network_id):

        network = self.client.networks.get(network_id)
        network.remove()

        return {
            "message": "Rede removida com sucesso"
        }
