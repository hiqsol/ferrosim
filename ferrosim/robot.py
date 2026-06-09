from __future__ import annotations

import logging
from threading import Lock

from ferrosim.model import (
    Command,
    CommandKind,
    ElevatorState,
    Result,
    RobotActivity,
    RobotConfig,
    RobotState,
    RobotStatus,
)

LOG = logging.getLogger(__name__)


class Robot:
    def __init__(self, state: RobotState, config: RobotConfig):
        self._state = state.clone()
        self._config = config
        self._lock = Lock()

    @property
    def robot_id(self) -> str:
        return self._state.robot_id

    def perform(self, command: Command) -> Result:
        with self._lock:
            result = self._perform_locked(command)
            self._log_result(command, result)
            return result

    def snapshot(self) -> RobotState:
        with self._lock:
            return self._state.clone()

    def _perform_locked(self, command: Command) -> Result:
        state = self._state
        if state.status.IsError():
            return Result(error=f"robot {state.robot_id} is in error state")
        if command.start_time < state.last_finish_time:
            return Result(
                error=(
                    f"start_time {command.start_time} is earlier than robot "
                    f"last_finish_time {state.last_finish_time}"
                )
            )

        params_error = self._validate_params(command)
        if params_error:
            return Result(error=params_error)

        transition_error = self._validate_transition(command.kind)
        if transition_error:
            state.status = RobotStatus.ERROR
            return Result(error=transition_error)

        duration = self._duration(command)
        if duration < 0:
            return Result(error=f"computed negative duration for {command.kind.value}")

        activity = self._activity(command.kind)
        idle_gap = command.start_time - state.last_finish_time
        idle_drain = idle_gap * self._config.battery.drain_rate(RobotActivity.IDLE)
        activity_drain = duration * self._config.battery.drain_rate(activity)
        voltage_after_idle = state.voltage - idle_drain
        voltage_after_command = voltage_after_idle - activity_drain

        if voltage_after_idle < self._config.battery.min_voltage:
            state.voltage = self._config.battery.min_voltage
            state.status = RobotStatus.ERROR
            return Result(error=f"battery depleted before command {command.kind.value}")

        if voltage_after_command < self._config.battery.min_voltage:
            state.voltage = voltage_after_idle
            state.status = RobotStatus.ERROR
            return Result(error=f"battery depleted during command {command.kind.value}")

        finish_time = command.start_time + duration
        state.voltage = voltage_after_command
        state.activity = RobotActivity.IDLE
        state.last_finish_time = finish_time
        self._apply_successful_transition(command)
        return Result(finish_time=finish_time)

    def _validate_params(self, command: Command) -> str:
        if command.start_time < 0:
            return "start_time must be non-negative"
        if command.kind.IsMove():
            if not command.dst:
                return f"{command.kind.value} requires dst"
            if command.expected_duration is None:
                return f"{command.kind.value} requires expected_duration"
            if command.expected_duration < 0:
                return "expected_duration must be non-negative"
            return ""
        if command.kind.IsLiftWithHeight():
            if command.lifting_height is None:
                return f"{command.kind.value} requires lifting_height"
            if command.lifting_height < 0:
                return "lifting_height must be non-negative"
            return ""
        if command.kind.IsLiftWithoutHeight():
            return ""
        return f"unsupported command kind: {command.kind}"

    def _validate_transition(self, kind: CommandKind) -> str:
        elevator = self._state.elevator
        if kind.IsSend() and not elevator.IsEmpty():
            return "send requires empty elevator"
        if kind.IsHaul() and not elevator.IsHoldingBin():
            return "haul requires gripped or loaded elevator"
        if kind.IsTake() and not elevator.IsEmpty():
            return "take requires empty elevator"
        if kind.IsGive() and not elevator.IsGripped():
            return "give requires gripped elevator"
        if kind.IsLoad() and not elevator.IsEmpty():
            return "load requires empty elevator"
        if kind.IsPass() and not elevator.IsLoaded():
            return "pass requires loaded elevator"
        return ""

    def _duration(self, command: Command) -> float:
        fn = self._config.durations[command.kind]
        if command.kind.IsMove():
            return fn.evaluate(command.expected_duration or 0.0)
        if command.kind.IsLiftWithHeight():
            return fn.evaluate(command.lifting_height or 0.0)
        return fn.evaluate(0.0)

    def _activity(self, kind: CommandKind) -> RobotActivity:
        if kind.IsMove():
            return RobotActivity.MOVING
        return RobotActivity.LIFTING

    def _apply_successful_transition(self, command: Command) -> None:
        if command.kind.IsMove():
            self._state.position = command.dst or self._state.position
        elif command.kind.IsTake():
            self._state.elevator = ElevatorState.GRIPPED
        elif command.kind.IsGive():
            self._state.elevator = ElevatorState.EMPTY
        elif command.kind.IsLoad():
            self._state.elevator = ElevatorState.LOADED
        elif command.kind.IsPass():
            self._state.elevator = ElevatorState.EMPTY

    def _log_result(self, command: Command, result: Result) -> None:
        if result.ok:
            LOG.info(
                "robot=%s command=%s finish_time=%.6f voltage=%.3f level=%.1f%%",
                command.robot_id,
                command.kind.value,
                result.finish_time,
                self._state.voltage,
                self._config.battery.level_percent(self._state.voltage),
            )
        else:
            LOG.warning(
                "robot=%s command=%s error=%s voltage=%.3f",
                command.robot_id,
                command.kind.value,
                result.error,
                self._state.voltage,
            )
