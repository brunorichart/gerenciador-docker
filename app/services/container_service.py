
import shutil
import re
import shlex
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path, PurePosixPath

from app.core.docker_client import DockerClient
from docker.errors import NotFound
from docker.types import Mount


PACKAGE_MAP = {
    "apt": {
        "ping": "iputils-ping", "vim": "vim", "curl": "curl",
        "ssh-client": "openssh-client", "ssh-server": "openssh-server",
        "wget": "wget", "git": "git", "process-tools": "procps", "dns-tools": "dnsutils",
    },
    "apk": {
        "ping": "iputils", "vim": "vim", "curl": "curl",
        "ssh-client": "openssh-client", "ssh-server": "openssh-server",
        "wget": "wget", "git": "git", "process-tools": "procps", "dns-tools": "bind-tools",
    },
    "dnf": {
        "ping": "iputils", "vim": "vim-enhanced", "curl": "curl",
        "ssh-client": "openssh-clients", "ssh-server": "openssh-server",
        "wget": "wget", "git": "git", "process-tools": "procps-ng", "dns-tools": "bind-utils",
    },
    "yum": {
        "ping": "iputils", "vim": "vim-enhanced", "curl": "curl",
        "ssh-client": "openssh-clients", "ssh-server": "openssh-server",
        "wget": "wget", "git": "git", "process-tools": "procps-ng", "dns-tools": "bind-utils",
    },
}


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
            shell_command = data.command
            if self._is_ping_command(shell_command):
                shell_command = self._limitar_ping(shell_command)
            command = [data.shell, "-lc", shell_command]

        result = container.exec_run(command, demux=True)
        stdout, stderr = result.output or (None, None)
        output = b"".join(part for part in (stdout, stderr) if part)

        return {
            "exit_code": result.exit_code,
            "output": output.decode("utf-8", errors="replace")[-65536:]
        }

    @staticmethod
    def _is_ping_command(command):

        match = re.match(r"^\s*(?:/[\w./-]+/)?ping(?:\s|$)", command)
        return bool(match)

    @staticmethod
    def _limitar_ping(command):

        parts = shlex.split(command)
        if not parts:
            return command

        limited_parts = [parts[0]]
        index = 1
        while index < len(parts):
            part = parts[index]
            if part == "-c":
                index += 2
                continue
            if part.startswith("-c") and part[2:].isdigit():
                index += 1
                continue
            if part in {"-w", "-W"}:
                index += 2
                continue
            if (part.startswith("-w") or part.startswith("-W")) and part[2:].isdigit():
                index += 1
                continue
            limited_parts.append(part)
            index += 1

        limited_parts[0:1] = [parts[0], "-c", "4", "-W", "2", "-w", "10"]
        return shlex.join(limited_parts)

    def instalar_ferramentas(self, container_id, tools):

        container = self.client.containers.get(container_id)
        script = self._build_package_install_script(tools)
        result = container.exec_run(
            ["/bin/sh", "-lc", script],
            user="0",
            demux=True
        )
        stdout, stderr = result.output or (None, None)
        output = b"".join(part for part in (stdout, stderr) if part)
        return {
            "exit_code": result.exit_code,
            "output": output.decode("utf-8", errors="replace")[-65536:]
        }

    @staticmethod
    def _build_package_install_script(tools):

        tool_names = list(dict.fromkeys(tools))
        manager_branches = []
        for manager, package_map in PACKAGE_MAP.items():
            packages = sorted({package_map[tool] for tool in tool_names})
            package_list = shlex.join(packages)
            if manager == "apt":
                install = f"apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends {package_list}"
            elif manager == "apk":
                install = f"apk add --no-cache {package_list}"
            else:
                install = f"{manager} install -y {package_list}"
            keyword = "if" if not manager_branches else "elif"
            detector = "apt-get" if manager == "apt" else manager
            manager_branches.append(f"{keyword} command -v {detector} >/dev/null 2>&1; then\n    {install}")
        script = "\n".join(manager_branches)
        script += "\nelse\n    printf '%s\\n' 'Nenhum gerenciador de pacotes compatível encontrado.' >&2\n    exit 127\nfi"
        return script

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
