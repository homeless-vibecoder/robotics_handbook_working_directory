"""Verify designer design save/load helpers for robot, environment, custom assets."""
from __future__ import annotations

from pathlib import Path

from core.config import BodyConfig, WorldConfig, RobotConfig, CustomObjectConfig, MaterialConfig
from core.persistence import (
    save_robot_design,
    load_robot_design,
    save_environment_design,
    load_environment_design,
    save_custom_asset,
    load_custom_asset,
)


def _tmp(tmp_path: Path, name: str) -> Path:
    return tmp_path / f"{name}.json"


def test_robot_design_roundtrip(tmp_path: Path) -> None:
    robot = RobotConfig(
        bodies=[
            BodyConfig(
                name="base",
                points=[(0.0, 0.0), (0.2, 0.0), (0.2, 0.1), (0.0, 0.1)],
                edges=[(0, 1), (1, 2), (2, 3), (3, 0)],
            )
        ]
    )
    path = _tmp(tmp_path, "robot")
    save_robot_design(path, robot)
    loaded = load_robot_design(path)
    assert len(loaded.bodies) == 1
    assert loaded.bodies[0].name == "base"
    assert loaded.bodies[0].points == robot.bodies[0].points


def test_environment_design_roundtrip(tmp_path: Path) -> None:
    world = WorldConfig(drawings=[], bounds=None, metadata={"note": "env"})
    path = _tmp(tmp_path, "env")
    save_environment_design(path, world)
    loaded = load_environment_design(path)
    assert loaded.metadata.get("note") == "env"
    assert loaded.drawings == []


def test_custom_asset_roundtrip(tmp_path: Path) -> None:
    body = BodyConfig(
        name="custom_body",
        points=[(0.0, 0.0), (0.1, 0.0), (0.1, 0.1)],
        edges=[(0, 1), (1, 2), (2, 0)],
        material=MaterialConfig(color=(10, 20, 30)),
    )
    asset = CustomObjectConfig(name="custom_asset", body=body, kind="custom", metadata={"tag": "test"})
    path = _tmp(tmp_path, "custom")
    save_custom_asset(path, asset)
    loaded = load_custom_asset(path)
    assert loaded.name == "custom_asset"
    assert loaded.body.points == body.points
    assert loaded.metadata.get("tag") == "test"
