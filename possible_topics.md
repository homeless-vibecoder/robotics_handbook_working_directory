Big goal: improve intuition - ability to practically make something work. This is absolutely different from rigorous understanding - rigorous understanding is basically useless

Topics/ideas:

Complex numbers, Quaternions

Splines - a good approximation/interpolation tool

PID

Taking measurements - language python?

Few tricks (to prevent division by zero, perhaps some good code-writing practices - e.g. assert)
    - trying to attack the issue of gaussian error in measurements/movements - do not use numbers as you expect them - use them under gaussian error

Understanding derivative as a control variable - need of planning ahead of time

We need some General strategy on how to fix something - an alternative to brute force trial and error

General methods of remembering/representing a state
    - have a certain complexity/explanation power (in evolving the state): if measurements go too unexpected, restart the state - make it visible for the user - too many restarts indicate a problem

some extra things
    - easy/rough simulation
    - tuning of parameters (maybe more useful when fine-tuning - similar to GD final touch)
    - how to write good heuristics


Abstract ideas:

running state, and necessary input knowledge to get knowledge from the measurement.

redundancy vs ease of computation

multi-resolution state/information/action

GCS - separate discrete and continuous parts of the problem

optimization/principle of least action, sparsity - a general technique to decide over or underdetermined system - elaborate
    - Issue of extra DOF


More topics to write on:

sensors/motors - what is the basic machinery and when they work well + how to use


Specific robot examples:

Line follower robot

Robotic arm