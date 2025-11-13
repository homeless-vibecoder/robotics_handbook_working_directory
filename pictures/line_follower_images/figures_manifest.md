Line Follower Chapter Figures
================================

1. line_follower_setup.png — Conceptual diagram of the robot on the track showing wheelbase, sensor placement, and the black line. Supports the introduction that describes hardware layout.
2. bang_bang_tracking.png — Time-series from a simple bang-bang controller: lateral error `y`, heading `θ`, wheel speeds, and sensor states to illustrate oscillatory behavior noted in “Attempt 1”.
3. wheel_speed_clipping.png — Illustration of velocity saturation: commanded vs clipped wheel speeds when `v=1` and `w` toggles, demonstrating the “not going out of range” section.
4. timescale_step_response.png — Comparison of fast motor current response vs slower vehicle velocity change to visualize the time-scale separation discussion in “Classification via time-scales”.
5. order_of_control_effect.png — Step responses for first- vs second-order control loops highlighting overshoot and oscillation, tying into the “Classification via order of control” narrative.

All outputs should be saved as PNGs in this directory for direct inclusion in `line_follower_draft2_garbage.md`.

