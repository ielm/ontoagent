from ontoagent.engine.operation import Operable, Operation
from ontoagent.engine.report import Report
from ontoagent.engine.signal import Signal
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase, TestableExecutable
from unittest.mock import MagicMock, patch


class OperableTestCase(OntoAgentTestCase):

    def test_operations(self):
        o = Frame("@TEST.OPERABLE.?")
        op = Frame("@TEST.OPERATION.?")

        o["HAS-OPERATION"] += op

        self.assertEqual([op], Operable(o).operations())

    def test_add_operation(self):
        o = Frame("@TEST.OPERABLE.?")
        op = Frame("@TEST.OPERATION.?")

        self.assertEqual([], o["HAS-OPERATION"])

        Operable(o).add_operation(op)
        self.assertEqual([op], o["HAS-OPERATION"])

    def test_clear_operations(self):
        o = Frame("@TEST.OPERABLE.?")
        op = Frame("@TEST.OPERATION.?")

        o["HAS-OPERATION"] += op
        self.assertEqual([op], Operable(o).operations())

        Operable(o).clear_operations()
        self.assertEqual([], Operable(o).operations())


class OperationTestCase(OntoAgentTestCase):

    def test_executable(self):
        o = Frame("@TEST.OPERATION.?")
        o["EXECUTABLE"] = TestableExecutable

        self.assertIsInstance(Operation(o).executable(), TestableExecutable)

    def test_set_executable(self):
        o = Frame("@TEST.OPERATION.?")
        self.assertEqual([], o["EXECUTABLE"])

        Operation(o).set_executable(TestableExecutable)
        self.assertEqual([TestableExecutable], o["EXECUTABLE"])

    def test_requires_effector(self):
        o = Frame("@TEST.OPERATION.?")
        e = Frame("@TEST.EFFECTOR.?")
        o["REQUIRES-EFFECTOR"] = e

        self.assertEqual(e, Operation(o).requires_effector())

    def test_default_requires_effector(self):
        o = Frame("@TEST.OPERATION.?")
        self.assertIsNone(Operation(o).requires_effector())

    def test_set_requires_effector(self):
        o = Frame("@TEST.OPERATION.?")
        e = Frame("@TEST.EFFECTOR.?")
        self.assertEqual([], o["REQUIRES-EFFECTOR"])

        Operation(o).set_requires_effector(e)
        self.assertEqual([e], o["REQUIRES-EFFECTOR"])
