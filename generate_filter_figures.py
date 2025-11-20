#!/usr/bin/env python3
"""
Generate conceptual figures for the filters chapter.

All outputs are saved into `pictures/filters/` relative to this file.

Figures generated (matching filenames used in filters_draft1.md):
- noisy_distance_sensor_raw.png
    True constant distance vs noisy distance sensor readings.
- distance_moving_average.png
    Raw noisy distance vs moving-average filtered distance.
- ema_step_response.png
    Step response of an exponential moving average for different alpha values.
- ema_noise_filtering.png
    Noisy constant distance with exponential moving-average filters.
- motor_speed_timescales.png
    Motor speed signal with fast jitter and slow drift, plus a heavily smoothed version.
- predict_correct_distance.png
    True distance to a wall vs raw sensor, pure prediction, and predict–correct estimate.
- complementary_tilt.png
    True tilt vs gyro-only estimate, accelerometer-only estimate, and complementary-filter estimate.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


OUTPUT_DIR = Path(__file__).parent / "pictures" / "filters"


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def _setup_time_series_axes(
    ax: plt.Axes,
    xlabel: str,
    ylabel: str,
    title: str | None = None,
    grid: bool = True,
) -> None:
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    if grid:
        ax.grid(alpha=0.3, linestyle="--", linewidth=0.5)


def plot_noisy_distance_raw(output_dir: Path) -> None:
    """
    Figure: noisy_distance_sensor_raw.png

    - True distance is constant at 1.0 m.
    - Sensor readings are noisy samples around that value.
    - Shows why a single reading is not trustworthy.
    """
    rng = np.random.default_rng(0)
    t = np.linspace(0.0, 10.0, 400)
    true_distance = np.ones_like(t) * 1.0
    noise = rng.normal(loc=0.0, scale=0.05, size=t.shape)
    measurements = true_distance + noise

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(t, true_distance, color="black", linewidth=2.0, label="True distance")
    ax.plot(
        t,
        measurements,
        color="#1f77b4",
        linewidth=1.0,
        alpha=0.8,
        label="Raw sensor readings",
    )

    _setup_time_series_axes(
        ax, xlabel="Time (s)", ylabel="Distance to wall (m)", title="Noisy distance sensor"
    )
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(output_dir / "noisy_distance_sensor_raw.png", dpi=300)
    plt.close(fig)


def _moving_average(x: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return x.copy()
    kernel = np.ones(window) / float(window)
    # Use "same" mode to keep length; pad with reflection to avoid edge artifacts.
    padded = np.pad(x, (window // 2, window - 1 - window // 2), mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def plot_distance_moving_average(output_dir: Path) -> None:
    """
    Figure: distance_moving_average.png

    - Same noisy distance signal as in the raw figure.
    - Overlaid with a moving-average filtered signal (window N=5).
    - Highlights noise reduction and small time lag.
    """
    rng = np.random.default_rng(0)
    t = np.linspace(0.0, 10.0, 400)
    true_distance = np.ones_like(t) * 1.0
    noise = rng.normal(loc=0.0, scale=0.05, size=t.shape)
    measurements = true_distance + noise

    window = 5
    filtered = _moving_average(measurements, window)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(
        t,
        measurements,
        color="#1f77b4",
        linewidth=0.8,
        alpha=0.6,
        label="Raw sensor",
    )
    ax.plot(
        t,
        filtered,
        color="#ff7f0e",
        linewidth=2.0,
        label=f"Moving average (N = {window})",
    )
    ax.axhline(1.0, color="black", linestyle=":", linewidth=1.0, alpha=0.7)

    _setup_time_series_axes(
        ax,
        xlabel="Time (s)",
        ylabel="Distance to wall (m)",
        title="Moving average smoothing",
    )
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(output_dir / "distance_moving_average.png", dpi=300)
    plt.close(fig)


def plot_ema_step_response(output_dir: Path) -> None:
    """
    Figure: ema_step_response.png

    - True distance steps from 1.0 m down to 0.5 m.
    - Exponential moving-average filters with different alpha values show
      different lags.
    """
    dt = 0.02
    t = np.arange(0.0, 4.0, dt)
    step_time = 1.0
    true_distance = np.where(t < step_time, 1.0, 0.5)

    alphas = [0.1, 0.5]
    colors = ["#1f77b4", "#ff7f0e"]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(
        t,
        true_distance,
        color="black",
        linestyle="--",
        linewidth=1.5,
        label="True distance",
    )

    for alpha, color in zip(alphas, colors):
        filtered = np.empty_like(t)
        filtered[0] = true_distance[0]
        for i in range(1, len(t)):
            m = true_distance[i]  # perfect measurement of the step
            filtered[i] = (1.0 - alpha) * filtered[i - 1] + alpha * m
        ax.plot(
            t,
            filtered,
            color=color,
            linewidth=2.0,
            label=f"Filtered (alpha = {alpha})",
        )

    _setup_time_series_axes(
        ax,
        xlabel="Time (s)",
        ylabel="Distance to wall (m)",
        title="Exponential moving-average step response",
    )
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(output_dir / "ema_step_response.png", dpi=300)
    plt.close(fig)


def plot_ema_noise_filtering(output_dir: Path) -> None:
    """
    Figure: ema_noise_filtering.png

    - True distance is constant at 1.0 m.
    - Raw measurements are noisy.
    - Two exponential filters (small and large alpha) show the tradeoff
      between smoothness and responsiveness.
    """
    rng = np.random.default_rng(1)
    t = np.linspace(0.0, 10.0, 400)
    true_distance = np.ones_like(t) * 1.0
    noise = rng.normal(loc=0.0, scale=0.06, size=t.shape)
    measurements = true_distance + noise

    alphas = [0.1, 0.5]
    colors = ["#2ca02c", "#d62728"]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(
        t,
        measurements,
        color="#1f77b4",
        linewidth=0.8,
        alpha=0.4,
        label="Raw sensor",
    )

    for alpha, color in zip(alphas, colors):
        filtered = np.empty_like(t)
        filtered[0] = measurements[0]
        for i in range(1, len(t)):
            m = measurements[i]
            filtered[i] = (1.0 - alpha) * filtered[i - 1] + alpha * m
        ax.plot(
            t,
            filtered,
            color=color,
            linewidth=2.0,
            label=f"Filtered (alpha = {alpha})",
        )

    ax.axhline(1.0, color="black", linestyle=":", linewidth=1.0, alpha=0.7)

    _setup_time_series_axes(
        ax,
        xlabel="Time (s)",
        ylabel="Distance to wall (m)",
        title="Exponential filtering of noisy distance",
    )
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(output_dir / "ema_noise_filtering.png", dpi=300)
    plt.close(fig)


def plot_motor_speed_timescales(output_dir: Path) -> None:
    """
    Figure: motor_speed_timescales.png

    - Motor speed with:
        * Slow drift (e.g., battery voltage / friction effects).
        * Fast jitter (encoder quantization and small disturbances).
    - Heavily smoothed exponential filter showing only the slow trend.
    """
    rng = np.random.default_rng(2)
    dt = 0.02
    t = np.arange(0.0, 10.0, dt)

    # Slow drift: base speed plus a slow sinusoidal variation.
    base = 0.4
    slow = 0.08 * np.sin(2 * np.pi * t / 6.0)

    # Fast jitter: small high-frequency noise.
    jitter = rng.normal(loc=0.0, scale=0.02, size=t.shape)

    speed_measured = base + slow + jitter

    # Heavily smoothed exponential filter (long time-scale).
    alpha = 0.02
    speed_slow = np.empty_like(t)
    speed_slow[0] = speed_measured[0]
    for i in range(1, len(t)):
        speed_slow[i] = (1.0 - alpha) * speed_slow[i - 1] + alpha * speed_measured[i]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(
        t,
        speed_measured,
        color="#1f77b4",
        linewidth=0.8,
        alpha=0.6,
        label="Measured speed (fast + slow)",
    )
    ax.plot(
        t,
        speed_slow,
        color="#ff7f0e",
        linewidth=2.0,
        label="Heavily smoothed (slow trend)",
    )

    _setup_time_series_axes(
        ax,
        xlabel="Time (s)",
        ylabel="Wheel speed (m/s)",
        title="Motor speed: fast jitter vs slow trend",
    )
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(output_dir / "motor_speed_timescales.png", dpi=300)
    plt.close(fig)


def plot_predict_correct_distance(output_dir: Path) -> None:
    """
    Figure: predict_correct_distance.png

    - Robot driving towards a wall.
    - True distance decreases linearly with small random disturbances.
    - Raw sensor readings are noisy.
    - Pure prediction from a slightly wrong velocity model drifts away.
    - Predict–correct estimate stays close to the truth.
    """
    rng = np.random.default_rng(3)
    dt = 0.05
    t = np.arange(0.0, 8.0, dt)

    d0 = 4.0
    v_true = 0.4
    # True distance with small random disturbance on top of a linear approach.
    process_noise = rng.normal(loc=0.0, scale=0.01, size=t.shape)
    true_distance = np.maximum(d0 - v_true * t + np.cumsum(process_noise) * dt, 0.0)

    # Noisy sensor readings.
    sensor_noise = rng.normal(loc=0.0, scale=0.08, size=t.shape)
    measurements = true_distance + sensor_noise

    # Pure prediction using a slightly wrong model of the speed.
    v_model = 0.35  # underestimates how fast we approach the wall
    d_pred = np.empty_like(t)
    d_pred[0] = d0
    for i in range(1, len(t)):
        d_pred[i] = max(d_pred[i - 1] - v_model * dt, 0.0)

    # Predict–correct filter.
    beta = 0.2
    d_est = np.empty_like(t)
    d_est[0] = d0
    for i in range(1, len(t)):
        # Predict
        d_predict = max(d_est[i - 1] - v_model * dt, 0.0)
        # Correct
        innovation = measurements[i] - d_predict
        d_est[i] = d_predict + beta * innovation

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(
        t,
        true_distance,
        color="black",
        linewidth=2.0,
        label="True distance",
    )
    ax.plot(
        t,
        measurements,
        color="#1f77b4",
        linewidth=0.8,
        alpha=0.4,
        label="Noisy sensor",
    )
    ax.plot(
        t,
        d_pred,
        color="#ff7f0e",
        linewidth=1.5,
        linestyle="--",
        label="Pure prediction (model only)",
    )
    ax.plot(
        t,
        d_est,
        color="#2ca02c",
        linewidth=2.0,
        label="Predict–correct estimate",
    )

    _setup_time_series_axes(
        ax,
        xlabel="Time (s)",
        ylabel="Distance to wall (m)",
        title="Predict–correct distance estimation",
    )
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(output_dir / "predict_correct_distance.png", dpi=300)
    plt.close(fig)


def _simulate_tilt(
    total_time: float = 10.0, dt: float = 0.01
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Simulate a simple tilt motion:
    - True tilt is a combination of slow and faster motions.
    - Gyro rate is derivative of tilt plus a small constant bias.
    - Accelerometer tilt is noisy measurement of the true tilt.
    """
    rng = np.random.default_rng(4)
    t = np.arange(0.0, total_time, dt)

    # True tilt (in radians): gentle slow oscillation with a superimposed bump.
    tilt_true = 10.0 * np.sin(2 * np.pi * t / 8.0)  # degrees
    tilt_true += 5.0 * np.exp(-0.5 * ((t - 5.0) / 0.6) ** 2)  # small bump

    tilt_true_rad = np.deg2rad(tilt_true)

    # Gyro rate: derivative of true tilt plus small bias.
    gyro_bias = np.deg2rad(0.3)  # slow drift in deg/s
    gyro_rate = np.gradient(tilt_true_rad, dt) + gyro_bias

    # Accelerometer-derived tilt: noisy measurement of true tilt.
    accel_noise = np.deg2rad(2.0)  # fairly noisy
    accel_tilt = tilt_true_rad + rng.normal(loc=0.0, scale=accel_noise, size=t.shape)

    return t, tilt_true_rad, gyro_rate, accel_tilt


def plot_complementary_tilt(output_dir: Path) -> None:
    """
    Figure: complementary_tilt.png

    - True tilt over time.
    - Gyro-only estimate (integrated rate with bias) that drifts slowly.
    - Accelerometer-only estimate that is noisy but centered.
    - Complementary-filter estimate that is smooth and accurate.
    """
    dt = 0.01
    t, tilt_true_rad, gyro_rate, accel_tilt = _simulate_tilt(total_time=10.0, dt=dt)

    # Gyro-only integration
    tilt_gyro = np.empty_like(tilt_true_rad)
    tilt_gyro[0] = tilt_true_rad[0]
    for i in range(1, len(t)):
        tilt_gyro[i] = tilt_gyro[i - 1] + gyro_rate[i] * dt

    # Simple low-pass on accelerometer for visualization.
    alpha_accel = 0.1
    tilt_accel_lp = np.empty_like(accel_tilt)
    tilt_accel_lp[0] = accel_tilt[0]
    for i in range(1, len(t)):
        tilt_accel_lp[i] = (1.0 - alpha_accel) * tilt_accel_lp[i - 1] + alpha_accel * accel_tilt[i]

    # Complementary filter: mostly gyro in the short term, slow correction from accel.
    k = 0.02
    tilt_comp = np.empty_like(tilt_true_rad)
    tilt_comp[0] = tilt_true_rad[0]
    for i in range(1, len(t)):
        # Predict using gyro
        theta_pred = tilt_comp[i - 1] + gyro_rate[i] * dt
        # Correct slowly towards accelerometer
        tilt_comp[i] = (1.0 - k) * theta_pred + k * accel_tilt[i]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(
        t,
        np.rad2deg(tilt_true_rad),
        color="black",
        linewidth=2.0,
        label="True tilt",
    )
    ax.plot(
        t,
        np.rad2deg(tilt_gyro),
        color="#ff7f0e",
        linewidth=1.5,
        linestyle="--",
        label="Gyro-only (drifting)",
    )
    ax.plot(
        t,
        np.rad2deg(tilt_accel_lp),
        color="#1f77b4",
        linewidth=1.0,
        alpha=0.8,
        label="Accelerometer (noisy, low-pass)",
    )
    ax.plot(
        t,
        np.rad2deg(tilt_comp),
        color="#2ca02c",
        linewidth=2.0,
        label="Complementary filter",
    )

    _setup_time_series_axes(
        ax,
        xlabel="Time (s)",
        ylabel="Tilt angle (deg)",
        title="Complementary filtering of tilt",
    )
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(output_dir / "complementary_tilt.png", dpi=300)
    plt.close(fig)


def main() -> None:
    """
    Generate all filter-related figures used in filters_draft1.md.

    Run this script from the project root with:
        python RBE_IQP/generate_filter_figures.py
    """
    output_dir = ensure_output_dir()

    plot_noisy_distance_raw(output_dir)
    plot_distance_moving_average(output_dir)
    plot_ema_step_response(output_dir)
    plot_ema_noise_filtering(output_dir)
    plot_motor_speed_timescales(output_dir)
    plot_predict_correct_distance(output_dir)
    plot_complementary_tilt(output_dir)

    print(f"Saved filter figures to {output_dir}")


if __name__ == "__main__":
    main()


