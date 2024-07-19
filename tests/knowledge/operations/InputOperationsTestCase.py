from ontoagent.engine.signal import XMR
from ontoagent.knowledge.operations.input import HandleInputSpeechExecutable
from ontoagent.utils.analysis import Analyzer, TextAnalyzer
from ontograph.Frame import Frame
from pkgutil import get_data
from service.input import input_speech
from tests.OntoAgentTestCase import OntoAgentTestCase
from unittest.mock import MagicMock
import json


class InputOperationsTestCase(OntoAgentTestCase):

    def test_run(self):
        self.agent.handle = MagicMock()

        # Cache the results of analysis for this test
        ontosem = json.loads(get_data("tests.resources", "SampleTMR.json"))
        ontolang = TextAnalyzer()._text_analysis_format_ontosem_results_to_ontolang(
            ontosem
        )
        Analyzer().cache("Give me the dowel.", ontolang)

        # Create the initial input signal
        signal = input_speech({"speaker": {}, "text": "Give me the dowel."})

        # Execute the operation
        HandleInputSpeechExecutable().run(self.agent, signal)

        # The TMR is now queued
        self.agent.handle.assert_called_once()
        signal: XMR = self.agent.handle.call_args[0][0]

        # signal = self.agent.queue().signals()[0]
        self.assertEqual(Frame("@IO.TMR.1"), signal.anchor)
        self.assertEqual(Frame("@TMR#1.REQUEST-ACTION.1"), signal.root())

        # The TMR root has an agent and beneficiary
        self.assertEqual(Frame("@TMR#1.HUMAN.1"), signal.root()["AGENT"])
        self.assertEqual(Frame("@TMR#1.ROBOT.1"), signal.root()["BENEFICIARY"])

        # The TMR root HAS-CONSTITUENTS
        self.assertEqual(5, len(XMR(signal.anchor).constituents()))

    def test_not_valid_if_agent_is_self(self):
        # Create the initial input signal
        signal = input_speech({"speaker": {}, "text": "Give me the dowel."})
        signal.root()["AGENT"] = self.agent.identity()

        # Validate
        self.assertFalse(HandleInputSpeechExecutable().validate(self.agent, signal))

    def test_run_does_nothing_if_theme_is_not_raw_text(self):
        # Create the initial input signal
        signal = input_speech({"speaker": {}, "text": "Give me the dowel."})
        signal.root()["THEME"] = Frame("@TEST.SOMETHING-ELSE")

        # Validate
        self.assertFalse(HandleInputSpeechExecutable().validate(self.agent, signal))
