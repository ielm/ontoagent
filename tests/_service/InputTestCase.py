from ontograph.Frame import Frame
from service.input import input_speech
from tests.OntoAgentTestCase import OntoAgentTestCase


class InputSpeechTestCase(OntoAgentTestCase):

    def setUp(self):
        super().setUp()
        self.input = {
            "speaker": {"attribute-1": 123, "attribute-2": "abc", "attribute-3": False},
            "text": "Test speech.",
        }

    def test_input_speech_creates_anchor(self):
        signal = input_speech(self.input)
        anchor = signal.anchor

        self.assertEqual("IO", anchor.space())
        self.assertTrue(anchor ^ Frame("@ONT.SYSTEM-SIGNAL"))

    def test_input_speech_creates_space(self):
        signal = input_speech(self.input)
        space = signal.space()

        self.assertEqual("IO#1", space)

    def test_input_speech_creates_root(self):
        signal = input_speech(self.input)
        root = signal.root()

        self.assertEqual(signal.space(), root.space())
        self.assertTrue(root ^ Frame("@ONT.SPEECH-ACT"))

    def test_input_speech_assigned_agent(self):
        signal = input_speech({"speaker": "@TEST.HUMAN.1", "text": "Test speech."})
        agent = signal.root()["AGENT"].singleton()

        self.assertEqual(Frame("@TEST.HUMAN.1"), agent)

    def test_input_speech_creates_agent(self):
        signal = input_speech(self.input)
        agent = signal.root()["AGENT"].singleton()

        self.assertEqual(signal.space(), agent.space())
        self.assertTrue(agent ^ Frame("@ONT.ANIMATE"))
        self.assertEqual(123, agent["attribute-1"])
        self.assertEqual("abc", agent["attribute-2"])
        self.assertEqual(False, agent["attribute-3"])

    def test_input_speech_creates_theme(self):
        signal = input_speech(self.input)
        theme = signal.root()["THEME"].singleton()

        self.assertEqual(signal.space(), theme.space())
        self.assertTrue(theme ^ Frame("@ONT.RAW-TEXT"))
        self.assertTrue("Test speech.", theme["VALUE"])

    def test_constituents(self):
        signal = input_speech(self.input)

        root = signal.root()
        agent = signal.root()["AGENT"].singleton()
        theme = signal.root()["THEME"].singleton()

        self.assertEqual({root, agent, theme}, set(signal.constituents()))
