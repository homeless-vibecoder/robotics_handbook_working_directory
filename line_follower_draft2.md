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


Maybe: time shift

MAYBE: compare different strategies - introduce cost function.


If necessary: Maybe try an abstract variant: control x through x'' (motor speed control was x', line follower is x''').
Notes on making the problem more difficult: different variants (high speed, wheels vs sensors far away)


____________________________________________________________________________________________________________________________________________________________


____
Extra notes:

Independent split


Classification of time-scales and order of control + time-scale separation as an indepdendent split

To setup line follower robot, analyze what are time-scales, roughly, and say which model is most relevant

____



# Line follower robot:

## Introduction:

Suppose we have a line follower robot. It is supposed to follow a black line on a white floor. The goal is to stay on the line - otherwise the robot gets lost (ofc, refine the setup). ATTACH A GRAPH/IMAGE
It has 2 motors/wheels, 2 sensors, one on each side - and it outputs either 0 (if it doesn't see the line) or 1 (it sees the line).
We control power to each motor (so, we control acceleration in motor - we cannot instantly set the speed to whatever we want).


## Decomposition into independent parts:

In robotics, most problems involve a lot of indepent parts that have to be dealt with separately.
So, it is important to be good at breaking up the problem into different parts, and be able to have a high-level understanding.
Even in a relatively simple scenario - line follower robot - this becomes very relevant.


## Decomposing motion:
In this section, we try to derive how rotation in motors (what we control) corresponds to movement of the robot (high-level, simplified view).
The plan is: motor's angular velocity $\to$ wheel's linear velocity $\to$ robot's rotation and linear motion.

### motor angular velocity to wheel's linear velocity:



## 