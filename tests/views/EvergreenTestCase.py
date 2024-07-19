from ontoagent.views.agenda import Goal
from ontoagent.views.evergreen import EvergreenGoals, LTGoal, ObservableValue
from ontograph.Frame import Frame
from ontograph.Space import Space
from tests.OntoAgentTestCase import OntoAgentTestCase


class ObservableValueTestCase(OntoAgentTestCase):

    def test_comparator(self):
        ov = Frame("@TEST.OBSERVABLE-VALUE.?")
        ov["COMPARATOR"] = ObservableValue.Comparator.GTE

        self.assertEqual(
            ObservableValue.Comparator.GTE, ObservableValue(ov).comparator()
        )

    def test_set_comparator(self):
        ov = Frame("@TEST.OBSERVABLE-VALUE.?")
        self.assertEqual([], ov["COMPARATOR"])

        ObservableValue(ov).set_comparator(ObservableValue.Comparator.GTE)
        self.assertEqual(ObservableValue.Comparator.GTE, ov["COMPARATOR"])

    def test_value(self):
        ov = Frame("@TEST.OBSERVABLE-VALUE.?")
        ov["VALUE"] = 123

        self.assertEqual(123, ObservableValue(ov).value())

    def test_set_value(self):
        ov = Frame("@TEST.OBSERVABLE-VALUE.?")
        self.assertEqual([], ov["VALUE"])

        ObservableValue(ov).set_value(123)
        self.assertEqual(123, ov["VALUE"])

    def test_is_observed(self):
        ov = ObservableValue.build(Space("TEST"), ObservableValue.Comparator.GTE, 0.5)

        f = Frame("@TEST.FRAME.?")
        self.assertFalse(
            ov.is_observed(f, "SLOT")
        )  # There is no filler for SLOT, so it must be false

        f["SLOT"] = "xyz"
        self.assertFalse(
            ov.is_observed(f, "SLOT")
        )  # The filler for SLOT is not a number, so it must be false

        f["SLOT"] = 0.1
        self.assertFalse(
            ov.is_observed(f, "SLOT")
        )  # The filler for SLOT is less than 0.5, so it must be false

        f["SLOT"] = 0.6
        self.assertTrue(
            ov.is_observed(f, "SLOT")
        )  # The filler for SLOT is >= 0.5, so it must be true

        f["SLOT"] = ["xyz", 0.1, 0.6]
        self.assertTrue(
            ov.is_observed(f, "SLOT")
        )  # At least one filler is a numeric >= 0.6, so it must be true

    def test_is_observed_with_and(self):
        # If the comparator is AND and the values are not ObservableValues
        # then return true if each value exists
        ov = ObservableValue.build(
            Space("TEST"), ObservableValue.Comparator.AND, [0.5, 1.0]
        )

        f = Frame("@TEST.FRAME.?")
        self.assertFalse(ov.is_observed(f, "SLOT"))

        f["SLOT"] = 0.5
        self.assertFalse(ov.is_observed(f, "SLOT"))

        f["SLOT"] = 1.0
        self.assertFalse(ov.is_observed(f, "SLOT"))

        f["SLOT"] = [0.5, 1.0]
        self.assertTrue(ov.is_observed(f, "SLOT"))

        f["SLOT"] = [0.5, 1.0, 1.5]
        self.assertTrue(ov.is_observed(f, "SLOT"))

    def test_is_observed_with_or(self):
        # If the comparator is OR and the values are not ObservableValues
        # then return true if any one value exists
        ov = ObservableValue.build(
            Space("TEST"), ObservableValue.Comparator.OR, [0.5, 1.0]
        )

        f = Frame("@TEST.FRAME.?")
        self.assertFalse(ov.is_observed(f, "SLOT"))

        f["SLOT"] = 0.5
        self.assertTrue(ov.is_observed(f, "SLOT"))

        f["SLOT"] = 1.0
        self.assertTrue(ov.is_observed(f, "SLOT"))

        f["SLOT"] = [0.5, 1.0]
        self.assertTrue(ov.is_observed(f, "SLOT"))

        f["SLOT"] = [0.5, 1.0, 1.5]
        self.assertTrue(ov.is_observed(f, "SLOT"))

        f["SLOT"] = 1.5
        self.assertFalse(ov.is_observed(f, "SLOT"))

    def test_is_observed_with_and_subcomparators(self):
        # If the comparator is AND and the values are all ObservableValues, then the result is the ANDed result of the values
        ov = ObservableValue.build(
            Space("TEST"),
            ObservableValue.Comparator.AND,
            [
                ObservableValue.build(
                    Space("TEST"), ObservableValue.Comparator.GTE, 0.5
                ),
                ObservableValue.build(
                    Space("TEST"), ObservableValue.Comparator.LTE, 1.0
                ),
            ],
        )

        f = Frame("@TEST.FRAME.?")
        self.assertFalse(ov.is_observed(f, "SLOT"))

        f["SLOT"] = 0.4
        self.assertFalse(ov.is_observed(f, "SLOT"))

        f["SLOT"] = 1.1
        self.assertFalse(ov.is_observed(f, "SLOT"))

        f["SLOT"] = 0.75
        self.assertTrue(ov.is_observed(f, "SLOT"))

    def test_is_observed_with_or_subcomparators(self):
        # If the comparator is AND and the values are all ObservableValues, then the result is the ORed result of the values
        ov = ObservableValue.build(
            Space("TEST"),
            ObservableValue.Comparator.OR,
            [
                ObservableValue.build(
                    Space("TEST"), ObservableValue.Comparator.GTE, 0.5
                ),
                ObservableValue.build(
                    Space("TEST"), ObservableValue.Comparator.LTE, 0.4
                ),
            ],
        )

        f = Frame("@TEST.FRAME.?")
        self.assertFalse(ov.is_observed(f, "SLOT"))

        f["SLOT"] = 0.3
        self.assertTrue(ov.is_observed(f, "SLOT"))

        f["SLOT"] = 0.6
        self.assertTrue(ov.is_observed(f, "SLOT"))

        f["SLOT"] = 0.45
        self.assertFalse(ov.is_observed(f, "SLOT"))


class LTGoalTestCase(OntoAgentTestCase):

    def test_name(self):
        ltg = Frame("@TEST.LT-GOAL.?")
        ltg["NAME"] = "Be Healthy"

        self.assertEqual("Be Healthy", LTGoal(ltg).name())

    def test_set_name(self):
        ltg = Frame("@TEST.LT-GOAL.?")
        self.assertEqual([], ltg["NAME"])

        LTGoal(ltg).set_name("Be Healthy")
        self.assertEqual("Be Healthy", ltg["NAME"])

    def test_status(self):
        ltg = Frame("@TEST.LT-GOAL.?")
        ltg["STATUS"] = LTGoal.Status.SATISFIED

        self.assertEqual(LTGoal.Status.SATISFIED, LTGoal(ltg).status())

    def test_set_status(self):
        ltg = Frame("@TEST.LT-GOAL.?")
        self.assertEqual([], ltg["STATUS"])

        LTGoal(ltg).set_status(LTGoal.Status.SATISFIED)
        self.assertEqual(LTGoal.Status.SATISFIED, ltg["STATUS"])

    def test_beneficiary(self):
        ltg = Frame("@TEST.LT-GOAL.?")
        ltg["BENEFICIARY"] = self.agent.anchor

        self.assertEqual(self.agent.anchor, LTGoal(ltg).beneficiary())

    def test_set_beneficiary(self):
        ltg = Frame("@TEST.LT-GOAL.?")
        self.assertEqual([], ltg["BENEFICIARY"])

        LTGoal(ltg).set_beneficiary(self.agent.anchor)
        self.assertEqual(self.agent.anchor, ltg["BENEFICIARY"])

    def test_theme(self):
        ltg = Frame("@TEST.LT-GOAL.?")
        ltg["THEME"] = "MYSLOT"

        self.assertEqual("MYSLOT", LTGoal(ltg).theme())

    def test_set_theme(self):
        ltg = Frame("@TEST.LT-GOAL.?")
        self.assertEqual([], ltg["THEME"])

        LTGoal(ltg).set_theme("MYSLOT")
        self.assertEqual("MYSLOT", ltg["THEME"])

    def test_value(self):
        ov = ObservableValue.build(Space("TEST"), ObservableValue.Comparator.EQUALS, 1)

        ltg = Frame("@TEST.LT-GOAL.?")
        ltg["VALUE"] = ov

        self.assertEqual(ov, LTGoal(ltg).value())
        self.assertIsInstance(LTGoal(ltg).value(), ObservableValue)

    def test_set_value(self):
        ov = ObservableValue.build(Space("TEST"), ObservableValue.Comparator.EQUALS, 1)

        ltg = Frame("@TEST.LT-GOAL.?")
        self.assertEqual([], ltg["VALUE"])

        LTGoal(ltg).set_value(ov)
        self.assertEqual(ov, ltg["VALUE"])

    def test_resolution(self):
        resolution = Frame("@ONT.SOME-GOAL-DEFINITION.?")

        ltg = Frame("@TEST.LT-GOAL.?")
        ltg["RESOLUTION"] = resolution

        self.assertEqual(resolution, LTGoal(ltg).resolution())

    def test_set_resolution(self):
        resolution = Frame("@ONT.SOME-GOAL-DEFINITION.?")

        ltg = Frame("@TEST.LT-GOAL.?")
        self.assertEqual([], ltg["RESOLUTION"])

        LTGoal(ltg).set_resolution(resolution)
        self.assertEqual(resolution, ltg["RESOLUTION"])

    def test_pending(self):
        ltg = Frame("@TEST.LT-GOAL.?")
        self.assertIsNone(LTGoal(ltg).pending())

        goal = Goal(Frame("@TEST.GOAL.?"))
        ltg["PENDING"] = goal
        self.assertEqual(goal, LTGoal(ltg).pending())
        self.assertIsInstance(LTGoal(ltg).pending(), Goal)

    def test_set_pending(self):
        goal = Goal(Frame("@TEST.GOAL.?"))

        ltg = Frame("@TEST.LT-GOAL.?")
        self.assertEqual([], ltg["PENDING"])

        LTGoal(ltg).set_pending(goal)
        self.assertEqual(goal, ltg["PENDING"])

    def test_is_observed(self):
        frame = Frame("@TEST.FRAME.?")
        ov = ObservableValue.build(
            Space("TEST"), ObservableValue.Comparator.EQUALS, 123
        )
        ltg = LTGoal.build(
            Space("TEST"), frame, "SLOT", ov, Frame("@TEST.GOAL-DEFINITION.?")
        )

        self.assertFalse(ltg.is_observed())

        frame["SLOT"] = 123
        self.assertTrue(ltg.is_observed())

    def test_update_changes_status(self):
        frame = Frame("@TEST.FRAME.?")
        ov = ObservableValue.build(
            Space("TEST"), ObservableValue.Comparator.EQUALS, 123
        )
        ltg = LTGoal.build(
            Space("TEST"), frame, "SLOT", ov, Frame("@TEST.GOAL-DEFINITION.?")
        )

        self.assertEqual(LTGoal.Status.UNSATISFIED, ltg.status())

        frame["SLOT"] = 123
        ltg.update()
        self.assertEqual(LTGoal.Status.SATISFIED, ltg.status())

        frame["SLOT"] = 456
        ltg.update()
        self.assertEqual(LTGoal.Status.UNSATISFIED, ltg.status())

    def test_update_clears_finished_pending_goals(self):
        frame = Frame("@TEST.FRAME.?")
        ov = ObservableValue.build(
            Space("TEST"), ObservableValue.Comparator.EQUALS, 123
        )
        ltg = LTGoal.build(
            Space("TEST"), frame, "SLOT", ov, Frame("@TEST.GOAL-DEFINITION.?")
        )

        goal = Goal(Frame("@TEST.GOAL.?"))
        goal.set_status(Goal.Status.ACTIVE)
        ltg.set_pending(goal)

        self.assertEqual(goal, ltg.pending())

        ltg.update()
        self.assertEqual(goal, ltg.pending())

        goal.set_status(Goal.Status.SATISFIED)
        ltg.update()
        self.assertNotEqual(goal, ltg.pending())

    def test_update_instances_resolution_if_not_observed_and_not_pending(self):
        definition = Frame("@TEST.GOAL-DEFINITION.?")
        frame = Frame("@TEST.FRAME.?")
        ov = ObservableValue.build(
            Space("TEST"), ObservableValue.Comparator.EQUALS, 123
        )
        ltg = LTGoal.build(Space("TEST"), frame, "SLOT", ov, definition)

        # To start, there is nothing pending
        self.assertIsNone(ltg.pending())

        # If the status is observed, an update will not make anything pending
        frame["SLOT"] = 123
        ltg.update()
        self.assertIsNone(ltg.pending())

        # If the slot is not observed, but something is already pending, nothing new will be pending
        frame["SLOT"] = []
        goal = Goal(Frame("@TEST.GOAL.?"))
        ltg.set_pending(goal)
        ltg.update()
        self.assertEqual(goal, ltg.pending())

        # If the slot is not observed, and nothing is pending, the resolution will be instanced and pending
        frame["SLOT"] = []
        ltg.anchor["PENDING"] = []
        ltg.update()
        self.assertTrue(ltg.pending().anchor ^ definition)


class EvergreenGoalsTestCase(OntoAgentTestCase):

    def test_lt_goals(self):
        ltg1 = LTGoal.build(
            Space("TEST"),
            Frame("@TEST.FRAME.?"),
            "SLOT",
            ObservableValue.build(
                Space("TEST"), ObservableValue.Comparator.EQUALS, 123
            ),
            Frame("@TEST.GOAL-DEFINITION.?"),
        )

        ltg2 = LTGoal.build(
            Space("TEST"),
            Frame("@TEST.FRAME.?"),
            "SLOT",
            ObservableValue.build(
                Space("TEST"), ObservableValue.Comparator.EQUALS, 123
            ),
            Frame("@TEST.GOAL-DEFINITION.?"),
        )

        eg = Frame("@TEST.EVERGREEN-GOALS.?")
        eg["HAS-GOAL"] = [ltg1, ltg2]

        self.assertIn(ltg1, EvergreenGoals(eg).lt_goals())
        self.assertIn(ltg2, EvergreenGoals(eg).lt_goals())

    def test_add_lt_goal(self):
        ltg1 = LTGoal.build(
            Space("TEST"),
            Frame("@TEST.FRAME.?"),
            "SLOT",
            ObservableValue.build(
                Space("TEST"), ObservableValue.Comparator.EQUALS, 123
            ),
            Frame("@TEST.GOAL-DEFINITION.?"),
        )

        ltg2 = LTGoal.build(
            Space("TEST"),
            Frame("@TEST.FRAME.?"),
            "SLOT",
            ObservableValue.build(
                Space("TEST"), ObservableValue.Comparator.EQUALS, 123
            ),
            Frame("@TEST.GOAL-DEFINITION.?"),
        )

        eg = Frame("@TEST.EVERGREEN-GOALS.?")
        self.assertEqual([], eg["HAS-GOAL"])

        EvergreenGoals(eg).add_lt_goal(ltg1)
        self.assertEqual(ltg1, eg["HAS-GOAL"])
        self.assertNotEqual(ltg2, eg["HAS-GOAL"])

        EvergreenGoals(eg).add_lt_goal(ltg2)
        self.assertEqual(ltg1, eg["HAS-GOAL"])
        self.assertEqual(ltg2, eg["HAS-GOAL"])

    def test_update(self):
        ltg1 = LTGoal.build(
            Space("TEST"),
            Frame("@TEST.FRAME.?"),
            "SLOT",
            ObservableValue.build(
                Space("TEST"), ObservableValue.Comparator.EQUALS, 123
            ),
            Frame("@TEST.GOAL-DEFINITION.?"),
        )

        ltg2 = LTGoal.build(
            Space("TEST"),
            Frame("@TEST.FRAME.?"),
            "SLOT",
            ObservableValue.build(
                Space("TEST"), ObservableValue.Comparator.EQUALS, 123
            ),
            Frame("@TEST.GOAL-DEFINITION.?"),
        )

        self.assertIsNone(ltg1.pending())
        self.assertIsNone(ltg2.pending())

        eg = EvergreenGoals.build(Space("TEST"), lt_goals=[ltg1, ltg2])
        eg.update()

        self.assertIsNotNone(ltg1.pending())
        self.assertIsNotNone(ltg2.pending())

    def test_pending_resolutions(self):
        ltg1 = LTGoal.build(
            Space("TEST"),
            Frame("@TEST.FRAME.?"),
            "SLOT",
            ObservableValue.build(
                Space("TEST"), ObservableValue.Comparator.EQUALS, 123
            ),
            Frame("@TEST.GOAL-DEFINITION.?"),
        )

        ltg2 = LTGoal.build(
            Space("TEST"),
            Frame("@TEST.FRAME.?"),
            "SLOT",
            ObservableValue.build(
                Space("TEST"), ObservableValue.Comparator.EQUALS, 123
            ),
            Frame("@TEST.GOAL-DEFINITION.?"),
        )

        eg = EvergreenGoals.build(Space("TEST"), lt_goals=[ltg1, ltg2])
        eg.update()

        pending = eg.pending_resolutions()
        self.assertIn(ltg1.pending(), pending)
        self.assertIn(ltg2.pending(), pending)
