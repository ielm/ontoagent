from enum import Enum
from ontoagent.engine.effector import Effector
from ontoagent.engine.operation import Operable
from ontoagent.engine.signal import XMR
from ontoagent.utils.common import AnchoredObject
from ontograph.Focus import Focus
from ontograph.Frame import Frame
from ontograph.Space import Space
from typing import List, Type, Union
import time


class Agenda(AnchoredObject):

    def goals(self) -> List["Goal"]:
        return list(
            map(lambda frame: Goal(frame), self.anchor["HAS-GOAL", Focus.Inh.LOC])
        )

    def add_goal(self, goal: Union[Frame, "Goal"]):
        if isinstance(goal, Goal):
            goal = goal.anchor
        self.anchor["HAS-GOAL"] += goal

    def options(self) -> List["Option"]:
        return list(
            filter(
                lambda option: option.status() == Option.Status.CURRENT,
                map(
                    lambda filler: Option(filler),
                    self.anchor["HAS-OPTION", Focus.Inh.LOC],
                ),
            )
        )

    def add_option(self, option: Union[Frame, "Option"]):
        if isinstance(option, Option):
            option = option.anchor
        self.anchor["HAS-OPTION"] += option


class Goal(AnchoredObject):

    class Status(Enum):
        ACTIVE = "ACTIVE"
        ABANDONED = "ABANDONED"
        SATISFIED = "SATISFIED"

    def plans(self) -> List["Plan"]:
        return list(
            map(lambda frame: Plan(frame), self.anchor["HAS-PLAN", Focus.Inh.LOC])
        )

    def add_plan(self, plan: Union[Frame, "Plan"]):
        if isinstance(plan, Plan):
            plan = plan.anchor
        self.anchor["HAS-PLAN"] += plan

    def priority(self) -> float:
        if "PRIORITY" not in self.anchor:
            return 0.5
        return self.anchor["PRIORITY"].singleton()

    def set_priority(self, priority: float):
        self.anchor["PRIORITY"] += priority

    def status(self) -> Status:
        if "STATUS" not in self.anchor:
            return Goal.Status.ACTIVE
        return self.anchor["STATUS"].singleton()

    def set_status(self, status: Status):
        self.anchor["STATUS"] = status


class Plan(AnchoredObject):

    class Status(Enum):
        PENDING = "PENDING"
        FINISHED = "FINISHED"

    def steps(self) -> List["Step"]:
        return list(
            map(lambda frame: Step(frame), self.anchor["HAS-STEP", Focus.Inh.LOC])
        )

    def add_step(self, step: Union[Frame, "Step"]):
        if isinstance(step, Step):
            step = step.anchor
        self.anchor["HAS-STEP"] += step

    def cost(self) -> float:
        if "COST" not in self.anchor:
            return 0.5
        return self.anchor["COST"].singleton()

    def set_cost(self, cost: float):
        self.anchor["COST"] += cost

    def status(self) -> Status:
        if "STATUS" not in self.anchor:
            return Plan.Status.PENDING
        return self.anchor["STATUS"].singleton()

    def set_status(self, status: Status):
        self.anchor["STATUS"] = status


class Step(Operable):

    class Status(Enum):
        PLANNED = "PLANNED"
        EXECUTING = "EXECUTING"
        IMPASSED = "IMPASSED"
        DEFERRED = "DEFERRED"
        FINISHED = "FINISHED"

    def status(self) -> Status:
        if "STEP-STATUS" in self.anchor:
            return self.anchor["STEP-STATUS"].singleton()
        return Step.Status.PLANNED

    def set_status(self, status: Status):
        self.anchor["STEP-STATUS"] = status

    def impasses(self) -> List["Impasse"]:
        return list(map(lambda filler: Impasse(filler), self.anchor["HAS-IMPASSE"]))

    def add_impasse(self, impasse: Union[Frame, "Impasse"]):
        if isinstance(impasse, Impasse):
            impasse = impasse.anchor
        self.anchor["HAS-IMPASSE"] += impasse

    def subgoals(self) -> List[Goal]:
        return list(map(lambda filler: Goal(filler), self.anchor["HAS-SUBGOAL"]))

    def add_subgoal(self, subgoal: Union[Frame, Goal]):
        if isinstance(subgoal, Goal):
            subgoal = subgoal.anchor
        self.anchor["HAS-SUBGOAL"] += subgoal

    def xmr(self) -> Union[None, XMR]:
        if "GENERATED-XMR" not in self.anchor:
            return None
        return XMR(self.anchor["GENERATED-XMR"].singleton())

    def set_xmr(self, xmr: Union[Frame, XMR]):
        if isinstance(xmr, XMR):
            xmr = xmr.anchor
        self.anchor["GENERATED-XMR"] = xmr

    def with_effector(self) -> Union[None, Effector]:
        if "WITH-EFFECTOR" in self.anchor:
            return Effector(self.anchor["WITH-EFFECTOR"].singleton())
        return None

    def set_with_effector(self, effector: Union[None, Frame, Effector]):
        if isinstance(effector, Effector):
            effector = effector.anchor
        self.anchor["WITH-EFFECTOR"] = effector


class Option(AnchoredObject):

    class Status(Enum):
        CURRENT = "CURRENT"
        EXPIRED = "EXPIRED"

    @classmethod
    def build(
        cls,
        goal: Union[Frame, Goal],
        plan: Union[Frame, Plan],
        step: Union[Frame, Step],
        space: Union[str, Space] = None,
        timestamp: int = None,
        status: "Option.Status" = None,
    ) -> "Option":
        if space is None:
            space = "EXE"
        if isinstance(space, str):
            space = Space(space)
        if timestamp is None:
            timestamp = time.time_ns()
        if status is None:
            status = Option.Status.CURRENT

        option = Option(space.frame("@.OPTION.?"))
        option.set_goal(goal)
        option.set_plan(plan)
        option.set_step(step)
        option.set_timestamp(timestamp)
        option.set_status(status)

        return option

    def goal(self) -> Goal:
        return Goal(self.anchor["GOAL"].singleton())

    def set_goal(self, goal: Union[Frame, Goal]):
        if isinstance(goal, Goal):
            goal = goal.anchor
        self.anchor["GOAL"] = goal

    def plan(self) -> Plan:
        return Plan(self.anchor["PLAN"].singleton())

    def set_plan(self, plan: Union[Frame, Plan]):
        if isinstance(plan, Plan):
            plan = plan.anchor
        self.anchor["PLAN"] = plan

    def step(self) -> Step:
        return Step(self.anchor["STEP"].singleton())

    def set_step(self, step: Union[Frame, Step]):
        if isinstance(step, Step):
            step = step.anchor
        self.anchor["STEP"] = step

    def timestamp(self) -> int:
        return self.anchor["TIMESTAMP"].singleton()

    def set_timestamp(self, timestamp: int):
        self.anchor["TIMESTAMP"] = timestamp

    def status(self) -> Status:
        if "STATUS" not in self.anchor:
            return Option.Status.CURRENT
        return self.anchor["STATUS"].singleton()

    def set_status(self, status: Status):
        self.anchor["STATUS"] = status

    def selected(self) -> bool:
        if "SELECTED" not in self.anchor:
            return False
        return self.anchor["SELECTED"].singleton()

    def set_selected(self, selected: bool):
        self.anchor["SELECTED"] = selected

    def score(self) -> float:
        if "SCORE" not in self.anchor:
            return 0.0
        return self.anchor["SCORE"].singleton()

    def set_score(self, score: float):
        self.anchor["SCORE"] = score


class Impasse(AnchoredObject):

    def detect(self) -> Type["ImpasseDetectionExecutable"]:
        return self.anchor["DETECT"].singleton()

    def set_detect(self, detect: Type["ImpasseDetectionExecutable"]):
        self.anchor["DETECT"] = detect

    def resolutions(self) -> List["Resolution"]:
        return list(
            map(lambda filler: Resolution(filler), self.anchor["HAS-RESOLUTION"])
        )

    def add_resolution(self, resolution: Union[Frame, "Resolution"]):
        if isinstance(resolution, Resolution):
            resolution = resolution.anchor
        self.anchor["HAS-RESOLUTION"] += resolution


class Resolution(AnchoredObject):

    def goal(self) -> Goal:
        return Goal(self.anchor["HAS-GOAL"].singleton())

    def set_goal(self, goal: Union[Frame, Goal]):
        if isinstance(goal, Goal):
            goal = goal.anchor
        self.anchor["HAS-GOAL"] = goal


class ImpasseDetectionExecutable(object):

    def __init__(self, step: Step):
        self.step = step

    def detect(self) -> bool:
        raise NotImplementedError
