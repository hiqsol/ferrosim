# c-ferrosim

A deterministic robot fleet simulator for an FMS that already speaks a robot
command contract. The simulator stores per-robot state, validates elevator and
battery rules, computes command durations, and answers immediately.

## Contract

The gRPC API is defined in [proto/ferrosim.proto](proto/ferrosim.proto):

- `FleetSim.Execute(Command) -> Result`
- `Command`: robot id, command kind, start time, and command-specific params
- `Result`: finish time on success, or error text on failure

Empty `error` means success. On success, `finish_time = start_time + duration`.

## Run

Install the package with gRPC dependencies, then start a server:

```bash
python3 -m pip install -e .
ferrosim-server --config config/example.yaml --bind 127.0.0.1:50051
```

The fleet is static. Restart the server to reset a scenario.

## Config

See [config/example.yaml](config/example.yaml). The config defines:

- duration functions per command kind as `k * x + b`
- battery drain rates in volts per second
- static robot initial states

## Test

The core simulator does not require gRPC:

```bash
python3 -m unittest discover -s tests
```

## Generate gRPC Stubs

The repository includes committed Python stubs for the current proto. If the
proto changes, regenerate them after installing the dev extra:

```bash
python3 -m grpc_tools.protoc \
  -I proto \
  --python_out=ferrosim/generated \
  --grpc_python_out=ferrosim/generated \
  proto/ferrosim.proto
```
