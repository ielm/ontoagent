from ontoagent.engine.effector import Effector
from ontoagent.engine.signal import XMR
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase, TestableExecutable


class EffectorTestCase(OntoAgentTestCase):

    def test_status(self):
        e = Frame("@TEST.EFFECTOR.?")
        e["STATUS"] = Effector.Status.RESERVED

        self.assertEqual(Effector.Status.RESERVED, Effector(e).status())

    def test_default_status(self):
        e = Frame("@TEST.EFFECTOR.?")

        self.assertEqual(Effector.Status.AVAILABLE, Effector(e).status())

    def test_set_status(self):
        e = Frame("@TEST.EFFECTOR.?")
        self.assertEqual([], e["STATUS"])

        Effector(e).set_status(Effector.Status.RESERVED)
        self.assertEqual(Effector.Status.RESERVED, e["STATUS"])

    def test_reserved_to(self):
        e = Frame("@TEST.EFFECTOR.?")

        xmr = XMR.build(Frame("@TEST.FRAME.?"))
        e["RESERVED-TO"] = xmr

        self.assertEqual(xmr, Effector(e).reserved_to())

    def test_set_reserved_to(self):
        e = Frame("@TEST.EFFECTOR.?")
        self.assertEqual([], e["RESERVED-TO"])

        xmr = XMR.build(Frame("@TEST.FRAME.?"))

        Effector(e).set_reserved_to(xmr)
        self.assertEqual(xmr, e["RESERVED-TO"])

    def test_executable(self):
        e = Frame("@TEST.EFFECTOR.?")
        e["EXECUTABLE"] = TestableExecutable

        self.assertIsInstance(Effector(e).executable(), TestableExecutable)

    def test_set_executable(self):
        e = Frame("@TEST.EFFECTOR.?")
        self.assertEqual([], e["EXECUTABLE"])

        Effector(e).set_executable(TestableExecutable)
        self.assertEqual([TestableExecutable], e["EXECUTABLE"])

    def test_interrupt(self):
        e = Frame("@TEST.EFFECTOR.?")
        e["INTERRUPT"] = TestableExecutable

        self.assertEqual(TestableExecutable, Effector(e).interrupt())

    def test_set_interrupt(self):
        e = Frame("@TEST.EFFECTOR.?")
        self.assertEqual([], e["INTERRUPT"])

        Effector(e).set_interrupt(TestableExecutable)
        self.assertEqual([TestableExecutable], e["INTERRUPT"])
