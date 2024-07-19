from ontoagent.engine.effector import Effector
from ontoagent.engine.executable import HandleExecutable, ProactiveExecutable
from ontoagent.engine.signal import Signal, XMR
from ontoagent.utils.instancing import instanceof, Instantiable
from ontoagent.utils.states import does_state_exist
from ontoagent.views.agenda import Goal, Impasse, Option, Plan, Step
from ontograph.Frame import Frame
from typing import Iterable, List
import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ontoagent.agent import Agent


class AddGoalInstanceExecutable(HandleExecutable):

    def run(self, agent: "Agent", signal: Signal):
        goal = self._instance_goal(signal)
        goal = self.flatten(goal)

        for step in self._subgoal_of(signal):
            Step(step).add_subgoal(goal)

        agent.agenda().add_goal(goal)

    def _instance_goal(self, signal: Signal) -> Frame:
        variables = {}
        for var in Instantiable(signal.root()).bindings():
            variables[var.bind_to()] = var.bind_local()

        definition = signal.root()["THEME"].singleton()
        goal = instanceof(definition, "AGENDA", variables=variables)
        return goal

    def _subgoal_of(self, signal: Signal) -> List[Frame]:
        return signal.root()["SUBGOAL-OF"]

    @classmethod
    def flatten(cls, goal_instance: Frame) -> Goal:
        goal = Goal(goal_instance)
        for plan in goal.plans():
            for step in cls._flatten_event(plan.anchor):
                plan.add_step(step)

        return goal

    @classmethod
    def _flatten_event(cls, event: Frame) -> Iterable[Frame]:
        if len(list(event["HAS-EVENT-AS-PART"])) == 0:
            yield event
        else:
            for subevent in event["HAS-EVENT-AS-PART"]:
                for _subevent in cls._flatten_event(subevent):
                    yield _subevent


class ProcessAgendaExecutable(ProactiveExecutable):

    def run(self, agent: "Agent"):
        self.handle_impasses(agent)
        self.generate_options(agent)
        effectors_map = self.select_options(agent)
        self.queue_options(agent, effectors_map)
        self.cleanup(agent)

    def handle_impasses(self, agent: "Agent"):
        agenda = agent.agenda()

        def _build_impasse(step: Step, impasse: Impasse):
            step.set_status(Step.Status.IMPASSED)
            for resolution in impasse.resolutions():
                space = XMR.next_available_space("MMR")

                root = space.frame("@.ADD-GOAL-INSTANCE.?").add_parent(
                    "@ONT.ADD-GOAL-INSTANCE"
                )
                root["THEME"] = resolution.goal().anchor
                root["SUBGOAL-OF"] = step.anchor

                for binding in Instantiable(resolution.anchor).bindings():
                    bind_local = None
                    for varmap in Instantiable(resolution.anchor).varmaps():
                        if varmap.defined() == binding.bind_local():
                            bind_local = varmap.realized()
                    if bind_local is not None:
                        bind_to = binding.bind_to()
                        Instantiable(root).build_binding(
                            binding.range(), bind_local, bind_to
                        )

                xmr = XMR.build(root, space=space)
                agent.handle(xmr)

        for goal in agenda.goals():
            for plan in goal.plans():
                for step in plan.steps():
                    if step.status() == Step.Status.IMPASSED:
                        if (
                            len(
                                list(
                                    filter(
                                        lambda subgoal: subgoal.status()
                                        == Goal.Status.SATISFIED,
                                        step.subgoals(),
                                    )
                                )
                            )
                            > 0
                        ):
                            step.set_status(Step.Status.PLANNED)

                    if step.status() == Step.Status.PLANNED:
                        for impasse in step.impasses():
                            if impasse.detect()(step).detect():
                                _build_impasse(step, impasse)

    def generate_options(self, agent: "Agent"):
        agenda = agent.agenda()

        timestamp = time.time_ns()

        for goal in agenda.goals():
            for plan in goal.plans():
                for step in plan.steps():
                    if step.status() == Step.Status.FINISHED:
                        continue
                    if step.status() == Step.Status.PLANNED:
                        option = Option.build(goal, plan, step, timestamp=timestamp)

                        priority_weight = (
                            1.0
                            if "PRIORITY-WEIGHT" not in agent.anchor
                            else agent.anchor["PRIORITY-WEIGHT"].singleton()
                        )
                        cost_weight = (
                            1.0
                            if "COST-WEIGHT" not in agent.anchor
                            else agent.anchor["COST-WEIGHT"].singleton()
                        )
                        score = (goal.priority() * priority_weight) - (
                            plan.cost() * cost_weight
                        )
                        option.set_score(score)

                        agenda.add_option(option)
                    break

    def select_options(self, agent: "Agent") -> dict:
        effectors_map = {}

        def _select(option: Option):
            option.set_selected(True)
            option.step().set_status(Step.Status.EXECUTING)

        options = sorted(
            agent.agenda().options(), key=lambda o: o.score(), reverse=True
        )
        for option in options:
            if (
                len(list(option.step().anchor["AGENT"])) > 0
                and option.step().anchor["AGENT"] != agent
            ):
                option.step().set_status(Step.Status.DEFERRED)
                continue

            required_effector = None
            if len(option.step().operations()) == 1:
                required_effector = option.step().operations()[0].requires_effector()

            if required_effector is None:
                _select(option)
                continue

            available_effectors = agent.effectors()
            available_effectors = filter(
                lambda effector: effector.status() == Effector.Status.AVAILABLE,
                available_effectors,
            )
            available_effectors = filter(
                lambda effector: effector.anchor ^ required_effector,
                available_effectors,
            )
            available_effectors = list(available_effectors)

            for effector in available_effectors:
                if effector not in effectors_map.values():
                    _select(option)
                    effectors_map[option.anchor] = effector

        return effectors_map

    def queue_options(self, agent: "Agent", effectors_map: dict):
        options = agent.agenda().options()
        options = filter(
            lambda option: option.status() == Option.Status.CURRENT, options
        )
        options = filter(lambda option: option.selected(), options)

        for option in options:
            xmr = XMR.build(option.step().anchor)
            option.step().set_xmr(xmr)

            if option.anchor in effectors_map:
                effector = effectors_map[option.anchor]
                effector.set_status(Effector.Status.RESERVED)
                agent.output(xmr, effector)
                option.step().set_with_effector(effector)
            else:
                agent.handle(xmr)
                option.step().set_with_effector(None)

    def cleanup(self, agent: "Agent"):
        options = agent.agenda().options()
        options = filter(
            lambda option: option.status() == Option.Status.CURRENT, options
        )

        for option in options:
            option.set_status(Option.Status.EXPIRED)

        for goal in agent.agenda().goals():
            for plan in goal.plans():
                for step in plan.steps():
                    if step.status() != Step.Status.FINISHED and does_state_exist(
                        step.anchor
                    ):
                        step.set_status(Step.Status.FINISHED)
                if (
                    len(
                        list(
                            filter(
                                lambda step: step.status() != Step.Status.FINISHED,
                                plan.steps(),
                            )
                        )
                    )
                    == 0
                ):
                    plan.set_status(Plan.Status.FINISHED)
            if (
                len(
                    list(
                        filter(
                            lambda plan: plan.status() == Plan.Status.FINISHED,
                            goal.plans(),
                        )
                    )
                )
                > 0
            ):
                goal.set_status(Goal.Status.SATISFIED)
