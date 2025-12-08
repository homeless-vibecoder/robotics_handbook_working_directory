"""Reference motor/actuator implementations."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional

from low_level_mechanics.world import Pose2D, World
from low_level_mechanics.entities import SimObject

from .base import Motor
from .presets import WHEEL_PRESETS, WheelMotorPreset


def _apply_impulse(body: SimObject, impulse: tuple[float, float], contact_point: tuple[float, float]) -> None:
    """Apply an impulse at a world point, updating linear and angular velocity."""
    if not body.can_move or body.state.mass <= 0:
        return
    inv_mass = 1.0 / max(body.state.mass, 1e-9)
    inv_inertia = 0.0 if body.state.moment_of_inertia <= 0 else 1.0 / body.state.moment_of_inertia
    rx = contact_point[0] - body.pose.x
    ry = contact_point[1] - body.pose.y
    jx, jy = impulse
    vx, vy = body.state.linear_velocity
    body.state.linear_velocity = (vx + jx * inv_mass, vy + jy * inv_mass)
    body.state.angular_velocity += (rx * jy - ry * jx) * inv_inertia


def _contact_velocity(body: SimObject, contact_point: tuple[float, float]) -> tuple[float, float]:
    """Compute the velocity of a world-space contact point on the body."""
    vx, vy = body.state.linear_velocity
    omega = body.state.angular_velocity
    rx = contact_point[0] - body.pose.x
    ry = contact_point[1] - body.pose.y
    return (vx - omega * ry, vy + omega * rx)


def _inv_mass_term(body: SimObject, contact_point: tuple[float, float], axis: tuple[float, float]) -> float:
    """Effective inverse mass along an axis at a contact point (2D rigid body)."""
    inv_mass = 0.0 if not body.can_move or body.state.mass <= 0 else 1.0 / body.state.mass
    inv_inertia = 0.0 if body.state.moment_of_inertia <= 0 else 1.0 / body.state.moment_of_inertia
    rx = contact_point[0] - body.pose.x
    ry = contact_point[1] - body.pose.y
    r_cross_n = rx * axis[1] - ry * axis[0]
    return inv_mass + (r_cross_n * r_cross_n) * inv_inertia


def _solve_wheel_traction(
    body: SimObject,
    contact_point: tuple[float, float],
    forward: tuple[float, float],
    drive_impulse: float,
    *,
    mu_long: float,
    mu_lat: float,
    normal_load: float,
    lateral_damping: float,
    dt: float,
) -> float:
    """Apply longitudinal drive and lateral slip constraint with Coulomb-style caps."""
    if not body.can_move:
        return 0.0
    normal_load = max(normal_load, 0.0)
    lateral_damping = _clamp(lateral_damping, 0.0, 1.0)
    lateral = (-forward[1], forward[0])
    max_long_impulse = abs(mu_long) * normal_load * dt
    max_lat_impulse = abs(mu_lat) * normal_load * dt

    # Longitudinal drive (friction-limited)
    j_drive = _clamp(drive_impulse, -max_long_impulse, max_long_impulse) if max_long_impulse > 0 else 0.0
    if j_drive != 0.0:
        _apply_impulse(body, (forward[0] * j_drive, forward[1] * j_drive), contact_point)

    # Lateral slip correction (constraint-like)
    if max_lat_impulse > 0.0:
        vcx, vcy = _contact_velocity(body, contact_point)
        v_lat = vcx * lateral[0] + vcy * lateral[1]
        if abs(v_lat) > 1e-5:
            inv_mass_term = _inv_mass_term(body, contact_point, lateral)
            if inv_mass_term > 1e-9:
                j_lat = -v_lat / inv_mass_term
                j_lat *= (1.0 - lateral_damping)
                j_lat = _clamp(j_lat, -max_lat_impulse, max_lat_impulse)
                _apply_impulse(body, (lateral[0] * j_lat, lateral[1] * j_lat), contact_point)
    return j_drive


class WheelMotor(Motor):
    """Applies a longitudinal force along the wheel's heading with traction limits."""

    def __init__(
        self,
        name: str,
        *,
        mount_pose: Pose2D | None = None,
        max_force: float = 2.0,
        mu_long: float = 0.9,
        mu_lat: float = 0.8,
        g_equiv: float = 9.81,
        normal_force: float | None = None,
        lateral_damping: float = 0.25,
        wheel_count: int = 2,
        wheel_radius: float = 0.03,
    ) -> None:
        super().__init__(name, mount_pose=mount_pose, max_command=1.0)
        self.max_force = max_force
        self.mu_long = mu_long
        self.mu_lat = mu_lat
        self.g_equiv = g_equiv
        self.normal_force = normal_force
        self.lateral_damping = lateral_damping
        self.wheel_count = max(1, wheel_count)
        self.wheel_radius = wheel_radius

    def _apply(self, value: float, world: World, dt: float) -> None:
        if not self.parent or not self.parent.can_move:
            return
        pose = self.parent.pose.compose(self.mount_pose)
        direction = (math.cos(pose.theta), math.sin(pose.theta))
        normal_load = self.normal_force
        if normal_load is None:
            normal_load = self.parent.state.mass * self.g_equiv / float(max(self.wheel_count, 1))
        drive_impulse = self.max_force * value * dt
        _solve_wheel_traction(
            self.parent,
            (pose.x, pose.y),
            direction,
            drive_impulse,
            mu_long=self.mu_long,
            mu_lat=self.mu_lat,
            normal_load=normal_load,
            lateral_damping=self.lateral_damping,
            dt=dt,
        )

    def as_dict(self):
        data = super().as_dict()
        data.update({
            "max_force": self.max_force,
            "mu_long": self.mu_long,
            "mu_lat": self.mu_lat,
            "g_equiv": self.g_equiv,
            "normal_force": self.normal_force,
            "lateral_damping": self.lateral_damping,
            "wheel_count": self.wheel_count,
            "wheel_radius": self.wheel_radius,
        })
        return data

    @property
    def visual_tag(self) -> str:
        return "motor.wheel"

    def visual_state(self):
        if not self.parent:
            return None
        return {
            "command": self.last_command,
            "max_force": self.max_force,
            "detail": "force",
        }


class WheelMotorDetailed(Motor):
    """Wheel model that converts commands into torque/speed with traction limits."""

    def __init__(
        self,
        name: str,
        preset: str = "wheel_small",
        *,
        mount_pose: Pose2D | None = None,
    ) -> None:
        preset_info = WHEEL_PRESETS[preset]
        super().__init__(name, mount_pose=mount_pose, max_command=preset_info.max_command)
        self.preset = preset_info
        self.angular_speed = 0.0

    def _apply(self, value: float, world: World, dt: float) -> None:
        if not self.parent or not self.parent.can_move:
            return
        torque = self.preset.max_torque * value
        # Apply first-order response
        self.angular_speed += (torque / max(self.preset.motor_inertia, 1e-6)) * dt
        self.angular_speed = _clamp(self.angular_speed, -100.0, 100.0)
        traction_force = (torque * self.preset.gear_ratio) / self.preset.wheel_radius
        heading = self.parent.pose.compose(self.mount_pose)
        direction = (math.cos(heading.theta), math.sin(heading.theta))
        normal_load = self.preset.normal_force
        if normal_load is None:
            normal_load = self.parent.state.mass * self.preset.g_equiv / float(max(self.preset.wheel_count, 1))
        drive_impulse = traction_force * dt
        _solve_wheel_traction(
            self.parent,
            (heading.x, heading.y),
            direction,
            drive_impulse,
            mu_long=self.preset.mu_long,
            mu_lat=self.preset.mu_lat,
            normal_load=normal_load,
            lateral_damping=self.preset.lateral_damping,
            dt=dt,
        )

    def as_dict(self):
        data = super().as_dict()
        data.update({
            "preset": self.preset.name,
            "wheel_radius": self.preset.wheel_radius,
            "max_torque": self.preset.max_torque,
            "mu_long": self.preset.mu_long,
            "mu_lat": self.preset.mu_lat,
            "g_equiv": self.preset.g_equiv,
            "normal_force": self.preset.normal_force,
            "lateral_damping": self.preset.lateral_damping,
            "wheel_count": self.preset.wheel_count,
        })
        return data

    @property
    def visual_tag(self) -> str:
        return "motor.wheel"

    def visual_state(self):
        if not self.parent:
            return None
        return {
            "command": self.last_command,
            "max_torque": self.preset.max_torque,
            "wheel_radius": self.preset.wheel_radius,
            "angular_speed": self.angular_speed,
            "detail": "torque",
        }


@dataclass
class DifferentialDrive:
    """Convenience wrapper around two wheel motors."""

    wheel_base: float = 0.18
    max_force: float = 2.0
    detailed: bool = False
    preset: str = "wheel_small"

    def __post_init__(self) -> None:
        half = self.wheel_base / 2
        motor_cls = WheelMotorDetailed if self.detailed else WheelMotor
        motor_kwargs = {"preset": self.preset} if self.detailed else {"max_force": self.max_force}
        self.left = motor_cls(
            name="left_wheel",
            mount_pose=Pose2D(0.0, half, 0.0),
            **motor_kwargs,
        )
        self.right = motor_cls(
            name="right_wheel",
            mount_pose=Pose2D(0.0, -half, 0.0),
            **motor_kwargs,
        )

    def attach(self, parent: SimObject) -> None:
        self.left.attach(parent)
        self.right.attach(parent)

    def command(self, left: float, right: float, world: World, dt: float) -> None:
        self.left.command(left, world, dt)
        self.right.command(right, world, dt)

    def as_dict(self) -> dict:
        return {
            "wheel_base": self.wheel_base,
            "left": self.left.as_dict(),
            "right": self.right.as_dict(),
        }


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
