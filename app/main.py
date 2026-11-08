
from fastapi import FastAPI

from app.routes import containers
from app.routes import image
from app.routes import volume
from app.routes import networks


app = FastAPI(
    title="Docker Manager API",
    description="API para gerenciamento de recursos Docker",
    version="1.0.0"
)


# Registrar rotas
app.include_router(containers.router, prefix="/api")
app.include_router(image.router, prefix="/api")
app.include_router(volume.router, prefix="/api")
app.include_router(networks.router, prefix="/api")


@app.get("/", tags=["Home"])
def home():

    return {
        "application": "Docker Manager API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
def health():

    from app.core.docker_client import DockerClient

    try:
        client = DockerClient.get_client()

        return {
            "api": "online",
            "docker": "online",
            "docker_version": client.version()["Version"]
        }

    except Exception as error:

        return {
            "api": "online",
            "docker": "offline",
            "error": str(error)
        }
