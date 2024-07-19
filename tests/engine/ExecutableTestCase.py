from ontoagent.agent import Agent
from ontoagent.engine.effector import Effector
from ontoagent.engine.executable import (
    EffectorExecutable,
    HandleExecutable,
    ProactiveExecutable,
)
from ontoagent.engine.report import Report
from ontoagent.engine.signal import Signal, XMR
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase
from unittest.mock import MagicMock, patch


class HandleExecutableTestCase(OntoAgentTestCase):

    class TestableHandleExecutable(HandleExecutable):
        def validate(self, agent: Agent, signal: Signal):
            return Frame("@TEST.EXECUTABLE")["VALIDATE"].singleton()

    def test_fails_if_no_signal_provided(self):
        e = HandleExecutableTestCase.TestableHandleExecutable()
        e.run = MagicMock()
        report = e._run(self.agent)

        self.assertEqual(Report.Status.FAILED, report.status())
        e.run.assert_not_called()

    def test_run_calls_validate(self):
        s = Signal.build(Frame("@TEST.SIGNAL.?"))
        e = HandleExecutableTestCase.TestableHandleExecutable()
        e.validate = MagicMock()

        e._run(self.agent, signal=s)
        e.validate.assert_called_once_with(self.agent, s)

    def test_run_adds_report_to_signal(self):
        s = Signal(Frame("@TEST.SIGNAL.?"))
        self.assertEqual([], s.reports())

        e1 = HandleExecutableTestCase.TestableHandleExecutable()
        e1._run(self.agent, signal=s)
        self.assertEqual([e1.report], s.reports())

        e2 = HandleExecutableTestCase.TestableHandleExecutable()
        e2._run(self.agent, signal=s)
        self.assertEqual([e1.report, e2.report], s.reports())

    def test_run_updates_report_status(self):
        s = Signal(Frame("@TEST.SIGNAL.?"))
        e = HandleExecutableTestCase.TestableHandleExecutable()
        e._run(self.agent, signal=s)

        self.assertEqual(Report.Status.FINISHED, e.report.status())

    def test_validate_marks_report(self):
        Frame("@TEST.EXECUTABLE")["VALIDATE"] = False

        s = Signal(Frame("@TEST.SIGNAL.?"))
        e = HandleExecutableTestCase.TestableHandleExecutable()
        e._run(self.agent, signal=s)

        self.assertFalse(e.report.validation())

    def test_run_calls_run_if_validated(self):
        Frame("@TEST.EXECUTABLE")["VALIDATE"] = True

        s = Signal(Frame("@TEST.SIGNAL.?"))
        e = HandleExecutableTestCase.TestableHandleExecutable()
        e.run = MagicMock()
        e._run(self.agent, signal=s)

        e.run.assert_called_once()

    def test_run_does_not_call_run_if_not_validated(self):
        Frame("@TEST.EXECUTABLE")["VALIDATE"] = False

        s = Signal(Frame("@TEST.SIGNAL.?"))
        e = HandleExecutableTestCase.TestableHandleExecutable()
        e.run = MagicMock()
        e._run(self.agent, signal=s)

        e.run.assert_not_called()


class ProactiveExecutableTestCase(OntoAgentTestCase):

    class TestableProactiveExecutable(ProactiveExecutable):
        def run(self, agent: "Agent"):
            pass

    def test_calls_run(self):
        e = ProactiveExecutableTestCase.TestableProactiveExecutable()
        e.run = MagicMock()

        e._run(self.agent)
        e.run.assert_called_once()

    def test_run_updates_report_status(self):
        e = ProactiveExecutableTestCase.TestableProactiveExecutable()
        e._run(self.agent)

        self.assertEqual(Report.Status.FINISHED, e.report.status())


class EffectorExecutableTestCase(OntoAgentTestCase):

    class TestableEffectorExecutable(EffectorExecutable):
        def run(self, agent: "Agent", xmr: "XMR", effector: "Effector"):
            pass

    def test_fails_if_no_xmr_provided(self):
        e = EffectorExecutableTestCase.TestableEffectorExecutable()
        e.run = MagicMock()
        report = e._run(self.agent, effector=Effector.build())

        self.assertEqual(Report.Status.FAILED, report.status())
        e.run.assert_not_called()

    def test_fails_if_no_effector_provided(self):
        e = EffectorExecutableTestCase.TestableEffectorExecutable()
        e.run = MagicMock()
        report = e._run(self.agent, xmr=XMR.build(Frame("@TEST.ROOT.?")))

        self.assertEqual(Report.Status.FAILED, report.status())
        e.run.assert_not_called()

    def test_calls_run(self):
        e = EffectorExecutableTestCase.TestableEffectorExecutable()
        e.run = MagicMock()

        e._run(
            self.agent, xmr=XMR.build(Frame("@TEST.ROOT.?")), effector=Effector.build()
        )
        e.run.assert_called_once()

    def test_run_updates_report_status(self):
        e = EffectorExecutableTestCase.TestableEffectorExecutable()
        e._run(
            self.agent, xmr=XMR.build(Frame("@TEST.ROOT.?")), effector=Effector.build()
        )

        self.assertEqual(Report.Status.FINISHED, e.report.status())
