from ontoagent.engine.signal import Signal, XMR
from ontoagent.utils.analysis import Analyzer, TextAnalyzer
from ontoagent.utils.leia import ontosem_analyze_endpoint
from ontograph.Frame import Frame
from pkgutil import get_data
from tests.OntoAgentTestCase import OntoAgentTestCase
from typing import Any
from unittest.mock import MagicMock, patch
import json


class AnalyzerTestCase(OntoAgentTestCase):

    def test_analyzer_cache_store_and_lookup(self):
        text = "The man hit the building."
        analysis = """
            @[TMR].HIT.1? = { 
                IS-A    @ONT.HIT;
                AGENT   @[TMR].HUMAN.1?;
                THEME   @[TMR].BUILDING.1?;
            };
            @[TMR].HUMAN.1? = { IS-A @ONT.HUMAN; };
            @[TMR].BUILDING.1? = { IS-A @ONT.BUILDING; };
        """

        self.assertIsNone(Analyzer().lookup(text))

        Analyzer().cache(text, analysis)

        self.assertEqual(analysis, Analyzer().lookup(text))

    @patch("ontoagent.utils.analysis.Analyzer._analyze")
    def test_analyzer_returns_cached_results(self, mock_analyzer_analyze: MagicMock):
        text = "The man hit the building."
        analysis = "SOME-ANALYSIS-RESULTS"

        Analyzer().cache(text, analysis)

        results = Analyzer().analyze(text)
        self.assertEqual(analysis, results)
        mock_analyzer_analyze.assert_not_called()

    @patch("ontoagent.utils.analysis.Analyzer._analyze")
    def test_analyzer_analyzes_uncached_results(self, mock_analyzer_analyze: MagicMock):
        text = "The man hit the building."
        analysis = "SOME-ANALYSIS-RESULTS"

        mock_analyzer_analyze.return_value = analysis

        results = Analyzer().analyze(text)
        self.assertEqual(analysis, results)
        mock_analyzer_analyze.assert_called_once_with(text)

    def test_register_analyzer(self):
        self.assertEqual([TextAnalyzer], Analyzer.get_registered_analyzers())

        Analyzer.register_analyzer(TestableAnalyzer)

        self.assertIn(TextAnalyzer, Analyzer.get_registered_analyzers())
        self.assertIn(TestableAnalyzer, Analyzer.get_registered_analyzers())

    def test_analyzer_for_signal_with_custom_analyzer(self):
        signal = Signal.build(Frame("@TEST.SIGNAL.?"))

        with self.assertRaises(NotImplementedError):
            Analyzer.analyzer_for_signal(signal)

        Analyzer.register_analyzer(TestableAnalyzer)

        self.assertIsInstance(Analyzer.analyzer_for_signal(signal), TestableAnalyzer)


class TextAnalyzerTestCase(OntoAgentTestCase):

    @patch("ontoagent.utils.analysis.TextAnalyzer._text_analysis_call_ontosem_service")
    def test_text_analysis_returns_cached_results(
        self, mock_text_analysis_call_ontosem_service: MagicMock
    ):
        text = "The man hit the building."
        analysis = "SOME-ANALYSIS-RESULTS"

        Analyzer().cache(text, analysis)

        results = TextAnalyzer().analyze(text)
        self.assertEqual(analysis, results)
        mock_text_analysis_call_ontosem_service.assert_not_called()

    @patch("ontoagent.utils.analysis.TextAnalyzer._text_analysis_call_ontosem_service")
    @patch(
        "ontoagent.utils.analysis.TextAnalyzer._text_analysis_format_ontosem_results_to_ontolang"
    )
    def test_text_analysis_returns_analyzed_and_formatted_results(
        self,
        mock_text_analysis_format_ontosem_results_to_ontolang: MagicMock,
        mock_text_analysis_call_ontosem_service: MagicMock,
    ):
        text = "The man hit the building."

        def MockFormat(ontosem: str) -> str:
            if ontosem == "FROM-ONTOSEM":
                return "FORMATTED"
            return "ERROR"

        mock_text_analysis_call_ontosem_service.return_value = "FROM-ONTOSEM"
        mock_text_analysis_format_ontosem_results_to_ontolang.side_effect = MockFormat

        results = TextAnalyzer().analyze(text)

        self.assertEqual("FORMATTED", results)

    @patch("ontoagent.utils.analysis.Analyzer.cache")
    @patch("ontoagent.utils.analysis.TextAnalyzer._text_analysis_call_ontosem_service")
    @patch(
        "ontoagent.utils.analysis.TextAnalyzer._text_analysis_format_ontosem_results_to_ontolang"
    )
    def test_text_analysis_caches_analyzed_and_formatted_results(
        self,
        mock_text_analysis_format_ontosem_results_to_ontolang: MagicMock,
        mock_text_analysis_call_ontosem_service: MagicMock,
        mock_analysis_cache: MagicMock,
    ):
        text = "The man hit the building."

        def MockFormat(ontosem: str) -> str:
            if ontosem == "FROM-ONTOSEM":
                return "FORMATTED"
            return "ERROR"

        mock_text_analysis_call_ontosem_service.return_value = "FROM-ONTOSEM"
        mock_text_analysis_format_ontosem_results_to_ontolang.side_effect = MockFormat

        results = TextAnalyzer().analyze(text)

        mock_analysis_cache.assert_called_once_with(text, "FORMATTED")

    @patch("ontoagent.utils.analysis.requests.post")
    def test_text_analysis_call_ontosem_service(self, mock_post: MagicMock):
        text = "The man hit the building."

        class MockRequest(object):
            def __init__(self):
                self.text = json.dumps({"ontosem": "test"})

        mock_post.return_value = MockRequest()
        result = TextAnalyzer()._text_analysis_call_ontosem_service(text)

        mock_post.assert_called_once_with(
            url=ontosem_analyze_endpoint(), data={"text": text}
        )
        self.assertEqual({"ontosem": "test"}, result)

    def test_text_analysis_format_ontosem_results_to_ontolang(self):
        ontosem = json.loads(get_data("tests.resources", "SampleTMR.json"))
        ontolang = """
            @[TMR].REQUEST-ACTION.1? = {
                IS-A        @ONT.REQUEST-ACTION;
                AGENT       @[TMR].HUMAN.1?;
                BENEFICIARY @[TMR].ROBOT.1?;
                THEME       @[TMR].GIVE.1?;
                TMR-ROOT    True;
                TIME        "FIND-ANCHOR-TIME";
            };
            
            @[TMR].GIVE.1? = {
                IS-A        @ONT.GIVE;
                BENEFICIARY @[TMR].HUMAN.1?;
                AGENT       @[TMR].ROBOT.1?;
                THEME       @[TMR].DOWEL.1?;
            };
            
            @[TMR].DOWEL.1? = {
                IS-A            @ONT.DOWEL;
                MADE-OF         "WOOD";
                SHAPE           "CYLINDRICAL";
                GROUNDING-MP    "ground_to_most_recently_used";
            };
            
            @[TMR].HUMAN.1? = {
                IS-A        @ONT.HUMAN;
            };
            
            @[TMR].ROBOT.1? = {
                IS-A        @ONT.ROBOT;
            };
        """

        results = TextAnalyzer()._text_analysis_format_ontosem_results_to_ontolang(
            ontosem
        )

        from ontograph import graph

        results_processors = graph.ontolang().parse(results.replace("[TMR]", "TMR#123"))
        ontolang_processors = graph.ontolang().parse(
            ontolang.replace("[TMR]", "TMR#123")
        )

        for processor in ontolang_processors:
            self.assertIn(processor, results_processors)

        for processor in results_processors:
            self.assertIn(processor, ontolang_processors)


class TestableAnalyzer(Analyzer):

    def is_appropriate(self, signal: Signal):
        return True

    def _analyze(self, input: Any):
        root = Frame("@TEST.XMR.?")
        root["FROM-INPUT"] = input
        return XMR(root)
