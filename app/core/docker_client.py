
import docker
from docker.errors import DockerException


class DockerClient:

    _client = None

    @classmethod
    def get_client(cls):

        if cls._client is None:
            try:
                cls._client = docker.from_env()

                # Verifica se o Docker está acessível
                cls._client.ping()

            except DockerException as error:
                raise RuntimeError(
                    f"Não foi possível conectar ao Docker: {error}"
                )

        return cls._client
