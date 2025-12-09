# Scenario Library (curated)

- `bounded_maze`: Bounded maze with left-hand wall follower robot; distance sensors front/left/right; bounds keep robot inside; sample log saved under `logs/bounded_maze_sample.json`.
- `slalom_field`: Zig-zag posts with oscillating gait; open bounds; safety slowdown on close hits; sample log `logs/slalom_field_sample.json`.
- `tight_corridor`: Narrow S-bend corridor tuned for distance centering; logs in `logs/tight_corridor_sample.json`.
- `line_loop`: Closed rectangular line track with line-array follower and optional front range guard; log at `logs/line_loop_sample.json`.
- `composed_generic`: Uses shared assets (`assets/environments/generic_world.json`, `assets/robots/generic_robot.json`) plus its own controller.
- `composed_slalom`: Uses shared assets (`assets/environments/slalom_world.json`, `assets/robots/slalom_robot.json`) plus its own controller.

Loading: scenarios show up automatically in Runner/Designer dropdowns via `apps.shared_ui.list_scenarios` (now supports `scenario.json` descriptors or legacy `world.json` + `robot.json`). Controllers live beside each scenario and hot-reload when Runner reloads code.

Compatibility: All scenarios use top-down gravity-off worlds, deterministic seeds, and `world.json`/`robot.json` schemas already used in `generic/`. Line track uses `line_intensity` terrain materials; bounds/wall strokes rely on the existing collision conversion in `core.simulator`.
