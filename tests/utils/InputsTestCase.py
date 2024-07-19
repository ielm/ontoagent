from ontoagent.utils.inputs import InputSignalSpeech
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase


class InputSignalSpeechTestCase(OntoAgentTestCase):

    def test_signal_has_unique_io_space(self):
        signal = InputSignalSpeech.build_from_text("test")
        self.assertEqual("IO#1", signal.space().name)

    def test_signal_root(self):
        signal = InputSignalSpeech.build_from_text("test")
        self.assertTrue(signal.root() ^ Frame("@ONT.SPEECH-ACT"))

    def test_signal_speaker_assigned(self):
        speaker = Frame("@TEST.SPEAKER.?")
        signal = InputSignalSpeech.build_from_text("test", speaker=speaker)
        self.assertEqual(speaker, signal.root()["AGENT"].singleton())

    def test_signal_speaker_unassigned(self):
        signal = InputSignalSpeech.build_from_text("test")
        speaker = signal.root()["AGENT"].singleton()
        self.assertTrue(speaker ^ Frame("@ONT.ANIMATE"))

    def test_raw_text(self):
        signal = InputSignalSpeech.build_from_text("test")
        raw_text = signal.root()["THEME"].singleton()
        self.assertTrue(raw_text ^ Frame("@ONT.RAW-TEXT"))
        self.assertEqual("test", raw_text["VALUE"])

    def test_constituents(self):
        signal = InputSignalSpeech.build_from_text("test")
        agent = signal.root()["AGENT"].singleton()
        theme = signal.root()["THEME"].singleton()

        self.assertIn(agent, signal.constituents())
        self.assertIn(theme, signal.constituents())
