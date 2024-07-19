from ontoagent.engine.report import Report

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ontoagent.agent import Agent
    from ontoagent.engine.effector import Effector
    from ontoagent.engine.signal import Signal, XMR


class Executable(object):

    def _run(self, agent: "Agent", **kwargs) -> Report:
        raise NotImplementedError

    def run(self, *args):
        raise NotImplementedError


class HandleExecutable(Executable):

    def _run(self, agent: "Agent", **kwargs) -> Report:
        self.report = Report.build(self.__class__)

        signal: Signal = kwargs["signal"] if "signal" in kwargs else None
        if signal is None:
            self.report.set_status(Report.Status.FAILED)
            self.report.anchor["MESSAGE"] = "No signal provided."
            return self.report

        signal.add_report(self.report)

        try:
            valid = self.validate(agent, signal)
            self.report.set_validation(valid)
            if valid:
                self.run(agent, signal)
        except Exception as e:
            self.report.add_execution_exception(e)

        self.report.set_status(Report.Status.FINISHED)
        return self.report

    def validate(self, agent: "Agent", signal: "Signal") -> bool:
        return True

    def run(self, agent: "Agent", signal: "Signal"):
        raise NotImplementedError


class ProactiveExecutable(Executable):

    def _run(self, agent: "Agent", **kwargs) -> Report:
        self.report = Report.build(self.__class__)
        self.run(agent)
        self.report.set_status(Report.Status.FINISHED)
        return self.report

    def run(self, agent: "Agent"):
        raise NotImplementedError


class EffectorExecutable(Executable):

    def _run(self, agent: "Agent", **kwargs) -> Report:
        self.report = Report.build(self.__class__)

        xmr: XMR = kwargs["xmr"] if "xmr" in kwargs else None
        effector: Effector = kwargs["effector"] if "effector" in kwargs else None

        if xmr is None:
            self.report.set_status(Report.Status.FAILED)
            self.report.anchor["MESSAGE"] = "No XMR provided."
            return self.report

        xmr.add_report(self.report)

        if effector is None:
            self.report.set_status(Report.Status.FAILED)
            self.report.anchor["MESSAGE"] = "No effector provided."
            return self.report

        self.run(agent, xmr, effector)
        self.report.set_status(Report.Status.FINISHED)
        return self.report

    def run(self, agent: "Agent", xmr: "XMR", effector: "Effector"):
        raise NotImplementedError
