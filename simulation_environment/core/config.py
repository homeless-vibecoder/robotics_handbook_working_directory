"""Data models and JSON helpers for sim scenarios."""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, get_type_hints, get_origin, get_args

PoseTuple = Tuple[float, float, float]
Point = Tuple[float, float]
Edge = Tuple[int, int]


@dataclass
class MaterialConfig:
    color: Tuple[int, int, int] = (180, 180, 180)
    roughness: float = 0.5
    friction: float = 0.8
    restitution: float = 0.1
    reflect_line: float = 0.5
    reflect_distance: float = 0.5
    thickness: float = 0.02
    custom: Dict[str, object] = field(default_factory=dict)


@dataclass
class BodyConfig:
    name: str
    points: List[Point]
    edges: List[Edge]
    pose: PoseTuple = (0.0, 0.0, 0.0)
    can_move: bool = True
    mass: float = 1.0
    inertia: float = 1.0
    material: MaterialConfig = field(default_factory=MaterialConfig)


@dataclass
class JointConfig:
    name: str
    parent: str
    child: str
    type: str = "rigid"  # rigid | hinge
    anchor_parent: Point = (0.0, 0.0)
    anchor_child: Point = (0.0, 0.0)
    lower_limit: float = 0.0
    upper_limit: float = 0.0
    stiffness: float = 1000.0
    damping: float = 10.0


@dataclass
class ActuatorConfig:
    name: str
    type: str  # "motor"
    body: str
    mount_pose: PoseTuple = (0.0, 0.0, 0.0)
    params: Dict[str, object] = field(default_factory=dict)


@dataclass
class SensorConfig:
    name: str
    type: str  # "distance" | "line" | "encoder" | "imu"
    body: str
    mount_pose: PoseTuple = (0.0, 0.0, 0.0)
    params: Dict[str, object] = field(default_factory=dict)


@dataclass
class MeasurementConfig:
    name: str
    signal: str  # e.g., "wheel_speed", "sensor.line_left"
    body: Optional[str] = None
    window: float = 5.0


@dataclass
class RobotConfig:
    spawn_pose: PoseTuple = (0.0, 0.0, 0.0)
    bodies: List[BodyConfig] = field(default_factory=list)
    joints: List[JointConfig] = field(default_factory=list)
    actuators: List[ActuatorConfig] = field(default_factory=list)
    sensors: List[SensorConfig] = field(default_factory=list)
    measurements: List[MeasurementConfig] = field(default_factory=list)
    controller_module: str = "controller"


@dataclass
class WorldObjectConfig:
    name: str
    body: BodyConfig


@dataclass
class WorldConfig:
    name: str = "world"
    seed: Optional[int] = None
    gravity: Tuple[float, float] = (0.0, 0.0)
    timestep: float = 1.0 / 120.0
    terrain: List[WorldObjectConfig] = field(default_factory=list)
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class SnapshotState:
    time: float
    step: int
    bodies: Dict[str, Dict[str, object]]
    controller_state: Optional[Dict[str, object]] = None


def _dataclass_from_dict(cls, data: Dict) -> object:
    field_types = get_type_hints(cls)
    kwargs = {}
    for key, value in data.items():
        expected = field_types.get(key)
        origin = get_origin(expected)
        if origin is list:
            inner = get_args(expected)[0]
            if hasattr(inner, "__dataclass_fields__"):
                kwargs[key] = [_dataclass_from_dict(inner, v) for v in value]
                continue
        if hasattr(expected, "__dataclass_fields__"):
            kwargs[key] = _dataclass_from_dict(expected, value)
        else:
            kwargs[key] = value
    return cls(**kwargs)


def load_json(path: Path, cls):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return _dataclass_from_dict(cls, data)


def save_json(path: Path, obj) -> None:
    def _encode(o):
        if hasattr(o, "__dataclass_fields__"):
            return {k: _encode(v) for k, v in asdict(o).items()}
        if isinstance(o, (list, tuple)):
            return [_encode(v) for v in o]
        if isinstance(o, dict):
            return {k: _encode(v) for k, v in o.items()}
        return o

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(_encode(obj), f, indent=2)

