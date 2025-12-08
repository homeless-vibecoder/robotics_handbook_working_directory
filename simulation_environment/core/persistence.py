"""File I/O helpers for scenarios and snapshots."""
from __future__ import annotations

from pathlib import Path
import json
from typing import Tuple

from .config import WorldConfig, RobotConfig, SnapshotState, load_json, save_json


def load_scenario(path: Path) -> Tuple[WorldConfig, RobotConfig]:
    world_cfg = load_json(path / "world.json", WorldConfig)
    robot_cfg = load_json(path / "robot.json", RobotConfig)
    return world_cfg, robot_cfg


def save_scenario(path: Path, world_cfg: WorldConfig, robot_cfg: RobotConfig) -> None:
    save_json(path / "world.json", world_cfg)
    save_json(path / "robot.json", robot_cfg)


def save_snapshot(path: Path, snap: SnapshotState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "time": snap.time,
                "step": snap.step,
                "bodies": snap.bodies,
                "controller_state": snap.controller_state,
            },
            f,
            indent=2,
        )


def load_snapshot(path: Path) -> SnapshotState:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return SnapshotState(
        time=data.get("time", 0.0),
        step=data.get("step", 0),
        bodies=data.get("bodies", {}),
        controller_state=data.get("controller_state"),
    )

