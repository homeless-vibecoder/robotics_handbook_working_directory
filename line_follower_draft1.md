Breaking down line follower robot:
we have 2 motors, 2 sensors. We can decompose the motion into pure straight motion, and pure rotation - very useful decomposition.

Topics to include/rough structure/outline:

Motion decomposition (from two wheels' speeds to straight motion + pure rotation)

Maybe: Another motion decomposition - along line vs away from line (cos, sin theta).


Simple/heuristic strategy: go towards the direction of error (so, turn right/left if we see line with left/right sensor - by a fixed amount).
Damping - lagged response oscillation. Draw a parallel between bang-bang strategy in motor speed control and simple "bang-bang" strategy in line follower (more discussion on how to fix after "arbitrary choice").
Also, derive speed at which line follower follows line vs when it doesn't - if it moves too fast (same as saying, iteration time takes too long) there is a point at which the oscillation of bang-bang in x' (same oscillation as in motor speed control) is large enough to not be able to recover (ie, the D > time it takes the robot to cross the line when slightly tilted).
Draw a parallel with the whole control discussed in motor speed control (what would, for line follower, proportional turn mean? How would algorithm/response of line follower be analogous - and to what situations in motor control?).


Again, emphasize arbitrary choice and try a few other possibilities/experiments (and graph)

Maybe: include error (and show for different functions in arbitrary choice)


Minimization of cost - good line follower vs bad line follower have large difference in performance with thin line (good line follower turns less and goes faster).
In line follower, we have a relatively good idea about how our actions change the output - we have almost direct control over x'' (theta', theta - how fast the robot goes towards/away from the line), unlike in motor speed control, where we (assumed that we) can only control x' roughly, using c (so, we just assumed that they are positively correlated).
So, it is easier to find optimal solution (which isn't PID).
Bang-bang strategy - store state (e.g. storing when was last time you saw line - and assume, robot's orientation was, on average, off by ...) - and try to optimize for getting close to the line, as well as keeping parallel with it.

IMPORTANT distinction to stress: PID is optimal when you don't have much information about the system, but if you can model it well, more optimal solutions exist.


Issue of not having access to variable you want to use (e.g. deviation from center at any moment or maybe, for motor speed control, we don't know friction - otherwise we would just compensate for it, without the integral term).


Would be nice: if could include some "numerical trick" - zero-division, using robot variables as having gaussian error on them.

____________________________________________________________________________________________________________________________________________________________


Plan:
Introduce the problem (short)

Decompose motions: motors to translation + rotation (and general lesson/principle), motion along + perpendicular to the line (so, introduce/decompose as theta, speed and mention how theta is x', where x is distance of the robot from the line)

Discuss what control we have over the robot and contrast with motor speed control: here we want to control x, and instead we can control power/acceleration to/of the motors. Velocity of motors control theta', so acceleration controls theta''. theta itself controls x'. So, we have control over x'''.
    - introduce/understand the hierarchy of control, and how one determines it

Do control of x by x''' - this discussion should be (structurally) similar to that of motor speed control: analyse different control algorithms, find analogies with motor speed control (analogies in strategies). Note that it is important to discuss strategies in robot language: even though we have the ability to get rid of the robot and talk about x, x''' abstractly, we shouldn't do that - it should be a mix, always reinforcing.
    - talk about state, unknown information (when doing analogies), include approximation from state - MAYBE don't worry about filtering or maybe it could be a good opportunity to talk about it
    - say, "what if we could ... (e.g. instantly turn/set theta)"? Then, analogies with motor speed control are easy.

MAYBE: compare different strategies - introduce cost function.


If necessary: Maybe try an abstract variant: control x through x'' (motor speed control was x', line follower is x''').
Notes on making the problem more difficult: different variants (high speed, wheels vs sensors far away)


____________________________________________________________________________________________________________________________________________________________



Line follower robot:

Introduction:
Suppose we have a line follower robot. It is supposed to follow a black line on a white floor. The goal is to stay on the line - otherwise the robot gets lost (ofc, refine the setup). ATTACH A GRAPH/IMAGE
It has 2 motors/wheels, 2 sensors, one on each side - and it outputs either 0 (if it doesn't see the line) or 1 (it sees the line).
We control power to each motor (so, we control acceleration in motor - we cannot instantly set the speed to whatever we want).



Decomposing Motion - NEEDS TO BE FINISHED (not sure how much knowledge to assume - should we derive (1) motor angular velocity + wheel radius to wheel velocity (2) wheel velocities + radius of robot to robot motion (3) $v, \theta$ to motion perpendicular + along the line):
First step into controlling the robot is to clearly understand how motor movement determines the motion of the robot.
This is a relatively basic but very helpful decomposition of motion: think of robot motion as pure straight motion + pure rotation (about the center - between the wheels). So, our robot moves with velocity $v$, and towards direction $\theta$ - relative to the line (let's say, counter-clockwise is the positive direction).

Suppose the left/right wheels spin at velocities $v_l, v_r$.
If $v_l=v_r$, then the robot moves straight (this is the robot's velocity).
On the other hand, if $v_l=-v_r$, we get pure rotation.

Now, imagine decomposing the motion in terms of $v, w$ - linear and angular/rotational velocities.

This is important to understand: ANY motion can be decomposed as $v, w$.
So, given $v_l, v_r$ (in m/s), we can find $v, w$ by $v=\frac{v_r+v_l}{2}$m/s, and $w=\frac{v_r-v_l}{2R}$rad/s, where $R$ is the "radius" of the robot (distance from center to a wheel).


This step is always important - to separate the specific robot details (like power to each motor) and the useful abstraction (motion of the robot as speed and direction) that is easier to work with. Doesn't sound like much, but this step is very easy to overlook!




Discuss what control we have over the robot and contrast with motor speed control: here we want to control x, and instead we can control power/acceleration to/of the motors. Velocity of motors control theta', so acceleration controls theta''. theta itself controls x'. So, we have control over x'''.
    - introduce/understand the hierarchy of control, and how one determines it

By the way ($x'', x'''$ are useless for us):
$x'=v\sin(\theta)\approx v\theta$ at small angles, but we don't even need to worry about it - we roughly know, $x'$ corresponds to $\theta$, so $\theta''$ corresponds to $x'''$.
$x''=v\cos(\theta)*\theta'$
$x'''=v(\cos(\theta)*\theta''-\sin(\theta)*\theta'^2)$

Let us now understand what variable we directly control. It isn't instantly obvious, so let us start from the following observation: if we give some power to motors, they will start accelerating respectively. We can control power/current to motors instantenously - the only delay is one for the electronic parts to start sending the current to motor (so, that lag in electric components is negligible - order of milliseconds in a slow case).
This means, we control $v_r', v_l'$.
So, if the motion of our robot is $(v, \theta)$, we have control over $v'$ and $w'=\theta''$ (this is because $v=\frac{v_r+v_l}{2}$ and $\theta'=w=\frac{v_r-v_l}{2R}$).

It might be a little difficult to wrap one's head around the fact that we control $v'$ and $\theta''$. It is useful to realize what this means: we control acceleration

So, to restate: controlling motor power is same as controlling $v_r', v_l'$. Equivallently, $v', w'=\theta''$. And finally, $x'=v\sin(\theta)\approx v\theta$ and $y'=v\cos(\theta)\approx v$.
Our goal when controlling the robot is to stay on the line - ie keep $|x|$ small. For simplicity, let us assume the speed $v$ stays constant - so our control only deals with turning left/right (think about what this assumption means for the robot).

If we fix the speed and only control the rotation, we can roughly think of having direct access to $x'''$.

Maybe: talk about different orders of magnitude: if we control x''', but can set it to a very high value - basically no delay for x''.


____________________________________________________________________________________________________________________________________________________________

NEW PLAN:
Introduce the problem (short)

Decomposition into independent parts (unfortunately, the text format doesn't allow for proper arrangement):

1) Decompose motions:
    - motor angular velocity to wheel linear velocity
    - wheel velocity to linear, angular velocities $v, w$
    - MAYBE? direction + linear speed to along vs perpendicular to the line

2) Discuss different time-scales and what our OP is:
    - electric components (almost instant control over current/acceleration of motor)
    - setting motor to a certain velocity (hence, controlling $v, w$)
    - how fast we can turn (so, control $\theta$ using $w$)
    - don't forget to then sum up, and say that different time-scales can be considered separately/independently - delay from electric components can be ignored on the scale of $w\to \theta$
General principle: we don't even care about whether we control $x', x'''$ or whatnot. Only thing that matters is amount of delay - otherwise, we can think of (approximate) control of (PV) $x$ by $x'$, which is bounded (the approximation breaks at small $x$ - quadratic vs linear becomes more relevant).

Note: we have "direct control" over output (OP) - ie the manipulated/control variable, and we try to indirectly influence the process variable (PV).

2) Possibly: discuss/demonstrate different latencies as well as different orders of control (at extrema, momentum, etc.) NOTE: motor speed control should also have a similar discussion

3) Talk about the fact that we have incomplete information (+ discuss strategies), hence introduce estimating certain values and state (mention that there is no set way of doing it):
    - high-level view of the decomposition/splitting of the parts (what needs to be taken care of together/separately)
    - assume constant speed (note: this is necessary for now - so that the strategy "just set motor velocities to zero and stay on the line" doesn't exist. later, we will/might discuss cost function and remove the assumption). Discuss how to estimate $x$ - distance to line, given the line sensor information (so, store the last time you saw the line, and get $tv\sin(\theta)$). Assume instant control over $\theta$.
        - elaborate on implementation issues + fact-check the assumptions:
            - assume slight delay in setting $\theta$, and add small error to $\theta$
            - handle the case of two consecutive time/line measurements ()
            - measurement as a random variable - it is a good practice to ignore the reading if you don't know what implications it has on your state
            - NEEDS MORE WORK
    - 

Note: here, emphasize the split into independent parts - each part has its own "state" with its own low-level corrections, and at each level we don't worry about other control/state of other levels - we assume that we have some X degree of control




MAYBE: compare different strategies - introduce cost function.


If necessary: Maybe try an abstract variant: control x through x'' (motor speed control was x', line follower is x''').
Notes on making the problem more difficult: different variants (high speed, wheels vs sensors far away)


____________________________________________________________________________________________________________________________________________________________
