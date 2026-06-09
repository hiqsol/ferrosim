import unittest

from ferrosim.config import parse_config
from ferrosim.model import CommandKind, ElevatorState, RobotActivity, RobotStatus


def base_config():
    return {
        "durations": {
            "send": {"k": 1.0, "b": 0.0},
            "haul": {"k": 1.0, "b": 0.0},
            "take": {"k": 2.0, "b": 1.0},
            "give": {"k": 2.0, "b": 1.0},
            "load": {"k": 0.0, "b": 3.0},
            "pass": {"k": 0.0, "b": 3.0},
        },
        "battery": {
            "min_voltage": 18.0,
            "max_voltage": 25.0,
            "drain_rates": {"idle": 0.1, "moving": 0.2, "lifting": 0.3},
        },
        "robots": [
            {
                "id": "r1",
                "position": "a",
                "status": "ok",
                "activity": "idle",
                "elevator": "empty",
                "voltage": 24.0,
                "last_finish_time": 0.0,
            }
        ],
    }


class ConfigTests(unittest.TestCase):
    def test_parse_valid_config(self):
        config = parse_config(base_config())

        self.assertIn(CommandKind.SEND, config.robot_config.durations)
        self.assertEqual(config.robot_config.durations[CommandKind.LOAD].b, 3.0)
        self.assertEqual(config.robots["r1"].status, RobotStatus.OK)
        self.assertEqual(config.robots["r1"].elevator, ElevatorState.EMPTY)

    def test_duplicate_robot_ids_fail(self):
        raw = base_config()
        raw["robots"].append(dict(raw["robots"][0]))

        with self.assertRaisesRegex(ValueError, "duplicate robot id"):
            parse_config(raw)

    def test_missing_duration_kind_fails(self):
        raw = base_config()
        del raw["durations"]["pass"]

        with self.assertRaisesRegex(ValueError, "durations missing"):
            parse_config(raw)


class ModelPredicateTests(unittest.TestCase):
    def test_command_kind_predicates(self):
        self.assertTrue(CommandKind.SEND.IsSend())
        self.assertTrue(CommandKind.SEND.IsMove())
        self.assertTrue(CommandKind.HAUL.IsMove())
        self.assertTrue(CommandKind.TAKE.IsLiftWithHeight())
        self.assertTrue(CommandKind.GIVE.IsLiftWithHeight())
        self.assertTrue(CommandKind.LOAD.IsLiftWithoutHeight())
        self.assertTrue(CommandKind.PASS.IsLiftWithoutHeight())
        self.assertFalse(CommandKind.TAKE.IsMove())

    def test_state_predicates(self):
        self.assertTrue(RobotStatus.OK.IsOk())
        self.assertTrue(RobotStatus.ERROR.IsError())
        self.assertTrue(RobotActivity.IDLE.IsIdle())
        self.assertTrue(RobotActivity.MOVING.IsMoving())
        self.assertTrue(RobotActivity.LIFTING.IsLifting())
        self.assertTrue(ElevatorState.EMPTY.IsEmpty())
        self.assertTrue(ElevatorState.GRIPPED.IsHoldingBin())
        self.assertTrue(ElevatorState.LOADED.IsHoldingBin())
        self.assertFalse(ElevatorState.EMPTY.IsHoldingBin())


if __name__ == "__main__":
    unittest.main()
