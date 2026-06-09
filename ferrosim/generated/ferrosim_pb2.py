# Generated-compatible protobuf definitions for proto/ferrosim.proto.
# Regenerate with grpc_tools.protoc when changing the proto contract.

from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

_sym_db = _symbol_database.Default()


def _build_file_descriptor_proto():
    file_proto = _descriptor_pb2.FileDescriptorProto()
    file_proto.name = "ferrosim.proto"
    file_proto.package = "ferrosim.v1"
    file_proto.syntax = "proto3"

    enum = file_proto.enum_type.add()
    enum.name = "CommandKind"
    for name, number in (
        ("COMMAND_KIND_UNSPECIFIED", 0),
        ("COMMAND_KIND_SEND", 1),
        ("COMMAND_KIND_HAUL", 2),
        ("COMMAND_KIND_TAKE", 3),
        ("COMMAND_KIND_GIVE", 4),
        ("COMMAND_KIND_LOAD", 5),
        ("COMMAND_KIND_PASS", 6),
    ):
        value = enum.value.add()
        value.name = name
        value.number = number

    move = file_proto.message_type.add()
    move.name = "MoveParams"
    field = move.field.add()
    field.name = "src"
    field.number = 1
    field.label = _descriptor.FieldDescriptor.LABEL_OPTIONAL
    field.type = _descriptor.FieldDescriptor.TYPE_STRING
    field = move.field.add()
    field.name = "dst"
    field.number = 2
    field.label = _descriptor.FieldDescriptor.LABEL_OPTIONAL
    field.type = _descriptor.FieldDescriptor.TYPE_STRING
    field = move.field.add()
    field.name = "expected_duration"
    field.number = 3
    field.label = _descriptor.FieldDescriptor.LABEL_OPTIONAL
    field.type = _descriptor.FieldDescriptor.TYPE_DOUBLE

    lift = file_proto.message_type.add()
    lift.name = "LiftParams"
    field = lift.field.add()
    field.name = "lifting_height"
    field.number = 1
    field.label = _descriptor.FieldDescriptor.LABEL_OPTIONAL
    field.type = _descriptor.FieldDescriptor.TYPE_DOUBLE

    command = file_proto.message_type.add()
    command.name = "Command"
    field = command.field.add()
    field.name = "robot_id"
    field.number = 1
    field.label = _descriptor.FieldDescriptor.LABEL_OPTIONAL
    field.type = _descriptor.FieldDescriptor.TYPE_STRING
    field = command.field.add()
    field.name = "kind"
    field.number = 2
    field.label = _descriptor.FieldDescriptor.LABEL_OPTIONAL
    field.type = _descriptor.FieldDescriptor.TYPE_ENUM
    field.type_name = ".ferrosim.v1.CommandKind"
    field = command.field.add()
    field.name = "start_time"
    field.number = 3
    field.label = _descriptor.FieldDescriptor.LABEL_OPTIONAL
    field.type = _descriptor.FieldDescriptor.TYPE_DOUBLE
    field = command.field.add()
    field.name = "move"
    field.number = 4
    field.label = _descriptor.FieldDescriptor.LABEL_OPTIONAL
    field.type = _descriptor.FieldDescriptor.TYPE_MESSAGE
    field.type_name = ".ferrosim.v1.MoveParams"
    field = command.field.add()
    field.name = "lift"
    field.number = 5
    field.label = _descriptor.FieldDescriptor.LABEL_OPTIONAL
    field.type = _descriptor.FieldDescriptor.TYPE_MESSAGE
    field.type_name = ".ferrosim.v1.LiftParams"

    result = file_proto.message_type.add()
    result.name = "Result"
    field = result.field.add()
    field.name = "finish_time"
    field.number = 1
    field.label = _descriptor.FieldDescriptor.LABEL_OPTIONAL
    field.type = _descriptor.FieldDescriptor.TYPE_DOUBLE
    field = result.field.add()
    field.name = "error"
    field.number = 2
    field.label = _descriptor.FieldDescriptor.LABEL_OPTIONAL
    field.type = _descriptor.FieldDescriptor.TYPE_STRING

    service = file_proto.service.add()
    service.name = "FleetSim"
    method = service.method.add()
    method.name = "Execute"
    method.input_type = ".ferrosim.v1.Command"
    method.output_type = ".ferrosim.v1.Result"
    return file_proto


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    _build_file_descriptor_proto().SerializeToString()
)

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "ferrosim_pb2", globals())

if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None

