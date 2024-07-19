from enum import Enum
from ontoagent.engine.report import Report
from ontoagent.engine.signal import Signal
from ontoagent.utils.loader import KnowledgeLoader
from ontoagent.views.agenda import Agenda, Goal, Impasse, Option, Plan, Resolution, Step
from ontograph import graph
from ontograph.Focus import Focus
from ontograph.Frame import Frame
from ontograph.Space import Space
from typing import List

import inspect


class Payload(object):

    @classmethod
    def output_knowledge_resources(cls) -> list:
        return list(
            map(
                lambda k: {
                    "package": k[0],
                    "file": k[1],
                    "loaded": k[0] + "." + k[1] in KnowledgeLoader.loaded,
                },
                KnowledgeLoader.list_all_resources(),
            )
        )

    @classmethod
    def output_agenda(cls, agenda: Agenda) -> dict:
        return {
            "goals": list(map(lambda goal: Payload.output_goal(goal), agenda.goals())),
            "options": list(
                map(lambda option: Payload.output_option(option), agenda.options())
            ),
        }

    @classmethod
    def output_goal(cls, goal: Goal) -> dict:
        return {
            "anchor": goal.anchor.id,
            "status": goal.status().name,
            "priority": goal.priority(),
            "plans": list(map(lambda plan: Payload.output_plan(plan), goal.plans())),
        }

    @classmethod
    def output_plan(cls, plan: Plan) -> dict:
        return {
            "anchor": plan.anchor.id,
            "status": plan.status().name,
            "cost": plan.cost(),
            "steps": list(map(lambda step: Payload.output_step(step), plan.steps())),
        }

    @classmethod
    def output_step(cls, step: Step) -> dict:
        xmr = step.xmr()
        effector = step.with_effector()

        return {
            "anchor": step.anchor.id,
            "status": step.status().name,
            "impasses": list(map(lambda impasse: impasse.anchor.id, step.impasses())),
            "subgoals": list(map(lambda subgoal: subgoal.anchor.id, step.subgoals())),
            "xmr": None if xmr is None else xmr.anchor.id,
            "effector": None if effector is None else effector.anchor.id,
        }

    @classmethod
    def output_impasse(cls, impasse: Impasse) -> dict:
        return {
            "anchor": impasse.anchor.id,
            "detect-module": impasse.detect().__module__,
            "detect-class": impasse.detect().__name__,
            "source": inspect.getsource(impasse.detect()),
            "resolutions": list(
                map(
                    lambda resolution: Payload.output_resolution(resolution),
                    impasse.resolutions(),
                )
            ),
        }

    @classmethod
    def output_resolution(cls, resolution: Resolution) -> dict:
        return {"anchor": resolution.anchor.id, "goal": resolution.goal().anchor.id}

    @classmethod
    def output_option(cls, option: Option) -> dict:
        return {
            "anchor": option.anchor.id,
            "goal": option.goal().anchor.id,
            "plan": option.plan().anchor.id,
            "step": option.step().anchor.id,
            "timestamp": option.timestamp(),
            "status": option.status().name,
            "selected": option.selected(),
            "score": option.score(),
        }

    @classmethod
    def output_report(cls, report: Report) -> dict:
        return {
            "anchor": report.anchor.id,
            "executable-module": report.executable().__module__,
            "executable-class": report.executable().__name__,
            "status": report.status().name,
            "validation": report.validation(),
            "timestamp": report.timestamp(),
            "contents": Payload.output_frame(report.anchor),
        }

    @classmethod
    def output_signal_anchor(cls, signal: Signal) -> dict:
        return {
            "anchor": signal.anchor.id,
            "status": signal.status().name,
            "timestamp": signal.timestamp(),
            "root": signal.root().id,
            "reports": list(map(lambda report: report.anchor.id, signal.reports())),
        }

    @classmethod
    def output_signal_contents(cls, signal: Signal) -> List[dict]:
        constituents = signal.constituents()

        return list(map(lambda frame: Payload.output_frame(frame), constituents))

    @classmethod
    def output_signals(
        cls, status: Signal.Status = Signal.Status.CONSUMED
    ) -> List[dict]:
        signals = map(lambda frame: Signal(frame), Space("IO"))
        signals = filter(lambda signal: signal.status() == status, signals)
        return list(map(lambda signal: Payload.output_signal_anchor(signal), signals))

    @classmethod
    def output_frame(
        cls, frame: Frame, include_all: bool = False, focus: Focus = None
    ) -> dict:
        if focus is None:
            focus = Focus()

        def _output_filler(filler):
            if isinstance(filler, Frame):
                return filler.id
            if isinstance(filler, type):
                return [filler.__module__, filler.__name__]
            return graph.driver.cast_filler(filler)[0]

        def _output_filler_type(filler, focus: Focus) -> str:
            if isinstance(filler, Frame):
                if focus.dir == Focus.Dir.DIR:
                    return "relation/direct"
                return "relation/inverse"
            if isinstance(filler, str):
                return "attribute/text"
            if isinstance(filler, int) or isinstance(filler, float):
                return "attribute/number"
            if isinstance(filler, bool):
                return "attribute/boolean"
            if isinstance(filler, Enum):
                return "attribute/enum"
            if isinstance(filler, type):
                return "attribute/exec"
            return "attribute/other"

        fillers = []
        for slot in frame.slots(include_all=include_all, focus=focus):
            for facet in slot.facets():
                for filler in facet:
                    fillers.append(
                        {
                            "slot": slot.property,
                            "facet": facet.type,
                            "filler": _output_filler(filler),
                            "type": _output_filler_type(filler, focus),
                        }
                    )

        return {"id": frame.id, "fillers": fillers}
