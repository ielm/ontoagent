from ontoagent.engine.signal import XMR
from ontoagent.views.agenda import (
    Agenda,
    Goal,
    Impasse,
    ImpasseDetectionExecutable,
    Option,
    Plan,
    Resolution,
    Step,
)
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase


class AgendaTestCase(OntoAgentTestCase):

    def test_goals(self):
        a = Frame("@TEST.AGENDA.?")
        g1 = Frame("@TEST.GOAL.?")
        g2 = Frame("@TEST.GOAL.?")

        a["HAS-GOAL"] += g1
        a["HAS-GOAL"] += g2

        self.assertEqual([Goal(g1), Goal(g2)], Agenda(a).goals())

    def test_add_goal(self):
        a = Frame("@TEST.AGENDA.?")
        g1 = Frame("@TEST.GOAL.?")
        g2 = Frame("@TEST.GOAL.?")

        Agenda(a).add_goal(g1)
        Agenda(a).add_goal(Goal(g2))

        self.assertEqual([g1, g2], a["HAS-GOAL"])

    def test_options(self):
        a = Frame("@TEST.AGENDA.?")
        o1 = Frame("@TEST.OPTION.?")
        o2 = Frame("@TEST.OPTION.?")

        a["HAS-OPTION"] = [o1, o2]

        self.assertEqual([o1, o2], Agenda(a).options())

    def test_options_shows_current_options(self):
        a = Frame("@TEST.AGENDA.?")
        o1 = Frame("@TEST.OPTION.?")
        o2 = Frame("@TEST.OPTION.?")

        Option(o2).set_status(Option.Status.EXPIRED)

        a["HAS-OPTION"] = [o1, o2]

        self.assertEqual([o1], Agenda(a).options())

    def test_add_option(self):
        a = Frame("@TEST.AGENDA.?")
        o1 = Frame("@TEST.OPTION.?")
        o2 = Frame("@TEST.OPTION.?")

        Agenda(a).add_option(o1)
        Agenda(a).add_option(o2)

        self.assertEqual([o1, o2], a["HAS-OPTION"])


class GoalTestCase(OntoAgentTestCase):

    def test_plans(self):
        g = Frame("@TEST.GOAL.?")
        p1 = Frame("@TEST.PLAN.?")
        p2 = Frame("@TEST.PLAN.?")

        g["HAS-PLAN"] += p1
        g["HAS-PLAN"] += p2

        self.assertEqual([Plan(p1), Plan(p2)], Goal(g).plans())

    def test_add_plan(self):
        g = Frame("@TEST.GOAL.?")
        p1 = Frame("@TEST.PLAN.?")
        p2 = Frame("@TEST.PLAN.?")

        Goal(g).add_plan(p1)
        Goal(g).add_plan(Plan(p2))

        self.assertEqual([p1, p2], g["HAS-PLAN"])

    def test_priority(self):
        g = Frame("@TEST.GOAL.?")
        g["PRIORITY"] = 0.75
        self.assertEqual(0.75, Goal(g).priority())

    def test_default_priority(self):
        g = Frame("@TEST.GOAL.?")
        self.assertEqual(0.5, Goal(g).priority())

    def test_set_priority(self):
        g = Frame("@TEST.GOAL.?")
        self.assertEqual([], g["PRIORITY"])
        Goal(g).set_priority(0.75)
        self.assertEqual(0.75, g["PRIORITY"])

    def test_status(self):
        g = Frame("@TEST.GOAL.?")
        g["STATUS"] = Goal.Status.SATISFIED
        self.assertEqual(Goal.Status.SATISFIED, Goal(g).status())

    def test_default_status(self):
        g = Frame("@TEST.GOAL.?")
        self.assertEqual(Goal.Status.ACTIVE, Goal(g).status())

    def test_set_status(self):
        g = Frame("@TEST.GOAL.?")
        self.assertEqual([], g["STATUS"])
        Goal(g).set_status(Goal.Status.SATISFIED)
        self.assertEqual(Goal.Status.SATISFIED, g["STATUS"])


class PlanTestCase(OntoAgentTestCase):

    def test_steps(self):
        p = Frame("@TEST.PLAN.?")
        s1 = Frame("@TEST.STEP.?")
        s2 = Frame("@TEST.STEP.?")

        p["HAS-STEP"] += s1
        p["HAS-STEP"] += s2

        self.assertEqual([Step(s1), Step(s2)], Plan(p).steps())

    def test_add_step(self):
        p = Frame("@TEST.PLAN.?")
        s1 = Frame("@TEST.STEP.?")
        s2 = Frame("@TEST.STEP.?")

        Plan(p).add_step(s1)
        Plan(p).add_step(Step(s2))

        self.assertEqual([s1, s2], p["HAS-STEP"])

    def test_cost(self):
        p = Frame("@TEST.PLAN.?")
        p["COST"] = 0.75
        self.assertEqual(0.75, Plan(p).cost())

    def test_default_cost(self):
        p = Frame("@TEST.PLAN.?")
        self.assertEqual(0.5, Plan(p).cost())

    def test_set_cost(self):
        p = Frame("@TEST.PLAN.?")
        self.assertEqual([], p["COST"])
        Plan(p).set_cost(0.75)
        self.assertEqual(0.75, p["COST"])

    def test_status(self):
        p = Frame("@TEST.PLAN.?")
        p["STATUS"] = Plan.Status.FINISHED
        self.assertEqual(Plan.Status.FINISHED, Plan(p).status())

    def test_default_status(self):
        p = Frame("@TEST.PLAN.?")
        self.assertEqual(Plan.Status.PENDING, Plan(p).status())

    def test_set_status(self):
        p = Frame("@TEST.PLAN.?")
        self.assertEqual([], p["STATUS"])
        Plan(p).set_status(Plan.Status.FINISHED)
        self.assertEqual(Plan.Status.FINISHED, p["STATUS"])


class StepTestCase(OntoAgentTestCase):

    def test_status(self):
        s = Frame("@TEST.STEP.?")
        s["STEP-STATUS"] = Step.Status.IMPASSED
        self.assertEqual(Step.Status.IMPASSED, Step(s).status())

    def test_default_status(self):
        s = Frame("@TEST.STEP.?")
        self.assertEqual(Step.Status.PLANNED, Step(s).status())

    def test_set_status(self):
        s = Frame("@TEST.STEP.?")
        self.assertEqual([], s["STEP-STATUS"])
        Step(s).set_status(Step.Status.IMPASSED)
        self.assertEqual(Step.Status.IMPASSED, s["STEP-STATUS"])

    def test_impasses(self):
        s = Frame("@TEST.STEP.?")
        i1 = Frame("@SYS.IMPASSE.?")
        i2 = Frame("@SYS.IMPASSE.?")

        s["HAS-IMPASSE"] = [i1, i2]
        self.assertEqual([i1, i2], Step(s).impasses())
        self.assertIsInstance(Step(s).impasses()[0], Impasse)

    def test_add_impasse(self):
        s = Frame("@TEST.STEP.?")
        i1 = Frame("@SYS.IMPASSE.?")
        i2 = Frame("@SYS.IMPASSE.?")

        self.assertEqual([], s["HAS-IMPASSE"])

        Step(s).add_impasse(i1)
        Step(s).add_impasse(i2)

        self.assertEqual([i1, i2], s["HAS-IMPASSE"])

    def test_subgoals(self):
        s = Frame("@TEST.STEP.?")
        g1 = Frame("@TEST.GOAL.?")
        g2 = Frame("@TEST.GOAL.?")

        s["HAS-SUBGOAL"] += g1
        s["HAS-SUBGOAL"] += g2

        self.assertEqual([g1, g2], Step(s).subgoals())
        self.assertIsInstance(Step(s).subgoals()[0], Goal)

    def test_add_subgoal(self):
        s = Frame("@TEST.STEP.?")
        g1 = Frame("@TEST.GOAL.?")
        g2 = Frame("@TEST.GOAL.?")

        self.assertEqual([], s["HAS-SUBGOAL"])

        Step(s).add_subgoal(g1)
        Step(s).add_subgoal(Goal(g2))

        self.assertEqual([g1, g2], s["HAS-SUBGOAL"])

    def test_xmr(self):
        s = Frame("@TEST.STEP.?")
        xmr = Frame("@IO.XMR.?")

        s["GENERATED-XMR"] = xmr
        self.assertEqual(xmr, Step(s).xmr())
        self.assertIsInstance(Step(s).xmr(), XMR)

    def test_default_xmr(self):
        s = Frame("@TEST.STEP.?")
        self.assertIsNone(Step(s).xmr())

    def test_set_xmr(self):
        s = Frame("@TEST.STEP.?")
        xmr = Frame("@IO.XMR.?")

        self.assertEqual([], s["GENERATED-XMR"])

        Step(s).set_xmr(xmr)

        self.assertEqual(xmr, s["GENERATED-XMR"])


class OptionTestCase(OntoAgentTestCase):

    def test_goal(self):
        o = Frame("@TEST.OPTION.?")
        g = Frame("@TEST.GOAL.?")

        o["GOAL"] = g

        self.assertEqual(g, Option(o).goal())
        self.assertIsInstance(Option(o).goal(), Goal)

    def test_set_goal(self):
        o = Frame("@TEST.OPTION.?")
        g = Frame("@TEST.GOAL.?")

        self.assertEqual([], o["GOAL"])
        Option(o).set_goal(g)
        self.assertEqual(g, o["GOAL"])

    def test_plan(self):
        o = Frame("@TEST.OPTION.?")
        p = Frame("@TEST.PLAN.?")

        o["PLAN"] = p

        self.assertEqual(p, Option(o).plan())
        self.assertIsInstance(Option(o).plan(), Plan)

    def test_set_plan(self):
        o = Frame("@TEST.OPTION.?")
        p = Frame("@TEST.PLAN.?")

        self.assertEqual([], o["PLAN"])
        Option(o).set_plan(p)
        self.assertEqual(p, o["PLAN"])

    def test_step(self):
        o = Frame("@TEST.OPTION.?")
        s = Frame("@TEST.STEP.?")

        o["STEP"] = s

        self.assertEqual(s, Option(o).step())
        self.assertIsInstance(Option(o).step(), Step)

    def test_set_step(self):
        o = Frame("@TEST.OPTION.?")
        s = Frame("@TEST.STEP.?")

        self.assertEqual([], o["STEP"])
        Option(o).set_step(s)
        self.assertEqual(s, o["STEP"])

    def test_timestamp(self):
        o = Frame("@TEST.OPTION.?")
        o["TIMESTAMP"] = 1234

        self.assertEqual(1234, Option(o).timestamp())

    def test_set_timestamp(self):
        o = Frame("@TEST.OPTION.?")

        self.assertEqual([], o["TIMESTAMP"])
        Option(o).set_timestamp(1234)
        self.assertEqual(1234, o["TIMESTAMP"])

    def test_status(self):
        o = Frame("@TEST.OPTION.?")
        o["STATUS"] = Option.Status.CURRENT

        self.assertEqual(Option.Status.CURRENT, Option(o).status())

    def test_default_status(self):
        o = Frame("@TEST.OPTION.?")

        self.assertEqual(Option.Status.CURRENT, Option(o).status())

    def test_set_status(self):
        o = Frame("@TEST.OPTION.?")

        self.assertEqual([], o["STATUS"])
        Option(o).set_status(Option.Status.CURRENT)
        self.assertEqual(Option.Status.CURRENT, o["STATUS"])

    def test_selected(self):
        o = Frame("@TEST.OPTION.?")
        o["SELECTED"] = True

        self.assertEqual(True, Option(o).selected())

    def test_default_selected(self):
        o = Frame("@TEST.OPTION.?")

        self.assertEqual(False, Option(o).selected())

    def test_set_selected(self):
        o = Frame("@TEST.OPTION.?")

        self.assertEqual([], o["SELECTED"])
        Option(o).set_selected(True)
        self.assertEqual(True, o["SELECTED"])

    def test_score(self):
        o = Frame("@TEST.OPTION.?")
        o["SCORE"] = 0.75

        self.assertEqual(0.75, Option(o).score())

    def test_default_score(self):
        o = Frame("@TEST.OPTION.?")

        self.assertEqual(0.0, Option(o).score())

    def test_set_score(self):
        o = Frame("@TEST.OPTION.?")

        self.assertEqual([], o["SCORE"])
        Option(o).set_score(0.75)
        self.assertEqual(0.75, o["SCORE"])


class ImpasseTestCase(OntoAgentTestCase):

    def test_detect(self):
        i = Frame("@SYS.IMPASSE.?")
        i["DETECT"] = TestableImpasseDetectionExecutable

        self.assertEqual(TestableImpasseDetectionExecutable, Impasse(i).detect())

    def test_set_detect(self):
        i = Frame("@SYS.IMPASSE.?")
        self.assertEqual([], i["DETECT"])

        Impasse(i).set_detect(TestableImpasseDetectionExecutable)
        self.assertEqual(TestableImpasseDetectionExecutable, i["DETECT"])

    def test_resolutions(self):
        i = Frame("@SYS.IMPASSE.?")
        r1 = Frame("@SYS.RESOLUTION.?")
        r2 = Frame("@SYS.RESOLUTION.?")

        i["HAS-RESOLUTION"] = [r1, r2]

        self.assertEqual([r1, r2], Impasse(i).resolutions())
        self.assertIsInstance(Impasse(i).resolutions()[0], Resolution)

    def test_add_resolution(self):
        i = Frame("@SYS.IMPASSE.?")
        r1 = Frame("@SYS.RESOLUTION.?")
        r2 = Frame("@SYS.RESOLUTION.?")

        self.assertEqual([], i["HAS-RESOLUTION"])

        Impasse(i).add_resolution(r1)
        Impasse(i).add_resolution(Resolution(r2))

        self.assertEqual([r1, r2], i["HAS-RESOLUTION"])


class ResolutionTestCase(OntoAgentTestCase):

    def test_goal(self):
        r = Frame("@SYS.RESOLUTION.?")
        g = Frame("@GOALS.GOAL.?")

        r["HAS-GOAL"] += g
        self.assertEqual(g, Resolution(r).goal())
        self.assertIsInstance(Resolution(r).goal(), Goal)

    def test_set_goal(self):
        r = Frame("@SYS.RESOLUTION.?")
        g = Frame("@GOALS.GOAL.?")

        self.assertEqual([], r["HAS-GOAL"])

        Resolution(r).set_goal(g)

        self.assertEqual(g, r["HAS-GOAL"])


class TestableImpasseDetectionExecutable(ImpasseDetectionExecutable):

    def detect(self) -> bool:
        return self.step.anchor["TEST"].singleton()
