from ontoagent.engine.operation import Report
from ontoagent.engine.signal import Signal, TMR, XMR
from ontograph.Frame import Frame
from ontograph.Space import Space
from tests.OntoAgentTestCase import OntoAgentTestCase
import time


class SignalTestCase(OntoAgentTestCase):

    def test_status(self):
        s = Frame("@TEST.SIGNAL.?")
        s["STATUS"] = Signal.Status.CONSUMED

        self.assertEqual(Signal.Status.CONSUMED, Signal(s).status())

    def test_default_status(self):
        s = Frame("@TEST.SIGNAL.?")
        self.assertEqual(Signal.Status.RECEIVED, Signal(s).status())

    def test_set_status(self):
        s = Frame("@TEST.SIGNAL.?")

        self.assertEqual([], s["STATUS"])

        Signal(s).set_status(Signal.Status.RECEIVED)

        self.assertEqual(Signal.Status.RECEIVED, s["STATUS"])

        Signal(s).set_status(Signal.Status.CONSUMED)

        self.assertNotEqual(Signal.Status.RECEIVED, s["STATUS"])
        self.assertEqual(Signal.Status.CONSUMED, s["STATUS"])

    def test_root(self):
        s = Frame("@TEST.SIGNAL.?")
        r = Frame("@TEST.ROOT.?")
        s["ROOT"] = r

        self.assertEqual(r, Signal(s).root())

    def test_set_root(self):
        s = Frame("@TEST.SIGNAL.?")

        self.assertEqual([], s["ROOT"])

        r1 = Frame("@TEST.ROOT.?")
        Signal(s).set_root(r1)

        self.assertEqual(r1, s["ROOT"])

        r2 = Frame("@TEST.ROOT.?")
        Signal(s).set_root(r2)

        self.assertNotEqual(r1, s["ROOT"])
        self.assertEqual(r2, s["ROOT"])

    def test_timestamp(self):
        s = Frame("@TEST.SIGNAL.?")
        t = time.time_ns()
        s["TIMESTAMP"] = t

        self.assertEqual(t, Signal(s).timestamp())

    def test_set_timestamp(self):
        s = Frame("@TEST.SIGNAL.?")

        self.assertEqual([], s["TIMESTAMP"])

        t1 = time.time_ns()
        Signal(s).set_timestamp(t1)

        self.assertEqual(t1, s["TIMESTAMP"])

        t2 = time.time_ns()
        Signal(s).set_timestamp(t2)

        self.assertNotEqual(t1, s["TIMESTAMP"])
        self.assertEqual(t2, s["TIMESTAMP"])

    def test_get_root_concept(self):
        c = Frame("@ONT.CONCEPT")
        r = Frame("@TEST.ROOT.?")
        r.add_parent(c)

        s = Signal(Frame("@TEST.SIGNAL.?"))
        s.set_root(r)

        self.assertEqual(c, s.get_root_concept())

    def test_get_root_concept_nearest_ontological_parent(self):
        c1 = Frame("@ONT.CONCEPT.?")
        c2 = Frame("@ONT.CONCEPT.?")
        f = Frame("@TEST.FRAME.?")
        r = Frame("@TEST.ROOT.?")

        c2.add_parent(c1)
        f.add_parent(c2)
        r.add_parent(f)

        s = Signal(Frame("@TEST.SIGNAL.?"))
        s.set_root(r)

        self.assertEqual(c2, s.get_root_concept())

    def test_get_root_concept_when_root_is_a_concept(self):
        c = Frame("@ONT.CONCEPT")

        s = Signal(Frame("@TEST.SIGNAL.?"))
        s.set_root(c)

        self.assertEqual(c, s.get_root_concept())

    def test_space(self):
        s = Frame("@TEST.SIGNAL.?")
        s["SPACE"] = "@XYZ"

        self.assertEqual(Space("XYZ"), XMR(s).space())

    def test_set_space(self):
        s = Frame("@TEST.SIGNAL.?")

        self.assertEqual([], s["SPACE"])

        XMR(s).set_space("@XYZ")

        self.assertEqual("@XYZ", s["SPACE"])

        XMR(s).set_space(Space("ABC"))

        self.assertNotEqual("@XYZ", s["SPACE"])
        self.assertEqual("@ABC", s["SPACE"])

    def test_next_available_space(self):
        self.assertEqual(Space("XMR#1"), XMR.next_available_space())
        self.assertEqual(Space("XMR#1"), XMR.next_available_space())
        self.assertEqual(Space("XMR#1"), XMR.next_available_space())

        self.assertEqual(Space("MMR#1"), XMR.next_available_space("MMR"))

        Frame("@XMR#1.FRAME.?")
        self.assertEqual(Space("XMR#2"), XMR.next_available_space())

    def test_constituents(self):
        s = Frame("@TEST.SIGNAL.?")
        c1 = Frame("@TEST.CONSTITUENT.?")
        c2 = Frame("@TEST.CONSTITUENT.?")

        s["HAS-CONSTITUENT"] = [c1, c2]

        self.assertEqual([c1, c2], Signal(s).constituents())

    def test_add_constituent(self):
        s = Frame("@TEST.SIGNAL.?")
        c1 = Frame("@TEST.CONSTITUENT.?")
        c2 = Frame("@TEST.CONSTITUENT.?")

        self.assertEqual([], s["HAS-CONSTITUENT"])

        Signal(s).add_constituent(c1)

        self.assertEqual([c1], s["HAS-CONSTITUENT"])

        Signal(s).add_constituent(c2)

        self.assertEqual([c1, c2], s["HAS-CONSTITUENT"])

    def test_reports(self):
        s = Frame("@TEST.SIGNAL.?")
        r1 = Frame("@TEST.REPORT.?")
        r2 = Frame("@TEST.REPORT.?")

        s["HAS-REPORT"] = [r1, r2]

        self.assertEqual([r1, r2], Signal(s).reports())
        self.assertIsInstance(Signal(s).reports()[0], Report)

    def test_default_reports(self):
        s = Signal(Frame("@TEST.SIGNAL.?"))
        self.assertEqual([], s.reports())

    def test_add_report(self):
        s = Frame("@TEST.SIGNAL.?")
        r1 = Frame("@TEST.REPORT.?")
        r2 = Frame("@TEST.REPORT.?")

        self.assertEqual([], s["HAS-REPORT"])

        Signal(s).add_report(r1)

        self.assertEqual([r1], s["HAS-REPORT"])

        Signal(s).add_report(r2)

        self.assertEqual([r1, r2], s["HAS-REPORT"])


class XMRTestCase(OntoAgentTestCase):

    pass


class TMRTestCase(OntoAgentTestCase):

    def test_speaker(self):
        speaker = Frame("@TEST.HUMAN.?")

        root = Frame("@TEST.SPEECH-ACT.?")
        root["AGENT"] = speaker

        tmr = TMR.build(root)
        self.assertEqual(speaker, tmr.speaker())

    def test_listeners(self):
        listener1 = Frame("@TEST.HUMAN.?")
        listener2 = Frame("@TEST.HUMAN.?")

        root = Frame("@TEST.SPEECH-ACT.?")
        root["BENEFICIARY"] += listener1
        root["BENEFICIARY"] += listener2

        tmr = TMR.build(root)
        self.assertEqual([listener1, listener2], tmr.listeners())
