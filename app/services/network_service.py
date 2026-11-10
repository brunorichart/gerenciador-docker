
import ipaddress
import re
import socket

from app.core.docker_client import DockerClient


def get_host_addresses():

    addresses = set()
    for result in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
        address = result[4][0]
        if not ipaddress.ip_address(address).is_loopback:
            addresses.add(address)
    return sorted(addresses)


class NetworkService:

    def __init__(self):
        self.client = DockerClient.get_client()

    def listar(self):

        networks = self.client.networks.list()
        containers = self.client.containers.list(all=True)
        host_addresses = get_host_addresses()

        return [
            {
                "id": network.short_id,
                "name": network.name,
                "driver": network.attrs.get("Driver"),
                "subnet": self._network_ipam_value(network, "Subnet"),
                "gateway": self._network_ipam_value(network, "Gateway"),
                "host_addresses": host_addresses,
                "containers": self._network_containers(network, containers)
            }
            for network in networks
        ]

    @staticmethod
    def _network_ipam_value(network, key):

        configurations = network.attrs.get("IPAM", {}).get("Config") or []
        return next((config.get(key) for config in configurations if config.get(key)), None)

    @staticmethod
    def _network_containers(network, containers):

        members = []
        for container in containers:
            endpoint = container.attrs.get("NetworkSettings", {}).get("Networks", {}).get(network.name)
            if endpoint and (endpoint.get("NetworkID") or endpoint.get("EndpointID")):
                members.append({
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                    "ipv4_address": endpoint.get("IPAddress") or None,
                    "aliases": endpoint.get("Aliases") or []
                })
        return members

    def host_addresses(self):

        return {"addresses": get_host_addresses()}

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

    def conectar(self, network_id, container_id):

        network = self.client.networks.get(network_id)
        container = self.client.containers.get(container_id)
        network.connect(container, aliases=[container.name])
        return {"message": f"Container {container.name} conectado à rede {network.name}"}

    def desconectar(self, network_id, container_id):

        network = self.client.networks.get(network_id)
        container = self.client.containers.get(container_id)
        network.disconnect(container)
        return {"message": f"Container {container.name} desconectado da rede {network.name}"}

    def ping(self, network_id, source_container_id, target):

        network = self.client.networks.get(network_id)
        container = self.client.containers.get(source_container_id)
        container.reload()
        if container.status != "running":
            raise ValueError("O container escolhido precisa estar em execução.")

        endpoint = container.attrs.get("NetworkSettings", {}).get("Networks", {}).get(network.name)
        if not endpoint or not (endpoint.get("NetworkID") or endpoint.get("EndpointID")):
            raise ValueError("Conecte o container à rede antes de testar o ping.")

        destination = target.strip()
        if not self._is_valid_ping_target(destination):
            raise ValueError("Informe um endereço IPv4, IPv6 ou nome de máquina válido.")

        result = container.exec_run(
            ["ping", "-c", "4", "-W", "2", "-w", "10", destination],
            demux=True
        )
        stdout, stderr = result.output or (None, None)
        output = b"".join(part for part in (stdout, stderr) if part)
        if result.exit_code == 127 and b"ping" in output.lower():
            raise ValueError("A imagem deste container não inclui o comando ping. Escolha outra origem ou instale iputils-ping no container.")
        return {
            "exit_code": result.exit_code,
            "output": output.decode("utf-8", errors="replace")[-16384:]
        }

    @staticmethod
    def _is_valid_ping_target(target):

        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            pass

        if len(target) > 253:
            return False
        labels = target.rstrip(".").split(".")
        return all(
            label and len(label) <= 63 and re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?", label)
            for label in labels
        )

    def remover(self, network_id):

        network = self.client.networks.get(network_id)
        network.remove()

        return {
            "message": "Rede removida com sucesso"
        }
