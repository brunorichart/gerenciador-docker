import platform
import socket

import psutil

from app.services.network_service import get_host_addresses


def get_machine_info():

    memory = psutil.virtual_memory()
    disks = []
    for partition in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except (PermissionError, OSError):
            continue
        disks.append({
            "device": partition.device,
            "mountpoint": partition.mountpoint,
            "filesystem": partition.fstype or "unknown",
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "used_percent": usage.percent,
        })

    return {
        "hostname": socket.gethostname(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "Não identificado",
        "cpu_count": psutil.cpu_count(logical=False) or psutil.cpu_count() or 0,
        "cpu_logical_count": psutil.cpu_count(logical=True) or 0,
        "cpu_percent": psutil.cpu_percent(interval=0.25),
        "memory": {
            "total_bytes": memory.total,
            "available_bytes": memory.available,
            "used_bytes": memory.used,
            "used_percent": memory.percent,
        },
        "disks": disks,
        "ip_addresses": get_host_addresses(),
    }