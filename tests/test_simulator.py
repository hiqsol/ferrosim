import unittest

from ferrosim.config import parse_config
from ferrosim.fleet import Fleet
from ferrosim.model import Command, CommandKind, ElevatorState, RobotStatus
from ferrosim.robot import Robot
from tests.test_config import base_config


class FleetTests(unittest.TestCase):
    def make_fleet(self, mutate=None):
        raw = base_config()
        if mutate is not None:
            mutate(raw)
        return Fleet(parse_config(raw))

    def test_send_moves_empty_robot_and_drains_idle_then_moving(self):
        fleet = self.make_fleet()

        result = fleet.execute(
            Command(
                robot_id="r1",
                kind=CommandKind.SEND,
                start_time=5.0,
                src="a",
                dst="b",
                expected_duration=10.0,
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.finish_time, 15.0)
        state = fleet.snapshot("r1")
        self.assertEqual(state.position, "b")
        self.assertAlmostEqual(state.voltage, 24.0 - 5.0 * 0.1 - 10.0 * 0.2)
        self.assertEqual(state.last_finish_time, 15.0)

    def test_take_then_give_elevator_transitions(self):
        fleet = self.make_fleet()

        take = fleet.execute(
            Command(
                robot_id="r1",
                kind=CommandKind.TAKE,
                start_time=0.0,
                lifting_height=2.0,
            )
        )
        give = fleet.execute(
            Command(
                robot_id="r1",
                kind=CommandKind.GIVE,
                start_time=take.finish_time,
                lifting_height=1.0,
            )
        )

        self.assertTrue(take.ok)
        self.assertEqual(take.finish_time, 5.0)
        self.assertTrue(give.ok)
        self.assertEqual(give.finish_time, 8.0)
        self.assertEqual(fleet.snapshot("r1").elevator, ElevatorState.EMPTY)

    def test_invalid_elevator_transition_sets_robot_error(self):
        fleet = self.make_fleet()

        result = fleet.execute(
            Command(robot_id="r1", kind=CommandKind.GIVE, start_time=0.0, lifting_height=1.0)
        )
        after = fleet.execute(
            Command(
                robot_id="r1",
                kind=CommandKind.SEND,
                start_time=1.0,
                dst="b",
                expected_duration=1.0,
            )
        )

        self.assertFalse(result.ok)
        self.assertIn("give requires gripped", result.error)
        self.assertEqual(fleet.snapshot("r1").status, RobotStatus.ERROR)
        self.assertIn("error state", after.error)

    def test_haul_requires_loaded_or_gripped(self):
        fleet = self.make_fleet()

        result = fleet.execute(
            Command(
                robot_id="r1",
                kind=CommandKind.HAUL,
                start_time=0.0,
                dst="b",
                expected_duration=1.0,
            )
        )

        self.assertFalse(result.ok)
        self.assertIn("haul requires", result.error)

    def test_load_then_pass(self):
        fleet = self.make_fleet()

        load = fleet.execute(Command(robot_id="r1", kind=CommandKind.LOAD, start_time=0.0))
        passed = fleet.execute(Command(robot_id="r1", kind=CommandKind.PASS, start_time=3.0))

        self.assertTrue(load.ok)
        self.assertEqual(load.finish_time, 3.0)
        self.assertTrue(passed.ok)
        self.assertEqual(passed.finish_time, 6.0)
        self.assertEqual(fleet.snapshot("r1").elevator, ElevatorState.EMPTY)

    def test_causality_rejects_start_before_last_finish_without_erroring_robot(self):
        fleet = self.make_fleet()

        first = fleet.execute(
            Command(
                robot_id="r1",
                kind=CommandKind.SEND,
                start_time=0.0,
                dst="b",
                expected_duration=2.0,
            )
        )
        second = fleet.execute(
            Command(
                robot_id="r1",
                kind=CommandKind.SEND,
                start_time=1.0,
                dst="c",
                expected_duration=1.0,
            )
        )

        self.assertTrue(first.ok)
        self.assertFalse(second.ok)
        self.assertIn("earlier than robot last_finish_time", second.error)
        self.assertEqual(fleet.snapshot("r1").status, RobotStatus.OK)

    def test_battery_depletion_sets_error_and_has_no_finish_time(self):
        def mutate(raw):
            raw["robots"][0]["voltage"] = 18.5

        fleet = self.make_fleet(mutate)

        result = fleet.execute(
            Command(
                robot_id="r1",
                kind=CommandKind.SEND,
                start_time=0.0,
                dst="b",
                expected_duration=10.0,
            )
        )

        self.assertFalse(result.ok)
        self.assertIsNone(result.finish_time)
        self.assertIn("battery depleted", result.error)
        self.assertEqual(fleet.snapshot("r1").status, RobotStatus.ERROR)

    def test_unknown_robot_fails(self):
        fleet = self.make_fleet()

        result = fleet.execute(
            Command(
                robot_id="missing",
                kind=CommandKind.SEND,
                start_time=0.0,
                dst="b",
                expected_duration=1.0,
            )
        )

        self.assertFalse(result.ok)
        self.assertIn("unknown robot", result.error)

    def test_multiple_robots_have_independent_state(self):
        def mutate(raw):
            other = dict(raw["robots"][0])
            other["id"] = "r2"
            other["position"] = "x"
            raw["robots"].append(other)

        fleet = self.make_fleet(mutate)

        result = fleet.execute(
            Command(
                robot_id="r1",
                kind=CommandKind.SEND,
                start_time=0.0,
                dst="b",
                expected_duration=1.0,
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(fleet.snapshot("r1").position, "b")
        self.assertEqual(fleet.snapshot("r2").position, "x")


class RobotTests(unittest.TestCase):
    def make_robot(self, mutate=None):
        raw = base_config()
        if mutate is not None:
            mutate(raw)
        config = parse_config(raw)
        return Robot(config.robots["r1"], config.robot_config)

    def test_perform_send_updates_state_and_drains_battery(self):
        robot = self.make_robot()

        result = robot.perform(
            Command(
                robot_id="r1",
                kind=CommandKind.SEND,
                start_time=5.0,
                src="a",
                dst="b",
                expected_duration=10.0,
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.finish_time, 15.0)
        state = robot.snapshot()
        self.assertEqual(state.position, "b")
        self.assertAlmostEqual(state.voltage, 24.0 - 5.0 * 0.1 - 10.0 * 0.2)
        self.assertEqual(state.last_finish_time, 15.0)

    def test_perform_elevator_transitions(self):
        robot = self.make_robot()

        take = robot.perform(
            Command(robot_id="r1", kind=CommandKind.TAKE, start_time=0.0, lifting_height=2.0)
        )
        give = robot.perform(
            Command(
                robot_id="r1",
                kind=CommandKind.GIVE,
                start_time=take.finish_time,
                lifting_height=1.0,
            )
        )
        load = robot.perform(Command(robot_id="r1", kind=CommandKind.LOAD, start_time=give.finish_time))
        passed = robot.perform(Command(robot_id="r1", kind=CommandKind.PASS, start_time=load.finish_time))

        self.assertTrue(take.ok)
        self.assertTrue(give.ok)
        self.assertTrue(load.ok)
        self.assertTrue(passed.ok)
        self.assertEqual(robot.snapshot().elevator, ElevatorState.EMPTY)

    def test_perform_invalid_transition_sets_robot_error(self):
        robot = self.make_robot()

        result = robot.perform(
            Command(robot_id="r1", kind=CommandKind.GIVE, start_time=0.0, lifting_height=1.0)
        )

        self.assertFalse(result.ok)
        self.assertIn("give requires gripped", result.error)
        self.assertEqual(robot.snapshot().status, RobotStatus.ERROR)

    def test_perform_causality_rejection_does_not_error_robot(self):
        robot = self.make_robot()

        first = robot.perform(
            Command(
                robot_id="r1",
                kind=CommandKind.SEND,
                start_time=0.0,
                dst="b",
                expected_duration=2.0,
            )
        )
        second = robot.perform(
            Command(
                robot_id="r1",
                kind=CommandKind.SEND,
                start_time=1.0,
                dst="c",
                expected_duration=1.0,
            )
        )

        self.assertTrue(first.ok)
        self.assertFalse(second.ok)
        self.assertIn("earlier than robot last_finish_time", second.error)
        self.assertEqual(robot.snapshot().status, RobotStatus.OK)

    def test_snapshot_returns_clone(self):
        robot = self.make_robot()
        snapshot = robot.snapshot()

        snapshot.position = "mutated"

        self.assertEqual(robot.snapshot().position, "a")


if __name__ == "__main__":
    unittest.main()
