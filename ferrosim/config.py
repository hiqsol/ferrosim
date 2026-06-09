from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ferrosim.model import (
    BatteryConfig,
    CommandKind,
    ElevatorState,
    LinearFunction,
    RobotActivity,
    RobotConfig,
    RobotState,
    RobotStatus,
    SimConfig,
)


def load_config(path: str | Path) -> SimConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return parse_config(raw)


def parse_config(raw: Any) -> SimConfig:
    if not isinstance(raw, dict):
        raise ValueError("config must be a mapping")

    durations = _parse_durations(raw.get("durations"))
    battery = _parse_battery(raw.get("battery"))
    robots = _parse_robots(raw.get("robots"), battery)
    robot_config = RobotConfig(durations=durations, battery=battery)
    return SimConfig(robot_config=robot_config, robots=robots)


def _parse_durations(raw: Any) -> dict[CommandKind, LinearFunction]:
    if not isinstance(raw, dict):
        raise ValueError("durations must be a mapping")

    durations: dict[CommandKind, LinearFunction] = {}
    missing: list[str] = []
    for kind in CommandKind:
        item = raw.get(kind.value)
        if not isinstance(item, dict):
            missing.append(kind.value)
            continue
        try:
            durations[kind] = LinearFunction(k=float(item["k"]), b=float(item["b"]))
        except KeyError as exc:
            raise ValueError(f"duration {kind.value!r} is missing {exc.args[0]!r}") from exc
    if missing:
        raise ValueError(f"durations missing command kinds: {', '.join(missing)}")
    return durations


def _parse_battery(raw: Any) -> BatteryConfig:
    if not isinstance(raw, dict):
        raise ValueError("battery must be a mapping")
    rates = raw.get("drain_rates")
    if not isinstance(rates, dict):
        raise ValueError("battery.drain_rates must be a mapping")

    battery = BatteryConfig(
        min_voltage=float(raw.get("min_voltage", 18.0)),
        max_voltage=float(raw.get("max_voltage", 25.0)),
        idle_drain=float(rates["idle"]),
        moving_drain=float(rates["moving"]),
        lifting_drain=float(rates["lifting"]),
    )
    if battery.max_voltage <= battery.min_voltage:
        raise ValueError("battery.max_voltage must be greater than min_voltage")
    for name, rate in (
        ("idle", battery.idle_drain),
        ("moving", battery.moving_drain),
        ("lifting", battery.lifting_drain),
    ):
        if rate < 0:
            raise ValueError(f"battery drain rate {name!r} must be non-negative")
    return battery


def _parse_robots(raw: Any, battery: BatteryConfig) -> dict[str, RobotState]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("robots must be a non-empty list")

    robots: dict[str, RobotState] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each robot must be a mapping")
        robot_id = str(item.get("id", ""))
        if not robot_id:
            raise ValueError("robot id must be non-empty")
        if robot_id in robots:
            raise ValueError(f"duplicate robot id: {robot_id}")
        voltage = float(item.get("voltage", battery.max_voltage))
        if voltage < battery.min_voltage or voltage > battery.max_voltage:
            raise ValueError(f"robot {robot_id!r} voltage outside configured battery range")

        robots[robot_id] = RobotState(
            robot_id=robot_id,
            position=str(item.get("position", "")),
            status=RobotStatus(str(item.get("status", RobotStatus.OK.value))),
            activity=RobotActivity(str(item.get("activity", RobotActivity.IDLE.value))),
            elevator=ElevatorState(str(item.get("elevator", ElevatorState.EMPTY.value))),
            voltage=voltage,
            last_finish_time=float(item.get("last_finish_time", 0.0)),
        )
    return robots
