from ontoagent.knowledge.operations.proactivity import (
    UpdateEvergreenGoalsProactiveExecutable,
)
from ontoagent.views.evergreen import LTGoal, ObservableValue
from ontograph.Frame import Frame
from ontograph.Space import Space
from tests.OntoAgentTestCase import OntoAgentTestCase


class ProactivityOperationsTestCase(OntoAgentTestCase):

    def test_update_evergreens(self):
        definition = Frame("@TEST.GOAL-DEFINITION.?")

        lt_goal = LTGoal.build(
            Space("TEST"),
            Frame("@TEST.FRAME.?"),
            "SLOT",
            ObservableValue.build(
                Space("TEST"), ObservableValue.Comparator.EQUALS, 123
            ),
            definition,
        )

        self.agent.evergreens().add_lt_goal(lt_goal)

        self.assertEqual([], self.agent.agenda().goals())

        UpdateEvergreenGoalsProactiveExecutable().run(self.agent)

        self.assertTrue(self.agent.agenda().goals()[0].anchor ^ definition)
