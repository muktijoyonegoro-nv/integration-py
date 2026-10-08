"""Resource monitoring and container telemetry collector."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from harness.config import load_config
from harness.env.podman import setup_podman_environment

logger = logging.getLogger(__name__)


def parse_human_bytes(s: str) -> int:
    """Parses human strings like '4.231MB', '3.793GB', '388.5kB', '10 B' into raw bytes."""
    s = s.strip()
    if not s or s == "--":
        return 0

    units = [
        ("GiB", 1024 * 1024 * 1024),
        ("GB", 1000 * 1000 * 1000),
        ("MiB", 1024 * 1024),
        ("MB", 1000 * 1000),
        ("KiB", 1024),
        ("kB", 1000),
        ("KB", 1000),
        ("B", 1),
    ]

    for suffix, factor in units:
        if s.endswith(suffix):
            num_str = s[: -len(suffix)].strip()
            try:
                return int(float(num_str) * factor)
            except ValueError:
                pass

    try:
        return int(float(s))
    except ValueError:
        return 0


def format_bytes(b: int) -> str:
    """Formats raw bytes into human readable binary units."""
    if b < 0:
        return "-" + format_bytes(-b)
    unit = 1024
    if b < unit:
        return f"{b} B"
    div = unit
    exp = 0
    units = ["KiB", "MiB", "GiB", "TiB"]
    while b / div >= unit and exp < len(units) - 1:
        div *= unit
        exp += 1
    return f"{b / div:.2f} {units[exp]}"


def format_duration(seconds: float) -> str:
    """Formats elapsed seconds into minutes and seconds."""
    if seconds >= 60:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}m {s:.2f}s"
    return f"{seconds:.2f}s"


def extract_image_short_name(image: str) -> str:
    """Extracts clean base name (e.g. 'docker.io/library/redis:7-alpine' -> 'redis')."""
    image = image.strip()
    if not image:
        return "container"

    if "@" in image:
        image = image.split("@", 1)[0]

    base = image.split("/")[-1]
    if ":" in base:
        base = base.split(":", 1)[0]

    if base.startswith("cp-"):
        base = base[3:]

    return base.lower()


@dataclass
class ContainerInfo:
    id: str
    name: str
    image: str
    short_name: str
    service: str = ""
    run_id: str = ""


class ContainerMetrics:
    """Tracks aggregated container resource metrics over time."""

    def __init__(self, run_id: Optional[str] = None) -> None:
        self.lock = threading.Lock()
        self.run_id = run_id
        self.containers: Dict[str, ContainerInfo] = {}
        self.ignored_container_ids: set[str] = set()
        self.peak_container_mem: Dict[str, int] = {}
        self.peak_total_mem_bytes: int = 0
        self.peak_total_cpu: float = 0.0
        self.latest_net_rx_bytes: int = 0
        self.latest_net_tx_bytes: int = 0
        self.latest_block_read: int = 0
        self.latest_block_write: int = 0
        self.peak_concurrent_pids: int = 0

    def update(self, entries: List[dict], podman_bin: str, podman_url: str) -> None:
        with self.lock:
            current_total_mem = 0
            current_total_cpu = 0.0
            current_total_pids = 0
            total_net_rx = 0
            total_net_tx = 0
            total_block_read = 0
            total_block_write = 0

            for e in entries:
                cid = str(e.get("id", "") or e.get("name", "")).strip()
                if not cid:
                    continue

                if cid in self.ignored_container_ids:
                    continue

                if cid not in self.containers:
                    img, svc, container_run_id = self._inspect_container(
                        podman_bin, podman_url, cid
                    )
                    if self.run_id and container_run_id != self.run_id:
                        self.ignored_container_ids.add(cid)
                        continue
                    short_name = extract_image_short_name(img) or extract_image_short_name(
                        e.get("name", "")
                    )
                    self.containers[cid] = ContainerInfo(
                        id=cid,
                        name=e.get("name", ""),
                        image=img,
                        short_name=short_name,
                        service=svc,
                        run_id=container_run_id,
                    )

                # Memory: "4.231MB / 3.793GB"
                mem_usage = str(e.get("mem_usage", ""))
                if " / " in mem_usage:
                    used_str = mem_usage.split(" / ")[0]
                    mem_bytes = parse_human_bytes(used_str)
                    current_total_mem += mem_bytes
                    if mem_bytes > self.peak_container_mem.get(cid, 0):
                        self.peak_container_mem[cid] = mem_bytes

                # CPU: "0.18%"
                cpu_str = str(e.get("cpu_percent", "")).rstrip("%").strip()
                try:
                    current_total_cpu += float(cpu_str)
                except ValueError:
                    pass

                # PIDs
                pids_str = str(e.get("pids", "")).strip()
                try:
                    current_total_pids += int(pids_str)
                except ValueError:
                    pass

                # Network I/O: "388.5kB / 318.7kB"
                net_io = str(e.get("net_io", ""))
                if " / " in net_io:
                    net_parts = net_io.split(" / ")
                    total_net_rx += parse_human_bytes(net_parts[0])
                    total_net_tx += parse_human_bytes(net_parts[1])

                # Block I/O: "11.42MB / 56.3MB"
                block_io = str(e.get("block_io", ""))
                if " / " in block_io:
                    blk_parts = block_io.split(" / ")
                    total_block_read += parse_human_bytes(blk_parts[0])
                    total_block_write += parse_human_bytes(blk_parts[1])

            if current_total_mem > self.peak_total_mem_bytes:
                self.peak_total_mem_bytes = current_total_mem
            if current_total_cpu > self.peak_total_cpu:
                self.peak_total_cpu = current_total_cpu
            if current_total_pids > self.peak_concurrent_pids:
                self.peak_concurrent_pids = current_total_pids
            if total_net_rx > self.latest_net_rx_bytes:
                self.latest_net_rx_bytes = total_net_rx
            if total_net_tx > self.latest_net_tx_bytes:
                self.latest_net_tx_bytes = total_net_tx
            if total_block_read > self.latest_block_read:
                self.latest_block_read = total_block_read
            if total_block_write > self.latest_block_write:
                self.latest_block_write = total_block_write

    def _inspect_container(
        self, podman_bin: str, podman_url: str, cid: str
    ) -> Tuple[str, str, str]:
        cmd = [podman_bin]
        if podman_url:
            cmd.extend(["--url", podman_url])
        cmd.extend(
            [
                "inspect",
                cid,
                "--format",
                '{{.Config.Image}}|{{index .Config.Labels "harness.service"}}|{{index .Config.Labels "harness.run_id"}}',
            ]
        )
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2.0)
            if res.returncode == 0:
                parts = res.stdout.strip().split("|")
                img = parts[0] if len(parts) > 0 else ""
                svc = parts[1] if len(parts) > 1 else ""
                run_id = parts[2] if len(parts) > 2 else ""
                return img, svc, run_id
        except Exception:
            pass
        return "", "", ""


def get_dir_size(path: Path | str) -> int:
    """Calculates total size of files under path excluding .git."""
    total = 0
    p = Path(path)
    for root, dirs, files in os.walk(p):
        if ".git" in dirs:
            dirs.remove(".git")
        for f in files:
            fp = Path(root) / f
            try:
                total += fp.stat().st_size
            except OSError:
                pass
    return total


def get_disk_free(path: Path | str) -> int:
    """Returns free disk space in bytes."""
    try:
        stat = os.statvfs(path)
        return stat.f_bavail * stat.f_frsize
    except Exception:
        return 0


def fetch_podman_df(podman_bin: str, podman_url: str) -> Tuple[int, bool]:
    """Fetches total disk usage reported by podman system df."""
    cmd = [podman_bin]
    if podman_url:
        cmd.extend(["--url", podman_url])
    cmd.extend(["system", "df", "--format", "json"])
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3.0)
        if res.returncode != 0:
            return 0, False
        data = json.loads(res.stdout)
        total = 0
        for entry in data:
            if entry.get("Type") in ("Containers", "Local Volumes", "Images"):
                total += int(entry.get("RawSize", 0))
        return total, True
    except Exception:
        return 0, False


def poll_podman_stats(podman_bin: str, podman_url: str) -> List[dict]:
    """Polls a single stats snapshot from podman stats --no-stream."""
    cmd = [podman_bin]
    if podman_url:
        cmd.extend(["--url", podman_url])
    cmd.extend(["stats", "--no-stream", "--format", "json"])
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=2.0)
        if res.returncode == 0 and res.stdout.strip():
            return json.loads(res.stdout)
    except Exception:
        pass
    return []
