We want to create a good environment for simulating robot(s) scenarios.
We do everything in 2D and visualize from the top - that really simplifies a lot of things (3D is just not worth the pain).

## Rough structure and goal




## Lowest level mechanics and properties

    - world, and environment
        - ability to insert characters, environment
        - environment should be able to have some available tools, mostly to make a field/put physical stuff
            - however, it could also have more out-of-box attributes - e.g. a place/square that sends a certain signal/magnetism that is only received by a certain radio (specific code, frequency, etc. - like aruco/qr code)
    - robot
        - a construction/composite that has an associated program, as well as parts - sensors, motors, connections, some other attributes

## Basic environment tools

First, note that the environment tools aren't necessarily for the students to mess with - I currently don't see an easy way students could create their own custom maps.
Instead, let us focus on what we need from the environment so that it is easy to write simulations.
No need to worry about speed - simplicity takes priority (and also, we don't expect convoluted scenarios).

A possibility is to have objects in environment that have associated properties, including location, visual effects, interaction with other things, etc.
It is hard to say apriori what all of the useful properties are, so it would be nice if we could define some of them (especially the niche ones) on the fly.


    - center (translation - where it is)
    - scale (one by default)
    - points (relative to the center) whose convex hull is the region of this object (and maybe a bounding triangle/box for simple/quick checks of contact)
        - probably useful to assume: things can only interact if they intersect
    - visual aspect/color
    - interaction
        - friction and traction
            - perhaps also include viscosity/damping
        - secret code/invisible fields
        - blockage: whether or not something can pass through it (e.g. maybe define different classes of blockage/interaction, and each object has an array of them - if there is a commmon element, two objects cannot pass through each other)
        - reflectivity (for distance sensor)
    - boolean variable: can_move. If true, information/characteristics of "moving things" should be provided

### connection

    - type of connection (or its rigidity)...
    - anchor points

### moving things

    - moment of inertia/mass


### visuals

    - wheels should have an arrow to indicate the spin

### Idea
    
    - have a ranking of strength to determine scenarios where unstoppable force meets immovable object
        - force
        - rigidity/strength of connection

## Interaction of objects

### When do objects interact

To make it easy, we say, objects interact only if they intersect.
In addition, we have some simple intersection checks (bounding triangle, bbox, etc. to avoid overcomputation - also to be able to say - if two centers are farther apart than the bounding triangle sizes, no need to check intersection - good for logn sort and local/adjacent element comparison)

### How objects interact

Both objects have their attributes (friction, velocity, mass, etc.) that can be used to calculate their interaction.
We also need a function that determines how some properties of an object - location, velocity, etc. - change, given the contact between two objects.
Note, there might be extra considerations to take, instead of just doing instantenous interaction - maybe similar to how gyro/accelerometer work - we have larger time-scale interaction, and we have smaller time-scale determined by different equations, and our final "fusion" is smaller time-scale quick response, with a dirft towards larger time-scale prediction.



## Basic robot tools

This is to build robots with specific sensors, physical properties, code (computation, lag), etc.


### Sensors and motors

### Building mechanics


## Dec 6 plan:

- Think of a systematic way of making the gui - perhaps use pre-built one or webots inspiration, etc.
- Think of a few scenarios to have a specific goal
maybe for next milestone also, include a vscode-like experience

## Dec 7 plan:

when selecting a motor/imu, etc. be able to drag/move it, similar to a point
mark the center of the robot.
By default, make everything rigid unless specified otherwise.
add cntrl Z to undo and redo.
device placements aren't easy.
add wheels icon/shape for motor/wheel.
allow for 

allow to select multiple points to edit - to rotate things, translate, etc.
Take inspiration from drawing apps.

Add colors and rounded colors for nicer visuals.

configuration of the buttons must be adjusted - it seems too goofy, perhaps there should be comparmentalization/modularity of functionality - not it seems everything is just exposed and messy.
There should be an ability to close some tabs/make them smaller (drag, expand, shrink, etc.)
drag and pan is reversed.


Could you make that text different format - code-like (mmonosspace) fonr would be more appropriate. It doesn't need to show all the time - it can be togglable/dropdown menu. Also, could you add some viewing options to the screen, so that I can scroll out, for exaple in order to zoom in/out and to translate. 
The current gui is too exposed - everything is there, and there is no depth (nothing is hidden, so it is a bit convoluted and lacks functionality). I want to have ability to view state of the motors/sensors. I also want to be able to time-log them, etc (actually, put that in the plan - previously I thought the time-logger would be. part of the robot design, but now I think it would be better to be built-in the viewer/runner/simulator). Also, I feel like the control user has from the siulation isn't enough - there is ability to edit the program of the robot, but insstructions aren't that clear, and they cannot edit, for example how the simulation goes - e.g. it would be nice if they could drag the robot so that it starts from a different positiion - convenient things like that - the flexibility is lacking. Too few things are available to do in the pygame window, and the reason is that everyhting is exposed - there are no drop-down menus that allows one to access many things. Your context window is getting full, so I am planning to switch to a new chat. Please write these plans - what we want to do for next steps, perhaps update @planning_the_gui.md , and give me prompt for the next chat - I will be using plan mode. Thanks!

Dec 7 runner polish (implemented now)
- Collapsible tabs (Code / Devices / State / Logs) with sidebar hide/show to reduce clutter.
- In-viewport view dropdown for reset/center, grid toggle, motor arrows toggle, and quick reposition entry.
- State tab shows live motors/sensors and a selectable logger (pick signals, rate, duration) with CSV export.
- Reposition tool lets you drag/set the robot start pose; reset to spawn or save current pose as new spawn.
- View controls normalized: wheel zoom, middle/right pan (fixed direction), optional grid.


Add the plotter and etc as a window - be able to select the .csv log and be able to open the plotting/analysis window.

Round to 2-3 decimal places when showing numbers. e.g. imu doesn't need to get printed exactly.

Make it clearer - how to edit the robot code - have a "help" option that describes how to alter code, and what format is expected, what sensors/motors there are.
Define/comment what sim means, roughly how it works - it should be accessible from "help" - all the clear instructions on how to use the program, examples, etc. Currently it is very unintuitive.
There should be definitions - what is function step() used for what is _apply(), how are all these things utilized in the simulation - what functions need to be defined, etc.
"Help" is very important and it should open up an elaborate README-like explanation.
On one hand, it should be very short, fast, and easy guide, but it should refer to different chapters.
For example, when someone opens "help" and opens the insturctions, a user has to be able to navigate to the appropriate chapter e.g. "how to get and set values of sensors/motors", or "what functions need to be defined in the class, and how they are used in the simulation", or "general overview of how the simulation works", or "how simulation works - physics, etc. - more in-depth guide/explanation".

Be able to pick a file to edit/control algorithm, so that one can have different control algorithms and switch between them.

Add a designer of the environment - might be useful to be able to draw on the floor (could be drawing as a visual effect or even drawing a wall).
UI very similar to paint.


Improve visuals of the wheels and arrows.

Be able to resize windows from any corner, not just the right corner
