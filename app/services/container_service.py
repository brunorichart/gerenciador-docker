
from app.core.docker_client import DockerClient


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
                "status": container.status
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

        container = self.client.containers.run(
            image=data.image,
            name=data.name,
            ports=data.ports,
            environment=data.environment,
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
