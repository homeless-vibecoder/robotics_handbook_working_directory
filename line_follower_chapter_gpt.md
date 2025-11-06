# Line Follower Robot — A Modular, Time-Scale-First Guide

Short abstract: A practical, insight-focused chapter on designing a differential-drive line follower with two binary IR sensors. We use light math (v, w, small-angle) and emphasize time-scale separation: faster layers can be treated as near-instant within slower loops, with clear limits and guardrails.

---

## 1) Decomposition into independent parts (mindset)

Robotics problems are easier when broken into parts with simple interfaces between them. For a line follower:
- We actuate motors (manipulated variables, “OP”) and aim to control robot pose relative to a line (process variables, “PV”).
- Each part can be improved locally if its inputs/outputs are well defined: motor drive → wheel speed → robot motion → line-relative state → decisions.
- We avoid reasoning about everything at once; instead we stack layers that each run at a suitable time-scale.

Key interfaces (inputs → outputs):
- Motor command (PWM/current) → wheel angular velocity.
- Left/right wheel velocities → robot linear and angular velocities (v, w).
- (v, w) over a short horizon → heading and lateral error relative to the line.
- Binary sensors → observations that constrain which side of the line we are on and when we crossed it.

---

## 2) Decomposing motion (ω_motor → v_wheel → v, w)

We map what we command to what the robot actually does.

INCOMPLETE: there needs to be more clarification on units, and derivation

IMAGE NEEDED: maybe geometry/derivation would be easier to visualize

### 2.1 Motor angular velocity → wheel linear velocity
If wheel radius is r and wheel angular speed is ω, the rim speed is v_wheel = r·ω.

### 2.2 Wheel linear velocities → robot (v, w)
For differential drive with wheelbase b and wheel linear speeds v_R, v_L:
- v = (v_R + v_L)/2 = (r/2)(ω_R + ω_L)
- w = (v_R − v_L)/b = (r/b)(ω_R − ω_L)

These are the minimal equations we need. We use them qualitatively (what increases/decreases v or w) and quantitatively for small adjustments.

### 2.3 (Optional) Along vs perpendicular to the line
For short horizons, small-angle intuition helps: if heading error is θ (radians), lateral error change is roughly ẋ ≈ v·sin(θ) ≈ v·θ when θ is small. This is only for short spans; large errors or long durations break the approximation.

---

## 3) Different time-scales and what our OP is (time-scale separation)

ERROR: algebraic has nothing to do with what we are doing. Don't use technical terms without defining it or if they serve no purpose.

The central idea: faster layers can be treated as near-instant (algebraic) inside slower loops—within their limits.

### 3.1 Bandwidth ladder (from fastest to slowest)
1) Electrical current and motor torque response (very fast, near-instant for our purposes).
2) Wheel speed dynamics (fast but not instantaneous; affected by inertia, friction, voltage limits).
3) Robot heading and pose changes from (v, w) (medium; constrained by wheel speed and spacing b).
4) Line-relative error (what our sensors perceive) evolves on the slowest loop we design.

Within the heading/line-following loop, we often assume wheel speed commands translate to (v, w) “quickly enough.” Inside a wheel-speed loop, we treat current/torque changes as near-instant. These assumptions reduce complexity.

QUESTION: is it a good idea/practice to define $T_j$ - different time-scales?

### 3.2 OP vs PV, and why delay dominates
- OP (manipulated variable): what we set—here it is left/right motor setpoints (or directly v, w if we map them).
- PV (process variable): what we care about—lateral error x and heading θ relative to the line.
- Order vs delay: The exact order (x, ẋ, ẍ) matters less than the delays between layers. If an inner loop settles much faster than the outer loop’s sample period, treat it as an algebraic mapping (setpoint → achieved value) with constraints (saturation, rate limits).

REARRANGE: define OP, PV, and specify what order means. Don't use "algebraic mapping" - use more plain language. This section needs better explanations.

### 3.3 Limits to the approximation
- If we command changes faster than the inner loop can follow, we excite lag and oscillations.
- Saturation and rate limits (voltage, friction) create mismatch between setpoint and achieved response.
- As speed rises, sensor sample timing, quantization, and geometry (b, sensor spacing) shrink our valid small-angle window.

Practical rule: design outer loops so that inner loops converge within one outer tick (or a small fraction of it), and enforce rate limits so we don’t exceed inner loop bandwidth.

---

## 4) Incomplete information and estimation strategies

Our two binary sensors (Left, Right) report 0/1 for seeing the line. We don’t directly measure lateral error x or heading θ. We estimate just enough to steer reliably.

### 4.1 Interpreting binary patterns (quick guide)
- 00: neither sees the line. Most uncertain. Use last seen context; avoid impulsive moves.
- 01: right sees line; implies line is under the right sensor or we have drifted right.
- 10: left sees line; symmetric to above.
- 11: both see line; likely centered or the line is wide/thick or sensors are close.

Always treat patterns as constraints, not certainties. Lighting, surface, and curvature matter.

### 4.2 Constant-speed baseline and a short-horizon estimate of x
Assume nominal forward speed v_nom. Track the last sighting time t_last and which side saw the line. Over a short time Δt at speed v_nom with small θ, the lateral change is roughly Δx ≈ v_nom·Δt·sin(θ) ≈ v_nom·Δt·θ. This suggests:
- When a sensor flips, we know we crossed the line under that sensor.
- Between sightings, infer drift direction from the last sign and any heading correction we commanded.

This heuristic is useful but noisy; don’t over-trust it.

### 4.3 Implementation guardrails
- Add slight delay to θ changes in your mental model; do not assume perfect instant heading control.
- When two consecutive detections happen (L then R, or vice versa), reconcile with the motion you executed between them; large contradictions indicate slip or misread.
- Treat a reading as a random variable: if a reading doesn’t reduce uncertainty (e.g., glare causing flicker), prefer to ignore it and wait one more cycle.

---

## 5) Controllers under these assumptions

We present a progression. All assume the time-scale separation discussed above and include respect for inner-loop bandwidth.

### 5.1 Bang-bang (sign-only)
Logic: if the line is under the right sensor (01), steer right wheel slower / left faster (positive w); if under the left (10), steer left wheel slower / right faster (negative w). Add dwell/hysteresis to avoid chatter: require the same state for N ticks before switching.

Pros: simple, robust to noisy magnitudes. Cons: oscillatory, speed-limited.

### 5.2 Simple proportional on sign and persistence
Count how many consecutive ticks we’ve seen the same side (persistence). Larger persistence implies larger lateral error. Use a small proportional gain on this pseudo-error to scale w, and cap by rate limits to respect inner loops.

### 5.3 PD-style using flip rate as a derivative proxy
Rapid flips L↔R indicate aggressive overshoot. Add damping: reduce |w| when flip rate rises, or add a term proportional to recent change in the pseudo-error. Include a deadband for very small deviations.

### 5.4 Rate limiting and deadband
- Rate-limit changes in w (or in wheel setpoints) to what the wheel-speed loop can track.
- Add a small deadband around “centered” to prevent chattering when both sensors see the line intermittently.

---

## 6) Tuning workflow (symptom → fix)

Start slow. Increase speed only when stable.

- Oscillation near center: increase damping (PD term), add deadband/hysteresis, reduce proportional effect of persistence.
- Misses tight curves: allow larger |w| at higher persistence; consider slowing v_nom in high-turn-rate segments (speed scheduling).
- Flicker-triggered zigzags: ignore ambiguous readings for one tick; require persistence; add simple temporal filtering.
- Late reaction at higher speed: raise update rate of the outer loop or increase inner loop bandwidth; ensure rate limits aren’t overly conservative.

---

## 7) Failure modes and making it harder

- Lost line (00 for too long): execute a recovery pattern—search by spiraling or sweeping w with capped v_nom; remember last side seen and bias the search.
- Gaps/reflective glare: trust persistence over single-tick flips; prefer short memory with decay to ride through gaps.
- Junctions/splits: prefer a policy (e.g., always choose left at T-junctions) or mark counts; otherwise you need higher-level logic.
- Higher speed and wider geometry (large b, sensors further from axle): reduces the validity of small-angle and short-horizon assumptions—adjust gains and rate limits accordingly.

---

## 8) Abstract variant (optional): controlling x via higher derivatives

Motor speed control is like controlling x via ẋ (first derivative). Line following behaves more like influencing x via ẍ/x‴ (through w, which changes θ̇ and thus ẋ). The higher the derivative you act through, the more delay matters and the more valuable inner-loop bandwidth becomes. This is why time-scale separation is the central organizing principle here.

---

## 9) Implementation pseudocode (inner fast, outer slow)

We separate cadences: a faster loop updates wheel speeds smoothly; a slower loop interprets sensors and sets a target w. We assume a nominal forward speed v_nom.

```pseudo
const v_nom = 0.3            // m/s (example)
const w_max = 2.0            // rad/s cap from geometry and traction
const dw_max = 4.0           // rad/s^2 rate limit inner-loop can track
const deadband_ticks = 2     // hysteresis near center
const persist_k = 0.2        // scale from persistence to w command
const damping_k = 0.3        // PD-like damping on flip rate

state
  w_cmd_target = 0.0
  w_cmd_actual = 0.0
  last_seen = NONE           // {LEFT, RIGHT, BOTH, NONE}
  persist = 0
  flip_rate_est = 0.0        // exponential moving avg of flips per second
  t_prev = now()

loop outer at 50 Hz:
  L, R = read_binary_sensors()      // booleans

  // Interpret observation
  if L and not R:   obs = LEFT
  else if R and not L: obs = RIGHT
  else if L and R:  obs = BOTH
  else:             obs = NONE

  // Persistence & flip-rate estimation
  if obs == last_seen: persist += 1 else persist = 1
  if obs in {LEFT, RIGHT} and last_seen in {LEFT, RIGHT} and obs != last_seen:
      register_flip(); update(flip_rate_est)
  last_seen = obs

  // Decide target angular rate w based on observation
  if obs == LEFT:
      w_cmd_target =  clamp(+persist_k * persist, -w_max, w_max)
  else if obs == RIGHT:
      w_cmd_target =  clamp(-persist_k * persist, -w_max, w_max)
  else if obs == BOTH:
      if persist < deadband_ticks: w_cmd_target = 0.0
      else w_cmd_target = 0.0      // stay centered
  else: // NONE
      // uncertain: bias toward last known side, but tempered
      if last_seen == LEFT:  w_cmd_target = clamp(+persist_k, -w_max, w_max)
      else if last_seen == RIGHT: w_cmd_target = clamp(-persist_k, -w_max, w_max)
      else w_cmd_target = 0.0

  // PD-like damping using flip rate proxy
  w_cmd_target = w_cmd_target * (1.0 - damping_k * flip_rate_est)

  // Inner-loop respect: rate-limit actual command toward target
  dt = now() - t_prev; t_prev = now()
  delta = w_cmd_target - w_cmd_actual
  step = clamp(delta, -dw_max * dt, +dw_max * dt)
  w_cmd_actual = w_cmd_actual + step

  // Convert (v_nom, w_cmd_actual) to wheel speeds
  vL = v_nom - 0.5 * b * w_cmd_actual
  vR = v_nom + 0.5 * b * w_cmd_actual
  send_wheel_velocity_setpoints(vL, vR)

loop inner at 200–500 Hz:
  // Smoothly track wheel velocity setpoints (PI control, not shown)
  update_wheel_speed_controllers()
```

Notes:
- The outer loop runs slower (e.g., 50 Hz). The inner loop must be fast enough that rate-limited w changes look nearly instantaneous to the outer loop.
- The constants should be tuned for your robot; start conservative and increase only when stable.

---

## 10) Diagram placeholders and references

Diagram A (geometry & variables):
[DIAGRAM A PLACEHOLDER]
Alt text: Differential-drive geometry with wheelbase b, wheel radius r, left/right sensors ahead of axle, showing line, heading θ, lateral error x.

Diagram B (time-scale ladder):
[DIAGRAM B PLACEHOLDER]
Alt text: Ladder from current/torque (fast) → wheel speed (fast) → pose/heading (medium) → line-relative error (slow), annotated with approximate time constants and where rate limits apply.

Further reading: any standard differential-drive kinematics note, and introductory control texts focusing on cascaded loops and bandwidth.

---

## 11) Short introduction (overview)

We want a robot with two wheels and two digital line sensors to follow a black line on a white floor. The aim is not perfect derivations but reliable behavior via the right abstractions: map commands to motion, separate time-scales, estimate just enough from sparse sensors, and add guardrails (rate limits, hysteresis) so the outer loop doesn’t overdrive the inner loops. Keep it modular so each layer can be tuned or swapped without rewriting the whole system.


