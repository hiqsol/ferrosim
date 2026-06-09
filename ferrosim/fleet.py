from __future__ import annotations

from ferrosim.model import Command, Result, RobotState, SimConfig
from ferrosim.robot import Robot


class Fleet:
    def __init__(self, config: SimConfig):
        self._robots = {
            robot_id: Robot(state, config.robot_config)
            for robot_id, state in config.robots.items()
        }

    def execute(self, command: Command) -> Result:
        robot = self._robots.get(command.robot_id)
        if robot is None:
            return Result(error=f"unknown robot: {command.robot_id}")
        return robot.perform(command)

    def snapshot(self, robot_id: str) -> RobotState:
        return self._robots[robot_id].snapshot()
