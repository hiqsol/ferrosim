from __future__ import annotations

import logging
from concurrent import futures

from ferrosim.fleet import Fleet
from ferrosim.model import Command, CommandKind

LOG = logging.getLogger(__name__)


def create_server(fleet: Fleet, max_workers: int = 16):
    try:
        import grpc

        from ferrosim.generated import ferrosim_pb2, ferrosim_pb2_grpc
    except ImportError as exc:
        raise RuntimeError(
            "gRPC runtime is not installed. Install project dependencies with "
            "`python3 -m pip install -e .`."
        ) from exc

    class FleetSimService(ferrosim_pb2_grpc.FleetSimServicer):
        def Execute(self, request, context):
            command = _from_proto(request, ferrosim_pb2)
            result = fleet.execute(command)
            return ferrosim_pb2.Result(
                finish_time=result.finish_time or 0.0,
                error=result.error,
            )

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    ferrosim_pb2_grpc.add_FleetSimServicer_to_server(FleetSimService(), server)
    return server


def _from_proto(request, ferrosim_pb2) -> Command:
    kind = _kind_from_proto(request.kind, ferrosim_pb2)
    if kind.IsMove():
        return Command(
            robot_id=request.robot_id,
            kind=kind,
            start_time=request.start_time,
            src=request.move.src,
            dst=request.move.dst,
            expected_duration=request.move.expected_duration,
        )
    if kind.IsLiftWithHeight():
        return Command(
            robot_id=request.robot_id,
            kind=kind,
            start_time=request.start_time,
            lifting_height=request.lift.lifting_height,
        )
    return Command(robot_id=request.robot_id, kind=kind, start_time=request.start_time)


def _kind_from_proto(value: int, ferrosim_pb2) -> CommandKind:
    mapping = {
        ferrosim_pb2.COMMAND_KIND_SEND: CommandKind.SEND,
        ferrosim_pb2.COMMAND_KIND_HAUL: CommandKind.HAUL,
        ferrosim_pb2.COMMAND_KIND_TAKE: CommandKind.TAKE,
        ferrosim_pb2.COMMAND_KIND_GIVE: CommandKind.GIVE,
        ferrosim_pb2.COMMAND_KIND_LOAD: CommandKind.LOAD,
        ferrosim_pb2.COMMAND_KIND_PASS: CommandKind.PASS,
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"unsupported proto command kind: {value}") from exc
