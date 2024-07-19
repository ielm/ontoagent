from ontoagent.agent import Agent

from ontoagent.engine.effector import Effector
from ontoagent.engine.executable import HandleExecutable
from ontoagent.engine.signal import Signal, XMR
from ontoagent.utils.states import PhasedEvent


class ReleaseEffectorExecutable(HandleExecutable):

    def run(self, agent: "Agent", signal: "Signal"):
        effector = Effector(signal.root()["THEME"].singleton())
        effector.set_status(Effector.Status.AVAILABLE)

        xmr: XMR = effector.reserved_to()
        if xmr is not None:
            PhasedEvent(xmr.root()).set_ended()
