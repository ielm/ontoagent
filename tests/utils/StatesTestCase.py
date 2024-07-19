from ontoagent.utils.states import (
    does_state_exist,
    _find_similar_events,
    _is_event_satisfied,
    PhasedEvent,
)
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase
from unittest.mock import MagicMock, patch


class DoesStateExistTestCase(OntoAgentTestCase):

    @patch("ontoagent.utils.states._is_event_satisfied")
    def test_defers_to_is_event_satisfied(self, mock_is_event_satisfied: MagicMock):
        f1 = Frame("@TEST.FRAME.?").add_parent(Frame("@ONT.EVENT"))
        f2 = Frame("@TEST.FRAME.?")

        does_state_exist(f1)
        mock_is_event_satisfied.assert_called_once_with(f1)

        mock_is_event_satisfied.reset_mock()
        does_state_exist(f2)
        mock_is_event_satisfied.assert_not_called()

    @patch("ontoagent.utils.states._is_effect_perceived")
    def test_defers_to_is_effect_perceived(self, mock_is_effect_perceived: MagicMock):
        f1 = Frame("@TEST.FRAME.?").add_parent(Frame("@ONT.EFFECT"))
        f2 = Frame("@TEST.FRAME.?")

        does_state_exist(f1)
        mock_is_effect_perceived.assert_called_once_with(f1)

        mock_is_effect_perceived.reset_mock()
        does_state_exist(f2)
        mock_is_effect_perceived.assert_not_called()

    def test_event_throughput(self):
        agent = Frame("@TEST.OBJECT.?")
        theme = Frame("@TEST.OBJECT.?")

        event = Frame("@TEST.EVENT.?").add_parent(Frame("@ONT.EVENT"))
        event["AGENT"] = agent
        event["THEME"] = theme

        self.assertFalse(does_state_exist(event))

        match = Frame("@TEST.EVENT.?").add_parent(Frame("@ONT.EVENT"))
        match["AGENT"] = agent
        match["THEME"] = Frame("@TEST.OBJECT.?").add_parent(theme)

        self.assertFalse(does_state_exist(event))

        PhasedEvent(match).set_ended()

        self.assertTrue(does_state_exist(event))


class IsEventSatisfiedTestCase(OntoAgentTestCase):

    def test_event_phase_end_is_satisfied(self):
        f = Frame("@TEST.FRAME.?")
        PhasedEvent(f).set_ended()

        self.assertTrue(_is_event_satisfied(f))

    def test_event_phase_any_is_not_satisfied(self):
        f = Frame("@TEST.FRAME.?")
        PhasedEvent(f).set_phase("???")

        self.assertFalse(_is_event_satisfied(f))

    @patch("ontoagent.utils.states._find_similar_events")
    def test_event_no_phase_searches_for_candidates(
        self, mock_find_similar_events: MagicMock
    ):
        f = Frame("@TEST.FRAME.?")
        _is_event_satisfied(f)

        mock_find_similar_events.assert_called_once_with(f)

    @patch("ontoagent.utils.states._find_similar_events")
    def test_event_filters_candidates_with_phase_end(
        self, mock_find_similar_events: MagicMock
    ):
        f = Frame("@TEST.FRAME.?")

        c1 = Frame("@TEST.CANDIDATE.?")
        c2 = Frame("@TEST.CANDIDATE.?")
        c3 = Frame("@TEST.CANDIDATE.?")

        PhasedEvent(c1).set_ended()
        PhasedEvent(c2).set_phase("???")

        mock_find_similar_events.return_value = [c1, c2, c3]
        self.assertTrue(_is_event_satisfied(f))

        mock_find_similar_events.reset_mock()
        mock_find_similar_events.return_value = [c2, c3]
        self.assertFalse(_is_event_satisfied(f))


class FindSimilarEventsTestCase(OntoAgentTestCase):

    def test_candidates_must_be_descendants(self):
        p = Frame("@TEST.PARENT.?")
        t = Frame("@TEST.TARGET.?").add_parent(p)

        c1 = Frame("@TEST.CANDIDATE.?").add_parent(p)
        c2 = Frame("@TEST.CANDIDATE.?").add_parent(c1)
        c3 = Frame("@TEST.CANDIDATE.?")

        self.assertEqual([c1, c2], _find_similar_events(t))

    def test_candidates_must_match_specified_case_roles(self):
        p = Frame("@TEST.PARENT.?")

        agent = Frame("@ONT.HUMAN.?")
        theme = Frame("@ONT.OBJECT")

        t = Frame("@TEST.TARGET.?").add_parent(p)
        t["AGENT"] = agent
        t["THEME"] = theme

        # The agent and theme are an exact match
        c1 = Frame("@TEST.CANDIDATE.?").add_parent(p)
        c1["AGENT"] = agent
        c1["THEME"] = theme

        # The agent is an exact match, the theme is a descendant
        c2 = Frame("@TEST.CANDIDATE.?").add_parent(p)
        c2["AGENT"] = agent
        c2["THEME"] = Frame("@TEST.OBJECT.?").add_parent(theme)

        # The agent matches, but the theme does not
        c3 = Frame("@TEST.CANDIDATE.?").add_parent(p)
        c3["AGENT"] = agent
        c3["THEME"] = Frame("@TEST.OBJECT.?")

        self.assertEqual([c1, c2], _find_similar_events(t))

    def test_candidates_can_ignore_non_case_roles(self):
        p = Frame("@TEST.PARENT.?")

        t = Frame("@TEST.TARGET.?").add_parent(p)
        t["OTHER"] = 123

        c = Frame("@TEST.CANDIDATE.?").add_parent(p)

        self.assertEqual([c], _find_similar_events(t))

    def test_candidates_can_include_additional_fillers(self):
        p = Frame("@TEST.PARENT.?")

        t = Frame("@TEST.TARGET.?").add_parent(p)

        c = Frame("@TEST.CANDIDATE.?").add_parent(p)
        c["OTHER"] = 123

        self.assertEqual([c], _find_similar_events(t))


class PhasedEventTestCase(OntoAgentTestCase):

    def test_phase(self):
        f = Frame("@TEST.FRAME.?")
        f["PHASE"] = "XYZ"

        self.assertEqual("XYZ", PhasedEvent(f).phase())

    def test_default_phase(self):
        f = Frame("@TEST.FRAME.?")
        self.assertEqual(None, PhasedEvent(f).phase())

    def test_set_phase(self):
        f = Frame("@TEST.FRAME.?")
        self.assertEqual([], f["PHASE"])

        PhasedEvent(f).set_phase("XYZ")
        self.assertEqual("XYZ", f["PHASE"])

    def test_set_ended(self):
        f = Frame("@TEST.FRAME.?")
        self.assertEqual([], f["PHASE"])

        PhasedEvent(f).set_ended()
        self.assertEqual("END", f["PHASE"])

    def test_is_ended(self):
        f = Frame("@TEST.FRAME.?")
        self.assertFalse(PhasedEvent(f).is_ended())

        f["PHASE"] = "XYZ"
        self.assertFalse(PhasedEvent(f).is_ended())

        f["PHASE"] = "END"
        self.assertTrue(PhasedEvent(f).is_ended())
