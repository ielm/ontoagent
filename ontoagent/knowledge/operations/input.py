from ontoagent.agent import Agent
from ontoagent.engine.executable import HandleExecutable
from ontoagent.engine.signal import Signal
from ontoagent.utils.analysis import TextAnalyzer
from ontograph.Frame import Frame


class HandleInputSpeechExecutable(HandleExecutable):

    def validate(self, agent: "Agent", signal: "Signal") -> bool:
        if signal.root()["AGENT"].singleton() == agent:
            return False
        if not signal.root()["THEME"].singleton() ^ Frame("@ONT.RAW-TEXT"):
            return False
        return True

    def run(self, agent: "Agent", signal: "Signal"):
        input = signal.root()["THEME"].singleton()["VALUE"].singleton()
        tmr = TextAnalyzer().to_signal(input)

        # Input the TMR
        agent.handle(tmr)
