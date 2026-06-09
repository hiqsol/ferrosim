from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CommandKind(str, Enum):
    SEND = "send"
    HAUL = "haul"
    TAKE = "take"
    GIVE = "give"
    LOAD = "load"
    PASS = "pass"

    def IsSend(self) -> bool:
        return self == CommandKind.SEND

    def IsHaul(self) -> bool:
        return self == CommandKind.HAUL

    def IsTake(self) -> bool:
        return self == CommandKind.TAKE

    def IsGive(self) -> bool:
        return self == CommandKind.GIVE

    def IsLoad(self) -> bool:
        return self == CommandKind.LOAD

    def IsPass(self) -> bool:
        return self == CommandKind.PASS

    def IsMove(self) -> bool:
        return self.IsSend() or self.IsHaul()

    def IsLiftWithHeight(self) -> bool:
        return self.IsTake() or self.IsGive()

    def IsLiftWithoutHeight(self) -> bool:
        return self.IsLoad() or self.IsPass()


class RobotStatus(str, Enum):
    OK = "ok"
    ERROR = "error"

    def IsOk(self) -> bool:
        return self == RobotStatus.OK

    def IsError(self) -> bool:
        return self == RobotStatus.ERROR


class RobotActivity(str, Enum):
    IDLE = "idle"
    MOVING = "moving"
    LIFTING = "lifting"

    def IsIdle(self) -> bool:
        return self == RobotActivity.IDLE

    def IsMoving(self) -> bool:
        return self == RobotActivity.MOVING

    def IsLifting(self) -> bool:
        return self == RobotActivity.LIFTING


class ElevatorState(str, Enum):
    EMPTY = "empty"
    GRIPPED = "gripped"
    LOADED = "loaded"

    def IsEmpty(self) -> bool:
        return self == ElevatorState.EMPTY

    def IsGripped(self) -> bool:
        return self == ElevatorState.GRIPPED

    def IsLoaded(self) -> bool:
        return self == ElevatorState.LOADED

    def IsHoldingBin(self) -> bool:
        return self.IsGripped() or self.IsLoaded()


@dataclass(frozen=True)
class LinearFunction:
    k: float
    b: float

    def evaluate(self, x: float) -> float:
        return self.k * x + self.b


@dataclass(frozen=True)
class BatteryConfig:
    min_voltage: float
    max_voltage: float
    idle_drain: float
    moving_drain: float
    lifting_drain: float

    def drain_rate(self, activity: RobotActivity) -> float:
        if activity.IsIdle():
            return self.idle_drain
        if activity.IsMoving():
            return self.moving_drain
        if activity.IsLifting():
            return self.lifting_drain
        raise ValueError(f"unsupported activity: {activity}")

    def level_percent(self, voltage: float) -> float:
        span = self.max_voltage - self.min_voltage
        if span <= 0:
            return 0.0
        return (voltage - self.min_voltage) / span * 100.0


@dataclass(frozen=True)
class RobotConfig:
    durations: dict[CommandKind, LinearFunction]
    battery: BatteryConfig


@dataclass
class RobotState:
    robot_id: str
    position: str
    status: RobotStatus
    activity: RobotActivity
    elevator: ElevatorState
    voltage: float
    last_finish_time: float = 0.0

    def clone(self) -> "RobotState":
        return RobotState(
            robot_id=self.robot_id,
            position=self.position,
            status=self.status,
            activity=self.activity,
            elevator=self.elevator,
            voltage=self.voltage,
            last_finish_time=self.last_finish_time,
        )


@dataclass(frozen=True)
class SimConfig:
    robot_config: RobotConfig
    robots: dict[str, RobotState]


@dataclass(frozen=True)
class Command:
    robot_id: str
    kind: CommandKind
    start_time: float
    src: Optional[str] = None
    dst: Optional[str] = None
    expected_duration: Optional[float] = None
    lifting_height: Optional[float] = None


@dataclass(frozen=True)
class Result:
    finish_time: Optional[float] = None
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.error == ""
