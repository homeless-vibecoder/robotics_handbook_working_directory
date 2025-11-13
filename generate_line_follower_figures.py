#!/usr/bin/env python3
"""
Generate conceptual and simulation-based figures for the line follower chapter.
Outputs are saved into `pictures/line_follower_images/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import math
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches

OUTPUT_DIR = Path(__file__).parent / "pictures" / "line_follower_images"


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def draw_conceptual_diagram(output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))

    # Draw floor and line
    ax.add_patch(
        patches.Rectangle(
            (-0.1, -0.4), 1.2, 0.8, facecolor="#f2f2f2", edgecolor="none", zorder=0
        )
    )
    ax.add_patch(
        patches.Rectangle(
            (-0.1, -0.025), 1.2, 0.05, facecolor="black", edgecolor="none", zorder=1
        )
    )

    # Robot body
    robot = patches.FancyBboxPatch(
        (0.25, -0.15),
        0.35,
        0.3,
        boxstyle="round,pad=0.02",
        linewidth=2,
        edgecolor="#555555",
        facecolor="#ffffff",
        zorder=2,
    )
    ax.add_patch(robot)

    # Wheels
    wheel_width = 0.05
    wheel_height = 0.26
    ax.add_patch(
        patches.Rectangle(
            (0.23, -0.13), wheel_width, wheel_height, facecolor="#333333", zorder=3
        )
    )
    ax.add_patch(
        patches.Rectangle(
            (0.62, -0.13), wheel_width, wheel_height, facecolor="#333333", zorder=3
        )
    )

    # Sensors
    sensor_offset = 0.12
    sensor_size = 0.02
    sensor_positions = [(0.3, sensor_offset), (0.3, -sensor_offset)]
    for x, dy in sensor_positions:
        sensor = patches.Circle(
            (x, dy), sensor_size, facecolor="#3c78d8", edgecolor="#0b5394", zorder=4
        )
        ax.add_patch(sensor)

    ax.annotate(
        "Left IR sensor",
        xy=(sensor_positions[0][0], sensor_positions[0][1]),
        xytext=(0.05, 0.35),
        arrowprops=dict(arrowstyle="->", color="#0b5394"),
        color="#0b5394",
    )
    ax.annotate(
        "Right IR sensor",
        xy=(sensor_positions[1][0], sensor_positions[1][1]),
        xytext=(0.05, -0.35),
        arrowprops=dict(arrowstyle="->", color="#0b5394"),
        color="#0b5394",
    )

    ax.annotate(
        "Line to follow",
        xy=(0.9, 0),
        xytext=(0.75, 0.25),
        arrowprops=dict(arrowstyle="->", color="#444444"),
        color="#222222",
    )

    ax.text(
        0.425,
        0.18,
        "Forward\nvelocity v",
        ha="center",
        va="center",
        color="#444444",
    )
    ax.annotate(
        "",
        xy=(0.44, 0.15),
        xytext=(0.62, 0.15),
        arrowprops=dict(arrowstyle="-|>", color="#444444"),
    )

    ax.set_xlim(-0.1, 1.0)
    ax.set_ylim(-0.5, 0.5)
    ax.axis("off")

    fig.tight_layout()
    fig.savefig(output_dir / "line_follower_setup.png", dpi=300)
    plt.close(fig)


@dataclass
class SimulationTrace:
    time: np.ndarray
    y: np.ndarray
    theta: np.ndarray
    v_l: np.ndarray
    v_r: np.ndarray
    left_sensor: np.ndarray
    right_sensor: np.ndarray


def simulate_bang_bang_controller(total_time: float = 12.0, dt: float = 0.02) -> SimulationTrace:
    steps = int(total_time / dt)
    t = np.linspace(0.0, total_time, steps, endpoint=False)

    # Parameters
    line_half_width = 0.025
    base_v = 0.4
    rotation_speed = 0.5
    wheel_base = 0.12
    sensor_offset = 0.06

    # State
    y = np.zeros(steps)
    theta = np.zeros(steps)
    v_l = np.zeros(steps)
    v_r = np.zeros(steps)
    left_sensor = np.zeros(steps)
    right_sensor = np.zeros(steps)

    current_y = 0.03
    current_theta = 0.1
    current_v_l = base_v
    current_v_r = base_v

    for i in range(steps):
        # Sensor model (binary)
        left_y = current_y + sensor_offset
        right_y = current_y - sensor_offset
        left_hit = abs(left_y) <= line_half_width
        right_hit = abs(right_y) <= line_half_width

        # Controller
        if left_hit and not right_hit:
            w_cmd = -rotation_speed
        elif right_hit and not left_hit:
            w_cmd = rotation_speed
        else:
            w_cmd = 0.0

        current_v_l = np.clip(base_v - w_cmd, -1.0, 1.0)
        current_v_r = np.clip(base_v + w_cmd, -1.0, 1.0)

        v = 0.5 * (current_v_r + current_v_l)
        w = (current_v_r - current_v_l) / wheel_base

        current_theta = wrap_angle(current_theta + w * dt)
        current_y = current_y + v * math.sin(current_theta) * dt

        y[i] = current_y
        theta[i] = current_theta
        v_l[i] = current_v_l
        v_r[i] = current_v_r
        left_sensor[i] = 1 if left_hit else 0
        right_sensor[i] = 1 if right_hit else 0

    return SimulationTrace(t, y, theta, v_l, v_r, left_sensor, right_sensor)


def wrap_angle(angle: float) -> float:
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle <= -math.pi:
        angle += 2 * math.pi
    return angle


def plot_bang_bang_trace(trace: SimulationTrace, output_dir: Path) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(8, 8), sharex=True)

    axes[0].plot(trace.time, trace.y * 100.0, color="#1f77b4")
    axes[0].axhline(0.0, color="black", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Lateral error y (cm)")
    axes[0].set_title("Bang-bang line tracking behaviour")

    axes[1].plot(trace.time, np.degrees(trace.theta), color="#ff7f0e")
    axes[1].set_ylabel("Heading θ (deg)")

    axes[2].plot(trace.time, trace.v_l, label="Left wheel", color="#2ca02c")
    axes[2].plot(trace.time, trace.v_r, label="Right wheel", color="#d62728")
    axes[2].set_ylabel("Wheel speed (m/s)")
    axes[2].legend(loc="upper right")

    axes[3].step(trace.time, trace.left_sensor, where="post", label="Left sensor", color="#3c78d8")
    axes[3].step(
        trace.time,
        trace.right_sensor,
        where="post",
        label="Right sensor",
        color="#9467bd",
    )
    axes[3].set_ylabel("Sensor")
    axes[3].set_xlabel("Time (s)")
    axes[3].set_yticks([0, 1])
    axes[3].legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(output_dir / "bang_bang_tracking.png", dpi=300)
    plt.close(fig)


def plot_saturation_example(output_dir: Path) -> None:
    total_time = 8.0
    dt = 0.02
    t = np.arange(0.0, total_time, dt)

    base_v = 1.0
    rotation_speed = 0.6
    w_cmd = rotation_speed * np.sign(np.sin(0.8 * np.pi * t))

    left_command = base_v - w_cmd
    right_command = base_v + w_cmd

    left_clipped = np.clip(left_command, -1.0, 1.0)
    right_clipped = np.clip(right_command, -1.0, 1.0)

    fig, axes = plt.subplots(2, 1, figsize=(8, 5), sharex=True)

    axes[0].plot(t, left_command, label="Commanded left", color="#2ca02c")
    axes[0].plot(t, left_clipped, label="Clipped left", color="#98df8a", linestyle="--")
    axes[0].axhline(1.0, color="black", linewidth=1, linestyle=":")
    axes[0].axhline(-1.0, color="black", linewidth=1, linestyle=":")
    axes[0].set_ylabel("Left wheel speed")
    axes[0].legend(loc="upper right")

    axes[1].plot(t, right_command, label="Commanded right", color="#d62728")
    axes[1].plot(
        t, right_clipped, label="Clipped right", color="#ff9896", linestyle="--"
    )
    axes[1].axhline(1.0, color="black", linewidth=1, linestyle=":")
    axes[1].axhline(-1.0, color="black", linewidth=1, linestyle=":")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Right wheel speed")
    axes[1].legend(loc="upper right")

    fig.suptitle("Wheel-speed saturation when base velocity is maxed out")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(output_dir / "wheel_speed_clipping.png", dpi=300)
    plt.close(fig)


def plot_timescale_response(output_dir: Path) -> None:
    t = np.linspace(0.0, 2.0, 500)
    current_tau = 0.02
    velocity_tau = 0.5

    current_response = 1.0 - np.exp(-t / current_tau)
    velocity_response = 1.0 - np.exp(-t / velocity_tau)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(t, current_response, label="Motor current (fast)", color="#1f77b4")
    ax.plot(t, velocity_response, label="Wheel velocity (slow)", color="#ff7f0e")

    ax.axvline(current_tau * 3, color="#1f77b4", linestyle="--", alpha=0.5)
    ax.text(
        current_tau * 3,
        0.6,
        "≈60 ms",
        color="#1f77b4",
        rotation=90,
        va="center",
    )
    ax.axvline(velocity_tau * 3, color="#ff7f0e", linestyle="--", alpha=0.5)
    ax.text(
        velocity_tau * 3,
        0.4,
        "≈1.5 s",
        color="#ff7f0e",
        rotation=90,
        va="center",
    )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Normalized response")
    ax.set_title("Time-scale separation: actuator current vs chassis velocity")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right")

    fig.tight_layout()
    fig.savefig(output_dir / "timescale_step_response.png", dpi=300)
    plt.close(fig)


def plot_order_of_control(output_dir: Path) -> None:
    t = np.linspace(0.0, 5.0, 600)

    first_order_tau = 0.4
    first_order = 1.0 - np.exp(-t / first_order_tau)

    wn = 3.0
    zeta = 0.2
    second_order = 1 - (1 / math.sqrt(1 - zeta**2)) * np.exp(-zeta * wn * t) * np.sin(
        wn * math.sqrt(1 - zeta**2) * t + math.atan(math.sqrt(1 - zeta**2) / zeta)
    )

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(t, first_order, label="First-order control", color="#2ca02c")
    ax.plot(t, second_order, label="Second-order with momentum", color="#d62728")

    ax.axhline(1.0, color="black", linestyle=":", linewidth=1)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Response to unit step")
    ax.set_ylim(-0.2, 1.4)
    ax.set_title("Effect of control order on step response")
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(output_dir / "order_of_control_effect.png", dpi=300)
    plt.close(fig)


def main() -> None:
    output_dir = ensure_output_dir()

    draw_conceptual_diagram(output_dir)
    trace = simulate_bang_bang_controller()
    plot_bang_bang_trace(trace, output_dir)
    plot_saturation_example(output_dir)
    plot_timescale_response(output_dir)
    plot_order_of_control(output_dir)

    print(f"Saved figures to {output_dir}")


if __name__ == "__main__":
    main()

