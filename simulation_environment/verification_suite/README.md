# Verification Suite

Self-contained scripts that sanity-check the current physics and sensor stack. Run each from this directory with: python3 <script>.py. They only import the reusable packages so the core code stays untouched.

| Script | Purpose | Expected Output |
| --- | --- | --- |
| test_wheel_rotation.py | Applies a single off-center wheel force and ensures the chassis develops angular velocity. | Prints ang_vel magnitude (>0.01) plus PASS. |
| test_diff_drive_translation.py | Uses symmetric wheel commands to verify forward translation with near-zero spin. | Prints vx>0.1, ang≈0 and PASS. |
| test_sensors.py | Checks that line and distance sensors respond correctly to simple scenes. | Shows near-1.0 line reading on the stripe, <0.2 off stripe, close-range hit <0.9, and clear >1.0, ending with PASS. |
| test_component_outputs.py | Verifies components register with the robot and expose visual_state payloads (points, rays, commands). | Reports component count match and states=OK -> PASS. |

Add more scripts here as coverage expands (e.g., IMU noise checks).
