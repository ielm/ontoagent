from ontoagent.engine.effector import Effector
from ontoagent.engine.signal import XMR
from ontoagent.knowledge.operations.core import ReleaseEffectorExecutable
from ontoagent.utils.states import PhasedEvent
from ontograph.Frame import Frame
from ontograph.Space import Space
from tests.OntoAgentTestCase import OntoAgentTestCase


class ReleaseEffectorExecutableTestCase(OntoAgentTestCase):

    def test_run_releases_effector(self):
        effector = Effector(Frame("@TEST.EFFECTOR.?"))
        effector.set_status(Effector.Status.RESERVED)

        root = Frame("@MMR#1.RELEASE-EFFECTOR.?")
        root["THEME"] = effector.anchor
        signal = XMR.build(root, space=Space("MMR#1"))

        ReleaseEffectorExecutable().run(self.agent, signal)

        self.assertEqual(Effector.Status.AVAILABLE, effector.status())

    def test_run_marks_phase_end_of_xmr_root(self):
        event = Frame("@TEST.EVENT.?")

        effector = Effector(Frame("@TEST.EFFECTOR.?"))
        effector.set_status(Effector.Status.RESERVED)

        calling_xmr = XMR.build(event, space=Space("XMR#1"))
        effector.set_reserved_to(calling_xmr)

        root = Frame("@MMR#1.RELEASE-EFFECTOR.?")
        root["THEME"] = effector.anchor
        signal = XMR.build(root, space=Space("MMR#1"))

        self.assertFalse(PhasedEvent(event).is_ended())

        ReleaseEffectorExecutable().run(self.agent, signal)

        self.assertTrue(PhasedEvent(event).is_ended())
