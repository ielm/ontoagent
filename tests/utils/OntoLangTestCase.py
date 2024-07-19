from ontoagent.utils.ontolang import OntoAgentOntoLang
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase


class OntoAgentOntoLangTestCase(OntoAgentTestCase):

    def setUp(self):
        super().setUp()
        self.ontolang = OntoAgentOntoLang()

    def test_filler_as_class(self):
        self.ontolang.run(
            "@TEST.FRAME.1 = { THEME *tests.OntoAgentTestCase.OntoAgentTestCase; };"
        )
        frame = Frame("@TEST.FRAME.1")

        self.assertEqual(OntoAgentTestCase, frame["THEME"])

    def test_filler_as_other(self):
        self.ontolang.run("@TEST.FRAME.1 = { THEME 123; };")
        frame = Frame("@TEST.FRAME.1")
        self.assertEqual(123, frame["THEME"])
