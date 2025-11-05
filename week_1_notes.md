Good ideas:
1) Structure handbook by robotics problems/scenarios - solve the problems from first principles, and don't use them as proxy for explaining topics/concepts (like PID). Instead, make them the main part - the necessary topics will naturally emerge. Instead of having separate large sections for theories, attack each robotics scenario separately and there will be some recurring themes.
2) Add exercises - they should be in a form of a robotics (programming) problem: given ... scenario, write a good (control) algorithm. Might be realistic to write a few/many simulations on Github, where students go, download the files, and can create their "character" (simple instructions in README - commands like how to get velocity, how to set speed, etc.). It should have good UI. Realistic to do because it is easy with Cursor.


Main things to review:
0) General plan/good ideas
1) Motor speed control structure
2) Line follower plan/structure
Would be nice if we find more "lessons" we can put in.
3) IMPORTANT: analogy between line follower and motor speed control - is it worth doing this PID analogy or is there a better analogy to be made?

Questions:
1) Clipping, Arbitrary Choice sections
2) Integral term bringing in x'' - can we do without and are there alternatives (something that doesn't store "momentum")? Maybe it would be nice to introduce PID in line follower, not motor speed control - to emphasize controlling x using x' vs x''. Are there similar distinctions worth making - control over x' vs x'' (so, is making distinction between x', x'' actually useful in practice?). Maybe there are other (in robotics) important indirect ways to control a variable?
3) How much physics intuition to include? Is it confusing that we are controlling c, which is only somewhat related to x'?
4) Is it worth talking about (the idea of) minimizing cost functional (to compare multiple control algorithms)?
5) Is the behavior (there being x, x', x'' into play - even if not obvious from a problem, e.g. friction in motor control forced us to bring in x'') universal in robotics? If so, maybe it is worth including mechanical spring intuition for PID?

6) Line follower robot plan

7) Next week's topic? Could pick something related - representation of state, troubleshooting/tuning, or something less (directly) related: filters (less directly related, but not too unrelated), geometry/robotic arm (line follower does have small connections - motion decomposition - perhaps could be a good transition)

Representation of state
Controls

Filters and signals



Troubleshooting/tuning

Geometry - robotic arm