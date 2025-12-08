# Simulation environment (milestone 1)

Quick-start
- Install deps: `pip install pygame pygame_gui`.
- Runner (for coding/playback): `python apps/runner.py`
  - Pick a scenario from the dropdown (looks in `scenarios/`).
  - Play/Pause/Step, save/load snapshots, edit `controller.py` and hot-reload.
- Designer (for geometry/devices): `python apps/designer.py`
  - Pick a scenario, select a body, edit polygon points (add/move/delete), add motors/sensors, save back to JSON.

Controls (top bar)
- Play/Pause, Step one tick.
- Save snapshot (writes to `scenarios/generic/snapshots/`), Load snapshot (loads latest).
- Reload code (reloads controller module), Save code (writes editor buffer then reloads).

Code editor
- Right-side panel is a minimal text editor for `scenarios/generic/controller.py` (supports typing, backspace, newline, tab).
- Use Save code to persist and reload without restarting the app.

Robot designer (minimal draft)
- Select a body from the dropdown; click “Add point,” then click in the viewport to append a vertex (convex or non-convex).
- Save robot writes updated `robot.json` (edges are re-closed automatically).

Viewport
- Runner: draws world/robot polygons; wheel arrows show motor commands.
- Designer: shows polygons and vertices; zoom with +/-; pan with arrow keys; click to add/move/delete vertices when a mode is active.

Data layout
- `scenarios/<name>/world.json` – terrain/track, physics settings.
- `scenarios/<name>/robot.json` – bodies, sensors/motors, controller module name.
- `scenarios/<name>/controller.py` – student code (hot-reloaded).
- `scenarios/<name>/snapshots/` – saved states (include controller state).

Notes
- Solver uses XPBD-style joint correction + impulse contacts with reasonable defaults (dt ~1/120s).
- Generic devices: distance, line, IMU, encoder sensors; wheel motors with force limit.

Wheel traction (top-down, zero-g world)
- Traction uses a virtual normal load so you can reason about mass: `N = normal_force` or `mass * g_equiv / wheel_count` (defaults g_equiv=9.81, wheel_count=2).
- Longitudinal drive is capped by `mu_long * N`; lateral slip is constrained with `mu_lat * N` and a small damping term to avoid oscillation.
- Configure per motor via actuator params: `mu_long`, `mu_lat`, `g_equiv`, `normal_force` (optional override), `lateral_damping`, `wheel_count`, `wheel_radius`, `max_force` (or `preset` + `detailed=True` for torque models).
- If `wheel_count` is omitted, the simulator auto-counts wheel motors on the same body and splits the virtual normal load equally. Set `wheel_count` or `normal_force` explicitly to override.
- Physical units: meters, seconds, kg. E.g., a 0.5 kg robot with two wheels gets ~2.45 N of normal load per wheel by default.

