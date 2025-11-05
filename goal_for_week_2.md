In motor speed control, introduce bias term. Alternatively, introduce PID - state how we lose the x' control and get x'' only.

Line follower:
Introduce state - approximate variable x, even though we only have knowledge of it on discrete times. To optimal vs PID
Introduce cost function.

Idea: after line follower, do chapter about filters - to deal with inaccuracy in measurements (moving average, zero-division, analysis of what they do, and that all values in a robot are random variables).
Representation of state and filters, in some cases, go hand-in-hand (moving average, prevent zero-division in line follower - when doing last_time_line_seen)


REMEMBER: allow skipping of some parts - allow for chapters within the line follower - so that if there are many things introduced, student can take a break in the middle - and be sure to very explicitly/clearly state in the chapter: that this is a logical finish - if tired, don't continue.
REMEMBER: while parts can be abstracted out (e.g. x, x'), ALWAYS reinforce the analogy - how does the abstract thing correspond to the real thing - it is hard for students (in their initial years of training) to effectively think about a problem in completely abstract terms.

Note: when writing, different parts of a problem should be separate: (1) shows clearer problem-solving structure (2) so that some can be skipped (different parts e.g. abstracting out a problem into control of x, x' is separate from the control algorithm part)


Idea: write a separate section (called abstraction - general lessons learned through the handbook) for control of x via x', x'', x''', and the intuitions/applications