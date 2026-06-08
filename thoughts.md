# Raw thoughts

I want to build simple robot fleet simulation platform.
Simple means:
- no physics simulation
- no collision detection
- one concrete robot, no abstractions
- intended fleet size is small, up to 30 robots.

Robots can drive around warehouse and haul single bin.
Robot driving on ceiling can grip bin with it's elevator.
Robots at floor can get loaded with a bin.

I already have FMS (Fleet Management System) for robots working in warehouse.
It sends robots commands:
- move commands:
  - send - drive empty
  - haul - drive with bin (loaded or gripped)
- lift commands:
  - take - take bin with elevator
  - give - put bin
  - load - get loaded with bin by other robot
  - pass - get empty by other robot taking bin

I want my FMS be agnostic of is it working with real robots or simulation platform.
I want the simulation platform run as a server communicating over network.
FMS just sends commands and waits for boolean result success/not.
Real robots get an adapter to the same contract:
- command:
  - start time
  - command parameters:
    - move: src->dst positions, duration
    - take/give: lifting height
    - load/pass: none
- result:
  - error text, none if success
  - finish time (real time for real robots)
Internally FMS tracks dependencies between commands and sends proper start time.
I think these start/finish times are enough for whole simulation.

I want simulation run as fast as possible. FMS is ok with it.

Robots run in parallel.
Every command carries enough info to compute its duration deterministically up front:
- move: sim-duration = LinearFunction(expected duration)
- take/give: sim-duration = LinearFunction(lifting height)
use `kx+b` for LinearFunction in v1

I want to keep such robot internal state:
- position
- status: ok, error
- idle since: written after every command
- elevator state: empty, gripped, loaded (no bin identity)
- battery level - depleting constantly accordingly to current activity

## Decisions (brainstorm 2026-06-08)

- Stack: Python, gRPC.
- No map. Command carries planned duration + target node. Sim computes nothing
  about distance/speed.
- Sim value-add:
  - duration calculation with formulas
  - state tracking + battery + validation, not timing.
  - more later
- Time: no real clock, no tick loop. FMS owns the clock + dependency graph and
  assigns each command's start time. A command is a pure function
  (state, cmd, start) -> (state, finish | error), finish = start + duration.
  Server holds per-robot state + last_event_time only. "As fast as possible"
  is free: the server just answers instantly.
- Ordering: per-robot commands arrive causally ordered because FMS waits for a
  result before sending the next dependent command. Different robots concurrent.
- Battery: drain rate per activity (move/lift/idle) + capacity = server config.
  Fail the whole command (no partial finish time) if battery is not enough
  for the whole operation.
- Failures: battery depleted, invalid command (take-while-holding,
  give-while-empty, command-while-error, and so on). No movement legality (no map).
- No charging in v1: battery only depletes; a dead robot stays in error.
- No state-read RPC in v1: observability is logging only.
- Fleet lifecycle: static config at startup (robot ids + initial state). Restart
  server to re-run. No spawn/reset RPCs in v1.
- Idle drain: charge the gap before each command. On a command with start_time T,
  first drain idle_rate * (T - last_finish_time), then the command's own activity
  drain. Server already holds per-robot last_event_time.
- Handoff: independent per-robot. Each command validates/mutates only its own
  robot's elevator state. FMS guarantees the two sides are sent consistently. No
  cross-robot checks.
- Numerics: start/finish are float seconds. Battery is tracked as float voltage;
  level% = (voltage - 18.0) / (25.0 - 18.0) * 100.0. Drain rates in volts/second.
  Fail the whole command if it would drop voltage below 18.0 (0%).
- Defensive validation: reject start_time < last_finish_time (causality) even
  though FMS should never send it.
- gRPC: one service, one unary RPC Execute(Command)->Result. Command = {robot_id,
  kind, start_time, params}. Result = {finish_time, error}; empty error = success.
  Concurrent robots -> per-robot lock on the server.
- Elevator state is the spine of validation. Single-robot transitions:
  - send: requires empty
  - haul: requires gripped OR loaded
  - take: empty -> gripped     (elevator grips a bin)
  - give: gripped -> empty     (elevator releases)
  - load: empty -> loaded      (gets a bin placed on it)
  - pass: loaded -> empty      (its bin is taken away)
  One robot type; "on ceiling" vs "on floor" is not tracked, it's implied by which
  commands FMS sends. No need to model it.
- Activity mapping: send/haul -> moving; take/give/load/pass -> lifting. Returns to
  idle at finish. No charging activity in v1.
- Duration: move = k*expected_duration + b; take/give = k*lifting_height + b.
  load/pass carry no params -> constant duration (k*0 + b = b). k,b are global
  server config per command kind.
