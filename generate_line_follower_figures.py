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
    robot_x = 0.25
    robot_y = -0.15
    robot_width = 0.35
    robot_height = 0.3

    robot = patches.FancyBboxPatch(
        (robot_x, robot_y),
        robot_width,
        robot_height,
        boxstyle="round,pad=0.02",
        linewidth=2,
        edgecolor="#555555",
        facecolor="#ffffff",
        zorder=2,
    )
    ax.add_patch(robot)

    # Wheels, drawn so that the separation is clearly visible and can be
    # associated with the symbol L in the text.
    wheel_width = 0.05
    wheel_height = 0.26
    left_wheel_x = 0.23
    right_wheel_x = 0.62
    wheel_y = -0.13
    ax.add_patch(
        patches.Rectangle(
            (left_wheel_x, wheel_y),
            wheel_width,
            wheel_height,
            facecolor="#333333",
            zorder=3,
        )
    )
    ax.add_patch(
        patches.Rectangle(
            (right_wheel_x, wheel_y),
            wheel_width,
            wheel_height,
            facecolor="#333333",
            zorder=3,
        )
    )

    # Annotate wheel separation L.
    axle_y = wheel_y + 0.5 * wheel_height
    ax.annotate(
        "",
        xy=(left_wheel_x + wheel_width, axle_y + 0.03),
        xytext=(right_wheel_x, axle_y + 0.03),
        arrowprops=dict(arrowstyle="<->", color="#555555"),
    )
    ax.text(
        0.5 * (left_wheel_x + wheel_width + right_wheel_x),
        axle_y + 0.05,
        "wheel separation L",
        ha="center",
        va="bottom",
        color="#555555",
    )

    # Sensors
    sensor_offset = 0.12
    sensor_size = 0.02
    sensor_x = robot_x + 0.05
    sensor_positions = [(sensor_x, sensor_offset), (sensor_x, -sensor_offset)]
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

    # Forward velocity arrow.
    ax.text(
        robot_x + 0.18,
        robot_y + robot_height + 0.03,
        "Forward\nvelocity v",
        ha="center",
        va="center",
        color="#444444",
    )
    ax.annotate(
        "",
        xy=(robot_x + 0.18, robot_y + robot_height),
        xytext=(robot_x + 0.35, robot_y + robot_height),
        arrowprops=dict(arrowstyle="-|>", color="#444444"),
    )

    # Sensor offset annotation (distance from centreline).
    ax.annotate(
        "",
        xy=(sensor_x + 0.06, sensor_offset),
        xytext=(sensor_x + 0.06, -sensor_offset),
        arrowprops=dict(arrowstyle="<->", color="#0b5394"),
    )
    ax.text(
        sensor_x + 0.065,
        0.0,
        "sensor spacing d",
        rotation=90,
        va="center",
        ha="left",
        color="#0b5394",
    )

    ax.set_xlim(-0.1, 1.0)
    ax.set_ylim(-0.5, 0.5)
    ax.axis("off")

    fig.tight_layout()
    fig.savefig(output_dir / "line_follower_setup.png", dpi=300)
    plt.close(fig)


def draw_diff_drive_kinematics(output_dir: Path) -> None:
    """Conceptual kinematics diagram: straight, in-place rotation, and turning."""
    fig, ax = plt.subplots(figsize=(6.5, 4))

    # Common robot dimensions in plot coordinates.
    body_w = 0.4
    body_h = 0.22
    wheel_w = 0.04
    wheel_h = 0.18

    def draw_robot(center_x: float, center_y: float, heading: float, color: str) -> None:
        # Draw body rectangle rotated by heading.
        body = patches.FancyBboxPatch(
            (center_x - 0.5 * body_w, center_y - 0.5 * body_h),
            body_w,
            body_h,
            boxstyle="round,pad=0.02",
            linewidth=1.5,
            edgecolor=color,
            facecolor="#ffffff",
            zorder=2,
        )
        t = matplotlib.transforms.Affine2D().rotate_around(center_x, center_y, heading)
        body.set_transform(t + ax.transData)
        ax.add_patch(body)

        # Wheels along the body sides before rotation.
        left_wheel = patches.Rectangle(
            (center_x - 0.5 * body_w - wheel_w, center_y - 0.5 * wheel_h),
            wheel_w,
            wheel_h,
            facecolor="#333333",
            zorder=3,
        )
        right_wheel = patches.Rectangle(
            (center_x + 0.5 * body_w, center_y - 0.5 * wheel_h),
            wheel_w,
            wheel_h,
            facecolor="#333333",
            zorder=3,
        )
        left_wheel.set_transform(t + ax.transData)
        right_wheel.set_transform(t + ax.transData)
        ax.add_patch(left_wheel)
        ax.add_patch(right_wheel)

        # Heading arrow.
        arrow_length = 0.35
        dx = arrow_length * math.cos(heading)
        dy = arrow_length * math.sin(heading)
        ax.annotate(
            "",
            xy=(center_x + dx, center_y + dy),
            xytext=(center_x, center_y),
            arrowprops=dict(arrowstyle="-|>", color=color),
        )

    # Straight motion: v_l = v_r, no rotation.
    draw_robot(center_x=-0.3, center_y=0.25, heading=0.0, color="#1f77b4")
    ax.text(-0.3, 0.55, "Straight: v_l = v_r\nw = 0", ha="center", va="bottom")

    # In-place rotation: v_l = -v_r.
    draw_robot(center_x=0.35, center_y=0.25, heading=0.0, color="#d62728")
    ax.text(
        0.35,
        0.55,
        "In-place rotation:\n v_l = -v_r, v = 0",
        ha="center",
        va="bottom",
    )
    # Indicate rotation direction.
    rotation_arc = patches.Arc(
        (0.35, 0.25),
        0.6,
        0.6,
        angle=0,
        theta1=30,
        theta2=140,
        color="#d62728",
    )
    ax.add_patch(rotation_arc)
    ax.annotate(
        "w ≠ 0",
        xy=(
            0.35 + 0.3 * math.cos(math.radians(85)),
            0.25 + 0.3 * math.sin(math.radians(85)),
        ),
        xytext=(0.8, 0.3),
        arrowprops=dict(arrowstyle="->", color="#d62728"),
        color="#d62728",
    )

    # General turning around an ICC to the left of the robot.
    icc_x = -0.6
    icc_y = -0.45
    draw_robot(center_x=0.4, center_y=-0.25, heading=0.2, color="#2ca02c")
    ax.plot([icc_x, 0.4], [icc_y, -0.25], linestyle="--", color="#777777", linewidth=1)
    ax.text(
        icc_x,
        icc_y - 0.1,
        "ICC",
        ha="center",
        va="top",
        color="#777777",
    )
    turn_arc = patches.Arc(
        (icc_x, icc_y),
        1.8,
        1.8,
        angle=0,
        theta1=10,
        theta2=45,
        color="#2ca02c",
    )
    ax.add_patch(turn_arc)
    ax.text(
        0.4,
        -0.6,
        "Turning: v_l ≠ v_r,\n robot follows an arc\nabout the ICC",
        ha="center",
        va="top",
    )

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-1.0, 1.1)
    ax.set_ylim(-0.9, 0.9)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_dir / "diff_drive_kinematics.png", dpi=300)
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


@dataclass
class ComparisonTrace:
    time: np.ndarray
    y_bang: np.ndarray
    y_smooth: np.ndarray
    theta_bang: np.ndarray
    theta_smooth: np.ndarray


def simulate_bang_bang_controller(total_time: float = 12.0, dt: float = 0.02) -> SimulationTrace:
    steps = int(total_time / dt)
    t = np.linspace(0.0, total_time, steps, endpoint=False)

    # Parameters chosen for a clearly oscillatory but still plausible behaviour.
    # The exact numbers are not meant to match a specific robot; they just
    # produce the qualitative pattern described in the text (overshoot and
    # chattering around the line).
    line_half_width = 0.025
    base_v = 0.35
    rotation_speed = 0.7
    wheel_base = 0.12
    sensor_offset = 0.05

    # State
    y = np.zeros(steps)
    theta = np.zeros(steps)
    v_l = np.zeros(steps)
    v_r = np.zeros(steps)
    left_sensor = np.zeros(steps)
    right_sensor = np.zeros(steps)

    # Start slightly offset and yawed so the robot initially drifts off the
    # line and then has to correct.
    current_y = 0.03
    current_theta = 0.15
    current_v_l = base_v
    current_v_r = base_v

    # Simple first-order lags:
    # - on the effective turn command w_state to model finite turning agility
    # - on wheel speeds to model motor delay
    # Together these cause the robot to rotate a bit too long after the
    # sensors flip, so it overshoots from \"facing left of the line\" to
    # \"facing right of the line\" instead of ending perfectly parallel.
    w_tau = 0.4  # seconds
    w_alpha = dt / w_tau
    w_state = 0.0

    speed_tau = 0.25  # seconds
    speed_alpha = dt / speed_tau

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

        # Apply a first-order lag to the turn command itself. This means the
        # robot keeps rotating for a short while even after the sensor pattern
        # changes, which is exactly the \"turns a bit too much\" behaviour
        # described in the text.
        w_state += w_alpha * (w_cmd - w_state)

        target_v_l = np.clip(base_v - w_state, -1.0, 1.0)
        target_v_r = np.clip(base_v + w_state, -1.0, 1.0)

        # Apply first-order lag towards the commanded wheel speeds.
        current_v_l += speed_alpha * (target_v_l - current_v_l)
        current_v_r += speed_alpha * (target_v_r - current_v_r)

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


def simulate_state_feedback_controller(
    total_time: float = 12.0,
    dt: float = 0.02,
) -> SimulationTrace:
    """Rough state-feedback controller matching the pseudocode in the text.

    The dynamics are intentionally simple and share the same kinematic model and
    wheel-base as the bang-bang simulation so that their behaviour can be
    compared on the same track.
    """
    steps = int(total_time / dt)
    t = np.linspace(0.0, total_time, steps, endpoint=False)

    line_half_width = 0.025
    base_v = 0.35
    wheel_base = 0.12

    # Controller gains roughly inspired by the text.
    c_y = 5.0
    c_theta = 2.5
    c_w = 0.6
    k_y = 2.0
    k_theta = 1.5

    y = np.zeros(steps)
    theta = np.zeros(steps)
    v_l = np.zeros(steps)
    v_r = np.zeros(steps)
    left_sensor = np.zeros(steps)
    right_sensor = np.zeros(steps)

    current_y = 0.03
    current_theta = 0.15
    current_v_l = base_v
    current_v_r = base_v
    current_w = 0.0

    # Simple first-order lags again, kept a bit faster than for the bang-bang
    # case so that the \"smooth\" controller feels more responsive.
    w_tau = 0.3
    w_alpha = dt / w_tau
    speed_tau = 0.2
    speed_alpha = dt / speed_tau

    for i in range(steps):
        # Dead-reckoned state (no estimator here; we treat y, theta, v, w
        # themselves as the state available to the controller).
        v_meas = 0.5 * (current_v_r + current_v_l)
        w_meas = (current_v_r - current_v_l) / wheel_base

        # Turn-rate command from position, heading, and current spin.
        w_cmd = -c_y * current_y - c_theta * current_theta - c_w * w_meas

        # Forward-speed command that slows down when the error is large.
        v_cmd = base_v - k_y * abs(current_y) - k_theta * abs(current_theta)
        v_cmd = max(0.0, min(base_v, v_cmd))

        # Lagged turn-rate and wheel speeds.
        current_w += w_alpha * (w_cmd - current_w)
        target_v_l = v_cmd - 0.5 * wheel_base * current_w
        target_v_r = v_cmd + 0.5 * wheel_base * current_w

        current_v_l += speed_alpha * (target_v_l - current_v_l)
        current_v_r += speed_alpha * (target_v_r - current_v_r)

        # Kinematic update.
        v = 0.5 * (current_v_r + current_v_l)
        w = (current_v_r - current_v_l) / wheel_base
        current_theta = wrap_angle(current_theta + w * dt)
        current_y = current_y + v * math.sin(current_theta) * dt

        # Sensor bits for reference only.
        left_y = current_y + 0.05
        right_y = current_y - 0.05
        left_hit = abs(left_y) <= line_half_width
        right_hit = abs(right_y) <= line_half_width

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


def compare_controllers(output_dir: Path) -> None:
    """Side-by-side comparison of bang-bang vs smoother state-feedback."""
    bang_trace = simulate_bang_bang_controller()
    smooth_trace = simulate_state_feedback_controller(
        total_time=bang_trace.time[-1] + (bang_trace.time[1] - bang_trace.time[0]),
        dt=bang_trace.time[1] - bang_trace.time[0],
    )

    # Trim to the shorter length just in case of rounding differences.
    n = min(len(bang_trace.time), len(smooth_trace.time))
    t = bang_trace.time[:n]
    y_bang = bang_trace.y[:n] * 100.0
    y_smooth = smooth_trace.y[:n] * 100.0
    th_bang = np.degrees(bang_trace.theta[:n])
    th_smooth = np.degrees(smooth_trace.theta[:n])

    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    axes[0].plot(t, y_bang, label="Bang-bang", color="#1f77b4")
    axes[0].plot(t, y_smooth, label="State-feedback", color="#2ca02c")
    axes[0].axhline(0.0, color="black", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Lateral error y (cm)")
    axes[0].set_title("Bang-bang vs smoother state-based controller")
    axes[0].legend(loc="upper right")

    axes[1].plot(t, th_bang, label="Bang-bang", color="#ff7f0e")
    axes[1].plot(t, th_smooth, label="State-feedback", color="#d62728")
    axes[1].axhline(0.0, color="black", linestyle="--", linewidth=1)
    axes[1].set_ylabel("Heading θ (deg)")
    axes[1].set_xlabel("Time (s)")
    axes[1].legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(output_dir / "pid_like_line_following.png", dpi=300)
    plt.close(fig)


def plot_saturation_example(output_dir: Path) -> None:
    total_time = 4.0
    dt = 0.02
    t = np.arange(0.0, total_time, dt)

    # Match the narrative example: base velocity v = 1.0 in the valid range,
    # and a typical steering command w = 0.5 that occasionally pushes one
    # wheel past the allowed limits.
    base_v = 1.0
    rotation_speed = 0.5

    # Alternate between straight driving and turning left/right with w = ±0.5.
    phase = np.floor(t / 0.5).astype(int)
    w_cmd = np.zeros_like(t)
    w_cmd[phase % 3 == 1] = rotation_speed
    w_cmd[phase % 3 == 2] = -rotation_speed

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
    # We pick representative time constants so the plot roughly matches the
    # discussion in the text: motor current responds in ~20 ms, while wheel
    # velocity takes a few hundred milliseconds (we use 0.5 s as a round
    # number). The exact values are not meant to be precise measurements,
    # just a clean illustration of the separation of time-scales.
    t = np.linspace(0.0, 1.2, 500)
    current_tau = 0.02  # 20 ms characteristic time
    velocity_tau = 0.5  # 0.5 s characteristic time

    current_response = 1.0 - np.exp(-t / current_tau)
    velocity_response = 1.0 - np.exp(-t / velocity_tau)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(t, current_response, label="Motor current (fast)", color="#1f77b4")
    ax.plot(t, velocity_response, label="Wheel velocity (slow)", color="#ff7f0e")

    # Mark the approximate delays discussed in the text.
    current_marker = 0.02  # 20 ms
    velocity_marker = 0.5  # 0.5 s

    ax.axvline(current_marker, color="#1f77b4", linestyle="--", alpha=0.5)
    ax.text(
        current_marker,
        0.6,
        "≈20 ms",
        color="#1f77b4",
        rotation=90,
        va="center",
    )
    ax.axvline(velocity_marker, color="#ff7f0e", linestyle="--", alpha=0.5)
    ax.text(
        velocity_marker,
        0.4,
        "≈0.5 s",
        color="#ff7f0e",
        rotation=90,
        va="center",
    )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Normalized response")
    ax.set_title("Time-scale separation: actuator current vs chassis velocity")
    ax.set_xlim(0.0, 1.2)
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right")

    fig.tight_layout()
    fig.savefig(output_dir / "timescale_step_response.png", dpi=300)
    plt.close(fig)


def plot_order_of_control(output_dir: Path) -> None:
    t = np.linspace(0.0, 5.0, 600)

    # First-order response with a moderate time constant.
    first_order_tau = 0.4
    first_order = 1.0 - np.exp(-t / first_order_tau)

    # Second-order underdamped response. We choose a damping ratio that still
    # shows clear overshoot and oscillation, but is not excessively
    # oscillatory. This is meant as a qualitative illustration of the
    # \"momentum\" discussion in the text rather than a fit to a specific
    # plant.
    wn = 3.0
    zeta = 0.3
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


def plot_estimation_predict_correct(output_dir: Path) -> None:
    """Illustration of true vs dead-reckoned vs corrected lateral error.

    This is intentionally simple: we prescribe a \"true\" lateral error that
    drifts away from zero and is occasionally pushed back by corrections, then
    show how dead-reckoning alone can drift while a predict–correct estimate
    stays closer to the truth when line-sensor hits arrive.
    """
    total_time = 8.0
    dt = 0.02
    t = np.arange(0.0, total_time, dt)
    n = len(t)

    # Synthetic true lateral error: start at 0, then slowly drift away and back.
    y_true = 0.04 * np.sin(0.5 * t) + 0.01 * np.sin(2.5 * t)

    # Dead-reckoned estimate with a slow bias drift.
    bias_drift = 0.002 * (t / total_time)
    y_dead = y_true + bias_drift

    # Line-sensor "measurements" arrive at discrete times when the true lateral
    # error crosses roughly ±d/2. We convert those into noisy measurements and
    # blend them into the estimate using an exponential moving average.
    measurement_indices = []
    d_over_2 = 0.025
    for i in range(1, n):
        if (
            (y_true[i - 1] < d_over_2 <= y_true[i])
            or (y_true[i - 1] > -d_over_2 >= y_true[i])
            or (abs(y_true[i]) < 0.005 and abs(y_true[i - 1]) >= 0.005)
        ):
            measurement_indices.append(i)

    y_est = np.copy(y_dead)
    alpha = 0.35
    rng = np.random.default_rng(42)
    for idx in measurement_indices:
        # Noisy lateral measurement consistent with the sensor model: the line
        # is approximately under ±d/2 or 0 depending on where we are.
        if y_true[idx] > d_over_2:
            y_meas = d_over_2
        elif y_true[idx] < -d_over_2:
            y_meas = -d_over_2
        else:
            y_meas = 0.0
        y_meas += rng.normal(scale=0.002)
        y_est[idx:] = (1.0 - alpha) * y_est[idx:] + alpha * y_meas

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, y_true * 100.0, label="True y", color="#1f77b4")
    ax.plot(t, y_dead * 100.0, label="Dead-reckoned y (drifts)", color="#ff7f0e")
    ax.plot(t, y_est * 100.0, label="Predict–correct estimate", color="#2ca02c")

    for idx in measurement_indices:
        ax.axvline(t[idx], color="#bbbbbb", linestyle=":", linewidth=0.7)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Lateral error y (cm)")
    ax.set_title("Dead-reckoning vs predict–correct estimation of lateral error")
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(output_dir / "predict_correct_line_estimation.png", dpi=300)
    plt.close(fig)


def main() -> None:
    output_dir = ensure_output_dir()

    draw_conceptual_diagram(output_dir)
    draw_diff_drive_kinematics(output_dir)
    trace = simulate_bang_bang_controller()
    plot_bang_bang_trace(trace, output_dir)
    compare_controllers(output_dir)
    plot_saturation_example(output_dir)
    plot_timescale_response(output_dir)
    plot_order_of_control(output_dir)
    plot_estimation_predict_correct(output_dir)

    print(f"Saved figures to {output_dir}")


if __name__ == "__main__":
    main()

