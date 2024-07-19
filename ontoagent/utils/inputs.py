from ontoagent.engine.signal import Signal
from ontograph.Frame import Frame
from typing import Union


class InputSignalSpeech(Signal):

    @classmethod
    def build_from_text(
        cls, text: str, speaker: Union[str, Frame] = None
    ) -> "InputSignalSpeech":
        space = Signal.next_available_space("IO")

        root = space.frame("@.SPEECH-ACT.?").add_parent(Frame("@ONT.SPEECH-ACT"))
        theme = space.frame("@.RAW-TEXT.?").add_parent(Frame("@ONT.RAW-TEXT"))

        agent = speaker
        if agent is None:
            agent = space.frame("@.ANIMATE.?").add_parent(Frame("@ONT.ANIMATE"))
        elif isinstance(agent, str):
            agent = Frame(agent)

        root["AGENT"] = agent
        root["THEME"] = theme

        theme["VALUE"] = text

        signal = Signal.build(root, space=space, constituents=[agent, theme])

        return InputSignalSpeech(signal.anchor)

    def text(self) -> str:
        return self.root()["THEME"].singleton()["VALUE"].singleton()

    def speaker(self) -> Frame:
        return self.root()["AGENT"].singleton()

    def __hash__(self):
        return hash(self.text())

    def __eq__(self, other):
        if isinstance(other, str) and other == self.text():
            return True
        if isinstance(other, Frame) and InputSignalSpeech(other).text() == self.text():
            return True
        if isinstance(other, InputSignalSpeech) and other.text() == self.text():
            return True
        return super().__eq__(other)
