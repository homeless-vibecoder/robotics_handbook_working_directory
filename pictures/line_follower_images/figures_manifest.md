Line Follower Chapter Figures
================================

1. line_follower_setup.png — Top-down conceptual diagram of the robot on the track showing wheel separation `L`, sensor spacing `d`, and the black line to follow. Supports Section 1 (“The problem: staying on the line”).
2. diff_drive_kinematics.png — Conceptual illustration of differential-drive motion: (a) straight motion with `v_l = v_r`, (b) in-place rotation with `v_l = -v_r`, and (c) general turning around an instantaneous centre of curvature (ICC). Supports Section 2.
3. bang_bang_tracking.png — Time-series from a simple bang-bang controller: lateral error `y`, heading `θ`, wheel speeds, and sensor states showing the oscillatory “overshoot and correct” behaviour discussed in Section 3 (“Attempt 1”).
4. wheel_speed_clipping.png — Illustration of wheel-speed saturation: commanded vs clipped wheel speeds when base velocity is at its limit and steering commands `w = ±0.5` push one wheel past the allowed range, supporting Section 4.1.
5. timescale_step_response.png — Comparison of fast motor current response (≈20 ms characteristic delay) vs slower vehicle velocity change (≈0.5 s) to visualize the time-scale separation discussion in Section 5.
6. order_of_control_effect.png — Step responses for first- vs underdamped second-order control loops highlighting overshoot and oscillation, tying into the “order of control” narrative in Section 6.
7. pid_like_line_following.png — Comparison of bang-bang vs smoother state-based controller: lateral error and heading over time on the same track, illustrating the reduced overshoot and smoother behaviour in Section 7 (“Attempt 2”).
8. predict_correct_line_estimation.png — True lateral error vs dead-reckoned estimate vs simple predict–correct estimate, with vertical lines marking sensor update times, supporting Section 8 (“estimating (y, θ, v, w)”).

All outputs are saved as PNGs in this directory for direct inclusion in `line_follower_draft3.md`.
