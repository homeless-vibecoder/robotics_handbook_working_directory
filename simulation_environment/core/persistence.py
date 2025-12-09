"""File I/O helpers for scenarios and snapshots."""
from __future__ import annotations

from pathlib import Path
import json
from typing import Tuple

from .config import (
    EnvironmentBounds,
    WorldConfig,
    RobotConfig,
    SnapshotState,
    BodyConfig,
    WorldObjectConfig,
    CustomObjectConfig,
    DesignerState,
    load_json,
    save_json,
)


def _resolve_asset(base: Path, ref: str) -> Path:
    """Resolve an asset reference relative to the scenario folder or repository root."""
    ref_path = Path(ref)
    if ref_path.is_absolute():
        return ref_path
    # First try relative to scenario directory
    candidate = (base / ref_path).resolve()
    if candidate.exists():
        return candidate
    # Then try relative to repo root (scenario_dir/..)
    repo_root = base.parent
    candidate = (repo_root / ref_path).resolve()
    if candidate.exists():
        return candidate
    # Fall back to original reference (may raise later)
    return ref_path.resolve()


def load_scenario(path: Path) -> Tuple[WorldConfig, RobotConfig]:
    descriptor_path = path / "scenario.json"
    if descriptor_path.exists():
        with descriptor_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        env_ref = data.get("environment") or data.get("env")
        robot_ref = data.get("robot")
        robots_ref = data.get("robots") or []
        if not env_ref:
            raise ValueError(f"scenario.json missing 'environment': {descriptor_path}")
        if not robot_ref and robots_ref:
            robot_ref = robots_ref[0]
        if not robot_ref:
            raise ValueError(f"scenario.json missing 'robot': {descriptor_path}")
        env_path = _resolve_asset(path, env_ref)
        robot_path = _resolve_asset(path, robot_ref)
        world_cfg = load_environment_design(env_path)
        robot_cfg = load_robot_design(robot_path)
        _normalize_robot(robot_cfg)
        return world_cfg, robot_cfg

    # legacy pair in-place
    world_cfg = load_json(path / "world.json", WorldConfig)
    robot_cfg = load_json(path / "robot.json", RobotConfig)
    _normalize_robot(robot_cfg)
    return world_cfg, robot_cfg


def save_scenario(path: Path, world_cfg: WorldConfig, robot_cfg: RobotConfig) -> None:
    _normalize_world(world_cfg)
    _normalize_robot(robot_cfg)
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


def _normalize_world(world_cfg: WorldConfig) -> None:
    """Ensure world config fields stay deterministic when saving."""
    # Normalize bounds ordering
    if getattr(world_cfg, "bounds", None):
        b = world_cfg.bounds
        assert b
        min_x = min(b.min_x, b.max_x)
        max_x = max(b.min_x, b.max_x)
        min_y = min(b.min_y, b.max_y)
        max_y = max(b.min_y, b.max_y)
        world_cfg.bounds = EnvironmentBounds(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)
    # Normalize drawings (sort + clamp small negative thickness)
    drawings = getattr(world_cfg, "drawings", []) or []
    normalized = []
    for d in drawings:
        pts = [(float(p[0]), float(p[1])) for p in d.points]
        normalized.append(
            type(d)(
                kind=str(getattr(d, "kind", "mark")),
                thickness=max(1e-4, float(getattr(d, "thickness", 0.05))),
                points=pts,
                color=tuple(getattr(d, "color", (140, 180, 240))),
            )
        )
    world_cfg.drawings = sorted(
        normalized,
        key=lambda s: (
            s.kind,
            round(s.thickness, 6),
            len(s.points),
            [(round(p[0], 6), round(p[1], 6)) for p in s.points],
        ),
    )
    # Normalize shape objects (static or decorative geometry)
    shape_objects = getattr(world_cfg, "shape_objects", []) or []
    norm_shapes: list[WorldObjectConfig] = []
    for obj in shape_objects:
        body = getattr(obj, "body", None)
        if not body:
            continue
        pts = [(float(p[0]), float(p[1])) for p in body.points]
        edges = [(int(a), int(b)) for a, b in body.edges]
        norm_body = BodyConfig(
            name=str(body.name),
            points=pts,
            edges=edges,
            pose=tuple(float(v) for v in body.pose),
            can_move=bool(getattr(body, "can_move", False)),
            mass=float(getattr(body, "mass", 1.0)),
            inertia=float(getattr(body, "inertia", 1.0)),
            material=body.material,  # already dataclass
        )
        norm_shapes.append(WorldObjectConfig(name=str(obj.name), body=norm_body))
    world_cfg.shape_objects = sorted(norm_shapes, key=lambda o: o.name)
    # Normalize custom objects (metadata + geometry)
    custom_objects = getattr(world_cfg, "custom_objects", []) or []
    norm_customs: list[CustomObjectConfig] = []
    for obj in custom_objects:
        body = getattr(obj, "body", None)
        if not body:
            continue
        pts = [(float(p[0]), float(p[1])) for p in body.points]
        edges = [(int(a), int(b)) for a, b in body.edges]
        norm_body = BodyConfig(
            name=str(body.name),
            points=pts,
            edges=edges,
            pose=tuple(float(v) for v in body.pose),
            can_move=bool(getattr(body, "can_move", False)),
            mass=float(getattr(body, "mass", 1.0)),
            inertia=float(getattr(body, "inertia", 1.0)),
            material=body.material,
        )
        norm_customs.append(
            CustomObjectConfig(
                name=str(getattr(obj, "name", body.name)),
                body=norm_body,
                kind=str(getattr(obj, "kind", "custom")),
                metadata=dict(getattr(obj, "metadata", {}) or {}),
            )
        )
    world_cfg.custom_objects = sorted(norm_customs, key=lambda o: o.name)
    # Normalize designer state to keep numeric values stable
    ds = getattr(world_cfg, "designer_state", None) or DesignerState()
    ds.brush_thickness = max(1e-4, float(getattr(ds, "brush_thickness", 0.05)))
    if getattr(ds, "brush_kind", "") not in ("mark", "wall"):
        ds.brush_kind = "mark"
    if getattr(ds, "shape_tool", "") not in ("rect", "triangle", "line"):
        ds.shape_tool = "rect"
    if getattr(ds, "creation_context", "") not in ("robot", "environment", "custom"):
        ds.creation_context = "robot"
    world_cfg.designer_state = ds


def _normalize_robot(robot_cfg: RobotConfig) -> None:
    """Keep device ordering stable for deterministic saves."""
    # Ensure at least one body exists to avoid downstream None crashes.
    if not getattr(robot_cfg, "bodies", None):
        robot_cfg.bodies = [
            BodyConfig(
                name="body",
                points=[(0.1, -0.06), (0.1, 0.06), (-0.08, 0.06), (-0.08, -0.06)],
                edges=[(0, 1), (1, 2), (2, 3), (3, 0)],
                pose=(0.0, 0.0, 0.0),
                can_move=True,
            )
        ]
    robot_cfg.actuators = sorted(robot_cfg.actuators, key=lambda a: a.name)
    robot_cfg.sensors = sorted(robot_cfg.sensors, key=lambda s: s.name)
    robot_cfg.bodies = sorted(robot_cfg.bodies, key=lambda b: b.name)


# --- Design helpers (robot/env/custom) ---------------------------------------
def save_robot_design(path: Path, robot_cfg: RobotConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _normalize_robot(robot_cfg)
    save_json(path, robot_cfg)


def load_robot_design(path: Path) -> RobotConfig:
    robot = load_json(path, RobotConfig)
    _normalize_robot(robot)
    return robot


def save_environment_design(path: Path, world_cfg: WorldConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _normalize_world(world_cfg)
    save_json(path, world_cfg)


def load_environment_design(path: Path) -> WorldConfig:
    return load_json(path, WorldConfig)


def save_custom_asset(path: Path, asset: CustomObjectConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    save_json(path, asset)


def load_custom_asset(path: Path) -> CustomObjectConfig:
    return load_json(path, CustomObjectConfig)

