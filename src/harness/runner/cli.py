"""CLI entrypoint for test-runner wrapper and image pull utility."""

from __future__ import annotations

import os
import resource
import signal
import subprocess
import sys
import threading
import time
import uuid
from typing import List

from harness.config import load_config
from harness.env.podman import setup_podman_environment
from harness.runner.monitor import (
    ContainerMetrics,
    fetch_podman_df,
    get_dir_size,
    get_disk_free,
    poll_podman_stats,
)
from harness.runner.reporter import ReportData, print_report


def run_test_runner(args: List[str]) -> int:
    """Wraps target command execution with real-time background telemetry sampling."""
    if not args:
        print("Usage: test-runner <command> [args...]")
        return 1

    target_cmd = args[0]
    target_args = args[1:]

    cfg = load_config()
    podman_bin = cfg.get_podman_bin()
    setup_podman_environment()
    podman_url = os.environ.get("DOCKER_HOST", "")

    # Initial snapshots
    init_podman_storage, podman_available = fetch_podman_df(podman_bin, podman_url)
    init_workspace_size = get_dir_size(".")
    init_disk_free = get_disk_free(".")

    run_id = uuid.uuid4().hex
    metrics = ContainerMetrics(run_id=run_id)
    stop_event = threading.Event()

    def sample_loop():
        while not stop_event.is_set():
            entries = poll_podman_stats(podman_bin, podman_url)
            if entries:
                metrics.update(entries, podman_bin, podman_url)
            time.sleep(0.6)

    sampler_thread = None
    if podman_available:
        sampler_thread = threading.Thread(target=sample_loop, daemon=True)
        sampler_thread.start()

    start_time = time.time()
    proc = None
    terminated = False
    term_signal = ""

    def sig_handler(signum, frame):
        nonlocal terminated, term_signal
        terminated = True
        term_signal = signal.Signals(signum).name
        if proc and proc.poll() is None:
            proc.send_signal(signum)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    try:
        child_env = os.environ.copy()
        child_env["HARNESS_RUN_ID"] = run_id
        proc = subprocess.Popen([target_cmd] + target_args, env=child_env)
        proc.wait()
        exit_code = proc.returncode
    except FileNotFoundError as e:
        print(f"Failed to start command: {e}", file=sys.stderr)
        return 1
    finally:
        duration = time.time() - start_time
        stop_event.set()
        if sampler_thread:
            sampler_thread.join(timeout=2.0)

    # Final snapshots
    final_podman_storage, _ = fetch_podman_df(podman_bin, podman_url)
    final_workspace_size = get_dir_size(".")
    final_disk_free = get_disk_free(".")

    status_str = "PASSED"
    if terminated:
        status_str = f"TERMINATED ({term_signal})"
        exit_code = 130
    elif exit_code != 0:
        status_str = f"FAILED (exit code {exit_code})"

    # Host process rusage for children
    rusage = resource.getrusage(resource.RUSAGE_CHILDREN)
    # On macOS / Darwin, ru_maxrss is in bytes; on Linux, in KiB
    peak_host_rss = rusage.ru_maxrss if sys.platform == "darwin" else rusage.ru_maxrss * 1024

    report = ReportData(
        command=" ".join(args),
        status=status_str,
        duration_seconds=duration,
        peak_host_rss_bytes=peak_host_rss,
        user_cpu_seconds=rusage.ru_utime,
        sys_cpu_seconds=rusage.ru_stime,
        podman_available=podman_available,
        container_metrics=metrics,
        storage_delta_podman=final_podman_storage - init_podman_storage,
        workspace_delta=final_workspace_size - init_workspace_size,
        disk_free_delta=final_disk_free - init_disk_free,
    )

    print_report(report)
    return exit_code


def pull_images_cli() -> None:
    """Pre-pulls all required external images."""
    cfg = load_config()
    setup_podman_environment()
    podman_bin = cfg.get_podman_bin()

    images_to_pull = [
        cfg.get_image("mysql", "mysql:8.0"),
        cfg.get_image("redis", "redis:7-alpine"),
        cfg.get_image("kafka", "confluentinc/confluent-local:7.6.0"),
        cfg.get_image("wiremock", "docker.io/wiremock/wiremock:3.5.2"),
        cfg.get_image("flyway", "docker.io/flyway/flyway:11-alpine"),
    ]

    print("Pre-pulling required container images...")
    for img in images_to_pull:
        print(f"Pulling {img}...")
        subprocess.run([podman_bin, "pull", img], check=True)
    print("All base images are up-to-date.")


def main() -> None:
    exit_code = run_test_runner(sys.argv[1:])
    sys.exit(exit_code)
