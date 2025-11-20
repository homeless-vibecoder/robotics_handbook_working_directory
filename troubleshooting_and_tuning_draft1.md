## Plan

How to analyse trends, graph, what to look at, when recording a variable to troubleshoot.

How to tune a robot in general (e.g. PID, some other tuning)

Usual scenarios of when we need tuning or troubleshooting (where simple analysis would give good insight)



## Example by GPT:

Imagine you are in the lab late in the afternoon. The demo is tomorrow.  
Your robot *almost* works: it drives, turns, follows commands—until suddenly, at the worst possible moment, it does something that feels completely random.

In these moments, it is very tempting to start adding `if`-statements:

- If the error is big, slow down.
- If the robot is turning too much, reduce the left wheel speed.
- If it resets, maybe just catch the error and reboot.

Very quickly, this turns into a tangle of patches that nobody understands. This chapter is about an alternative way of thinking: **treating troubleshooting as an investigation**, guided by simple measurements and graphs, instead of guesswork.

We will walk through a few short stories. In each one, a robot misbehaves in a realistic, low‑level way, and we use very basic data (time, voltages, speeds, positions) to find out what is actually wrong.

---

### Story 1 – The robot that panics when it accelerates

The first robot we will meet is a small two‑wheeled differential‑drive platform with a microcontroller, a motor driver, and a Li‑ion battery pack. On the bench, everything looks fine. If you slowly push the joystick forward, the wheels spin. If you command a gentle turn, it responds smoothly.

But when you ask it to accelerate quickly—full speed across the lab—it behaves strangely:

- Sometimes the robot suddenly **stops and resets** right after you start moving.
- Other times, it manages a short burst of speed and then dies in the middle of the floor.

Someone suggests there might be a bug in the code: maybe the control loop divides by zero, or some array index goes out of bounds when the speed command is large. Another person suggests lowering the maximum speed in software “just to be safe”.

Before changing the code, you decide to ask a different question:

> “Is the hardware even *able* to do what we are asking?”

You add one extra thing to your logging: **battery voltage vs time**. You already have a timestamp in your loop; you add a line to record:

- Time
- Commanded left and right wheel speeds
- Measured wheel speeds from encoders
- **Battery voltage**

You run the robot three times:

1. Once with a very gentle acceleration.
2. Once with a medium acceleration.
3. Once with an aggressive push of the joystick to maximum.

You plot voltage vs time for these runs. The result is very clear:

- At rest, the battery sits around 12.2 V.
- With gentle motion, it dips briefly to around 11.7 V and recovers.
- With an aggressive command, it **drops to 9 V almost instantly**, then the microcontroller resets.

You also plot wheel speeds vs time and notice something interesting:

- Just before each reset, the wheel speeds **do not** reach their commanded values; instead, they stall as the voltage collapses.

At this point, the shape of the curves is more informative than any line of code. The robot is not failing because the control loop is clever or stupid; it is failing because:

- The **power system cannot supply** the current needed for aggressive acceleration.
- The voltage sag is large enough to trigger a brownout or reset.

The “random” resets are not random at all: they occur *exactly* when the current demand is highest.

In other words, the robot is physically incapable of doing what you ask, and the symptoms are telling you this. Without logging voltage, you might spend hours staring at the code, trying to fix a problem that is not in the code.

From here, there are several possible fixes:

- Use a battery with lower internal resistance (or a fresh, fully charged pack).
- Improve wiring and connectors to reduce extra resistance.
- Add a proper voltage regulator or brownout protection.
- Limit acceleration in software—but now as a conscious **design choice**, not as a blind guess.

The key point is not which fix you choose. The key point is that **a single, simple plot**—voltage vs time—completely changes the direction of your troubleshooting.

---

### Story 2 – The robot that cannot drive straight

Our second robot is also a differential‑drive platform. On paper, its control logic is very simple:

- To go straight: command the same speed to both wheels.
- To turn: command a higher speed to one wheel than the other.

In reality, when you command a straight line, the robot slowly curves to the right. No matter how carefully you aim it, it drifts off the intended path.

The first reaction from many students is to “fix” the drift in software:

- Subtract a small constant from the left wheel command.
- Add an extra term to the heading controller.
- Insert an `if` statement: “if we are drifting right, reduce left speed a bit”.

These patches might work in one part of the lab and fail in another, or work at low speed and fail at high speed. They do not explain **why** the robot prefers to turn right.

Instead, you treat this as an investigation. You want to know:

> “When I send the same command to both motors, do they actually behave the same?”

You set up a controlled experiment:

- Lift the robot so the wheels can spin freely.
- Sweep the command from low to high: for example, from 0% to 100% power in steps.
- At each step, record:
  - Commanded PWM value (or speed command).
  - Measured left wheel speed (from the encoder).
  - Measured right wheel speed.

You then create a simple graph: **measured speed vs command** for each wheel on the same plot.

The result is striking:

- The left wheel speed grows roughly linearly with command.
- The right wheel speed is lower at every command value.
- There is a visible **deadzone** for the right motor: for small commands, it does not move at all.

From this single plot, you learn several important things:

- Your two motors are **not identical**. Even if the driver sends the same command, the physical outcome is different.
- The “go straight with equal commands” assumption is **false**.
- The source of the curvature is a **systematic hardware asymmetry**, not a high‑level planning bug.

Armed with this information, your fix is very different:

- You construct a simple calibration table or linear model for each wheel, mapping desired speed to appropriate command.
- You apply inverse calibration so that when you ask for equal speeds, the commands are *different*, compensating for the weaker wheel.

When you try the straight‑line test again, the trajectory is much improved—without any mysterious constants or extra `if`‑statements scattered through your code.

The deeper lesson is that sometimes, the most effective “control algorithm” improvement is just **accepting the robot as it is**, measuring how it truly behaves, and designing around that, instead of pretending it matches the ideal equations.

---

### Story 3 – The line follower that jitters and gets lost

Our third robot has three reflective sensors pointing at the floor and is supposed to follow a black line on a white surface. Students often implement the logic as a series of rules:

- If the center sensor sees the line, go straight.
- If the left sensor sees the line, turn left.
- If the right sensor sees the line, turn right.

In practice, the robot **jitters from side to side** and sometimes loses the line entirely, especially on curves or in areas of the lab with bright sunlight.

To debug this, one could keep adding special cases:

- “If both left and center see the line, do something different.”
- “If all three see the line, slow down.”
- “If none see the line, spin in place until one does.”

However, this only hides the question:

> “What do the sensors actually see, numerically, when we are on the line vs off the line?”

You decide to ignore the high‑level behavior for a moment and just look at the raw data.

You run the robot slowly over the floor while logging, at each time step:

- Time
- Raw readings from the left, center, and right sensors
- A label (“on line” or “off line”), which you can approximate by watching the robot and marking intervals, or by moving it manually in a controlled way.

You then create two types of plots:

1. Sensor readings vs time as you move repeatedly from background to line and back.
2. Histograms of sensor values when “on line” vs “off line”.

The histograms reveal the heart of the problem:

- The “on line” values and “off line” values are **not cleanly separated**.
- There is a wide region where the readings overlap due to lighting variations and noise.

Your current threshold for deciding “line vs no line” happens to sit right in that overlap region. No amount of clever `if`‑logic can make this stable; the measurement itself is ambiguous.

Once you see this, the next steps feel almost obvious:

- Choose a new threshold (or pair of thresholds with hysteresis) that better separates the distributions.
- Add a small moving average filter to smooth rapid flickering due to noise.
- Re‑tune your line‑following controller now that the measurement is more reliable.

Again, notice how the nature of the fix changes once you look at the data. You are no longer arguing about whether to branch left or right in some special case; you are adjusting the underlying **measurement quality** so that the high‑level logic has something sensible to work with.

---

### Why these stories matter

These examples are intentionally simple. None of them require advanced mathematics or complicated algorithms. In each case, the key move is:

- Stop guessing.
- Pick one or two variables that might reveal what is really happening (voltage, speed, raw sensor values).
- Log those variables over time in a controlled experiment.
- Make a basic plot and see whether the behavior matches your mental picture.

In a real project, the details will change: you might be working with a manipulator, a drone, or a walking robot. The sensors and actuators will be different. But the underlying habit is the same:

> Treat troubleshooting as an experiment, not as a sequence of random code edits.

In the following sections, you can turn these ideas into exercises: giving students logs from “mysterious” robots and asking them to reconstruct the diagnosis, or asking them to design their own minimal logging and plotting strategy before they are allowed to touch the controller gains.

The goal is not to make every student an expert in electronics or control theory. The goal is to give them a **first reflex**: when a robot misbehaves, look for a simple, telling trend in the data before you reach for another `if`‑statement.

---

## Example by GPT (version 2, more in line‑follower style)

Extra notes:

- Keep it concrete.
- Use one \*slightly messy\* robot and look at it from a few angles.
- Try to avoid “high‑level wisdom” and instead let the examples do the work.

### Setup: small lab robot that “just kind of acts weird”

Suppose we have a small two‑wheeled robot in the lab. It is supposed to:

- drive straight for 2 meters,
- then execute a gentle turn,
- then stop near some marker on the floor.

Very basic task. No fancy mapping, no optimal control. Just “go there in a reasonably straight line”.

The hardware:

- 2 DC motors with encoders,
- 1 battery pack,
- a simple microcontroller board,
- some kind of distance or line sensor (doesn’t matter too much at first).

In practice, the robot does the following:

1. Sometimes it starts fine, then **veers gradually to the right**.
2. On some runs, when you ask it to accelerate quickly, it **resets halfway**.
3. On other runs (with a different code version), it never resets, but now the path is even more curved.

So, we have multiple “failure modes” mixed together. Temptation: open the main control loop and start adding if‑statements and magic constants until it kind of works for the demo.

Instead, we will treat this as a sequence of smaller, low‑level questions, each with its own small experiment.

---

### Part 1 – Sanity check: does the power system behave?

Question: is the power system stable when we do “normal” moves?

We are not trying to *fix* the path yet. We only want to know if the robot is secretly hurting itself every time we ask it to move quickly.

Minimal log to add:

- time \(t\),
- battery voltage \(V(t)\),
- left and right wheel commands \(u_L(t), u_R(t)\),
- maybe measured wheel speeds \(v_L(t), v_R(t)\) if we have them.

Experiment:

- Command a straight line with three different acceleration profiles:
  - slow ramp up,
  - medium ramp,
  - aggressive step.

Then, plot \(V(t)\) for these three cases on the same graph (or side by side).

There are two qualitatively different possibilities:

1. **Voltage stays flat-ish.** It maybe dips a little when motors start, but no dramatic collapse.  
   In that case, power is probably not the main suspect.
2. **Voltage collapses on aggressive commands.** It goes from (say) 12 V down to 9 V or lower when you push the command, often exactly when the robot resets.

Case (2) is extremely common in student robots. It means:

- the battery is too weak, too discharged, or too high‑impedance,
- or the wiring/regulator is undersized,
- or all of the above.

This is not a “control” problem in the usual sense. It is a “physics and hardware” problem. No amount of clever control logic will remove the brownout if we insist on asking for impossible currents from the battery.

Takeaway: before worrying about tuning, we want to know which world we live in: (1) or (2).

> If we are in case (2), our first “tuning knob” is actually the acceleration profile and wiring, not any PID gain.

NEED PLOTS – show a fake but realistic \(V(t)\) trace for the three profiles, explicitly mark reset events.

---

### Part 2 – Are the two motors actually symmetric?

Even if the power is okay (or okay enough), the robot might still drift. A simple mental model for a differential‑drive robot is:

$
v = \frac{v_R + v_L}{2}, \qquad
w = \frac{v_R - v_L}{L},
$

where:

- \(v\) is forward velocity,
- \(w\) is angular velocity (positive = turning left),
- \(v_L, v_R\) are left/right wheel velocities,
- \(L\) is the distance between wheels.

This model suggests: “if I send the same command to both wheels, robot goes straight” (since \(v_L = v_R \Rightarrow w=0\)).

This is the assumption we want to test empirically.

Experiment:

- Lift the robot so wheels can spin freely (no ground contact).
- For each command value \(u\) from 0 to 1 (or 0 to 100%), send \(u_L = u_R = u\).
- Wait a short time for speeds to settle.
- Record \(u\), measured \(v_L\), measured \(v_R\).

Now, plot **measured velocity vs command** for both wheels on the same axes:

- x‑axis: command \(u\),
- y‑axis: measured speed \(v\),
- one curve for left, one for right.

Possibilities:

1. Curves almost overlap → motors behave similarly, at least off‑ground.
2. One curve has a big **deadzone** (no motion until some threshold).
3. Slopes are different (for the same command, one wheel is always slower).

Case (2) or (3) means: the motors+drivers are not symmetric. The mapping \(u \mapsto v\) is different on left vs right. Then:

- “Go straight by sending equal commands” is simply wrong.
- Any heading controller on top of that is trying to fight hardware bias all the time.

Instead of hiding this, we can embrace it:

- Fit a simple model \(v_L \approx a_L u + b_L\), \(v_R \approx a_R u + b_R\).
- When we want \(v_L^\*\) and \(v_R^\*\), we solve backwards for the commands \(u_L, u_R\) using these fitted lines.

This turns a messy, drifting robot into something closer to the ideal model we think in terms of—without any extra high‑level conditionals. It is literally just: “measure it, then invert the mapping”.

NOTE: this experiment is tiny in code, but extremely informative. Worth doing for almost any differential‑drive robot in a course.

---

### Part 3 – Time‑scales: what can we actually control quickly?

So far we have looked at:

- “Is power okay?”,
- “Are motors symmetric?”.

There is a third basic question that often hides underneath tuning problems:

> “What quantity are we really controlling, and on what time‑scale?”

Example: suppose we try to correct heading error \(\theta\) very aggressively. Our naive mental picture is:

- “If \(\theta\) is positive, turn left (negative \(w\)) until \(\theta\) becomes zero.”

But in reality, we do not control \(\theta\) directly. We control wheel currents and voltages, which then control accelerations, which then change velocities, which then integrate into \(\theta\). So \(\theta\) reacts **with a delay**.

Sanity experiment:

- Start from standstill on the floor.
- Command a pure rotation (e.g. left wheel forward, right wheel backward with equal magnitude).
- Log:
  - time,
  - command \(u\),
  - estimated angular velocity \(w\),
  - heading \(\theta\).

Plot:

1. \(u(t)\) – the step in command.
2. \(w(t)\) – response of angular velocity.
3. \(\theta(t)\) – integrated angle.

You will typically see:

- almost instantaneous change in **command** (in code),
- a small but visible lag before \(w\) ramps up (motor + drivetrain dynamics),
- a much larger time for \(\theta\) to reach its new value.

The point is not to compute exact time constants, but to get a feeling:

- “I can change \(u\) basically instantly,”
- “\(w\) follows with a delay on the order of tens of milliseconds,”
- “\(\theta\) responds on the order of hundreds of milliseconds or seconds, depending on how far I rotate.”

This classification of time‑scales matters for troubleshooting because:

- If we sample the control loop faster than the plant can react, early measurements will show “no improvement yet” and we may over‑react (overshoot, oscillation).
- If our logs are too coarse in time, we might miss a fast voltage sag or current spike entirely.

So, when a robot “feels unstable” or “sluggish”, it is often useful to draw a rough timeline of the relevant variables and ask:

- which of them we actually influence directly,
- how long it takes for that influence to show up in the variable we care about.

This can prevent us from trying to fix a slow, second‑order behavior with a first‑order mental model.

---

### Putting it together: a small troubleshooting loop

We can now describe a very concrete loop, specialized to this simple lab robot (not a grand general theory):

1. **Check power under load.**  
   Log \(V(t)\) while executing a few “extreme” but repeatable motions. If voltage collapses, fix power or limit acceleration before touching anything else.
2. **Check motor symmetry.**  
   Do the off‑ground sweep of commands and plot \(v_L(u), v_R(u)\). If they differ a lot, add a calibration layer so that “equal desired speeds” actually correspond to equal physical motion.
3. **Look at time‑scales.**  
   Run a couple of step tests (straight acceleration, pure rotation), log commands and responses, and get a feeling for how quickly the robot can really change \(v\) and \(w\).
4. **Only then** start tuning higher‑level behavior (path following, line following, etc.).

Each of these steps has a very ordinary plot behind it—nothing fancy, mostly straight lines, ramps, and step responses. But they answer very different questions than “did the code crash?”:

- Is the robot’s body cooperating?
- Are our basic assumptions (symmetric motors, stable power) even roughly true?
- Are we trying to make the robot do something faster than physics allows?

If students internalize this particular set of sanity checks for *one* small robot, they will already be in a much better position for troubleshooting almost any other platform they meet later.

PLAN / TODO:

- Attach example plots for each experiment (fake or from a real robot).
- Maybe turn each part into a short exercise: give logs first, ask students to guess the underlying problem, then reveal the hardware.