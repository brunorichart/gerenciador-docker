
from app.core.docker_client import DockerClient


class ImageService:

    def __init__(self):
        self.client = DockerClient.get_client()

    def listar(self):

        images = self.client.images.list()

        return [
            {
                "id": image.short_id,
                "tags": image.tags,
                "size": image.attrs.get("Size")
            }
            for image in images
        ]

    def baixar(self, name):

        image = self.client.images.pull(name)

        return {
            "id": image.short_id,
            "tags": image.tags,
            "message": "Imagem baixada com sucesso"
        }

    def remover(self, image_id):

        self.client.images.remove(
            image=image_id,
            force=False
        )

        return {
            "message": "Imagem removida com sucesso"
        }
