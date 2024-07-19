from ontoagent.agent import Agent
from ontoagent.engine.effector import Effector
from ontoagent.engine.executable import HandleExecutable
from ontoagent.engine.operation import Operable, Operation
from ontoagent.engine.signal import Signal, XMR
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase, TestableExecutable
from unittest.mock import MagicMock, patch


class AgentTestCase(OntoAgentTestCase):

    def test_effectors(self):
        self.assertEqual([], self.agent.effectors())

        e1 = Effector.build()
        e2 = Effector.build()

        self.agent.anchor["HAS-EFFECTOR"] += e1.anchor
        self.agent.anchor["HAS-EFFECTOR"] += e2.anchor

        self.assertEqual([e1, e2], self.agent.effectors())

    def test_add_effector(self):
        self.assertEqual([], self.agent.anchor["HAS-EFFECTOR"])

        e1 = Effector.build()
        e2 = Effector.build()

        self.agent.add_effector(e1)
        self.agent.add_effector(e2)

        self.assertEqual([e1.anchor, e2.anchor], self.agent.anchor["HAS-EFFECTOR"])

    def test_add_response(self):
        event = Frame("@ONT.EVENT")
        self.assertEqual([], Operable(event).operations())

        self.agent.add_response(event, TestableExecutable)
        self.assertEqual(1, len(Operable(event).operations()))
        self.assertIsInstance(
            Operable(event).operations()[0].executable(), TestableExecutable
        )

    def test_add_response_with_effector(self):
        event = Frame("@ONT.EVENT")
        effector = Effector.build()

        self.assertEqual([], Operable(event).operations())

        self.agent.add_response(event, TestableExecutable, with_effector=effector)
        self.assertEqual(1, len(Operable(event).operations()))
        self.assertIsInstance(
            Operable(event).operations()[0].executable(), TestableExecutable
        )
        self.assertEqual(effector, Operable(event).operations()[0].requires_effector())

    def test_set_response(self):
        event = Frame("@ONT.EVENT")
        self.assertEqual([], Operable(event).operations())

        self.agent.add_response(event, TestableExecutable)
        self.assertEqual(1, len(Operable(event).operations()))
        self.assertIsInstance(
            Operable(event).operations()[0].executable(), TestableExecutable
        )

        self.agent.add_response(event, TestableExecutable)
        self.assertEqual(2, len(Operable(event).operations()))
        self.assertIsInstance(
            Operable(event).operations()[0].executable(), TestableExecutable
        )
        self.assertIsInstance(
            Operable(event).operations()[1].executable(), TestableExecutable
        )

        self.agent.set_response(event, TestableExecutable)
        self.assertEqual(1, len(Operable(event).operations()))
        self.assertIsInstance(
            Operable(event).operations()[0].executable(), TestableExecutable
        )

    @patch("ontoagent.agent.Agent.load_knowledge")
    def test_load_knowledge(self, mock_load_knowledge: MagicMock):
        self.agent.load_knowledge("test.package", "test.file")
        mock_load_knowledge.assert_called_once_with("test.package", "test.file")

    @patch("ontoagent.utils.analysis.Analyzer.analyzer_for_signal")
    def test_input_not_analyzed(self, mock_analyzer_for_signal: MagicMock):
        xmr = XMR.build(Frame("@ONT.ROOT"))

        mock_analyzer = MagicMock()
        mock_analyzer.to_signal = MagicMock()
        mock_analyzer.to_signal.return_value = xmr

        mock_analyzer_for_signal.return_value = mock_analyzer

        signal = Signal.build(Frame("@ONT.ROOT"))
        self.agent.handle = MagicMock()

        self.agent.input(signal, join=True)
        self.agent.handle.assert_called_once_with(xmr, join=True)

    @patch("ontoagent.utils.analysis.Analyzer.analyzer_for_signal")
    def test_input_analzyed(self, mock_analyzer_for_signal: MagicMock):
        xmr = XMR.build(Frame("@ONT.ROOT"))
        self.agent.handle = MagicMock()

        self.agent.input(xmr, join=True)
        self.agent.handle.assert_called_once_with(xmr, join=True)
        mock_analyzer_for_signal.assert_not_called()

    def test_handle(self):
        op1 = Operation.build("SYS", TestableExecutable1)
        op2 = Operation.build("SYS", TestableExecutable2)

        root = Frame("@ONT.ROOT")
        Operable(root).add_operation(op1)
        Operable(root).add_operation(op2)

        signal = Signal.build(root)

        self.agent.handle(signal, join=True)

        # Asserts that both executables (aka, both operations) were run
        self.assertEqual(1, Frame("@TEST.RESPONSE.1")["VALUE"])
        self.assertEqual(2, Frame("@TEST.RESPONSE.2")["VALUE"])

    def test_output(self):
        effector = Effector.build(
            Frame("@TEST.EFFECTOR.?"), executable=TestableExecutable
        )
        effector.interrupt = MagicMock()
        effector.run = MagicMock()

        xmr = XMR.build(Frame("@IO.TEST-EVENT.?"))
        self.agent.output(xmr, effector, join=True)

        effector.interrupt.assert_called_once()
        effector.run.assert_called_once_with(self.agent, xmr)


class TestableExecutable1(HandleExecutable):
    def run(self, agent: Agent, signal: Signal):
        Frame("@TEST.RESPONSE.1")["VALUE"] = 1


class TestableExecutable2(HandleExecutable):
    def run(self, agent: Agent, signal: Signal):
        Frame("@TEST.RESPONSE.2")["VALUE"] = 2
