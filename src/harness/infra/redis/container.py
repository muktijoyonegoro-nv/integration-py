"""Redis infrastructure container lifecycle and client initialization."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from harness.env.prune import default_labels
from harness.infra.redis.util import connect_redis
from harness.infra.wait import wait_for_port

if TYPE_CHECKING:
    from harness.config import Config
    from harness.env.environment import TestEnvironment

logger = logging.getLogger(__name__)


def provision_redis(
    client,
    net,
    cfg: Config,
    redis_aliases: list[str],
    shared_redis: bool,
    env: TestEnvironment,
) -> None:
    """Provisions Redis container(s) on the bridge network and initializes clients."""
    redis_image = cfg.get_image("redis", "redis:7-alpine")
    redis_alias_groups = [redis_aliases] if shared_redis else [[a] for a in redis_aliases]

    for aliases in redis_alias_groups:
        if not aliases:
            continue
        primary_alias = aliases[0]
        redis_endpoint_config = {
            net.name: client.api.create_endpoint_config(aliases=aliases)
        }
        rc = client.containers.run(
            image=redis_image,
            detach=True,
            ports={"6379/tcp": None},
            labels=default_labels(primary_alias),
            network=net.name,
            networking_config=redis_endpoint_config,
        )
        for alias in aliases:
            env.redis_containers[alias] = rc

        rc.reload()
        rport = int(rc.attrs["NetworkSettings"]["Ports"]["6379/tcp"][0]["HostPort"])
        addr = f"127.0.0.1:{rport}"
        wait_for_port(rport, timeout=60.0)
        redis_client = connect_redis(addr, timeout=60.0)
        for alias in aliases:
            env.redis_addrs[alias] = addr
            env.redis_clients[alias] = redis_client
