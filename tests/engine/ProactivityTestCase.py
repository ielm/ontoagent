from ontoagent.agent import Agent
from ontoagent.engine.executable import ProactiveExecutable
from ontoagent.engine.operation import Operation
from ontoagent.engine.proactivity import Proactivity
from ontograph.Frame import Frame
from ontograph.Space import Space
from tests.OntoAgentTestCase import OntoAgentTestCase


class TestableProactiveExecutable(ProactiveExecutable):

    def run(self, agent: Agent):
        Frame("@TEST.TESTABLE.1")["RUN"] += 123


class ProactivityTestCase(OntoAgentTestCase):

    def test_operations(self):
        po1 = Operation.build(Space("TEST"), TestableProactiveExecutable)
        po2 = Operation.build(Space("TEST"), TestableProactiveExecutable)

        p = Frame("@TEST.PROACTIVITY.?")
        p["HAS-OPERATION"] += po1
        p["HAS-OPERATION"] += po2

        self.assertIn(po1, Proactivity(p).operations())
        self.assertIn(po2, Proactivity(p).operations())

    def test_add_operation(self):
        po1 = Operation.build(Space("TEST"), TestableProactiveExecutable)
        po2 = Operation.build(Space("TEST"), TestableProactiveExecutable)

        p = Frame("@TEST.PROACTIVITY.?")
        self.assertEqual([], p["HAS-OPERATION"])

        Proactivity(p).add_operation(po1)
        Proactivity(p).add_operation(po2)

        self.assertIn(po1, p["HAS-OPERATION"])
        self.assertIn(po2, p["HAS-OPERATION"])

    def test_run(self):
        po1 = Operation.build(Space("TEST"), TestableProactiveExecutable)
        po2 = Operation.build(Space("TEST"), TestableProactiveExecutable)

        p = Proactivity.build(Space("TEST"), operations=[po1, po2])
        p.run(self.agent)

        self.assertEqual([123, 123], list(Frame("@TEST.TESTABLE.1")["RUN"]))

    def test_add_executable(self):
        p = Proactivity.build(Space("TEST"))
        self.assertEqual([], p.operations())

        p.add_executable(TestableProactiveExecutable)

        self.assertEqual(1, len(p.operations()))
        self.assertEqual("EXE", p.operations()[0].anchor.space())
        self.assertIsInstance(
            p.operations()[0].executable(), TestableProactiveExecutable
        )
        self.assertIsNone(p.operations()[0].requires_effector())
