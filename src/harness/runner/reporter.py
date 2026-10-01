"""Terminal reporting formatter for test-runner resource consumption."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

from harness.runner.monitor import (
    ContainerInfo,
    ContainerMetrics,
    format_bytes,
    format_duration,
)


@dataclass
class ReportData:
    command: str
    status: str
    duration_seconds: float
    peak_host_rss_bytes: int
    user_cpu_seconds: float
    sys_cpu_seconds: float
    podman_available: bool
    container_metrics: ContainerMetrics
    storage_delta_podman: int
    workspace_delta: int
    disk_free_delta: int


def print_report(d: ReportData) -> None:
    width = 80
    sep = "=" * width
    dash = "-" * width

    print()
    print(sep)
    print("TEST RUN RESOURCE CONSUMPTION REPORT".center(width))
    print(sep)
    print(f"  Status:            {d.status}")
    print(f"  Duration:          {format_duration(d.duration_seconds)}")
    print(f"  Command:           {d.command}")

    # Section 1: Host Process Tree
    print(dash)
    print("  HOST TEST RUNNER (Process Tree)")
    print(f"    Peak Memory (RSS):       {format_bytes(d.peak_host_rss_bytes)}")
    total_host_cpu = d.user_cpu_seconds + d.sys_cpu_seconds
    cpu_percent = 0.0
    if d.duration_seconds > 0:
        cpu_percent = (total_host_cpu / d.duration_seconds) * 100.0
    print(
        f"    CPU Time (User / Sys):   {format_duration(d.user_cpu_seconds)} / "
        f"{format_duration(d.sys_cpu_seconds)} (Total: {format_duration(total_host_cpu)})"
    )
    print(f"    Avg Host CPU Usage:      {cpu_percent:.1f}%")

    # Section 2: Containers
    print(dash)
    print("  CONTAINERS (Podman Workloads)")
    if not d.podman_available:
        print("    Podman not available or responsive during this run.")
    else:
        with d.container_metrics.lock:
            observed_count = len(d.container_metrics.containers)
            peak_total_mem = d.container_metrics.peak_total_mem_bytes
            peak_cpu = d.container_metrics.peak_total_cpu
            net_rx = d.container_metrics.latest_net_rx_bytes
            net_tx = d.container_metrics.latest_net_tx_bytes
            block_r = d.container_metrics.latest_block_read
            block_w = d.container_metrics.latest_block_write
            peak_pids = d.container_metrics.peak_concurrent_pids

            short_name_counts: Dict[str, int] = {}
            for info in d.container_metrics.containers.values():
                short_name_counts[info.short_name] = short_name_counts.get(info.short_name, 0) + 1

            items = []
            distinct_names = []
            name_idx_tracker: Dict[str, int] = {}

            for cid, info in d.container_metrics.containers.items():
                display_name = info.short_name
                if short_name_counts[info.short_name] > 1:
                    if info.service and info.service != info.short_name:
                        display_name = f"{info.short_name} ({info.service})"
                    else:
                        name_idx_tracker[info.short_name] = name_idx_tracker.get(info.short_name, 0) + 1
                        display_name = f"{info.short_name} (#{name_idx_tracker[info.short_name]})"

                peak_mem = d.container_metrics.peak_container_mem.get(cid, 0)
                items.append((display_name, peak_mem))
                distinct_names.append(display_name)

        if observed_count == 0:
            print("    No active containers observed during test run.")
        else:
            distinct_names.sort()
            items.sort(key=lambda x: x[1], reverse=True)

            print(f"    Containers Observed:     {observed_count} ({', '.join(distinct_names)})")
            print(f"    Peak Total Memory:       {format_bytes(peak_total_mem)}")
            for d_name, p_mem in items:
                if p_mem > 0:
                    lbl = (d_name + ":").ljust(22)
                    print(f"      └─ {lbl} {format_bytes(p_mem)}")
            print(f"    Peak Container CPU:      {peak_cpu:.1f}%")
            print(f"    Peak Concurrent PIDs:    {peak_pids}")
            print(f"    Network I/O (RX / TX):   {format_bytes(net_rx)} / {format_bytes(net_tx)}")
            print(f"    Block I/O (Read / Write): {format_bytes(block_r)} / {format_bytes(block_w)}")

    # Section 3: Disk & Storage Delta
    print(dash)
    print("  DISK & STORAGE DELTA")
    if d.podman_available:
        p_sign = "+" if d.storage_delta_podman >= 0 else ""
        print(f"    Podman Storage Delta:    {p_sign}{format_bytes(d.storage_delta_podman)} (images, containers, volumes)")

    ws_sign = "+" if d.workspace_delta >= 0 else ""
    print(f"    Workspace Delta:         {ws_sign}{format_bytes(d.workspace_delta)} (reports & local files)")

    if d.disk_free_delta != 0:
        f_sign = "+" if d.disk_free_delta >= 0 else ""
        print(f"    Host Disk Free Delta:    {f_sign}{format_bytes(d.disk_free_delta)}")

    print(sep)
    print()
