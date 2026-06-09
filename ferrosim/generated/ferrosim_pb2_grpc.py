# Generated-compatible gRPC bindings for proto/ferrosim.proto.

import grpc

from ferrosim.generated import ferrosim_pb2 as ferrosim_dot_generated_dot_ferrosim__pb2


class FleetSimStub(object):
    def __init__(self, channel):
        self.Execute = channel.unary_unary(
            "/ferrosim.v1.FleetSim/Execute",
            request_serializer=ferrosim_dot_generated_dot_ferrosim__pb2.Command.SerializeToString,
            response_deserializer=ferrosim_dot_generated_dot_ferrosim__pb2.Result.FromString,
        )


class FleetSimServicer(object):
    def Execute(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_FleetSimServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Execute": grpc.unary_unary_rpc_method_handler(
            servicer.Execute,
            request_deserializer=ferrosim_dot_generated_dot_ferrosim__pb2.Command.FromString,
            response_serializer=ferrosim_dot_generated_dot_ferrosim__pb2.Result.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "ferrosim.v1.FleetSim", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


class FleetSim(object):
    @staticmethod
    def Execute(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/ferrosim.v1.FleetSim/Execute",
            ferrosim_dot_generated_dot_ferrosim__pb2.Command.SerializeToString,
            ferrosim_dot_generated_dot_ferrosim__pb2.Result.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

