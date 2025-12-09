"""Deterministic load/run smoke tests for curated scenarios."""
from __future__ import annotations

import math
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core import Simulator, load_scenario  # noqa: E402

SCENARIOS = ["bounded_maze", "slalom_field", "tight_corridor", "line_loop", "composed_generic", "composed_slalom"]
STEPS = 180


def _finite_pose(body) -> bool:
    pose = body.pose
    lin_v = body.state.linear_velocity
    ang_v = body.state.angular_velocity
    return all(
        math.isfinite(v)
        for v in (
            pose.x,
            pose.y,
            pose.theta,
            lin_v[0],
            lin_v[1],
            ang_v,
        )
    )


def run_scenario(name: str) -> bool:
    scenario_path = BASE / "scenarios" / name
    world_cfg, robot_cfg = load_scenario(scenario_path)
    sim = Simulator()
    sim.load(scenario_path, world_cfg, robot_cfg, top_down=True)
    for _ in range(STEPS):
        sim.step()
    bodies_ok = all(_finite_pose(body) for body in sim.bodies.values())
    ctrl_ok = sim.last_controller_error is None
    phys_ok = sim.last_physics_warning is None
    return bodies_ok and ctrl_ok and phys_ok


def run() -> bool:
    results = {}
    all_ok = True
    for name in SCENARIOS:
        ok = run_scenario(name)
        results[name] = ok
        all_ok = all_ok and ok
    for name, status in results.items():
        print(f"[{name}] {'PASS' if status else 'FAIL'}")
    return all_ok


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
