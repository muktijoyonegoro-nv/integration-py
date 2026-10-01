"""Pydantic schema and loader for scenario config.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class DatabaseMigrationConfig(BaseModel):
    database: str
    migration_dir: str = ""


class MySQLScenarioConfig(BaseModel):
    databases: List[str] = Field(default_factory=list)
    migrations: List[DatabaseMigrationConfig] = Field(default_factory=list)
    check_tables: List[str] = Field(default_factory=list)


class KafkaScenarioConfig(BaseModel):
    topics: List[str] = Field(default_factory=list)


class ServiceScenarioConfig(BaseModel):
    name: str
    endpoint_key: str = ""
    expose_port: str = "9000/tcp"
    image_override: str = ""
    dump_logs_on_failure: bool = True
    env_overrides: Dict[str, str] = Field(default_factory=dict)


class ScenarioConfig(BaseModel):
    name: str
    network_name: str = ""
    startup_timeout: float = 300.0
    wiremock: bool = False
    mysql: MySQLScenarioConfig = Field(default_factory=MySQLScenarioConfig)
    kafka: KafkaScenarioConfig = Field(default_factory=KafkaScenarioConfig)
    redis_instances: List[str] = Field(default_factory=list)
    services: List[ServiceScenarioConfig] = Field(default_factory=list)


def load_scenario_config(yaml_path: Path | str) -> ScenarioConfig:
    """Loads and validates a scenario config.yaml file against ScenarioConfig schema."""
    p = Path(yaml_path).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Scenario configuration file not found at: {p}")

    content = p.read_text(encoding="utf-8")
    data = yaml.safe_load(content) or {}
    return ScenarioConfig.model_validate(data)
