"""Scenario runner app: pick a scenario, run sim, edit controller code, snapshots."""
from __future__ import annotations

import csv
import json
import math
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Callable, Set, Tuple

import pygame
import pygame_gui

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core import load_scenario, Simulator, save_snapshot, load_snapshot  # noqa: E402
from apps.shared_ui import list_scenarios, SimpleTextEditor, world_to_screen, screen_to_world, HoverMenu  # noqa: E402
from low_level_mechanics.geometry import Polygon  # noqa: E402


def frange(start: float, stop: float, step: float):
    x = start
    while x <= stop + 1e-9:
        yield x
        x += step


class _ConsoleTee:
    """Capture stdout while mirroring to original."""

    def __init__(self, original, sink: Callable[[str], None]) -> None:
        self.original = original
        self.sink = sink

    def write(self, data: str) -> None:
        try:
            self.original.write(data)
        except Exception:
            pass
        self.sink(data)

    def flush(self) -> None:
        try:
            self.original.flush()
        except Exception:
            pass


@dataclass
class DockItem:
    id: str
    title: str
    rect: pygame.Rect
    dock: str  # "floating" | "left" | "right" | "bottom"
    visible: bool = True
    min_size: Tuple[int, int] = (260, 200)
    z: int = 0


class RunnerApp:
    def __init__(self) -> None:
        pygame.init()
        # Enable key repeat for held keys (e.g., arrows, delete)
        pygame.key.set_repeat(300, 35)
        pygame.display.set_caption("Runner")
        self.window_size = (1280, 760)
        self.window_surface = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        self.manager = pygame_gui.UIManager(self.window_size)
        self.clock = pygame.time.Clock()
        self.running = True
        self.playing = True

        self.base_path = Path(__file__).resolve().parent.parent
        self.scenario_root = self.base_path / "scenarios"
        self.scenario_names = list_scenarios(self.scenario_root)
        self.scenario_name = self.scenario_names[0] if self.scenario_names else None
        self.sim: Optional[Simulator] = None
        self._sim_time_accum = 0.0
        # Layout parameters
        self.viewport_min = 520
        self.panel_header_h = 28
        self.panel_padding = 8
        self.scale = 400.0
        self.offset = (0.0, 0.0)
        self.pan_active = False
        self.pan_start: Optional[Tuple[int, int]] = None
        self.view_options = {"grid": False, "motor_arrows": True}
        # Panel/docking state
        self.dock_items: Dict[str, DockItem] = {}
        self.panel_inner_rects: Dict[str, pygame.Rect] = {}
        self.dock_dragging: Optional[Tuple[str, Tuple[int, int]]] = None
        self.dock_resizing: Optional[Tuple[str, str, Tuple[int, int]]] = None
        self.dock_active_panel: Optional[str] = None
        self.dock_last_action: Optional[str] = None
        self.hover_menu: Optional[HoverMenu] = None
        self.top_down_mode: bool = True
        self.force_empty_world: bool = True
        self.panel_menu_open = False
        self.panel_menu_regions: Dict[str, pygame.Rect] = {}
        self.panel_menu_anchor = "right"
        self.dock_z_counter = 0
        self.panel_layout_path = self.base_path / "runner_layout.json"
        self.reposition_mode = False
        self.reposition_dragging = False
        self.reposition_target: Optional[Tuple[float, float]] = None
        self.reposition_angle: float = 0.0
        self.show_device_help = True
        self._stepped_this_frame = False
        self.robot_dragging = False
        self.robot_drag_start: Optional[Tuple[float, float]] = None
        self.robot_drag_center: Optional[Tuple[float, float]] = None
        self.robot_drag_theta: float = 0.0
        self.hover_robot_center: bool = False
        self.pose_history: List[Tuple[float, float, float]] = []
        self.pose_redo: List[Tuple[float, float, float]] = []
        self.error_log: List[Dict[str, str]] = []
        self.console_lines: List[str] = []
        self._console_buffer: str = ""
        self.device_help_lines: List[str] = []
        self.live_state: Dict[str, Dict[str, object]] = {"motors": {}, "sensors": {}}
        self.logger_selected: Set[str] = set()
        self.logger_samples: List[Dict[str, object]] = []
        self.logger_enabled = False
        self.logger_interval = 1.0 / 30.0
        self.logger_duration = 15.0
        self._logger_timer = 0.0
        self._logger_elapsed = 0.0
        self.logger_status = "Logger idle"
        self.signal_hitboxes: Dict[str, pygame.Rect] = {}
        # Reserve bottom space in the right column for error drawer.
        self.viewport_rect = pygame.Rect(0, 0, 0, 0)  # set in _update_layout
        self.editor_rect = pygame.Rect(0, 0, 0, 0)
        self.status_text = "Ctrl+S to save + reload; Format for styling"
        self._orig_stdout = sys.stdout
        sys.stdout = _ConsoleTee(sys.stdout, self._append_console)

        self._build_ui()
        self._init_dock_panels()
        self._init_hover_menu()
        self._load_panel_layout()
        self._update_layout()
        self.editor = self._load_editor()
        self._load_sim()

    def _build_ui(self) -> None:
        self.dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=self.scenario_names or ["<none>"],
            starting_option=self.scenario_name or "<none>",
            relative_rect=pygame.Rect((20, 20), (200, 30)),
            manager=self.manager,
        )
        self.btn_reload_scenario = pygame_gui.elements.UIButton(
            pygame.Rect((230, 20), (120, 30)), "Load", manager=self.manager
        )
        self.btn_play = pygame_gui.elements.UIButton(
            pygame.Rect((360, 20), (80, 30)), "Pause", manager=self.manager
        )
        self.btn_step = pygame_gui.elements.UIButton(
            pygame.Rect((450, 20), (80, 30)), "Step", manager=self.manager
        )
        self.btn_snap = pygame_gui.elements.UIButton(
            pygame.Rect((540, 20), (140, 30)), "Save snapshot", manager=self.manager
        )
        self.btn_load_snap = pygame_gui.elements.UIButton(
            pygame.Rect((690, 20), (140, 30)), "Load snapshot", manager=self.manager
        )
        self.btn_reload_code = pygame_gui.elements.UIButton(
            pygame.Rect((840, 20), (120, 30)), "Reload code", manager=self.manager
        )
        self.btn_save_code = pygame_gui.elements.UIButton(
            pygame.Rect((970, 20), (120, 30)), "Save code", manager=self.manager
        )
        self.btn_format_code = pygame_gui.elements.UIButton(
            pygame.Rect((1100, 20), (100, 30)), "Format", manager=self.manager
        )
        self.btn_clear_errors = pygame_gui.elements.UIButton(
            pygame.Rect((0, 0), (180, 30)),  # positioned in _update_layout
            "Clear errors",
            manager=self.manager,
        )
        self.btn_toggle_panel = pygame_gui.elements.UIButton(
            pygame.Rect((0, 0), (210, 30)),  # positioned in _update_layout
            "Clear console",
            manager=self.manager,
        )
        # State/logging controls
        self.btn_logger_toggle = pygame_gui.elements.UIButton(
            pygame.Rect((0, 0), (140, 28)), "Start logging", manager=self.manager
        )
        self.btn_logger_export = pygame_gui.elements.UIButton(
            pygame.Rect((0, 0), (130, 28)), "Export log", manager=self.manager
        )
        self.dropdown_logger_rate = pygame_gui.elements.UIDropDownMenu(
            options_list=["120 Hz", "60 Hz", "30 Hz", "10 Hz"],
            starting_option="60 Hz",
            relative_rect=pygame.Rect((0, 0), (110, 28)),
            manager=self.manager,
        )
        self.dropdown_logger_duration = pygame_gui.elements.UIDropDownMenu(
            options_list=["5 s", "15 s", "60 s", "Unlimited"],
            starting_option="15 s",
            relative_rect=pygame.Rect((0, 0), (120, 28)),
            manager=self.manager,
        )
        self.btn_reposition_mode = pygame_gui.elements.UIButton(
            pygame.Rect((0, 0), (150, 28)), "Reposition robot", manager=self.manager
        )
        self.btn_reset_pose = pygame_gui.elements.UIButton(
            pygame.Rect((0, 0), (140, 28)), "Reset to spawn", manager=self.manager
        )
        self.btn_set_spawn = pygame_gui.elements.UIButton(
            pygame.Rect((0, 0), (140, 28)), "Save as spawn", manager=self.manager
        )
        self.btn_toggle_help = pygame_gui.elements.UIButton(
            pygame.Rect((0, 0), (150, 28)), "Hide device help", manager=self.manager
        )
        # Hide old top-row buttons; hover menus will replace them.
        for btn in [
            self.dropdown,
            self.btn_reload_scenario,
            self.btn_play,
            self.btn_step,
            self.btn_snap,
            self.btn_load_snap,
            self.btn_reload_code,
            self.btn_save_code,
            self.btn_format_code,
        ]:
            btn.hide()

    def _init_dock_panels(self) -> None:
        w, h = self.window_size
        right_w = 420
        bottom_h = 260
        base_x = max(220, w - right_w - 20)
        self.dock_items = {
            "code": DockItem(
                "code",
                "Code",
                pygame.Rect(base_x, 70, right_w, max(360, h - 200)),
                "right",
                True,
                (320, 260),
            ),
            "devices": DockItem(
                "devices", "Devices", pygame.Rect(base_x, 70, right_w, 260), "right", True, (280, 200)
            ),
            "state": DockItem(
                "state", "State", pygame.Rect(base_x, 70, right_w, 320), "right", True, (320, 240)
            ),
            "logs": DockItem(
                "logs",
                "Logs",
                pygame.Rect(base_x, h - bottom_h - 40, right_w, bottom_h),
                "bottom",
                True,
                (280, 200),
            ),
            "console": DockItem(
                "console",
                "Console",
                pygame.Rect(base_x - right_w - 20, h - bottom_h - 40, right_w, bottom_h),
                "bottom",
                True,
                (280, 200),
            ),
        }
        for i, item in enumerate(self.dock_items.values()):
            item.z = i
        self.panel_inner_rects = {}

    def _init_hover_menu(self) -> None:
        font = pygame.font.Font(pygame.font.get_default_font(), 14)
        self.hover_menu = HoverMenu(
            [
                (
                    "View",
                    [
                        {"label": "Reset view", "action": self._view_reset},
                        {"label": "Center robot", "action": self._view_center_robot},
                        {
                            "label": "Toggle grid",
                            "action": self._view_toggle_grid,
                            "checked": lambda: self.view_options.get("grid", False),
                        },
                        {
                            "label": "Toggle motor arrows",
                            "action": self._view_toggle_motor_arrows,
                            "checked": lambda: self.view_options.get("motor_arrows", True),
                        },
                        {"label": "Reposition robot", "action": self._view_reposition},
                    ],
                )
            ],
            pos=(20, 8),
            font=font,
        )

    # Menu helpers (shared actions for hover menu)
    def _toggle_play(self) -> None:
        if self.error_log:
            self.status_text = "Clear errors before running"
            self.playing = False
            return
        self.playing = not self.playing
        self.status_text = "Running" if self.playing else "Paused"
        try:
            self.btn_play.set_text("Play" if not self.playing else "Pause")
        except Exception:
            pass
        self._refresh_hover_menu()

    def _step_once(self) -> None:
        self.playing = False
        try:
            self.btn_play.set_text("Play")
        except Exception:
            pass
        if self.sim:
            try:
                self.sim.step(self.sim.dt)
            except Exception:
                self._record_error("Simulation error", traceback.format_exc())
            if self.sim and self.sim.last_controller_error:
                self._record_error("Controller error", self.sim.last_controller_error)
                self.sim.clear_controller_error()
        self._refresh_hover_menu()

    def _reload_code(self) -> None:
        if self.sim:
            self.sim.clear_controller_error()
            self.sim.reload_controller()
            if self.sim.last_controller_error:
                self._record_error("Controller reload failed", self.sim.last_controller_error)
                self.sim.clear_controller_error()
        self._refresh_hover_menu()

    def _select_scenario(self, name: str) -> None:
        self.scenario_name = name if name and name != "<none>" else None
        self._load_sim()
        self._refresh_hover_menu()

    def _toggle_panel(self, pid: str) -> None:
        item = self.dock_items.get(pid)
        if not item:
            return
        item.visible = not item.visible
        self._bump_panel(pid)
        self._update_layout()
        self._save_panel_layout()
        self._refresh_hover_menu()

    def _panel_header_rect(self, item: DockItem) -> pygame.Rect:
        return pygame.Rect(item.rect.x, item.rect.y, item.rect.width, self.panel_header_h)

    def _panel_close_rect(self, item: DockItem) -> pygame.Rect:
        return pygame.Rect(item.rect.right - 26, item.rect.y + 4, 20, 20)

    def _panel_resize_handles(self, item: DockItem) -> List[Tuple[str, pygame.Rect]]:
        size = 14
        r = item.rect
        handles = [
            ("tl", pygame.Rect(r.left - size // 2, r.top - size // 2, size, size)),
            ("tr", pygame.Rect(r.right - size // 2, r.top - size // 2, size, size)),
            ("bl", pygame.Rect(r.left - size // 2, r.bottom - size // 2, size, size)),
            ("br", pygame.Rect(r.right - size // 2, r.bottom - size // 2, size, size)),
            ("l", pygame.Rect(r.left - size // 2, r.centery - size // 2, size, size)),
            ("r", pygame.Rect(r.right - size // 2, r.centery - size // 2, size, size)),
            ("t", pygame.Rect(r.centerx - size // 2, r.top - size // 2, size, size)),
            ("b", pygame.Rect(r.centerx - size // 2, r.bottom - size // 2, size, size)),
        ]
        return handles

    def _panel_menu_rect(self) -> pygame.Rect:
        # Place below the top control row to avoid overlap with the Format button.
        y = 60
        if self.panel_menu_anchor == "left":
            return pygame.Rect(20, y, 180, 30)
        return pygame.Rect(self.window_size[0] - 200, y, 180, 30)

    def _panel_inner_rect(self, item: DockItem) -> pygame.Rect:
        pad = self.panel_padding
        inner_width = max(40, item.rect.width - 2 * pad)
        inner_height = max(32, item.rect.height - self.panel_header_h - pad)
        return pygame.Rect(item.rect.x + pad, item.rect.y + self.panel_header_h, inner_width, inner_height)

    def _panel_visible(self, panel_id: str) -> bool:
        item = self.dock_items.get(panel_id)
        return bool(item and item.visible)

    def _bump_panel(self, panel_id: str) -> None:
        item = self.dock_items.get(panel_id)
        if not item:
            return
        self.dock_z_counter += 1
        item.z = self.dock_z_counter

    def _load_panel_layout(self) -> None:
        if not self.panel_layout_path.exists():
            return
        try:
            data = json.loads(self.panel_layout_path.read_text(encoding="utf-8"))
        except Exception:
            return
        panels = data.get("panels", {})
        for pid, cfg in panels.items():
            item = self.dock_items.get(pid)
            if not item or not isinstance(cfg, dict):
                continue
            rect = cfg.get("rect")
            if rect and len(rect) == 4:
                item.rect = pygame.Rect(rect[0], rect[1], rect[2], rect[3])
            dock = cfg.get("dock")
            if dock in ("floating", "left", "right", "bottom"):
                item.dock = dock
            visible = cfg.get("visible")
            if isinstance(visible, bool):
                item.visible = visible

    def _save_panel_layout(self) -> None:
        try:
            payload = {
                "panels": {
                    pid: {
                        "rect": [item.rect.x, item.rect.y, item.rect.width, item.rect.height],
                        "dock": item.dock,
                        "visible": item.visible,
                    }
                    for pid, item in self.dock_items.items()
                }
            }
            self.panel_layout_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            # Persistence is best-effort; avoid crashing on save errors.
            pass

    def _load_editor(self) -> SimpleTextEditor:
        # Prefer a compact monospace font for code
        font = (
            pygame.font.SysFont("Menlo", 15)
            or pygame.font.SysFont("Consolas", 15)
            or pygame.font.SysFont("DejaVu Sans Mono", 15)
            or pygame.font.Font(pygame.font.get_default_font(), 15)
        )
        rect = self.editor_rect
        text = ""
        if self.scenario_name:
            controller = self.scenario_root / self.scenario_name / "controller.py"
            if controller.exists():
                text = controller.read_text(encoding="utf-8")
        return SimpleTextEditor(rect, font, text)

    def _refresh_device_help(self) -> None:
        lines: List[str] = []
        if not self.sim:
            self.device_help_lines = lines
            return
        motor_names = list(self.sim.motors.keys())
        sensor_items = []
        for name, sensor in self.sim.sensors.items():
            stype = getattr(sensor, "visual_tag", "") or sensor.__class__.__name__
            sensor_items.append(f"{name} ({stype})")
        lines.append(f"Motors: {', '.join(motor_names) if motor_names else 'none'}")
        lines.append(f"Sensors: {', '.join(sensor_items) if sensor_items else 'none'}")
        lines.append("Readings in step(): sensors['name']")
        lines.append("Command: sim.motors['name'].command(v, sim, dt)")
        self.device_help_lines = lines[:4]

    def _prime_logger_signals(self) -> None:
        self.logger_selected = set()
        if not self.sim:
            self.logger_samples.clear()
            return
        for name in self.sim.motors.keys():
            self.logger_selected.add(f"motor:{name}")
        for name in self.sim.sensors.keys():
            self.logger_selected.add(f"sensor:{name}")
        self.logger_samples.clear()
        self.logger_enabled = False
        self.logger_status = "Logger idle"
        self._logger_timer = 0.0
        self._logger_elapsed = 0.0

    def _update_layout(self) -> None:
        w, h = self.window_size
        margin = 20
        top_y = 70
        bottom_margin = 20

        dock_left = [i for i in self.dock_items.values() if i.visible and i.dock == "left"]
        dock_right = [i for i in self.dock_items.values() if i.visible and i.dock == "right"]
        dock_bottom = [i for i in self.dock_items.values() if i.visible and i.dock == "bottom"]

        left_w = max((max(i.rect.width, i.min_size[0]) for i in dock_left), default=0)
        right_w = max((max(i.rect.width, i.min_size[0]) for i in dock_right), default=0)
        bottom_h = max((max(i.rect.height, i.min_size[1]) for i in dock_bottom), default=0)

        max_side_space = max(0, w - 2 * margin - self.viewport_min)
        if left_w + right_w > max_side_space and (left_w + right_w) > 0:
            scale = max_side_space / (left_w + right_w)
            left_w = int(left_w * scale)
            right_w = int(right_w * scale)

        viewport_width = max(self.viewport_min, w - 2 * margin - left_w - right_w)
        viewport_height = max(260, h - top_y - bottom_margin - bottom_h)

        self.viewport_rect = pygame.Rect(margin + left_w, top_y, viewport_width, viewport_height)

        right_area = pygame.Rect(self.viewport_rect.right + 10, top_y, right_w, viewport_height) if right_w else pygame.Rect(0, 0, 0, 0)
        left_area = pygame.Rect(margin, top_y, left_w, viewport_height) if left_w else pygame.Rect(0, 0, 0, 0)
        bottom_area = (
            pygame.Rect(self.viewport_rect.x, self.viewport_rect.bottom + 10, viewport_width, bottom_h)
            if bottom_h
            else pygame.Rect(0, 0, 0, 0)
        )

        def stack_vertical(items: List[DockItem], area: pygame.Rect) -> None:
            if not items or area.width <= 0 or area.height <= 0:
                return
            gap = 8
            n = len(items)
            avail = max(0, area.height - gap * (n - 1))
            base_h = avail // n if n else 0
            y = area.y
            for idx, item in enumerate(items):
                height = max(item.min_size[1], base_h)
                max_allowed = area.y + area.height - y - gap * max(0, n - idx - 1)
                height = min(height, max_allowed)
                item.rect = pygame.Rect(area.x, y, max(area.width, item.min_size[0]), height)
                y += height + gap

        stack_vertical(sorted(dock_left, key=lambda d: d.z), left_area)
        stack_vertical(sorted(dock_right, key=lambda d: d.z), right_area)
        stack_vertical(sorted(dock_bottom, key=lambda d: d.z), bottom_area)

        # Keep floating panels inside the window bounds
        for item in self.dock_items.values():
            if not item.visible:
                continue
            if item.dock != "floating":
                continue
            item.rect.x = max(margin, min(item.rect.x, w - item.rect.width - margin))
            item.rect.y = max(top_y, min(item.rect.y, h - item.rect.height - bottom_margin))
            item.rect.width = max(item.min_size[0], min(item.rect.width, w - 2 * margin))
            item.rect.height = max(item.min_size[1], min(item.rect.height, h - top_y - bottom_margin))

        self.panel_inner_rects = {pid: self._panel_inner_rect(item) for pid, item in self.dock_items.items() if item.visible}
        self._position_panel_controls()

    def _position_panel_controls(self) -> None:
        controls = [
            self.btn_logger_toggle,
            self.btn_logger_export,
            self.dropdown_logger_rate,
            self.dropdown_logger_duration,
            self.btn_reposition_mode,
            self.btn_reset_pose,
            self.btn_set_spawn,
            self.btn_toggle_help,
            self.btn_clear_errors,
            self.btn_toggle_panel,
        ]
        for c in controls:
            c.hide()

        # Code panel/editor placement
        code_inner = self.panel_inner_rects.get("code")
        if code_inner:
            self.editor_rect = code_inner
            if hasattr(self, "editor"):
                self.editor.rect = self.editor_rect
                self.editor.scroll_offset = min(self.editor.scroll_offset, max(0, len(self.editor.lines) - 1))

        # Devices panel
        if self._panel_visible("devices"):
            item = self.dock_items["devices"]
            self.btn_toggle_help.show()
            self.btn_toggle_help.set_relative_position((item.rect.x + 8, item.rect.y + self.panel_header_h + 4))

        # State panel controls
        if self._panel_visible("state"):
            item = self.dock_items["state"]
            x = item.rect.x + 8
            row_y = item.rect.y + self.panel_header_h + 6
            self.btn_logger_toggle.show()
            self.btn_logger_toggle.set_relative_position((x, row_y))
            self.btn_logger_export.show()
            self.btn_logger_export.set_relative_position((x + 160, row_y))
            row_y += 32
            self.dropdown_logger_rate.show()
            self.dropdown_logger_rate.set_relative_position((x, row_y))
            self.dropdown_logger_duration.show()
            self.dropdown_logger_duration.set_relative_position((x + 120, row_y))
            row_y += 32
            self.btn_reposition_mode.show()
            self.btn_reposition_mode.set_relative_position((x, row_y))
            self.btn_reset_pose.show()
            self.btn_reset_pose.set_relative_position((x + 158, row_y))
            self.btn_set_spawn.show()
            self.btn_set_spawn.set_relative_position((x + 310, row_y))

        # Logs/errors
        if self._panel_visible("logs"):
            item = self.dock_items["logs"]
            self.btn_clear_errors.show()
            self.btn_clear_errors.set_relative_position((item.rect.x + 8, item.rect.y + self.panel_header_h + 4))

        # Console clear
        if self._panel_visible("console"):
            item = self.dock_items["console"]
            self.btn_toggle_panel.set_text("Clear console")
            self.btn_toggle_panel.show()
            self.btn_toggle_panel.set_relative_position((item.rect.x + 8, item.rect.y + self.panel_header_h + 4))

    def _panel_at_point(self, pos: Tuple[int, int]) -> Optional[DockItem]:
        visible_items = [i for i in self.dock_items.values() if i.visible]
        for item in sorted(visible_items, key=lambda d: d.z, reverse=True):
            if item.rect.collidepoint(pos):
                return item
        return None

    def _snap_panel(self, panel_id: Optional[str]) -> None:
        if not panel_id:
            return
        item = self.dock_items.get(panel_id)
        if not item:
            return
        margin = 20
        snap = 6
        w, h = self.window_size
        bottom_margin = 20
        near_left = 0 <= (item.rect.left - margin) <= snap
        near_right = 0 <= (w - margin - item.rect.right) <= snap
        near_bottom = 0 <= (h - bottom_margin - item.rect.bottom) <= snap
        if near_left:
            item.dock = "left"
        elif near_right:
            item.dock = "right"
        elif near_bottom:
            item.dock = "bottom"
        else:
            item.dock = "floating"

    def _handle_dock_mouse_down(self, event: pygame.event.Event) -> bool:
        if event.button != 1:
            return False
        target = self._panel_at_point(event.pos)
        if not target:
            return False
        if self._panel_close_rect(target).collidepoint(event.pos):
            target.visible = False
            self._save_panel_layout()
            self._update_layout()
            return True
        for mode, rect in self._panel_resize_handles(target):
            if rect.collidepoint(event.pos):
                self.dock_resizing = (target.id, mode, (event.pos[0], event.pos[1]))
                self.dock_active_panel = target.id
                self._bump_panel(target.id)
                self.dock_last_action = "resize"
                return True
        if self._panel_header_rect(target).collidepoint(event.pos):
            self.dock_dragging = (target.id, (event.pos[0] - target.rect.x, event.pos[1] - target.rect.y))
            self.dock_active_panel = target.id
            self._bump_panel(target.id)
            self.dock_last_action = "drag"
            return True
        return False

    def _handle_dock_mouse_motion(self, event: pygame.event.Event) -> bool:
        handled = False
        if self.dock_dragging:
            pid, offset = self.dock_dragging
            item = self.dock_items.get(pid)
            if item:
                item.dock = "floating"
                self.dock_last_action = "drag"
                item.rect.x = event.pos[0] - offset[0]
                item.rect.y = event.pos[1] - offset[1]
                handled = True
        if self.dock_resizing:
            pid, mode, start = self.dock_resizing
            item = self.dock_items.get(pid)
            if item:
                item.dock = "floating"
                self.dock_last_action = "resize"
                start_x, start_y = start
                dx = event.pos[0] - start[0]
                dy = event.pos[1] - start[1]
                r = item.rect
                min_w, min_h = item.min_size
                if "l" in mode:
                    new_x = r.x + dx
                    new_w = r.width - dx
                    if new_w >= min_w:
                        r.width = new_w
                        r.x = new_x
                        start_x = event.pos[0]
                if "r" in mode:
                    new_w = r.width + dx
                    if new_w >= min_w:
                        r.width = new_w
                        start_x = event.pos[0]
                if "t" in mode:
                    new_y = r.y + dy
                    new_h = r.height - dy
                    if new_h >= min_h:
                        r.height = new_h
                        r.y = new_y
                        start_y = event.pos[1]
                if "b" in mode:
                    new_h = r.height + dy
                    if new_h >= min_h:
                        r.height = new_h
                        start_y = event.pos[1]
                self.dock_resizing = (pid, mode, (start_x, start_y))
                handled = True
        if handled:
            self._update_layout()
        return handled

    def _handle_dock_mouse_up(self, event: pygame.event.Event) -> None:
        if event.button != 1:
            return
        active = self.dock_active_panel
        self.dock_dragging = None
        self.dock_resizing = None
        if active and self.dock_last_action == "drag":
            self._snap_panel(active)
            self._update_layout()
            self._save_panel_layout()
        self.dock_active_panel = None
        self.dock_last_action = None

    def _load_sim(self) -> None:
        if not self.scenario_name:
            return
        self._clear_errors()
        self._clear_console()
        scenario_path = self.scenario_root / self.scenario_name
        try:
            world_cfg, robot_cfg = load_scenario(scenario_path)
            self.sim = Simulator()
            self.sim.load(
                scenario_path,
                world_cfg,
                robot_cfg,
                top_down=self.top_down_mode,
                ignore_terrain=self.force_empty_world,
            )
        except Exception:
            self._record_error("Scenario load failed", traceback.format_exc())
            return
        self.status_text = f"Loaded scenario '{self.scenario_name}'"
        self._sim_time_accum = 0.0
        # refresh editor text
        controller = scenario_path / "controller.py"
        if controller.exists():
            self.editor.set_text(controller.read_text(encoding="utf-8"))
        if self.sim and self.sim.last_controller_error:
            self._record_error("Controller import failed", self.sim.last_controller_error)
            self.sim.clear_controller_error()
        self._refresh_device_help()
        self._prime_logger_signals()
        pose = self._robot_pose_now()
        if pose:
            self.pose_history = [pose]
            self.pose_redo.clear()
        self._refresh_hover_menu()

    def run(self) -> None:
        try:
            while self.running:
                dt = self.clock.tick(60) / 1000.0
                self._stepped_this_frame = False
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.type == pygame.KEYDOWN:
                        mods = getattr(event, "mod", 0)
                        code_focused = self._panel_visible("code") and self.editor.has_focus
                        # Editor-focused keys still go through, but we intercept global transport when editor unfocused.
                        if not code_focused:
                            if event.key == pygame.K_SPACE:
                                # toggle play/pause
                                self.playing = not self.playing
                                self.btn_play.set_text("Play" if not self.playing else "Pause")
                            elif event.key == pygame.K_RIGHT:
                                # single step
                                self.playing = False
                                self.btn_play.set_text("Play")
                                if self.sim:
                                    try:
                                        self.sim.step(self.sim.dt)
                                        self._stepped_this_frame = True
                                    except Exception:
                                        self._record_error("Simulation error", traceback.format_exc())
                                    if self.sim and self.sim.last_controller_error:
                                        self._record_error("Controller error", self.sim.last_controller_error)
                                        self.sim.clear_controller_error()
                        if event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                            self._zoom(1.1)
                        if event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                            self._zoom(1.0 / 1.1)
                        if (event.key == pygame.K_z) and (mods & (pygame.KMOD_CTRL | pygame.KMOD_META | pygame.KMOD_GUI)):
                            if mods & pygame.KMOD_SHIFT:
                                self._redo_robot_pose()
                            else:
                                self._undo_robot_pose()
                        if event.key in (pygame.K_y,) and (mods & (pygame.KMOD_CTRL | pygame.KMOD_META | pygame.KMOD_GUI)):
                            self._redo_robot_pose()
                    if event.type == pygame.VIDEORESIZE:
                        self.window_size = (event.w, event.h)
                        self.window_surface = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                        self.manager.set_window_resolution(self.window_size)
                        self._update_layout()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.hover_menu and self.hover_menu.handle_event(event):
                            continue
                        if self._handle_dock_mouse_down(event):
                            continue
                        self._handle_state_click(event)
                        self._handle_reposition_click(event)
                        self._handle_pan_start(event)
                    if event.type == pygame.MOUSEBUTTONUP:
                        if event.button in (1, 2, 3):
                            self.pan_active = False
                            self.pan_start = None
                        if event.button == 1:
                            self._finalize_reposition()
                            self._handle_dock_mouse_up(event)
                    if event.type == pygame.MOUSEMOTION:
                        if self.hover_menu:
                            self.hover_menu.handle_event(event)
                        if self._handle_dock_mouse_motion(event):
                            continue
                        self._handle_pan_motion(event)
                    if event.type == pygame.MOUSEWHEEL:
                        self._handle_scroll(event)
                    if event.type == pygame.KEYDOWN:
                        mods = getattr(event, "mod", 0)
                        if event.key == pygame.K_s and (mods & (pygame.KMOD_CTRL | pygame.KMOD_META | pygame.KMOD_GUI)):
                            self._save_code()
                        if event.key == pygame.K_f and (mods & (pygame.KMOD_CTRL | pygame.KMOD_META | pygame.KMOD_GUI)):
                            self._format_code()
                    # Always pass events to UI and editor so mouse clicks work
                    self.manager.process_events(event)
                    if self._panel_visible("code"):
                        self.editor.handle_event(event)
                    self._handle_ui_event(event)
                self.manager.update(dt)
                sim_advanced = 0.0
                if self.playing and self.sim:
                    try:
                        sim_dt = self.sim.dt
                        # Accumulate time with a small cap to avoid spiraling after stalls.
                        self._sim_time_accum = min(self._sim_time_accum + dt, sim_dt * 8.0)
                        steps = 0
                        while self._sim_time_accum >= sim_dt and steps < 8:
                            self.sim.step(sim_dt)
                            self._sim_time_accum -= sim_dt
                            steps += 1
                        if steps:
                            sim_advanced = steps * sim_dt
                            self._stepped_this_frame = True
                    except Exception:
                        self._record_error("Simulation error", traceback.format_exc())
                if self.sim and self.sim.last_controller_error:
                    self._record_error("Controller error", self.sim.last_controller_error)
                    self.sim.clear_controller_error()
                # Only log when the sim actually advances
                self._update_live_state(sim_advanced if self._stepped_this_frame else 0.0, self._stepped_this_frame)
                if self.hover_menu:
                    self.hover_menu.update_hover(pygame.mouse.get_pos())
                self._draw()
        finally:
            self._save_panel_layout()
            sys.stdout = self._orig_stdout
        pygame.quit()

    def _handle_ui_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.dropdown:
                self.scenario_name = event.text if event.text != "<none>" else None
            elif event.ui_element == self.dropdown_logger_rate:
                self._set_logger_rate(event.text)
            elif event.ui_element == self.dropdown_logger_duration:
                self._set_logger_duration(event.text)
        if event.type != pygame_gui.UI_BUTTON_PRESSED:
            return
        if event.ui_element == self.btn_reload_scenario:
            self._load_sim()
        elif event.ui_element == self.btn_play:
            if self.error_log:
                self.status_text = "Clear errors before running"
                self.playing = False
                self.btn_play.set_text("Play")
            else:
                self.playing = not self.playing
                self.btn_play.set_text("Play" if not self.playing else "Pause")
        elif event.ui_element == self.btn_step:
            self.playing = False
            self.btn_play.set_text("Play")
            if self.sim:
                try:
                    self.sim.step(self.sim.dt)
                except Exception:
                    self._record_error("Simulation error", traceback.format_exc())
                if self.sim and self.sim.last_controller_error:
                    self._record_error("Controller error", self.sim.last_controller_error)
                    self.sim.clear_controller_error()
        elif event.ui_element == self.btn_snap:
            self._save_snapshot()
        elif event.ui_element == self.btn_load_snap:
            self._load_snapshot()
        elif event.ui_element == self.btn_reload_code:
            if self.sim:
                self.sim.clear_controller_error()
                self.sim.reload_controller()
                if self.sim.last_controller_error:
                    self._record_error("Controller reload failed", self.sim.last_controller_error)
                    self.sim.clear_controller_error()
        elif event.ui_element == self.btn_save_code:
            self._save_code()
        elif event.ui_element == self.btn_format_code:
            self._format_code()
        elif event.ui_element == self.btn_clear_errors:
            self._clear_errors()
        elif event.ui_element == self.btn_toggle_panel:
            self._clear_console()
        elif event.ui_element == self.btn_logger_toggle:
            self._toggle_logging()
        elif event.ui_element == self.btn_logger_export:
            self._export_logger()
        elif event.ui_element == self.btn_reposition_mode:
            self.reposition_mode = not self.reposition_mode
            self.status_text = "Reposition mode on" if self.reposition_mode else "Reposition mode off"
        elif event.ui_element == self.btn_reset_pose:
            self._reset_pose()
        elif event.ui_element == self.btn_set_spawn:
            self._save_spawn_pose()
        elif event.ui_element == self.btn_toggle_help:
            self.show_device_help = not self.show_device_help
            self.btn_toggle_help.set_text("Show device help" if not self.show_device_help else "Hide device help")
            self.status_text = "Device help hidden" if not self.show_device_help else "Device help visible"
            self._update_layout()

    def _record_error(self, title: str, details: str, pause: bool = True) -> None:
        entry: Dict[str, str] = {"title": title, "details": details}
        hint = self._extract_line_hint(details)
        if hint:
            entry["line"] = hint
        self.error_log.append(entry)
        if len(self.error_log) > 6:
            self.error_log = self.error_log[-6:]
        if pause:
            self.playing = False
            self.btn_play.set_text("Play")
        self.status_text = f"{title} (paused)"
        logs_panel = self.dock_items.get("logs")
        if logs_panel:
            logs_panel.visible = True
            self._bump_panel("logs")
            self._update_layout()

    def _clear_errors(self) -> None:
        self.error_log.clear()
        if self.sim:
            self.sim.clear_controller_error()
        self.status_text = "Errors cleared; ready to run"

    def _clear_console(self) -> None:
        self.console_lines.clear()
        self._console_buffer = ""
        self.status_text = "Console cleared"

    def _append_console(self, data: str) -> None:
        # Accumulate by lines to keep panel tidy.
        self._console_buffer += data
        while "\n" in self._console_buffer:
            line, self._console_buffer = self._console_buffer.split("\n", 1)
            self.console_lines.append(line)
        if len(self.console_lines) > 200:
            self.console_lines = self.console_lines[-200:]

    def _extract_line_hint(self, tb: str) -> Optional[str]:
        for line in reversed(tb.splitlines()):
            if "controller.py" in line:
                return line.strip()
        return None

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        lines: List[str] = []
        for raw_line in text.splitlines():
            words = raw_line.split(" ")
            current = ""
            for w in words:
                trial = f"{current} {w}".strip()
                if font.size(trial)[0] > max_width and current:
                    lines.append(current)
                    current = w
                else:
                    current = trial
            lines.append(current)
        return lines

    def _update_live_state(self, sim_dt: float, stepped: bool) -> None:
        if not self.sim:
            self.live_state = {"motors": {}, "sensors": {}}
            return
        motors = {name: getattr(motor, "last_command", 0.0) for name, motor in self.sim.motors.items()}
        sensors = dict(getattr(self.sim, "last_sensor_readings", {}) or {})
        self.live_state = {"motors": motors, "sensors": sensors, "physics_warning": getattr(self.sim, "last_physics_warning", None)}
        if self.logger_enabled and stepped:
            self._logger_timer += sim_dt
            self._logger_elapsed += sim_dt
            if self._logger_timer >= self.logger_interval:
                self._logger_timer = 0.0
                sample: Dict[str, object] = {"t": getattr(self.sim, "time", 0.0)}
                for sig in sorted(self.logger_selected):
                    if sig.startswith("motor:"):
                        name = sig.split(":", 1)[1]
                        sample[sig] = motors.get(name, 0.0)
                    elif sig.startswith("sensor:"):
                        name = sig.split(":", 1)[1]
                        sample[sig] = sensors.get(name, None)
                self.logger_samples.append(sample)
                if len(self.logger_samples) > 1000:
                    self.logger_samples = self.logger_samples[-1000:]
                self.logger_status = "Logging"
            if self.logger_duration > 0 and self._logger_elapsed >= self.logger_duration:
                self.logger_enabled = False
                self.logger_status = "Logger stopped (duration reached)"
                self._logger_elapsed = 0.0
        elif not stepped:
            self._logger_timer = 0.0

    def _zoom(self, factor: float) -> None:
        self.scale = max(40.0, min(2000.0, self.scale * factor))
        self.status_text = f"Scale {self.scale:.1f}"

    def _handle_scroll(self, event: pygame.event.Event) -> None:
        mouse_pos = pygame.mouse.get_pos()
        if self.viewport_rect.collidepoint(mouse_pos):
            self._zoom(1.0 + 0.1 * event.y)
            self._update_hover_center(mouse_pos)

    def _handle_pan_start(self, event: pygame.event.Event) -> None:
        if not self.viewport_rect.collidepoint(event.pos):
            return
        world_point = screen_to_world(event.pos, self.viewport_rect, self.scale, self.offset)
        center = self._current_robot_center()
        near_center = False
        if center:
            cx, cy = world_to_screen(center, self.viewport_rect, self.scale, self.offset)
            dist = math.hypot(event.pos[0] - cx, event.pos[1] - cy)
            near_center = dist <= 14
        if event.button == 1 and near_center and self.sim:
            pose = self._robot_pose_now()
            if pose:
                self._ensure_pose_history_seed(pose)
                self.robot_dragging = True
                self.robot_drag_start = world_point
                self.robot_drag_center = center
                self.robot_drag_theta = pose[2]
                self.reposition_target = center
                self.status_text = "Drag to move robot; hold Shift while dragging to rotate"
        elif event.button in (1, 2, 3):
            # default pan
            self.pan_active = True
            self.pan_start = event.pos

    def _handle_pan_motion(self, event: pygame.event.Event) -> None:
        if self.robot_dragging and self.sim:
            world_point = screen_to_world(event.pos, self.viewport_rect, self.scale, self.offset)
            start = self.robot_drag_start or world_point
            center = self.robot_drag_center or start
            dx = world_point[0] - start[0]
            dy = world_point[1] - start[1]
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                start_angle = math.atan2(start[1] - center[1], start[0] - center[0])
                curr_angle = math.atan2(world_point[1] - center[1], world_point[0] - center[0])
                dtheta = curr_angle - start_angle
                self.reposition_angle = self.robot_drag_theta + dtheta
                self._apply_robot_reposition(center, self.reposition_angle)
            else:
                self.reposition_target = (center[0] + dx, center[1] + dy)
                self._apply_robot_reposition(self.reposition_target, self.robot_drag_theta)
            return
        if self.reposition_dragging and self.reposition_mode and self.viewport_rect.collidepoint(event.pos):
            self.reposition_target = screen_to_world(event.pos, self.viewport_rect, self.scale, self.offset)
            return
        if self.pan_active and self.pan_start:
            dx = (event.pos[0] - self.pan_start[0]) / max(self.scale, 1e-6)
            dy = (event.pos[1] - self.pan_start[1]) / max(self.scale, 1e-6)
            # Dragging right moves view right (invert previous direction)
            self.offset = (self.offset[0] + dx, self.offset[1] - dy)
            self.pan_start = event.pos
        else:
            self._update_hover_center(event.pos)

    def _view_reset(self) -> None:
        self.offset = (0.0, 0.0)
        self.scale = 400.0
        self.status_text = "View reset"

    def _view_center_robot(self) -> None:
        center = self._current_robot_center()
        if center:
            self.offset = (-center[0], -center[1])
            self.status_text = "View centered on robot"

    def _view_toggle_grid(self) -> None:
        self.view_options["grid"] = not self.view_options["grid"]
        self.status_text = "Grid on" if self.view_options["grid"] else "Grid off"

    def _view_toggle_motor_arrows(self) -> None:
        self.view_options["motor_arrows"] = not self.view_options["motor_arrows"]
        self.status_text = "Motor arrows on" if self.view_options["motor_arrows"] else "Motor arrows off"

    def _view_reposition(self) -> None:
        self.reposition_mode = True
        self.status_text = "Reposition: click-drag in viewport to place robot"

    def _current_robot_center(self) -> Optional[Tuple[float, float]]:
        if not self.sim or not self.sim.robot_cfg or not self.sim.robot_cfg.bodies:
            return None
        xs: List[float] = []
        ys: List[float] = []
        for body_cfg in self.sim.robot_cfg.bodies:
            body = self.sim.bodies.get(body_cfg.name)
            if not body:
                continue
            xs.append(body.pose.x)
            ys.append(body.pose.y)
        if not xs or not ys:
            return None
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def _update_hover_center(self, mouse_pos: Tuple[int, int]) -> None:
        center = self._current_robot_center()
        if not center:
            self.hover_robot_center = False
            return
        sx, sy = world_to_screen(center, self.viewport_rect, self.scale, self.offset)
        self.hover_robot_center = math.hypot(mouse_pos[0] - sx, mouse_pos[1] - sy) <= 14

    def _handle_reposition_click(self, event: pygame.event.Event) -> None:
        # legacy reposition button support (not needed for direct drag)
        if self.reposition_mode and event.button == 1 and self.viewport_rect.collidepoint(event.pos):
            world_point = screen_to_world(event.pos, self.viewport_rect, self.scale, self.offset)
            spawn = self._spawn_from_body()
            if spawn:
                self.reposition_angle = spawn[2]
            self.reposition_dragging = True
            self.reposition_target = world_point
            self.status_text = "Drag to set robot start; release to apply"

    def _finalize_reposition(self) -> None:
        if self.robot_dragging:
            self.robot_dragging = False
            self.reposition_dragging = False
            self.robot_drag_start = None
            self.robot_drag_center = None
            self.status_text = "Robot moved; play or save spawn"
            # record final pose for undo/redo
            pose = self._robot_pose_now()
            if pose:
                self._push_pose_history(pose)
            return
        if not (self.reposition_mode and self.reposition_target and self.sim):
            return
        self._apply_robot_reposition(self.reposition_target, self.reposition_angle)
        self.reposition_dragging = False
        self.status_text = "Robot moved; play or save spawn"

    def _apply_robot_reposition(self, pos: Tuple[float, float], theta: float) -> None:
        if not self.sim:
            return
        self.playing = False
        self.btn_play.set_text("Play")
        self.sim.reposition_robot((pos[0], pos[1], theta), zero_velocity=True, set_as_spawn=False)
        self.reposition_target = pos

    def _spawn_from_body(self) -> Optional[Tuple[float, float, float]]:
        if not self.sim or not self.sim.robot_cfg or not self.sim.robot_cfg.bodies:
            return None
        root_cfg = self.sim.robot_cfg.bodies[0]
        body = self.sim.bodies.get(root_cfg.name)
        if not body:
            return None
        return (body.pose.x - root_cfg.pose[0], body.pose.y - root_cfg.pose[1], body.pose.theta - root_cfg.pose[2])

    def _robot_pose_now(self) -> Optional[Tuple[float, float, float]]:
        if not self.sim or not self.sim.robot_cfg or not self.sim.robot_cfg.bodies:
            return None
        root_cfg = self.sim.robot_cfg.bodies[0]
        body = self.sim.bodies.get(root_cfg.name)
        if not body:
            return None
        return (body.pose.x - root_cfg.pose[0], body.pose.y - root_cfg.pose[1], body.pose.theta - root_cfg.pose[2])

    def _ensure_pose_history_seed(self, pose: Tuple[float, float, float]) -> None:
        if not self.pose_history:
            self.pose_history.append(pose)

    def _push_pose_history(self, pose: Tuple[float, float, float]) -> None:
        if self.pose_history and pose == self.pose_history[-1]:
            return
        self.pose_history.append(pose)
        if len(self.pose_history) > 50:
            self.pose_history = self.pose_history[-50:]
        self.pose_redo.clear()

    def _undo_robot_pose(self) -> None:
        if len(self.pose_history) < 2:
            self.status_text = "No undo available"
            return
        current = self.pose_history.pop()
        self.pose_redo.append(current)
        pose = self.pose_history[-1]
        self._apply_robot_reposition((pose[0], pose[1]), pose[2])
        self.status_text = "Undo robot pose"

    def _redo_robot_pose(self) -> None:
        if not self.pose_redo:
            self.status_text = "No redo available"
            return
        pose = self.pose_redo.pop()
        self._apply_robot_reposition((pose[0], pose[1]), pose[2])
        self.pose_history.append(pose)
        self.status_text = "Redo robot pose"

    def _handle_state_click(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        panel = self.dock_items.get("state")
        if not panel or not panel.visible or not panel.rect.collidepoint(event.pos):
            return
        for sig, rect in self.signal_hitboxes.items():
            if rect.collidepoint(event.pos):
                if sig in self.logger_selected:
                    self.logger_selected.remove(sig)
                else:
                    self.logger_selected.add(sig)
                return

    def _set_logger_rate(self, label: str) -> None:
        mapping = {"120 Hz": 1.0 / 120.0, "60 Hz": 1.0 / 60.0, "30 Hz": 1.0 / 30.0, "10 Hz": 0.1}
        self.logger_interval = mapping.get(label, 1.0 / 30.0)
        self.status_text = f"Logger rate {label}"

    def _set_logger_duration(self, label: str) -> None:
        mapping = {"5 s": 5.0, "15 s": 15.0, "60 s": 60.0, "Unlimited": 0.0}
        self.logger_duration = mapping.get(label, 15.0)
        self.status_text = f"Logger duration {label}"

    def _toggle_logging(self) -> None:
        if not self.sim:
            self.status_text = "Load a scenario before logging"
            return
        self.logger_enabled = not self.logger_enabled
        self._logger_elapsed = 0.0
        self._logger_timer = 0.0
        self.logger_status = "Logging…" if self.logger_enabled else "Logger paused"
        self.btn_logger_toggle.set_text("Stop logging" if self.logger_enabled else "Start logging")

    def _export_logger(self) -> None:
        if not self.scenario_name or not self.logger_samples:
            self.status_text = "No log samples to export"
            return
        log_dir = self.scenario_root / self.scenario_name / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        fname = log_dir / f"log_{self.sim.step_index:06d}.csv" if self.sim else log_dir / "log.csv"
        all_keys: List[str] = []
        for sample in self.logger_samples:
            for k in sample.keys():
                if k not in all_keys:
                    all_keys.append(k)
        try:
            with fname.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=all_keys)
                writer.writeheader()
                writer.writerows(self.logger_samples)
            self.status_text = f"Exported {len(self.logger_samples)} samples to {fname.name}"
        except Exception:
            self.status_text = "Failed to export log"

    def _reset_pose(self) -> None:
        if not self.sim:
            return
        self.sim.reset_to_spawn()
        self.playing = False
        self.btn_play.set_text("Play")
        self.status_text = "Reset to spawn pose"

    def _save_spawn_pose(self) -> None:
        if not self.sim:
            return
        spawn = self._spawn_from_body()
        if not spawn:
            self.status_text = "Unable to infer spawn pose"
            return
        self.sim.reposition_robot(spawn, zero_velocity=True, set_as_spawn=True)
        self.status_text = "Saved current pose as spawn"

    def _save_code(self) -> None:
        if not self.scenario_name:
            return
        controller = self.scenario_root / self.scenario_name / "controller.py"
        try:
            controller.write_text(self.editor.text(), encoding="utf-8")
            if self.sim:
                self.sim.clear_controller_error()
                self.sim.reload_controller()
                if self.sim.last_controller_error:
                    self._record_error("Controller reload failed", self.sim.last_controller_error)
                    self.sim.clear_controller_error()
                    return
            self.status_text = "Saved controller and reloaded"
        except Exception:
            self._record_error("Save/reload failed", traceback.format_exc())

    def _format_code(self) -> None:
        text = self.editor.text()
        formatted = None
        formatter = None
        try:
            import black

            formatted = black.format_str(text, mode=black.Mode())
            formatter = "black"
        except Exception:
            try:
                import autopep8

                formatted = autopep8.fix_code(text)
                formatter = "autopep8"
            except Exception:
                formatter = None
        if formatted:
            self.editor.set_text(formatted)
            self.status_text = f"Formatted with {formatter}"
        else:
            self.status_text = "Formatter unavailable; left text unchanged"

    def _save_snapshot(self) -> None:
        if not self.sim or not self.scenario_name:
            return
        snap = self.sim.snapshot()
        snap_dir = self.scenario_root / self.scenario_name / "snapshots"
        snap_path = snap_dir / f"snap_{self.sim.step_index:06d}.json"
        save_snapshot(snap_path, snap)
        print(f"Saved snapshot {snap_path}")

    def _load_snapshot(self) -> None:
        if not self.scenario_name or not self.sim:
            return
        snap_dir = self.scenario_root / self.scenario_name / "snapshots"
        snaps = sorted(snap_dir.glob("snap_*.json")) if snap_dir.exists() else []
        if not snaps:
            print("No snapshots found")
            return
        snap = load_snapshot(snaps[-1])
        self.sim.apply_snapshot(snap)
        print(f"Loaded snapshot {snaps[-1].name}")

    def _refresh_hover_menu(self) -> None:
        font = pygame.font.Font(pygame.font.get_default_font(), 14)
        def panel_toggle(pid: str, title: str) -> Dict[str, object]:
            return {
                "label": title,
                "action": lambda pid=pid: self._toggle_panel(pid),
                "checked": lambda pid=pid: self.dock_items.get(pid, None) and self.dock_items[pid].visible,
            }
        def scenario_entry(name: str) -> Dict[str, object]:
            return {"label": name, "action": lambda n=name: self._select_scenario(n)}
        self.hover_menu = HoverMenu(
            [
                ("Scenario", [{"label": "Reload", "action": self._load_sim}] + [scenario_entry(n) for n in self.scenario_names]),
                (
                    "Run",
                    [
                        {"label": "Play" if not self.playing else "Pause", "action": self._toggle_play},
                        {"label": "Step", "action": self._step_once},
                    ],
                ),
                (
                    "Code",
                    [
                        {"label": "Reload code", "action": self._reload_code},
                        {"label": "Save code", "action": self._save_code},
                        {"label": "Format code", "action": self._format_code},
                    ],
                ),
                (
                    "Snapshots",
                    [
                        {"label": "Save snapshot", "action": self._save_snapshot},
                        {"label": "Load snapshot", "action": self._load_snapshot},
                    ],
                ),
                (
                    "View",
                    [
                        {"label": "Reset view", "action": self._view_reset},
                        {"label": "Center robot", "action": self._view_center_robot},
                        {"label": "Toggle grid", "action": self._view_toggle_grid, "checked": lambda: self.view_options.get("grid", False)},
                        {
                            "label": "Toggle motor arrows",
                            "action": self._view_toggle_motor_arrows,
                            "checked": lambda: self.view_options.get("motor_arrows", True),
                        },
                        {"label": "Reposition robot", "action": self._view_reposition},
                    ],
                ),
                (
                    "Panels",
                    [
                        panel_toggle("code", "Code"),
                        panel_toggle("devices", "Devices"),
                        panel_toggle("state", "State"),
                        panel_toggle("logs", "Logs"),
                        panel_toggle("console", "Console"),
                    ],
                ),
                (
                    "Logging",
                    [
                        {"label": "Start/Stop logging", "action": self._toggle_logging},
                        {"label": "Export log", "action": self._export_logger},
                    ],
                ),
            ],
            pos=(20, 8),
            font=font,
        )
    def _draw(self) -> None:
        self.window_surface.fill((18, 18, 18))
        pygame.draw.rect(self.window_surface, (10, 10, 10), self.viewport_rect)
        pygame.draw.rect(self.window_surface, (80, 80, 80), self.viewport_rect, 1)
        if self.sim:
            self.window_surface.set_clip(self.viewport_rect)
            if self.view_options.get("grid", False):
                self._draw_grid()
            self._draw_world()
            self.window_surface.set_clip(None)
        if self.error_log:
            overlay_rect = pygame.Rect(self.viewport_rect.x + 12, self.viewport_rect.y + 12, 280, 60)
            pygame.draw.rect(self.window_surface, (60, 30, 30), overlay_rect)
            pygame.draw.rect(self.window_surface, (160, 80, 80), overlay_rect, 1)
            font_small = pygame.font.Font(pygame.font.get_default_font(), 14)
            self.window_surface.blit(
                font_small.render("Paused due to errors.", True, (240, 180, 180)),
                (overlay_rect.x + 8, overlay_rect.y + 8),
            )
            self.window_surface.blit(
                font_small.render("Open the Logs panel to inspect.", True, (220, 200, 200)),
                (overlay_rect.x + 8, overlay_rect.y + 30),
            )
        visible_panels = [item for item in self.dock_items.values() if item.visible]
        ordered = sorted(visible_panels, key=lambda d: (0 if d.dock != "floating" else 1, d.z))
        for item in ordered:
            self._render_panel(item)
        self.manager.draw_ui(self.window_surface)
        if self.hover_menu:
            self.hover_menu.draw(self.window_surface)
        font = pygame.font.Font(pygame.font.get_default_font(), 16)
        status = f"Scenario: {self.scenario_name or '<none>'} | Scale: {self.scale:.1f} | Offset: ({self.offset[0]:.2f},{self.offset[1]:.2f})"
        status_surf = font.render(status, True, (220, 220, 220))
        self.window_surface.blit(status_surf, (20, self.window_size[1] - 44))
        hint_surf = font.render(self.status_text, True, (190, 210, 230))
        self.window_surface.blit(hint_surf, (20, self.window_size[1] - 24))
        # Device help overlay near devices panel
        devices_inner = self.panel_inner_rects.get("devices")
        if self.device_help_lines and self._panel_visible("devices") and self.show_device_help and devices_inner:
            box_h = 18 * len(self.device_help_lines) + 8
            rect = pygame.Rect(devices_inner.x, max(50, devices_inner.y - box_h - 8), devices_inner.width, box_h)
            pygame.draw.rect(self.window_surface, (18, 22, 26), rect)
            pygame.draw.rect(self.window_surface, (70, 90, 110), rect, 1)
            for i, line in enumerate(self.device_help_lines):
                txt = font.render(line, True, (210, 220, 230))
                self.window_surface.blit(txt, (rect.x + 6, rect.y + 4 + i * 18))
        pygame.display.update()

    def _render_panel(self, item: DockItem) -> None:
        rect = item.rect
        header_rect = self._panel_header_rect(item)
        inner_rect = self.panel_inner_rects.get(item.id, self._panel_inner_rect(item))
        pygame.draw.rect(self.window_surface, (24, 28, 32), rect)
        pygame.draw.rect(self.window_surface, (90, 110, 130), rect, 1)
        pygame.draw.rect(self.window_surface, (34, 38, 44), header_rect)
        pygame.draw.rect(self.window_surface, (110, 130, 150), header_rect, 1)
        font = pygame.font.Font(pygame.font.get_default_font(), 14)
        self.window_surface.blit(font.render(item.title, True, (210, 220, 230)), (header_rect.x + 8, header_rect.y + 5))
        dock_label = {"left": "L", "right": "R", "bottom": "B", "floating": "F"}.get(item.dock, "")
        if dock_label:
            self.window_surface.blit(font.render(dock_label, True, (160, 190, 210)), (header_rect.right - 60, header_rect.y + 5))
        close_rect = self._panel_close_rect(item)
        pygame.draw.rect(self.window_surface, (70, 50, 50), close_rect)
        pygame.draw.rect(self.window_surface, (140, 110, 110), close_rect, 1)
        self.window_surface.blit(font.render("×", True, (240, 200, 200)), (close_rect.x + 5, close_rect.y + 2))
        for _, hrect in self._panel_resize_handles(item):
            pygame.draw.rect(self.window_surface, (50, 60, 70), hrect)
            pygame.draw.rect(self.window_surface, (120, 140, 160), hrect, 1)
        if inner_rect.width > 0 and inner_rect.height > 0:
            self._draw_panel_content(item.id, inner_rect)

    def _draw_panel_content(self, panel_id: str, inner_rect: pygame.Rect) -> None:
        if panel_id == "code":
            self.editor.rect = inner_rect
            self.editor.draw(self.window_surface)
        elif panel_id == "devices":
            self._draw_devices_panel(inner_rect)
        elif panel_id == "state":
            self._draw_state_panel(inner_rect)
        elif panel_id == "logs":
            self._draw_logs_panel(inner_rect)
        elif panel_id == "console":
            self._draw_console_panel(inner_rect)

    def _draw_grid(self) -> None:
        min_x, min_y = screen_to_world(self.viewport_rect.bottomleft, self.viewport_rect, self.scale, self.offset)
        max_x, max_y = screen_to_world(self.viewport_rect.topright, self.viewport_rect, self.scale, self.offset)
        min_x, max_x = sorted([min_x, max_x])
        min_y, max_y = sorted([min_y, max_y])
        spacing = 0.25
        if self.scale > 600:
            spacing = 0.1
        elif self.scale < 150:
            spacing = 0.5
        start_x = math.floor(min_x / spacing) * spacing
        start_y = math.floor(min_y / spacing) * spacing
        end_x = math.ceil(max_x / spacing) * spacing
        end_y = math.ceil(max_y / spacing) * spacing
        color = (28, 32, 36)
        for x in frange(start_x, end_x + spacing, spacing):
            p1 = world_to_screen((x, min_y), self.viewport_rect, self.scale, self.offset)
            p2 = world_to_screen((x, max_y), self.viewport_rect, self.scale, self.offset)
            pygame.draw.line(self.window_surface, color, p1, p2, 1)
        for y in frange(start_y, end_y + spacing, spacing):
            p1 = world_to_screen((min_x, y), self.viewport_rect, self.scale, self.offset)
            p2 = world_to_screen((max_x, y), self.viewport_rect, self.scale, self.offset)
            pygame.draw.line(self.window_surface, color, p1, p2, 1)

    def _draw_devices_panel(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.window_surface, (22, 26, 30), rect)
        pygame.draw.rect(self.window_surface, (70, 90, 120), rect, 1)
        font = pygame.font.Font(pygame.font.get_default_font(), 16)
        small = pygame.font.Font(pygame.font.get_default_font(), 14)
        mono = pygame.font.SysFont("Menlo", 14) or small
        self.window_surface.blit(font.render("Devices & controller hints", True, (190, 210, 230)), (rect.x + 8, rect.y + 6))
        y = rect.y + 36
        motors = ", ".join(self.sim.motors.keys()) if self.sim else "none"
        sensors = ", ".join(self.sim.sensors.keys()) if self.sim else "none"
        self.window_surface.blit(small.render(f"Motors: {motors or 'none'}", True, (200, 210, 220)), (rect.x + 8, y))
        y += 18
        self.window_surface.blit(small.render(f"Sensors: {sensors or 'none'}", True, (200, 210, 220)), (rect.x + 8, y))
        y += 26
        self.window_surface.blit(small.render("Control basics (examples):", True, (170, 200, 220)), (rect.x + 8, y))
        y += 18
        examples = [
            "Command motor:  sim.motors['left'].command(0.5, sim, dt)",
            "Read sensor:    value = sensors['front']",
            "Encoder ticks:  sensors['enc'].value",
        ]
        for line in examples:
            self.window_surface.blit(mono.render(line, True, (200, 220, 230)), (rect.x + 10, y))
            y += 18
        y += 10
        self.window_surface.blit(small.render("Tips:", True, (170, 200, 220)), (rect.x + 8, y))
        y += 18
        tips = [
            "Use the State tab to watch signals and log them.",
            "Toggle grid/view options from the dropdown in the viewport.",
            "Hide/show this help with the button above.",
        ]
        for line in tips:
            self.window_surface.blit(small.render(line, True, (200, 210, 220)), (rect.x + 10, y))
            y += 18
        if not self.show_device_help:
            warning = small.render("Help hidden (toggle to show).", True, (200, 180, 160))
            self.window_surface.blit(warning, (rect.x + 8, rect.bottom - 26))

    def _draw_state_panel(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.window_surface, (22, 24, 28), rect)
        pygame.draw.rect(self.window_surface, (70, 90, 120), rect, 1)
        font = pygame.font.Font(pygame.font.get_default_font(), 16)
        small = pygame.font.Font(pygame.font.get_default_font(), 14)
        self.signal_hitboxes = {}
        self.window_surface.blit(font.render("Live state + logger", True, (190, 210, 230)), (rect.x + 8, rect.y + 6))
        control_rows = 4 * 34 + 16
        y = rect.y + control_rows
        logger_line = f"{self.logger_status} | samples: {len(self.logger_samples)} | rate: {1.0/self.logger_interval:.1f} Hz"
        self.window_surface.blit(small.render(logger_line, True, (200, 210, 220)), (rect.x + 8, y))
        y += 20
        self.window_surface.blit(small.render("Live signals:", True, (180, 200, 220)), (rect.x + 8, y))
        y += 18
        motors = self.live_state.get("motors", {})
        sensors = self.live_state.get("sensors", {})
        for name, val in motors.items():
            line = f"motor {name}: {val:.2f}"
            self.window_surface.blit(small.render(line, True, (180, 220, 180)), (rect.x + 16, y))
            y += 16
        for name, val in sensors.items():
            line = f"sensor {name}: {val}"
            self.window_surface.blit(small.render(line, True, (200, 200, 180)), (rect.x + 16, y))
            y += 16
        y = max(y + 10, rect.y + 140)
        self.window_surface.blit(small.render("Signals to log (click to toggle):", True, (170, 200, 220)), (rect.x + 8, y))
        y += 18
        box_x = rect.x + 12
        box_w = rect.width - 24
        def draw_sig(label: str, enabled: bool, y_pos: int) -> None:
            box = pygame.Rect(box_x, y_pos, 14, 14)
            pygame.draw.rect(self.window_surface, (60, 70, 80), box, 1)
            if enabled:
                pygame.draw.rect(self.window_surface, (80, 200, 140), box.inflate(-4, -4))
            text = small.render(label, True, (210, 220, 230))
            self.window_surface.blit(text, (box.right + 6, y_pos - 2))
            self.signal_hitboxes[label] = pygame.Rect(box)
        for name in motors.keys():
            draw_sig(f"motor:{name}", f"motor:{name}" in self.logger_selected, y)
            y += 20
        for name in sensors.keys():
            draw_sig(f"sensor:{name}", f"sensor:{name}" in self.logger_selected, y)
            y += 20

    def _panel_menu_options(self) -> List[Tuple[str, str]]:
        return [
            ("code", "Code"),
            ("console", "Console"),
            ("devices", "Devices"),
            ("state", "State"),
            ("logs", "Logs"),
        ]

    def _handle_panel_menu_event(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        btn_rect = self._panel_menu_rect()
        if btn_rect.collidepoint(event.pos):
            self.panel_menu_open = not self.panel_menu_open
            return True
        if not self.panel_menu_open:
            return False
        for pid, rect in self.panel_menu_regions.items():
            if rect.collidepoint(event.pos):
                item = self.dock_items.get(pid)
                if item:
                    item.visible = not item.visible
                    self._bump_panel(pid)
                    self._update_layout()
                    self._save_panel_layout()
                return True
        # Close if clicked outside menu
        self.panel_menu_open = False
        return False

    def _draw_panel_menu(self) -> None:
        btn_rect = self._panel_menu_rect()
        pygame.draw.rect(self.window_surface, (30, 34, 38), btn_rect)
        pygame.draw.rect(self.window_surface, (90, 110, 130), btn_rect, 1)
        font = pygame.font.Font(pygame.font.get_default_font(), 14)
        label = "Panels ▼" if not self.panel_menu_open else "Panels ▲"
        self.window_surface.blit(font.render(label, True, (200, 210, 220)), (btn_rect.x + 8, btn_rect.y + 6))
        if not self.panel_menu_open:
            self.panel_menu_regions = {}
            return
        options = self._panel_menu_options()
        menu_w = 220
        menu_h = len(options) * 28 + 12
        menu_rect = pygame.Rect(btn_rect.x, btn_rect.bottom + 4, menu_w, menu_h)
        pygame.draw.rect(self.window_surface, (24, 26, 30), menu_rect)
        pygame.draw.rect(self.window_surface, (80, 100, 120), menu_rect, 1)
        self.panel_menu_regions = {}
        for i, (pid, label) in enumerate(options):
            row = pygame.Rect(menu_rect.x + 6, menu_rect.y + 6 + i * 28, menu_w - 12, 24)
            pygame.draw.rect(self.window_surface, (30, 34, 40), row)
            pygame.draw.rect(self.window_surface, (70, 90, 110), row, 1)
            item = self.dock_items.get(pid)
            checked = bool(item and item.visible)
            box = pygame.Rect(row.x + 6, row.y + 4, 16, 16)
            pygame.draw.rect(self.window_surface, (90, 110, 130), box, 1)
            if checked:
                pygame.draw.rect(self.window_surface, (120, 200, 150), box.inflate(-4, -4))
            self.window_surface.blit(font.render(label, True, (210, 220, 230)), (box.right + 6, row.y + 4))
            self.panel_menu_regions[pid] = row

    def _draw_logs_panel(self, rect: pygame.Rect) -> None:
        content_font = pygame.font.Font(pygame.font.get_default_font(), 14)
        font = pygame.font.Font(pygame.font.get_default_font(), 15)
        has_error = bool(self.error_log)
        bg = (30, 22, 22) if has_error else (22, 26, 22)
        pygame.draw.rect(self.window_surface, bg, rect)
        pygame.draw.rect(self.window_surface, (90, 70, 70) if has_error else (70, 90, 70), rect, 1)
        header = f"Errors ({len(self.error_log)})"
        self.window_surface.blit(
            font.render(header, True, (240, 140, 140) if has_error else (160, 190, 160)),
            (rect.x + 8, rect.y + 6),
        )
        y = rect.y + 28
        max_width = rect.width - 16
        if not has_error:
            self.window_surface.blit(
                content_font.render("No errors. Happy coding!", True, (170, 190, 170)),
                (rect.x + 8, y),
            )
            return
        latest = self.error_log[-1]
        body_lines: List[str] = []
        if latest.get("title"):
            body_lines.extend(self._wrap_text(latest["title"], content_font, max_width))
        if latest.get("line"):
            body_lines.append(latest["line"])
        detail_lines = self._wrap_text(latest.get("details", ""), content_font, max_width)
        body_lines.extend(detail_lines[-8:])
        for line in body_lines:
            if y > rect.bottom - 18:
                break
            self.window_surface.blit(content_font.render(line, True, (230, 200, 200)), (rect.x + 8, y))
            y += 18

    def _draw_console_panel(self, rect: pygame.Rect) -> None:
        content_font = pygame.font.Font(pygame.font.get_default_font(), 14)
        font = pygame.font.Font(pygame.font.get_default_font(), 15)
        bg = (22, 26, 30)
        pygame.draw.rect(self.window_surface, bg, rect)
        pygame.draw.rect(self.window_surface, (70, 90, 120), rect, 1)
        header = "Console output"
        self.window_surface.blit(font.render(header, True, (180, 210, 240)), (rect.x + 8, rect.y + 6))
        y = rect.y + 28
        max_width = rect.width - 16
        lines = self.console_lines[-20:] if self.console_lines else []
        if not lines:
            self.window_surface.blit(
                content_font.render("No prints yet.", True, (170, 190, 210)), (rect.x + 8, y)
            )
            return
        for line in lines:
            wrapped = self._wrap_text(line, content_font, max_width)
            for w in wrapped:
                if y > rect.bottom - 18:
                    return
                self.window_surface.blit(content_font.render(w, True, (210, 220, 230)), (rect.x + 8, y))
                y += 18

    def _draw_world(self) -> None:
        assert self.sim
        for body in self.sim.bodies.values():
            color = getattr(body.material, "custom", {}).get("color", None) or (140, 140, 140)
            if isinstance(body.shape, Polygon):
                verts = body.shape._world_vertices(body.pose)
                pts = [world_to_screen(v, self.viewport_rect, self.scale, self.offset) for v in verts]
                pygame.draw.polygon(self.window_surface, color, pts, 0)
                pygame.draw.polygon(self.window_surface, (30, 30, 30), pts, 1)
        if self.reposition_mode and self.reposition_target:
            px, py = self.reposition_target
            center = world_to_screen((px, py), self.viewport_rect, self.scale, self.offset)
            pygame.draw.circle(self.window_surface, (120, 160, 220), center, 8, 2)
            pygame.draw.line(self.window_surface, (120, 160, 220), (center[0] - 8, center[1]), (center[0] + 8, center[1]), 1)
            pygame.draw.line(self.window_surface, (120, 160, 220), (center[0], center[1] - 8), (center[0], center[1] + 8), 1)
        # motor arrows
        if self.view_options.get("motor_arrows", True):
            for motor in self.sim.motors.values():
                parent = motor.parent
                if not parent:
                    continue
                pose = parent.pose.compose(motor.mount_pose)
                start = world_to_screen((pose.x, pose.y), self.viewport_rect, self.scale, self.offset)
                length = 0.05 + abs(motor.last_command) * 0.1
                direction = (pygame.math.Vector2(1, 0).rotate_rad(pose.theta).x, pygame.math.Vector2(1, 0).rotate_rad(pose.theta).y)
                end_world = (pose.x + direction[0] * length, pose.y + direction[1] * length)
                end = world_to_screen(end_world, self.viewport_rect, self.scale, self.offset)
                color = (0, 200, 120) if motor.last_command >= 0 else (200, 80, 80)
                pygame.draw.line(self.window_surface, color, start, end, 3)
                pygame.draw.circle(self.window_surface, color, end, 4)
        # robot center hover indicator
        center = self._current_robot_center()
        if center:
            screen_center = world_to_screen(center, self.viewport_rect, self.scale, self.offset)
            color = (140, 200, 255) if (self.hover_robot_center or self.robot_dragging) else (90, 130, 170)
            pygame.draw.circle(self.window_surface, color, screen_center, 7, 2)
            pygame.draw.line(self.window_surface, color, (screen_center[0] - 6, screen_center[1]), (screen_center[0] + 6, screen_center[1]), 1)
            pygame.draw.line(self.window_surface, color, (screen_center[0], screen_center[1] - 6), (screen_center[0], screen_center[1] + 6), 1)


def main():
    app = RunnerApp()
    app.run()


if __name__ == "__main__":
    main()

