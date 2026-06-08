# Raw thoughts

I want to build simple robot fleet simulation platform.
Simple means:
- no physics simulation
- one concrete robot, no abstractions
- intended fleet size is small, up to 20 robots.

I already have FMS (Fleet Management System) for robots working in warehouse.
It sends robots commands:
- move - drive between nodes
- take - take bin with lift manipulator
- give - put bin

I want my FMS be agnostic of is it working with real robots or simulation platform.
FMS just sends commands and receives answers.

My research showed me that best way to implement what I want is to use SimPy library.

I want to keep such robot internal state:
- position
- manipulator state
- battery level
