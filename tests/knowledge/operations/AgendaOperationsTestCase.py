from ontoagent.agent import Agent
from ontoagent.engine.effector import Effector
from ontoagent.engine.executable import EffectorExecutable
from ontoagent.engine.operation import Operable, Operation
from ontoagent.engine.signal import VMR, XMR
from ontoagent.knowledge.operations.agenda import (
    AddGoalInstanceExecutable,
    ProcessAgendaExecutable,
)
from ontoagent.utils.instancing import instanceof, Instantiable, VarMap
from ontoagent.utils.loader import KnowledgeLoader
from ontoagent.utils.states import PhasedEvent
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
from ontograph.Space import Space
from tests.OntoAgentTestCase import (
    OntoAgentTestCase,
    TestableExecutable,
    TestImpasseDetectionExecutable,
)
from unittest.mock import MagicMock, patch


class AddGoalInstanceOperationTestCase(OntoAgentTestCase):

    def test_run_instances_goal(self):
        goal_def = Frame("@GOALS.TEST-GOAL")

        root = instanceof(Frame("@ONT.ADD-GOAL-INSTANCE"), "MMR#1")
        root["THEME"] = goal_def

        mmr = XMR.build(root, anchor="@IO.MMR.?")

        agenda = self.agent.agenda()
        self.assertEqual(0, len(agenda.goals()))

        op = AddGoalInstanceExecutable()
        op.run(self.agent, mmr)

        self.assertEqual(1, len(agenda.goals()))

        goal = agenda.goals()[0]
        self.assertIn(goal_def, goal.anchor.parents())

    def test_run_adds_instance_as_subgoal(self):
        step = Frame("@AGENDA.STEP.?")
        goal_def = Frame("@GOALS.TEST-GOAL")

        root = instanceof(Frame("@ONT.ADD-GOAL-INSTANCE"), "MMR#1")
        root["THEME"] = goal_def
        root["SUBGOAL-OF"] = step

        mmr = XMR.build(root, anchor="@IO.MMR.?")

        self.assertEqual(0, len(Step(step).subgoals()))
        op = AddGoalInstanceExecutable()
        op.run(self.agent, mmr)

        self.assertEqual(1, len(Step(step).subgoals()))
        self.assertEqual(self.agent.agenda().goals()[0], Step(step).subgoals()[0])

    def test_run_assigns_variables(self):
        goal_def = Frame("@GOALS.TEST-GOAL")
        theme = Frame("@ONT.THEME.?")
        goal_def["THEME"] = theme

        value = Frame("@TEST.THEME.?")
        root = instanceof(Frame("@ONT.ADD-GOAL-INSTANCE"), "MMR#1")
        root["THEME"] = goal_def
        Instantiable(root).build_binding(goal_def, value, theme)

        mmr = XMR.build(root, anchor="@IO.MMR.?")

        op = AddGoalInstanceExecutable()
        op.run(self.agent, mmr)

        self.assertEqual(1, len(self.agent.agenda().goals()))
        goal = self.agent.agenda().goals()[0]

        self.assertEqual(value, goal.anchor["THEME"])

    def test_run_calls_flatten(self):
        goal_def = Frame("@GOALS.TEST-GOAL").add_parent(Frame("@ONT.GOAL"))
        root = instanceof(Frame("@ONT.ADD-GOAL-INSTANCE"), "MMR#1")
        root["THEME"] = goal_def
        mmr = XMR.build(root, anchor="@IO.MMR.?")

        op = AddGoalInstanceExecutable()
        op.flatten = MagicMock(side_effect=op.flatten)
        op.run(self.agent, mmr)

        op.flatten.assert_called_once()

    def test_flatten_converts_event_instances_to_plans(self):
        goal_def = Frame("@GOALS.TEST-GOAL").add_parent(Frame("@ONT.GOAL"))
        plan = Frame("@ONT.TEST-PLAN").add_parent(Frame("@ONT.EVENT"))
        step1 = Frame("@ONT.A").add_parent(Frame("@ONT.EVENT"))
        step2 = Frame("@ONT.B").add_parent(Frame("@ONT.EVENT"))
        step3 = Frame("@ONT.C").add_parent(Frame("@ONT.EVENT"))
        step4 = Frame("@ONT.D").add_parent(Frame("@ONT.EVENT"))
        step5 = Frame("@ONT.E").add_parent(Frame("@ONT.EVENT"))

        goal_def["HAS-PLAN"] = plan
        plan["HAS-EVENT-AS-PART"] = [step1, step2]
        step1["HAS-EVENT-AS-PART"] = [step3, step4, step5]

        goal = instanceof(goal_def, "TEST")
        goal = AddGoalInstanceExecutable().flatten(goal)

        self.assertEqual(1, len(goal.plans()))
        plan = goal.plans()[0]

        self.assertEqual(4, len(plan.steps()))
        self.assertTrue(plan.steps()[0].anchor ^ step3)
        self.assertTrue(plan.steps()[1].anchor ^ step4)
        self.assertTrue(plan.steps()[2].anchor ^ step5)
        self.assertTrue(plan.steps()[3].anchor ^ step2)

    def test_flatten_converts_empty_plans_to_single_step_plans(self):
        goal_def = Frame("@GOALS.TEST-GOAL").add_parent(Frame("@ONT.GOAL"))
        plan_def = Frame("@ONT.TEST-PLAN").add_parent(Frame("@ONT.EVENT"))
        goal_def["HAS-PLAN"] = plan_def

        goal = instanceof(goal_def, "TEST")
        goal = AddGoalInstanceExecutable().flatten(goal)

        self.assertEqual(1, len(goal.plans()))
        plan = goal.plans()[0]

        self.assertEqual(1, len(plan.steps()))
        self.assertTrue(plan.steps()[0].anchor ^ plan)
        self.assertEqual(plan, plan.steps()[0])


class ProcessAgendaOperationTestCase(OntoAgentTestCase):

    def setUp(self):
        super().setUp()
        self.signal = XMR.build(Frame("@MMR#1.EVALUATE-AGENDA.?"), space=Space("MMR#1"))

    def test_run(self):
        selected = {"test": True}

        exe = ProcessAgendaExecutable()

        exe.handle_impasses = MagicMock()
        exe.generate_options = MagicMock()
        exe.select_options = MagicMock(return_value=selected)
        exe.queue_options = MagicMock()
        exe.cleanup = MagicMock()

        exe.run(self.agent)

        exe.handle_impasses.assert_called_once()
        exe.generate_options.assert_called_once()
        exe.select_options.assert_called_once()
        exe.queue_options.assert_called_once_with(self.agent, selected)
        exe.cleanup.assert_called_once()

    def test_handle_impasses_marks_steps_as_impassed(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        p1 = Plan(Frame("@AGENDA.PLAN.?"))
        p2 = Plan(Frame("@AGENDA.PLAN.?"))
        p3 = Plan(Frame("@AGENDA.PLAN.?"))
        s1 = Step(Frame("@AGENDA.STEP.?"))
        s2 = Step(Frame("@AGENDA.STEP.?"))
        s3 = Step(Frame("@AGENDA.STEP.?"))
        i1 = Impasse(Frame("@AGENDA.IMPASSE.?"))
        i2 = Impasse(Frame("@AGENDA.IMPASSE.?"))

        agenda.add_goal(goal)
        goal.add_plan(p1)
        goal.add_plan(p2)
        goal.add_plan(p3)
        p1.add_step(s1)
        p2.add_step(s2)
        p3.add_step(s3)
        s1.add_impasse(i1)
        s2.add_impasse(i2)

        s1.anchor["TEST"] = True
        s2.anchor["TEST"] = True

        i1.set_detect(TestImpasseDetectionExecutable)
        i2.set_detect(TestImpasseDetectionExecutable)

        ProcessAgendaExecutable().handle_impasses(self.agent)
        self.assertEqual(Step.Status.IMPASSED, s1.status())
        self.assertEqual(Step.Status.IMPASSED, s2.status())
        self.assertEqual(Step.Status.PLANNED, s3.status())

    def test_handle_impasses_queues_add_goal_instance(self):
        goal_def = Frame("@GOALS.TEST-GOAL-DEFINITION")
        theme = Frame("@ONT.THEME.?")

        value = Frame("@TEST.THEME.?")

        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        plan = Plan(Frame("@AGENDA.PLAN.?"))
        step = Step(Frame("@AGENDA.STEP.?"))
        impasse = Impasse(Frame("@AGENDA.IMPASSE.?").add_parent("@ONT.IMPASSE"))
        resolution = Resolution(
            Frame("@AGENDA.RESOLUTION.?").add_parent("@ONT.RESOLUTION")
        )

        agenda.add_goal(goal)
        goal.add_plan(plan)
        plan.add_step(step)
        step.add_impasse(impasse)

        step.anchor["TEST"] = True

        impasse.set_detect(TestImpasseDetectionExecutable)
        impasse.add_resolution(resolution)

        resolution.set_goal(goal_def)
        roi = Frame("@ONT.FRAME.?")
        Instantiable(resolution.anchor).add_varmap(VarMap.build(roi, value))
        binding = Instantiable(resolution.anchor).build_binding(goal_def, roi, theme)

        self.agent.handle = MagicMock()
        ProcessAgendaExecutable().handle_impasses(self.agent)
        self.agent.handle.assert_called_once()
        signal: XMR = self.agent.handle.call_args[0][0]

        self.assertTrue(signal.root() ^ Frame("@ONT.ADD-GOAL-INSTANCE"))
        self.assertEqual(goal_def, signal.root()["THEME"])
        self.assertEqual(step, signal.root()["SUBGOAL-OF"])

        self.assertEqual(1, len(Instantiable(signal.root()).bindings()))
        self.assertEqual(value, Instantiable(signal.root()).bindings()[0].bind_local())
        self.assertEqual(theme, Instantiable(signal.root()).bindings()[0].bind_to())

    def test_handle_impasses_resets_step_if_any_subgoal_is_satisfied(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        p1 = Plan(Frame("@AGENDA.PLAN.?"))
        p2 = Plan(Frame("@AGENDA.PLAN.?"))
        s1 = Step(Frame("@AGENDA.STEP.?"))
        s2 = Step(Frame("@AGENDA.STEP.?"))

        sg1 = Goal(Frame("@AGENDA.GOAL.?"))
        sg2 = Goal(Frame("@AGENDA.GOAL.?"))

        agenda.add_goal(goal)
        goal.add_plan(p1)
        goal.add_plan(p2)
        p1.add_step(s1)
        p2.add_step(s2)

        s1.set_status(Step.Status.IMPASSED)
        s2.set_status(Step.Status.IMPASSED)

        s1.add_subgoal(sg1)
        s2.add_subgoal(sg2)

        sg1.set_status(Goal.Status.SATISFIED)
        sg2.set_status(Goal.Status.ACTIVE)

        ProcessAgendaExecutable().handle_impasses(self.agent)

        self.assertNotEqual(Step.Status.IMPASSED, s1.status())
        self.assertEqual(Step.Status.IMPASSED, s2.status())

    def test_generate_options(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))

        g1 = Goal(Frame("@AGENDA.GOAL.?"))
        g2 = Goal(Frame("@AGENDA.GOAL.?"))

        p1 = Plan(Frame("@AGENDA.PLAN.?"))
        p2 = Plan(Frame("@AGENDA.PLAN.?"))
        p3 = Plan(Frame("@AGENDA.PLAN.?"))

        s1 = Step(Frame("@AGENDA.STEP.?"))
        s2 = Step(Frame("@AGENDA.STEP.?"))
        s3 = Step(Frame("@AGENDA.STEP.?"))

        agenda.add_goal(g1)
        agenda.add_goal(g2)

        g1.add_plan(p1)
        g1.add_plan(p2)
        g2.add_plan(p3)

        p1.add_step(s1)
        p2.add_step(s2)
        p3.add_step(s3)

        ProcessAgendaExecutable().generate_options(self.agent)

        options = agenda.options()
        self.assertEqual(3, len(options))

        targets = [[g1, p1, s1], [g1, p2, s2], [g2, p3, s3]]
        found = 0
        for target in targets:
            for option in options:
                if (
                    option.goal() == target[0]
                    and option.plan() == target[1]
                    and option.step() == target[2]
                ):
                    found += 1
        self.assertEqual(3, found)

    def test_generate_selects_next_step(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        plan = Plan(Frame("@AGENDA.PLAN.?"))

        s1 = Step(Frame("@AGENDA.STEP.?"))
        s2 = Step(Frame("@AGENDA.STEP.?"))
        s3 = Step(Frame("@AGENDA.STEP.?"))

        agenda.add_goal(goal)
        goal.add_plan(plan)
        plan.add_step(s1)
        plan.add_step(s2)
        plan.add_step(s3)

        s1.set_status(Step.Status.FINISHED)

        ProcessAgendaExecutable().generate_options(self.agent)

        options = agenda.options()
        self.assertEqual(1, len(options))

        self.assertEqual(s2, options[0].step())

    def test_generate_skips_option_if_executing(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        p1 = Plan(Frame("@AGENDA.PLAN.?"))
        p2 = Plan(Frame("@AGENDA.PLAN.?"))
        s1 = Step(Frame("@AGENDA.STEP.?"))
        s2 = Step(Frame("@AGENDA.STEP.?"))

        agenda.add_goal(goal)
        goal.add_plan(p1)
        goal.add_plan(p2)
        p1.add_step(s1)
        p2.add_step(s2)

        s1.set_status(Step.Status.EXECUTING)

        ProcessAgendaExecutable().generate_options(self.agent)

        options = agenda.options()
        self.assertEqual(1, len(options))

        self.assertEqual(p2, options[0].plan())
        self.assertEqual(s2, options[0].step())

    def test_generate_skips_option_if_impassed(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        p1 = Plan(Frame("@AGENDA.PLAN.?"))
        p2 = Plan(Frame("@AGENDA.PLAN.?"))
        s1 = Step(Frame("@AGENDA.STEP.?"))
        s2 = Step(Frame("@AGENDA.STEP.?"))

        agenda.add_goal(goal)
        goal.add_plan(p1)
        goal.add_plan(p2)
        p1.add_step(s1)
        p2.add_step(s2)

        s1.set_status(Step.Status.IMPASSED)

        ProcessAgendaExecutable().generate_options(self.agent)

        options = agenda.options()
        self.assertEqual(1, len(options))

        self.assertEqual(p2, options[0].plan())
        self.assertEqual(s2, options[0].step())

    def test_generate_calculates_score(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        p1 = Plan(Frame("@AGENDA.PLAN.?"))
        p2 = Plan(Frame("@AGENDA.PLAN.?"))
        s1 = Step(Frame("@AGENDA.STEP.?"))
        s2 = Step(Frame("@AGENDA.STEP.?"))

        agenda.add_goal(goal)
        goal.add_plan(p1)
        goal.add_plan(p2)
        p1.add_step(s1)
        p2.add_step(s2)

        goal.set_priority(0.75)
        p1.set_cost(0.3)
        p2.set_cost(0.1)

        self.agent.anchor["PRIORITY-WEIGHT"] = 0.6
        self.agent.anchor["COST-WEIGHT"] = 0.2

        ProcessAgendaExecutable().generate_options(self.agent)

        options = agenda.options()

        self.assertEqual(2, len(options))
        for option in options:
            if option.plan() == p1:
                self.assertAlmostEqual(0.39, option.score())
            elif option.plan() == p2:
                self.assertAlmostEqual(0.43, option.score())
            else:
                self.fail()

    def test_select_options(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        p1 = Plan(Frame("@AGENDA.PLAN.?"))
        p2 = Plan(Frame("@AGENDA.PLAN.?"))
        s1 = Step(Frame("@AGENDA.STEP.?"))
        s2 = Step(Frame("@AGENDA.STEP.?"))

        agenda.add_goal(goal)
        goal.add_plan(p1)
        goal.add_plan(p2)
        p1.add_step(s1)
        p2.add_step(s2)

        o1 = Option.build(goal, p1, s1)
        o2 = Option.build(goal, p1, s2)

        agenda.add_option(o1)
        agenda.add_option(o2)

        self.assertFalse(o1.selected())
        self.assertFalse(o2.selected())
        self.assertNotEqual(Step.Status.EXECUTING, s1.status())
        self.assertNotEqual(Step.Status.EXECUTING, s2.status())

        ProcessAgendaExecutable().select_options(self.agent)

        self.assertTrue(o1.selected())
        self.assertTrue(o2.selected())
        self.assertEqual(Step.Status.EXECUTING, s1.status())
        self.assertEqual(Step.Status.EXECUTING, s2.status())

    def test_select_options_chooses_effectors(self):
        operation = Operation(Frame("@SYS.OPERATION.?"))
        operation.set_requires_effector(Frame("@ONT.HAND"))
        event = Operable(Frame("@ONT.TEST-EVENT"))
        event.add_operation(operation)

        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        p = Plan(Frame("@AGENDA.PLAN.?"))
        s = Step(Frame("@AGENDA.STEP.?").add_parent("@ONT.TEST-EVENT"))

        e1 = Effector.build(type=Frame("@ONT.SPEAKER"))
        e2 = Effector.build(type=Frame("@ONT.HAND"))

        self.agent.add_effector(e1)
        self.agent.add_effector(e2)

        agenda.add_goal(goal)
        goal.add_plan(p)
        p.add_step(s)

        o = Option.build(goal, p, s)
        agenda.add_option(o)

        effectors_map = ProcessAgendaExecutable().select_options(self.agent)
        self.assertEqual({o.anchor: e2}, effectors_map)

    def test_select_options_prefers_higher_scores(self):
        operation = Operation(Frame("@SYS.OPERATION.?"))
        operation.set_requires_effector(Frame("@ONT.HAND"))
        event = Operable(Frame("@ONT.TEST-EVENT"))
        event.add_operation(operation)

        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        p1 = Plan(Frame("@AGENDA.PLAN.?"))
        p2 = Plan(Frame("@AGENDA.PLAN.?"))
        s1 = Step(Frame("@AGENDA.STEP.?").add_parent("@ONT.TEST-EVENT"))
        s2 = Step(Frame("@AGENDA.STEP.?").add_parent("@ONT.TEST-EVENT"))

        e = Effector.build(type=Frame("@ONT.HAND"))

        self.agent.add_effector(e)

        agenda.add_goal(goal)
        goal.add_plan(p1)
        goal.add_plan(p2)
        p1.add_step(s1)
        p2.add_step(s2)

        p1.set_cost(0.1)
        p2.set_cost(0.9)

        o1 = Option.build(goal, p1, s1)
        o2 = Option.build(goal, p2, s2)
        agenda.add_option(o1)
        agenda.add_option(o2)

        effectors_map = ProcessAgendaExecutable().select_options(self.agent)
        self.assertEqual({o1.anchor: e}, effectors_map)

    def test_select_options_marks_as_deferred_if_agent_is_specified_as_other(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        p1 = Plan(Frame("@AGENDA.PLAN.?"))
        p2 = Plan(Frame("@AGENDA.PLAN.?"))
        p3 = Plan(Frame("@AGENDA.PLAN.?"))
        s1 = Step(Frame("@AGENDA.STEP.?"))
        s2 = Step(Frame("@AGENDA.STEP.?"))
        s3 = Step(Frame("@AGENDA.STEP.?"))

        agenda.add_goal(goal)
        goal.add_plan(p1)
        goal.add_plan(p2)
        goal.add_plan(p3)
        p1.add_step(s1)
        p2.add_step(s2)
        p3.add_step(s3)

        s2.anchor["AGENT"] = self.agent.anchor
        s3.anchor["AGENT"] = Frame("@TEST.HUMAN.?")

        o1 = Option.build(goal, p1, s1)
        o2 = Option.build(goal, p2, s2)
        o3 = Option.build(goal, p3, s3)

        agenda.add_option(o1)
        agenda.add_option(o2)
        agenda.add_option(o3)

        ProcessAgendaExecutable().select_options(self.agent)

        self.assertNotEqual(Step.Status.DEFERRED, s1.status())
        self.assertNotEqual(Step.Status.DEFERRED, s2.status())
        self.assertEqual(Step.Status.DEFERRED, s3.status())

    def test_queue_options(self):
        operation = Operation(Frame("@SYS.OPERATION.?"))
        operation.set_requires_effector(Frame("@ONT.HAND"))
        event = Operable(Frame("@ONT.TEST-EVENT"))
        event.add_operation(operation)

        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        p1 = Plan(Frame("@AGENDA.PLAN.?"))
        p2 = Plan(Frame("@AGENDA.PLAN.?"))
        s1 = Step(Frame("@AGENDA.STEP.?").add_parent("@ONT.TEST-EVENT"))
        s2 = Step(Frame("@AGENDA.STEP.?").add_parent("@ONT.TEST-EVENT"))

        s1.set_status(Step.Status.EXECUTING)
        s1.anchor["THEME"] = 1

        s2.set_status(Step.Status.PLANNED)
        s2.anchor["THEME"] = 2

        o1 = Option.build(goal, p1, s1)
        o1.set_selected(True)
        o2 = Option.build(goal, p2, s2)
        o2.set_selected(False)

        agenda.add_option(o1)
        agenda.add_option(o2)

        self.agent.handle = MagicMock()
        ProcessAgendaExecutable().queue_options(self.agent, {})

        self.agent.handle.assert_called_once()
        signal: XMR = self.agent.handle.call_args[0][0]

        self.assertEqual(s1, signal.root())
        self.assertEqual(1, signal.root()["THEME"])
        self.assertTrue(signal.anchor ^ Frame("@ONT.XMR"))

    def test_queue_options_reserves_effectors(self):
        effector = Frame("@SELF.EFFECTOR.?")
        Effector(effector).set_executable(TestableExecutable)

        operation = Operation(Frame("@SYS.OPERATION.?"))
        operation.set_requires_effector(Frame("@ONT.HAND"))
        event = Operable(Frame("@ONT.TEST-EVENT"))
        event.add_operation(operation)

        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        plan = Plan(Frame("@AGENDA.PLAN.?"))
        step = Step(Frame("@AGENDA.STEP.?").add_parent("@ONT.TEST-EVENT"))

        step.set_status(Step.Status.EXECUTING)
        step.anchor["THEME"] = 1

        option = Option.build(goal, plan, step)
        option.set_selected(True)
        agenda.add_option(option)

        ProcessAgendaExecutable().queue_options(
            self.agent, {option.anchor: Effector(effector)}
        )

        self.assertEqual(Effector.Status.RESERVED, Effector(effector).status())
        self.assertEqual(effector, step.with_effector())

    def test_queue_options_adds_xmr_to_step(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        plan = Plan(Frame("@AGENDA.PLAN.?"))
        step = Step(Frame("@AGENDA.STEP.?").add_parent("@ONT.TEST-EVENT"))

        option = Option.build(goal, plan, step)
        option.set_selected(True)
        agenda.add_option(option)

        ProcessAgendaExecutable().queue_options(self.agent, {})
        xmr = step.xmr()
        self.assertTrue(xmr.root() ^ Frame("@ONT.TEST-EVENT"))

    def test_cleanup_expires_options(self):
        o1 = Option.build(
            Frame("@TEST.GOAL.?"), Frame("@TEST.PLAN.?"), Frame("@TEST.STEP.?")
        )
        o2 = Option.build(
            Frame("@TEST.GOAL.?"), Frame("@TEST.PLAN.?"), Frame("@TEST.STEP.?")
        )
        o3 = Option.build(
            Frame("@TEST.GOAL.?"), Frame("@TEST.PLAN.?"), Frame("@TEST.STEP.?")
        )

        self.agent.agenda().add_option(o1)
        self.agent.agenda().add_option(o2)
        self.agent.agenda().add_option(o3)

        self.assertEqual(Option.Status.CURRENT, o1.status())
        self.assertEqual(Option.Status.CURRENT, o2.status())
        self.assertEqual(Option.Status.CURRENT, o3.status())

        ProcessAgendaExecutable().cleanup(self.agent)

        self.assertEqual(Option.Status.EXPIRED, o1.status())
        self.assertEqual(Option.Status.EXPIRED, o2.status())
        self.assertEqual(Option.Status.EXPIRED, o3.status())

    @patch("ontoagent.knowledge.operations.agenda.does_state_exist")
    def test_cleanup_marks_steps_as_finished_when_the_expected_effect_exists(
        self, mock_does_state_exist: MagicMock
    ):
        mock_does_state_exist.return_value = True

        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        plan = Plan(Frame("@AGENDA.PLAN.?"))
        step = Step(Frame("@AGENDA.STEP.?").add_parent("@ONT.TEST-EVENT"))
        xmr = XMR.build(Frame("@TEST.ROOT.?"))

        agenda.add_goal(goal)
        goal.add_plan(plan)
        plan.add_step(step)

        step.set_status(Step.Status.EXECUTING)
        step.set_xmr(xmr)

        ProcessAgendaExecutable().cleanup(self.agent)

        self.assertEqual(Step.Status.FINISHED, step.status())
        mock_does_state_exist.assert_called_once_with(step.anchor)

    @patch("ontoagent.knowledge.operations.agenda.does_state_exist")
    def test_cleanup_does_not_mark_steps_as_finished_if_the_expected_effect_does_not_exist(
        self, mock_does_state_exist: MagicMock
    ):
        mock_does_state_exist.return_value = False

        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        plan = Plan(Frame("@AGENDA.PLAN.?"))
        step = Step(Frame("@AGENDA.STEP.?").add_parent("@ONT.TEST-EVENT"))
        xmr = XMR.build(Frame("@TEST.ROOT.?"))

        agenda.add_goal(goal)
        goal.add_plan(plan)
        plan.add_step(step)

        step.set_status(Step.Status.EXECUTING)
        step.set_xmr(xmr)

        ProcessAgendaExecutable().cleanup(self.agent)

        self.assertEqual(Step.Status.EXECUTING, step.status())
        mock_does_state_exist.assert_called_once_with(step.anchor)

    def test_cleanup_marks_plans_as_finished(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal = Goal(Frame("@AGENDA.GOAL.?"))
        plan1 = Plan(Frame("@AGENDA.PLAN.?"))
        plan2 = Plan(Frame("@AGENDA.PLAN.?"))
        step1 = Step(Frame("@AGENDA.STEP.?"))
        step2 = Step(Frame("@AGENDA.STEP.?"))
        step3 = Step(Frame("@AGENDA.STEP.?"))
        step4 = Step(Frame("@AGENDA.STEP.?"))

        agenda.add_goal(goal)
        goal.add_plan(plan1)
        goal.add_plan(plan2)
        plan1.add_step(step1)
        plan1.add_step(step2)
        plan2.add_step(step3)
        plan2.add_step(step4)

        step1.set_status(Step.Status.FINISHED)
        step2.set_status(Step.Status.FINISHED)
        step3.set_status(Step.Status.FINISHED)
        step4.set_status(Step.Status.EXECUTING)

        ProcessAgendaExecutable().cleanup(self.agent)

        self.assertEqual(Plan.Status.FINISHED, plan1.status())
        self.assertEqual(Plan.Status.PENDING, plan2.status())

    def test_cleanup_marks_goals_as_satisfied(self):
        agenda = Agenda(Frame("@SELF.AGENDA.1"))
        goal1 = Goal(Frame("@AGENDA.GOAL.?"))
        goal2 = Goal(Frame("@AGENDA.GOAL.?"))
        plan1 = Plan(Frame("@AGENDA.PLAN.?"))
        plan2 = Plan(Frame("@AGENDA.PLAN.?"))
        plan3 = Plan(Frame("@AGENDA.PLAN.?"))
        step = Step(Frame("@AGENDA.STEP.?"))

        agenda.add_goal(goal1)
        agenda.add_goal(goal2)
        goal1.add_plan(plan1)
        goal1.add_plan(plan2)
        goal2.add_plan(plan3)

        plan1.set_status(Plan.Status.FINISHED)
        plan2.set_status(Plan.Status.PENDING)
        plan3.set_status(Plan.Status.PENDING)
        plan3.add_step(step)

        step.set_status(Step.Status.EXECUTING)

        ProcessAgendaExecutable().cleanup(self.agent)

        self.assertEqual(Goal.Status.SATISFIED, goal1.status())
        self.assertEqual(Goal.Status.ACTIVE, goal2.status())


class ThroughputAgendaTestCase(OntoAgentTestCase):

    def setUp(self):
        super().setUp()
        Agent.join = True

    def test_throughput_inline(self):
        # Add some basic knowledge to the agent
        Frame("@ONT.HAND").add_parent("@ONT.PHYSICAL-OBJECT")
        Frame("@ONT.WHEEL").add_parent("@ONT.PHYSICAL-OBJECT")
        Frame("@ONT.SCREWDRIVER").add_parent("@ONT.PHYSICAL-OBJECT")

        # Add two effectors, a HAND, and a WHEEL, to the agent
        hand = Frame("@SELF.EFFECTOR.?").add_parent("@ONT.HAND")
        Effector(hand).set_executable(HoldExecutable)
        wheel = Frame("@SELF.EFFECTOR.?").add_parent("@ONT.WHEEL")
        Effector(wheel).set_executable(MoveExecutable)

        self.agent.add_effector(hand)
        self.agent.add_effector(wheel)

        # Define two goals
        take_object = Frame("@GOALS.TAKE-OBJECT").add_parent("@ONT.GOAL")
        approach_object = Frame("@GOALS.APPROACH-OBJECT").add_parent("@ONT.GOAL")

        ## Take Object; with a single plan, a HOLD event, requiring a HAND
        ## Take Object can be impassed if the target is too far away, in which case
        ## the resolution is to Approach Object
        take_object["HAS-PLAN"] += Frame("@ONT.HOLD")
        take_object_oi = Frame("@ONT.PHYSICAL-OBJECT.?")
        take_object["HAS-VARIABLE"] = take_object_oi

        hold = Frame("@ONT.HOLD").add_parent(Frame("@ONT.PHYSICAL-EVENT"))
        hold_operation = Operation(Frame("@SYS.OPERATION.?"))
        hold_operation.set_executable(HoldExecutable)
        hold_operation.set_requires_effector(hand)
        Operable(hold).add_operation(hold_operation)

        hold_oi = Frame("@ONT.PHYSICAL-OBJECT.?").add_parent("@ONT.PHYSICAL-OBJECT")
        hold["THEME"] = hold_oi

        too_far_away = Frame("@SYS.IMPASSE.?").add_parent("@ONT.IMPASSE")
        Impasse(too_far_away).set_detect(TooFarAwayImpasseDetectionExecutable)

        resolve_too_far_away = Frame("@SYS.RESOLUTION.?").add_parent("@ONT.RESOLUTION")
        Resolution(resolve_too_far_away).set_goal(approach_object)
        Impasse(too_far_away).add_resolution(resolve_too_far_away)

        Step(hold).add_impasse(too_far_away)

        ## Approach Object; with a single plan, a MOVE event, requiring a WHEEL
        ## Approach Object has no defined impasses.
        approach_object["HAS-PLAN"] += Frame("@ONT.MOVE")
        approach_object_oi = Frame("@ONT.PHYSICAL-OBJECT.?")
        approach_object["HAS-VARIABLE"] = approach_object_oi

        move = Frame("@ONT.MOVE").add_parent(Frame("@ONT.PHYSICAL-EVENT"))
        move_operation = Operation(Frame("@SYS.OPERATION.?"))
        move_operation.set_executable(MoveExecutable)
        move_operation.set_requires_effector(wheel)
        Operable(move).add_operation(move_operation)

        move_oi = Frame("@ONT.PHYSICAL-OBJECT.?").add_parent("@ONT.PHYSICAL-OBJECT")
        move["DESTINATION"] = move_oi

        ## Create bindings
        Instantiable(take_object).build_binding(hold, take_object_oi, hold_oi)
        Instantiable(resolve_too_far_away).build_binding(
            approach_object, hold_oi, approach_object_oi
        )
        Instantiable(approach_object).build_binding(move, approach_object_oi, move_oi)

        # Setup the environment - create a screwdriver, and simulate its distance from the agent
        screwdriver = Frame("@ENV.SCREWDRIVER.?").add_parent("@ONT.SCREWDRIVER")
        screwdriver["TEST-DISTANCE-TO-AGENT"] = 10

        # An MMR adds an instance of Take Object to the agenda
        # The queue immediately fires, and the agenda selects the new instance
        # An impasse is detected, causing a subgoal to be created (Approach Object)
        # The agenda fires again, selecting the new instance (ignoring the impassed one for now)
        # The move operation is put on the queue, reserving the effector
        # The system idles, as it waits for more input (the move operation is in process)

        space = XMR.next_available_space("MMR")
        root = instanceof(
            Frame("@ONT.ADD-GOAL-INSTANCE"),
            in_space=space,
            variables={Frame("@ONT.GOAL.1"): Frame("@GOALS.TAKE-OBJECT")},
        )
        Instantiable(root).build_binding(
            Frame("@GOALS.TAKE-OBJECT"), bind_local=screwdriver, bind_to=take_object_oi
        )
        mmr = XMR.build(root, anchor="@IO.MMR.?", space=space)
        self.agent.input(mmr)

        # Proactivity runs
        self.agent.background()

        ## There are two goals on the agenda (one is a subgoal)
        self.assertEqual(2, len(self.agent.agenda().goals()))

        take_goal = self.agent.agenda().goals()[0]
        approach_goal = self.agent.agenda().goals()[1]

        self.assertTrue(take_goal.anchor ^ Frame("@GOALS.TAKE-OBJECT"))
        self.assertTrue(approach_goal.anchor ^ Frame("@GOALS.APPROACH-OBJECT"))
        self.assertEqual(
            [self.agent.agenda().goals()[1]], take_goal.plans()[0].steps()[0].subgoals()
        )
        self.assertEqual(Step.Status.IMPASSED, take_goal.plans()[0].steps()[0].status())

        ## The WHEEL is reserved, waiting on the MOVE event to finish
        self.assertEqual(Effector.Status.RESERVED, Effector(wheel).status())
        self.assertEqual(
            approach_goal.plans()[0].steps()[0].xmr(), Effector(wheel).reserved_to()
        )

        # An RMR returns a message that the motor operation for the WHEEL is complete
        # The agenda is triggered again - the subgoal is satisfied, and the impasse is cleared
        # The hold operation can now begin; the HAND is now reserved
        # The system idles, as it waits for more input (the hold operation is in process)

        space = XMR.next_available_space("RMR")
        root = instanceof(
            Frame("@ONT.RELEASE-EFFECTOR"),
            in_space=space,
            variables={Frame("@ONT.EFFECTOR.1"): wheel},
        )
        mmr = XMR.build(root, anchor="@IO.RMR.?", space=space)
        self.agent.input(mmr)

        # Proactivity runs
        self.agent.background()

        ## The WHEEL is available again
        self.assertEqual(Effector.Status.AVAILABLE, Effector(wheel).status())

        ## The subgoal is now satisfied
        self.assertEqual(Goal.Status.ACTIVE, take_goal.status())
        self.assertEqual(Goal.Status.SATISFIED, approach_goal.status())

        # Proactivity runs
        self.agent.background()

        ## The HAND is reserved, waiting on the HOLD event to finish
        self.assertEqual(
            Step.Status.EXECUTING, take_goal.plans()[0].steps()[0].status()
        )
        self.assertEqual(Effector.Status.RESERVED, Effector(hand).status())
        self.assertEqual(
            take_goal.plans()[0].steps()[0].xmr(), Effector(hand).reserved_to()
        )

        # An RMR returns a message that the motor operation for the HAND is complete
        # The agenda is triggered again - the main goal is now satisfied
        # The system idles, with no active goals on the agenda

        space = XMR.next_available_space("RMR")
        root = instanceof(
            Frame("@ONT.RELEASE-EFFECTOR"),
            in_space=space,
            variables={Frame("@ONT.EFFECTOR.1"): hand},
        )
        mmr = XMR.build(root, anchor="@IO.RMR.?", space=space)
        self.agent.input(mmr)

        # Proactivity runs
        self.agent.background()

        ## The HAND is available again
        self.assertEqual(Effector.Status.AVAILABLE, Effector(hand).status())

        ## The main goal is now satisfied
        self.assertEqual(Goal.Status.SATISFIED, take_goal.status())
        self.assertEqual(Goal.Status.SATISFIED, approach_goal.status())

    def test_throughput_knowledge(self):
        KnowledgeLoader.load_resource(
            "tests.resources", "ThroughputAgendaTestCase.knowledge"
        )

        hand = Frame("@SELF.EFFECTOR.1")
        wheel = Frame("@SELF.EFFECTOR.2")

        # An MMR adds an instance of Take Object to the agenda
        # The queue immediately fires, and the agenda selects the new instance
        # An impasse is detected, causing a subgoal to be created (Approach Object)
        # The agenda fires again, selecting the new instance (ignoring the impassed one for now)
        # The move operation is put on the queue, reserving the effector
        # The system idles, as it waits for more input (the move operation is in process)

        take_object_var = Frame("@ONT.PHYSICAL-OBJECT.1")
        screwdriver = Frame("@ENV.SCREWDRIVER.5")

        space = XMR.next_available_space("MMR")
        root = instanceof(
            Frame("@ONT.ADD-GOAL-INSTANCE"),
            in_space=space,
            variables={Frame("@ONT.GOAL.1"): Frame("@GOALS.TAKE-OBJECT")},
        )
        Instantiable(root).build_binding(
            Frame("@GOALS.TAKE-OBJECT"), bind_local=screwdriver, bind_to=take_object_var
        )
        mmr = XMR.build(root, anchor="@IO.MMR.?", space=space)
        self.agent.input(mmr)

        # Proactivity runs
        self.agent.background()

        ## There are two goals on the agenda (one is a subgoal)
        self.assertEqual(2, len(self.agent.agenda().goals()))

        take_goal = self.agent.agenda().goals()[0]
        approach_goal = self.agent.agenda().goals()[1]

        self.assertTrue(take_goal.anchor ^ Frame("@GOALS.TAKE-OBJECT"))
        self.assertTrue(approach_goal.anchor ^ Frame("@GOALS.APPROACH-OBJECT"))
        self.assertEqual(
            [self.agent.agenda().goals()[1]], take_goal.plans()[0].steps()[0].subgoals()
        )
        self.assertEqual(Step.Status.IMPASSED, take_goal.plans()[0].steps()[0].status())

        ## The WHEEL is reserved, waiting on the MOVE event to finish
        self.assertEqual(Effector.Status.RESERVED, Effector(wheel).status())
        self.assertEqual(
            approach_goal.plans()[0].steps()[0].xmr(), Effector(wheel).reserved_to()
        )

        # An RMR returns a message that the motor operation for the WHEEL is complete
        # The agenda is triggered again - the subgoal is satisfied, and the impasse is cleared
        # The hold operation can now begin; the HAND is now reserved
        # The system idles, as it waits for more input (the hold operation is in process)

        space = XMR.next_available_space("RMR")
        root = instanceof(
            Frame("@ONT.RELEASE-EFFECTOR"),
            in_space=space,
            variables={Frame("@ONT.EFFECTOR.1"): wheel},
        )
        mmr = XMR.build(root, anchor="@IO.RMR.?", space=space)
        self.agent.input(mmr)

        # Proactivity runs
        self.agent.background()

        ## The WHEEL is available again
        self.assertEqual(Effector.Status.AVAILABLE, Effector(wheel).status())

        ## The subgoal is now satisfied
        self.assertEqual(Goal.Status.ACTIVE, take_goal.status())
        self.assertEqual(Goal.Status.SATISFIED, approach_goal.status())

        # Proactivity runs
        self.agent.background()

        ## The HAND is reserved, waiting on the HOLD event to finish
        self.assertEqual(
            Step.Status.EXECUTING, take_goal.plans()[0].steps()[0].status()
        )
        self.assertEqual(Effector.Status.RESERVED, Effector(hand).status())
        self.assertEqual(
            take_goal.plans()[0].steps()[0].xmr(), Effector(hand).reserved_to()
        )

        # An RMR returns a message that the motor operation for the HAND is complete
        # The agenda is triggered again - the main goal is now satisfied
        # The system idles, with no active goals on the agenda

        space = XMR.next_available_space("RMR")
        root = instanceof(
            Frame("@ONT.RELEASE-EFFECTOR"),
            in_space=space,
            variables={Frame("@ONT.EFFECTOR.1"): hand},
        )
        mmr = XMR.build(root, anchor="@IO.RMR.?", space=space)
        self.agent.input(mmr)

        # Proactivity runs
        self.agent.background()

        ## The HAND is available again
        self.assertEqual(Effector.Status.AVAILABLE, Effector(hand).status())

        ## The main goal is now satisfied
        self.assertEqual(Goal.Status.SATISFIED, take_goal.status())
        self.assertEqual(Goal.Status.SATISFIED, approach_goal.status())

    def test_throughput_inline_with_deferred_action(self):
        # Add a human to the enviroment; this human is responsible for the HOLD event
        human = Frame("@ENV.HUMAN.1")

        # Add some basic knowledge to the agent
        Frame("@ONT.HAND").add_parent("@ONT.PHYSICAL-OBJECT")
        # Frame("@ONT.WHEEL").add_parent("@ONT.PHYSICAL-OBJECT")
        Frame("@ONT.SCREWDRIVER").add_parent("@ONT.PHYSICAL-OBJECT")

        # Add an effector (a HAND)
        hand = Frame("@SELF.EFFECTOR.?").add_parent("@ONT.HAND")
        self.agent.add_effector(hand)

        # Define the goal
        take_object = Frame("@GOALS.TAKE-OBJECT").add_parent("@ONT.GOAL")

        ## Take Object; with a single plan, a HOLD event, requiring a HAND
        ## In this plan, the agent of HOLD is not the robot, so the robot must defer to the human
        take_object["HAS-PLAN"] += Frame("@ONT.HOLD")
        take_object_oi = Frame("@ONT.PHYSICAL-OBJECT.?")
        take_object["HAS-VARIABLE"] = take_object_oi

        hold = Frame("@ONT.HOLD").add_parent(Frame("@ONT.PHYSICAL-EVENT"))
        hold_operation = Operation(Frame("@SYS.OPERATION.?"))
        hold_operation.set_executable(HoldExecutable)
        hold_operation.set_requires_effector(hand)
        Operable(hold).add_operation(hold_operation)

        hold_oi = Frame("@ONT.PHYSICAL-OBJECT.?").add_parent("@ONT.PHYSICAL-OBJECT")
        hold["THEME"] = hold_oi
        hold["AGENT"] = human

        ## Create bindings
        Instantiable(take_object).build_binding(hold, take_object_oi, hold_oi)

        # Setup the environment - create a screwdriver
        screwdriver = Frame("@ENV.SCREWDRIVER.?").add_parent("@ONT.SCREWDRIVER")

        # An MMR adds an instance of Take Object to the agenda
        # The queue immediately fires, and the agenda selects the new instance
        # The only step is deferred; the HAND is not used, as the agent is not the robot
        # The system idles, as it waits for more input

        space = XMR.next_available_space("MMR")
        root = instanceof(
            Frame("@ONT.ADD-GOAL-INSTANCE"),
            in_space=space,
            variables={Frame("@ONT.GOAL.1"): Frame("@GOALS.TAKE-OBJECT")},
        )
        Instantiable(root).build_binding(
            Frame("@GOALS.TAKE-OBJECT"), bind_local=screwdriver, bind_to=take_object_oi
        )
        mmr = XMR.build(root, anchor="@IO.MMR.?", space=space)
        self.agent.input(mmr)

        # Proactivity runs
        self.agent.background()

        ## There is one goal on the agenda
        self.assertEqual(1, len(self.agent.agenda().goals()))

        take_goal = self.agent.agenda().goals()[0]

        self.assertTrue(take_goal.anchor ^ Frame("@GOALS.TAKE-OBJECT"))
        self.assertEqual(Step.Status.DEFERRED, take_goal.plans()[0].steps()[0].status())

        ## The HAND is not reserved
        self.assertEqual(Effector.Status.AVAILABLE, Effector(hand).status())

        # A VMR shows that the human has completed the task of holding the screwdriver
        # The agenda is triggered; during cleanup, the deferred step is marked as finished
        # The system idles

        space = XMR.next_available_space("VMR")
        root = instanceof(Frame("@ONT.HOLD"), in_space=space)
        root["THEME"] = screwdriver
        root["AGENT"] = human
        PhasedEvent(root).set_ended()
        vmr = VMR.build([root], anchor="@IO.VMR.?", space=space)
        self.agent.input(vmr)

        # Proactivity runs
        self.agent.background()

        ## The step is completed
        self.assertEqual(Step.Status.FINISHED, take_goal.plans()[0].steps()[0].status())

        ## The goal is now satisfied
        self.assertEqual(Goal.Status.SATISFIED, take_goal.status())


class TooFarAwayImpasseDetectionExecutable(ImpasseDetectionExecutable):
    def detect(self) -> bool:
        return (
            self.step.anchor["THEME"].singleton()["TEST-DISTANCE-TO-AGENT"].singleton()
            >= 5
        )


class HoldExecutable(EffectorExecutable):
    def run(self, agent: "Agent", xmr: "XMR", effector: "Effector"):
        Frame("@SELF.AGENT.1")["FINISHED"] = True


class MoveExecutable(EffectorExecutable):
    def run(self, agent: "Agent", xmr: "XMR", effector: "Effector"):
        xmr.root()["DESTINATION"].singleton()["TEST-DISTANCE-TO-AGENT"] = 1
