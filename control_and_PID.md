Control theory is about controling a variable to which you don't have a direct access to, but can indirectly change it.

For example, robot/car doesn't have direct control over the position (it cannot just dictate: let my position be X), however it can indirectly control it with velocity/acceleration.

We are trying to design an algorithm/scheme for changing our control variable (that we have control over) so that we "manipulate" some other variable to be what we want.

A very common situation is, manipulating variable, given that we have control over its derivative (second derivative/acceleration is more common, but let us simplify and talk about first derivative first).

When we say "we have control over a variable", it is a little bit wishy-washy. For example, if we have control over acceleration, we cannot set it to arbitrary value - we have some limits (say, we can set it to be X, as long as -C <= X <= C for some C).
Also, maybe we cannot instantly set acceleration to whatever we want (e.g. in motor, there is very very very small gap in changing the voltage/force/acceleration, but usually we can neglect it and say that we have complete control over acceleration of the motor, as long as it is in some range).

We could also think of position as being our "control variable", even if it is not. However, then we would have constrains on WHEN we can set the position. For example, acceleration has constraint that it has to be between -C and C. Likeweise, we could say, position IS a control variable, as long as it is within some range, as long as the change in time is less than ..., etc. Basically, we have a much more elaborate description of constrains if we pick position as a control variable, whereas with acceleration as control variable, we only have one constraint: [-C, C], and it doesn't depend on time, whatever, etc.

This perspective is not obvious - that anything can be a control variable, but with some constrains, and we usually pick ones that have simple description of constrains (and a few of them).


Suppose we pick control variables. We want to design an algorithm that is going to "schedule" or decide (at each point) what the value of the control variable will be, and that, to some degree, is specifying what the variales are going to do (the general behavior).

We can think of control algorithm as a part of the machine/robot. Think about it this way: we have a car, and it can accelerate within some range, up to certain speed.
Now, if we have a safety system which caps the speed to a lower value, even though the physical engine is still as powerful, our "control algorithm" changed the car - now it cannot accelerate past the lower speed.


Now, to understand what is considered an "optimal" strategy/control algorithm, we must first define what we are trying to optimize for.

Usually, people don't explicitly define what they are optimizing for, since there are some pretty consistent properties good control algorithm has; for example, if we want to manipulate Y - e.g. increase it by 10 - everyone would agree, if we have two control algorithms (identical, except for one detail): one allows increasing Y by 10 in at least 2 seconds, the other allows it in at least 5 seconds, the one which allows us to do more things (change Y in 2 seconds, as opposed to 5) is better.

There are some gray-area places, where it isn't obvious, what is better. Think of a signal/variable that we are trying to set to some value. Which is better: we can very quickly set it close to that value, but it takes long time to actually become that value vs we need medium amount of time to set it exactly to the value, but before that, it is inaccurate.
To decide such "edge cases", we need a more precise definition of better.
Note that this is more for a theoretical understanding rather than usual engineering tasks.
We can use a cost function - given a control algorithm, what is its cost? We say one is better than the other if it has less cost.



What are some reasonable cost functions?

Suppose we have control over x'' (absolutely bounded by C), and we are trying to control x. Let us evaluate score by how well/quickly we can change value of x: given we are currently at x_0 (let x_0=0), how quickly can we get to x_1>0 and stay there.
Let cost be L2 norm (dt). So, we have, x(0)=0, x'(0)=0, and goal is x(t)=x_1. \int |x(t)|^2 dt is the cost that we want minimized.




What does PID optimize for?





Line follower robot control algorithm:



___________________________________________________________________________________________________


We'd like to control x, over which we don't have direct control. Instead, we can directly control x'', and need to plan so that x behaves as we want.

Important to stress, a lot of ways to change x towards the direction of error - e.g. sgn(x)*|x|^p, p>0.
Functions with multiple scales - different p, x^p.

Demonstrate, on graph (control of variable under gaussian error - or maybe a better/more realistic error - gaussian error in inputs x', x - maybe gaussian error on output also), different p-s.


Simple/heuristic strategy: go towards the direction of error.

Damping - lagged response oscillation. USE IN LINE FOLLOWER

Bang-bang strategy - maybe requires state (e.g. storing when was last time you saw line - and assume, robot's orientation is, on average, off by ...)




Exercises: write program for ... simulation (so, student should write character for a simple game/physical simulation in python)


Notes: In motor control, we have control over x'. In line follower, we control x'' (distance from the line), but we have control over theta - angle between robot and path - acceleration of that.

The following pasted in motor_speed_control.md:
Breaking down line follower robot:
we have 2 motors, 2 sensors. We can decompose the motion into pure straight motion, and pure rotation - very useful decomposition.


____________________________________________________________________________________________motor_speed_control.md
Breaking down motor speed control:
We control power/current in [-1, 1], and the more power/current we have, the more (angular) acceleration we have (possibly assume power and acceleration are proportional).

Important intuitions in this scenario (the physical facts): without friction and other (electro-magnetic forces that oppose motion), 0 power would correspond to 0 (angular) acceleration - so, the motor would continue spinning forever on the same (angular) velocity.
Truth is, the faster the motor spins, the larger the opposing forces, so eventually, we get maximum velocity, where maximum power is needed just to cancel out the opposing forces - it is like we are filling up a tank, which has a hole on the bottom - the more full the tank is, the more water gets out of the hole.
Maybe include???: acceleration isn't exactly linear with power, but it is a good approximation, but we don't really need the dependence to be linear - same concept of going towards the error applies - except it is like using sgn(x)*|x|^p as error, instead of x^1.

Maybe remove - these are part of physical intuition:
____
Let us denote the angular velocity by x - that's the variable we want to control.

Because we can control the power, this is same as controling x' - angular acceleration.
It is important to understand, though we control "angular acceleration", we control x', not x'' - because our x is angular velocity. We note this because what the actual x represents is irrelevant. We would have the exact same problem if we wanted to control position (x) using velocity (x'). In other words, this pattern of controlling x while having access to x' isn't specific to this setup - it can be generalized.


We can increase/decrese x'. Roughly, x' is combination of p and R, p - how much power/current we give to the motor, R - how much resistance the motor has (note that it depends on velocity - faster you spin the motor, the more resistance it has).
The exact correspondence is irrelevant and not that easy to model. Instead, all we care about is, if we set high p, x' is going to increase. If we set low p (negative), x' is going to decrease (note that x' could be negative - decreasing it would make it even more negative).
____

We aren't exactly sure about what kind of correspondence we have - we are setting this value c(t), at each time t, which is how much power do we give the motor (takes on a value between 1 and -1)?
The only thing we know is, setting larger c(t) increases x'(t), while lower c(t) decreases x'(t) [For authors: is it better to use c(t), x'(t) or just c, x'?].

Even though the above is technically the correct setup, for the sake of simplicity, we will assume, x'(t)=c(t). This assumption doesn't really change what we do - even in practice, we can say, controlling the power is roughly same as controlling x'(t).


Suppose at this instant, we have the current angular velocity, x=x_0, but we want to reach x=x_g. Say, x_g>x_0.

It is very simple - just set x' to be maximum so that we increase x and reach x_g quickly.

So, in this case, we would have, at each time/iteration, measure x, check if x_g-x is positive, negative or zero. If positive/negative we set x' to be 1 or -1 respectively - otherwise, zero [fun fact: this strategy is called "bang-bang" in control theory].
Another way to write this is to set x'=sgn(x_g-x), where sgn(v)=1 if v>0, -1 if v<0, 0 if v=0.

Note that sgn(x_g-x) tells us the "direction" towards which we should correct: we are currently at x, and we are trying to reach x_g, so we take step away from x, towards x_g, ie x_g-x. For the magnitude, we pick the largest possible (so, 1, since we can choose x' to be between -1 and 1).

ATTACH A GRAPH of x'=sgn(x_g-x) - (slight, but ongoing) oscillation

This approach goes to the correct direction, as quickly as possible, and is effective when x is far from x_g.
However, it overshoots and then oscillates:
even when x is only a little bit below x_g, x', instead of being slightly positive, is very large.
So, instead of slowly approaching x_g and then settling, we speed through it, and then we find, we overshot - hence time to go back down at full speed: set x'=-1. The cycle continues - hence the oscillation around x_g.


It is important to understand what the oscillation is caused by.
One might have a slightly misleading intuition (in this case) of momentum: "if we approach a target x_g quickly, we need some time to slow down - we have momentum/inertia, and cannot stop instantenously - just like a car".
This intuition holds when we have control over x'' - acceleration of x. In that case, we cannot instatly set the momentum/velocity x'= 0, we need some time (and we will discuss such scenarios later).
However, our case is different: we have control over x', so we CAN set it instantly to 0.

The reason for oscillation in our case is only because of lag/delay in the iteration/loop: if we set x'=1, x - the angular velocity in real world - will keep accelerating until we set x' to a different value.
However, we are only going to measure/notice this change after some small time (but still non-zero). So, if it takes D seconds to realize/notice that we've overshot, the oscillation is going to have size/amplitude roughly D*x'= D.
To see this just think of the extreme case - suppose x is very, very slightly below x_g, we measure x, and set x'=1. After D seconds, we measure x, and find that x had changed by D*x'=D. So now x \approx x_g+D. Similar thing could happen in the other direction. So overall, we will have x oscillating between x_g-D and x_g+D. This oscillation isn't terrible (and would be much worse if we controlled x'' instead of x'), but we can do better.


[For authors: This is a section, where we discuss the optimal solution, but it is unrealistic, since we require knowing D, x exactly - not sure if it is worth including ]
If we knew D, x exactly, the optimal strategy would be to set x'=(x_g-x)/D, so that after D seconds (the next iteration/measurement of x), x=x_prev+Dx'=x_g.
Note, since x' can only be between -1 and 1, (x_g-x)/D would be same as sgn(x_g-x) if |x_g-x|>D - if we are far from x_g. However, if x_g and x are close, x'=(x_g-x)/D would give us the optimal x'.
Now, the problem with this approach is, we assume ideal conditions - remember the simplifications/assumptions we made. First, we don't directly control x' - instead, we control c, which "roughly has the same trend as x' - when c increases, x' also increases", but we cannot precisely control x'. Also, we cannot exactly measure x, nor can we exactly set x' (there will always be some error in the physical mechanism), nor do we know D - the time interval between iterations (it might not even be fixed). So, let us consider a different improvement/solution that is more robust and works for the real scenario.


The main problem with the bang-bang controller is that it is too aggressive near the goal. We can improve this by using smaller x' when we are close to x_g.
For example, consider setting x'=x_g-x. Now, if x and x_g are close, x' will be set to sgn(x_g-x)*|x_g-x|, which does what we want - small when |x_g-x| is small.
This idea of "scaling by error" is what control engineers call proportional feedback.

Using this sort of strategy has some details in implementation worth discussing, since similar issues come up frequently in Robotics.

Clipping:
Note that we can set x' to be anywhere between -1 and 1. However, x_g-x could be larger than 1. So, setting x'=x_g-x might be problematic. A simple solution is to "clip" the values - if x_g-x is larger than one, just set it to one (similarly for -1). If it is within the desired range (of -1, 1), just set x'=x_g-x, and no problems occur [For authors: maybe explain a little better with implementatin/pseudocode].

This is in general a useful principle - when setting values for variables, think about the range, and make sure the values are within the range (so, in our case x' should be set to something that is always between -1 and 1).


Arbitrary Choice:
Observe, when fixing the bang-bang strategy, we wanted an alternative that would be less aggressive when x\approx x_g. We picked x'=x_g-x as a solution. However, it is important to appreciate how arbitrary of a choice this is - many functions can achieve the same goal.
Consider, instead of x_g-x, we take, still arbitrary/specific choice, but a slightly more general version, k*sgn(x_g-x)|x_g-x|^p, where k>0, p>0 are some fixed numbers (for k=1, p=1, we just get x_g-x).
Let us broadly analyze the effects of k, p on the behaviour (let's use x'=k*sgn(x_g-x)|x_g-x|^p, with clipping between -1 and 1).
[For authors: might be worth mentioning more strange possible functions, e.g. |E|*sin(E), to demonstrate the point of this subsection]

ATTACH A GRAPH of x'=k*sgn(x_g-x)|x_g-x|^p with clipping, for a few k, p.
... Insert effects of k, p on the control (could also mention, in next subsection allowing for tuning is more relevant - when we have access over c, and not x').

This (the observation that our choice was arbitrary and only vaguely justified) is an important thing to note - quite often in engineering it is easy to think, the choices are justified and almost unique - that there is the "correct choice".
Even though there are good and bad choices, there might be multiple (maybe even infinite) good enough choices. This is a general thought one should keep in mind and not constrain oneself needlessly.
So, in similar cases where we want a certain behaviour, but are not sure about the exact form, it might be a good idea to allow for tunable parameters. So, instead of using x_g-x, it might be a better idea to use k*sgn(x_g-x)|x_g-x|^p, and set k=1, p=1 by default; it performs like x_g-x, but leaves the flexibility to change/tune k, p to get a different behaviour.



Closing the gap with real world: using c, instead of x' (x'=c-Resistance)

Introduce integral correction - proportional term and friction will be in equillibrium, so x will always stabilize slightly below/above x_g (how much below/above depends on friction, which depends on x_g). - a way to learn bias (maybe also offer an alternative fix - problem with integral is, it introduces acceleration term)

Tuning (of k, p in k*sgn(x_g-x)|x_g-x|^p) becomes more relevant

Maybe:
introduce noise, elaborate more on the delay (what if it was large?). Might leave derivative term for next chapter - it is more relevant when we control x'' (although integral term has a similar "momentum" behaviour).
____________________________________________________________________________________________motor_speed_control.md


Line follower:

