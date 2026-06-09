# Overview

A simple robot fleet simulation platform. It stands in for real robots behind the
same contract the FMS (Fleet Management System) already uses, so the FMS can't tell
whether it drives real hardware or the sim.

## Scope

- One concrete robot type, no abstractions. Fleet up to ~30 robots.
- No physics, no collisions, no map, no real clock, no tick loop.
- The FMS owns time and the command dependency graph; it assigns each command's
  start time and waits for the result before sending the next dependent command.

## Model

A command is a pure function: `(state, command, start_time) -> (state', result)`,
where `finish_time = start_time + duration` and `duration` is computed up front
from the command's parameters. The server only stores per-robot state and the last
event time, so "as fast as possible" is free — it answers instantly.

### Robot state
- position (target node, opaque)
- status: ok | error
- activity: idle | moving | lifting
- elevator: empty | gripped | loaded
- battery: voltage (float); `level% = (voltage - 18.0) / (25.0 - 18.0) * 100`

### Commands
- Move: `send` (drive empty), `haul` (drive carrying).
- Lift: `take` (grip a bin), `give` (release), `load` (receive a bin),
  `pass` (have its bin taken).
- Parameters: move carries src→dst + expected duration; take/give carry lifting
  height; load/pass carry none.

### Duration (LinearFunction `kx + b`, k/b are global config per kind)
- move: `k * expected_duration + b`
- take/give: `k * lifting_height + b`
- load/pass: constant `b`

### Elevator transitions (validation spine, single-robot only)
- send: requires empty · haul: requires gripped or loaded
- take: empty → gripped · give: gripped → empty
- load: empty → loaded · pass: loaded → empty

Handoffs (take/give ↔ load/pass) are validated independently per robot; the FMS
guarantees the two sides are sent consistently. No cross-robot checks.

### Battery
Per-activity drain rates in volts/second (move, lift, idle) + capacity, from
server config. On each command: first drain idle over the gap
`(start_time - last_finish_time)`, then drain the command's activity over its
duration. If the operation would drop voltage below 18.0 V (0%), the whole command
fails — no partial finish. A dead robot stays in error.

### Failures (return error text, no finish time)
Battery depleted, invalid elevator transition, command while in error state, and
start_time earlier than the robot's last finish time (causality).

## Interface

- Transport: gRPC, Python.
- One service, one unary RPC: `Execute(Command) -> Result`.
  - Command: `{ robot_id, kind, start_time, params }`
  - Result: `{ finish_time, error }` — empty error means success.
- Robots run in parallel; the server takes a per-robot lock per call.

## Lifecycle & observability (v1)

- Fleet is defined by a static config at startup (robot ids + initial state);
  restart the server to re-run a scenario. No spawn/reset RPCs.
- Observability is logging only — no state-read RPC.

## Explicitly out of scope (v1)

Charging, bin identity, maps/distance/speed, collisions, cross-robot handoff
checks, state-read RPCs, dynamic fleet management.
