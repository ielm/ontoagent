from enum import Enum
from functools import reduce
from ontoagent.knowledge.operations.agenda import AddGoalInstanceExecutable
from ontoagent.utils.common import AnchoredObject
from ontoagent.utils.instancing import instanceof
from ontoagent.views.agenda import Goal
from ontograph.Frame import Frame
from ontograph.Space import Space
from typing import Any, List, Union


class ObservableValue(AnchoredObject):

    class Comparator(Enum):
        EQUALS = "EQUALS"
        GT = "GT"
        GTE = "GTE"
        LT = "LT"
        LTE = "LTE"
        NOT = "NOT"
        AND = "AND"
        OR = "OR"

    @classmethod
    def build(
        cls,
        space: Union[str, Space],
        comparator: Comparator,
        value: Union[Any, List[Any]],
    ) -> "ObservableValue":
        if isinstance(space, str):
            space = Space(space)

        frame = space.frame("@.OBSERVABLE-VALUE.?").add_parent("@ONT.OBSERVABLE-VALUE")
        ov = ObservableValue(frame)
        ov.set_comparator(comparator)
        ov.set_value(value)

        return ov

    def comparator(self) -> Comparator:
        return self.anchor["COMPARATOR"].singleton()

    def set_comparator(self, comparator: Comparator):
        self.anchor["COMPARATOR"] = comparator

    def value(self) -> Any:
        values = list(self.anchor["VALUE"])
        if len(values) == 1:
            return values[0]
        return values

    def set_value(self, value: Union[Any, List[Any]]):
        if not isinstance(value, list):
            value = [value]
        self.anchor["VALUE"] = value

    def is_observed(self, frame: Frame, slot: str) -> bool:
        comparator = self.comparator()
        values = list(self.anchor["VALUE"])
        fillers = list(frame[slot])

        if comparator == ObservableValue.Comparator.AND:
            for value in values:
                if isinstance(value, ObservableValue):
                    if not value.is_observed(frame, slot):
                        return False
                elif not self._is_single_value_observed(
                    ObservableValue.Comparator.EQUALS, value, fillers
                ):
                    return False
            return True
        elif comparator == ObservableValue.Comparator.OR:
            for value in values:
                if isinstance(value, ObservableValue):
                    if value.is_observed(frame, slot):
                        return True
                elif self._is_single_value_observed(
                    ObservableValue.Comparator.EQUALS, value, fillers
                ):
                    return True
            return False
        else:
            if len(values) != 1:
                raise Exception(
                    "Exactly one value must be compared to type %s." % comparator.name
                )
            return self._is_single_value_observed(comparator, values[0], fillers)

    def _is_single_value_observed(
        self, comparator: Comparator, value: Any, fillers: List[Any]
    ) -> bool:
        if comparator == ObservableValue.Comparator.EQUALS:
            return value in fillers

        if comparator == ObservableValue.Comparator.NOT:
            return value not in fillers

        if len(fillers) == 0:
            return False

        numeric = list(
            filter(lambda y: isinstance(y, int) or isinstance(y, float), fillers)
        )
        if len(numeric) > 0:
            if comparator == ObservableValue.Comparator.GT:
                return reduce(lambda a, b: a or b, map(lambda x: x > value, numeric))
            if comparator == ObservableValue.Comparator.GTE:
                return reduce(lambda a, b: a or b, map(lambda x: x >= value, numeric))
            if comparator == ObservableValue.Comparator.LT:
                return reduce(lambda a, b: a or b, map(lambda x: x < value, numeric))
            if comparator == ObservableValue.Comparator.LTE:
                return reduce(lambda a, b: a or b, map(lambda x: x <= value, numeric))

        return False


class LTGoal(AnchoredObject):

    # The BENEFICIARY is the frame that is to be inspected for a certain state
    # The THEME is the slot (name) on the BENEFICIARY that is to be inspected
    # The VALUE is the ObservableValue to be look for in the BENEFICIARY.THEME
    # The RESOLUTION is the definition of a goal to instance if the stat is not found
    # The PENDING is an instance of the RESOLUTION goal that is in action (or None)
    # The STATUS is the current status of the desired state per last update (default to UNSATISFIED)

    class Status(Enum):
        UNSATISFIED = "UNSATISFIED"
        SATISFIED = "SATISFIED"

    @classmethod
    def build(
        cls,
        space: Union[str, Space],
        beneficiary: Frame,
        theme: str,
        value: Union[Frame, ObservableValue],
        resolution: Frame,
        name: str = None,
    ):
        if isinstance(space, str):
            space = Space(space)

        frame = space.frame("@.LT-GOAL.?").add_parent("@ONT.LT-GOAL")
        ltg = LTGoal(frame)
        ltg.set_beneficiary(beneficiary)
        ltg.set_theme(theme)
        ltg.set_value(value)
        ltg.set_resolution(resolution)
        ltg.set_status(LTGoal.Status.UNSATISFIED)

        if name is not None:
            ltg.set_name(name)

        return ltg

    def name(self) -> Union[str, None]:
        if "NAME" in self.anchor:
            return self.anchor["NAME"].singleton()
        return None

    def set_name(self, name: str):
        self.anchor["NAME"] = name

    def status(self) -> Status:
        try:
            return self.anchor["STATUS"].singleton()
        except:
            return LTGoal.Status.UNSATISFIED

    def set_status(self, status: Status):
        self.anchor["STATUS"] = status

    def beneficiary(self) -> Frame:
        return self.anchor["BENEFICIARY"].singleton()

    def set_beneficiary(self, beneficiary: Frame):
        self.anchor["BENEFICIARY"] = beneficiary

    def theme(self) -> str:
        return self.anchor["THEME"].singleton()

    def set_theme(self, theme: str):
        self.anchor["THEME"] = theme

    def value(self) -> ObservableValue:
        return self.anchor["VALUE"].singleton()

    def set_value(self, value: Union[Frame, ObservableValue]):
        if isinstance(value, Frame):
            value = ObservableValue(value)
        self.anchor["VALUE"] = value

    def resolution(self) -> Frame:
        return self.anchor["RESOLUTION"].singleton()

    def set_resolution(self, resolution: Frame):
        self.anchor["RESOLUTION"] = resolution

    def pending(self) -> Union[None, Goal]:
        try:
            return self.anchor["PENDING"].singleton()
        except:
            return None

    def set_pending(self, pending: Union[Frame, Goal]):
        if isinstance(pending, Frame):
            pending = Goal(pending)
        self.anchor["PENDING"] = pending

    def is_observed(self) -> bool:
        return self.value().is_observed(self.beneficiary(), self.theme())

    def update(self):
        # Update the STATUS depending on the state of observation
        if self.is_observed():
            self.set_status(LTGoal.Status.SATISFIED)
        else:
            self.set_status(LTGoal.Status.UNSATISFIED)

        # Remove any pending goals that are complete
        pending = self.pending()
        if pending is not None:
            status = pending.status()
            if status == Goal.Status.SATISFIED or status == Goal.Status.ABANDONED:
                self.anchor["PENDING"] = []

        # If UNSATISFIED and there is nothing pending, then instance the resolution
        if self.status() == LTGoal.Status.UNSATISFIED and self.pending() is None:
            definition = self.resolution()
            goal = instanceof(definition, "AGENDA")
            goal = AddGoalInstanceExecutable.flatten(goal)
            self.set_pending(goal)

            # Note, it is up to the calling entity to assign the pending resolution to the agenda (or otherwise use it)


class EvergreenGoals(AnchoredObject):

    @classmethod
    def build(cls, space: Union[str, Space], lt_goals: List[LTGoal] = None):
        if isinstance(space, str):
            space = Space(space)
        if lt_goals is None:
            lt_goals = []

        frame = space.frame("@.EVERGREEN-GOALS.?").add_parent("@ONT.EVERGREEN-GOALS")
        eg = EvergreenGoals(frame)

        for lt_goal in lt_goals:
            eg.add_lt_goal(lt_goal)

        return eg

    def lt_goals(self) -> List[LTGoal]:
        return list(self.anchor["HAS-GOAL"])

    def add_lt_goal(self, lt_goal: Union[Frame, LTGoal]):
        if isinstance(lt_goal, Frame):
            lt_goal = LTGoal(lt_goal)
        self.anchor["HAS-GOAL"] += lt_goal

    def update(self):
        for lt_goal in self.lt_goals():
            lt_goal.update()

    def pending_resolutions(self) -> List[Goal]:
        return list(
            filter(
                lambda pending: pending is not None,
                map(lambda lt_goal: lt_goal.pending(), self.lt_goals()),
            )
        )
