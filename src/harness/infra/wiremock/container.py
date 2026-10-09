"""WireMock container lifecycle and AAA mock configuration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from harness.env.prune import default_labels
from harness.infra.wait import wait_for_port
from harness.infra.wiremock.util import setup_wiremock_aaa

if TYPE_CHECKING:
    from harness.config import Config
    from harness.env.environment import TestEnvironment

logger = logging.getLogger(__name__)


def provision_wiremock(
    client,
    net,
    cfg: Config,
    env: TestEnvironment,
) -> None:
    """Provisions WireMock container on the bridge network and seeds base AAA mock."""
    wm_image = cfg.get_image("wiremock", "docker.io/wiremock/wiremock:3.5.2")
    wm_endpoint_config = {
        net.name: client.api.create_endpoint_config(aliases=["mock-services"])
    }
    wm_c = client.containers.run(
        image=wm_image,
        detach=True,
        ports={"8080/tcp": None},
        labels=default_labels("wiremock"),
        network=net.name,
        networking_config=wm_endpoint_config,
    )
    env.wiremock_container = wm_c

    wm_c.reload()
    wm_port = int(wm_c.attrs["NetworkSettings"]["Ports"]["8080/tcp"][0]["HostPort"])
    env.wiremock_host_url = f"http://127.0.0.1:{wm_port}"

    wait_for_port(wm_port, timeout=60.0)
    setup_wiremock_aaa(env.wiremock_host_url)
