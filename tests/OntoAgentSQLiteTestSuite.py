from ontoagent.agent import Agent
from ontoagent.utils.ontology import OntologyOntoLangLoader
from ontograph import graph
from ontograph.drivers.SQLiteDriver import SQLiteDriver
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase
import unittest


class OntoAgentSQLiteTestSuite(unittest.TestSuite):

    def __init__(self):
        loader = unittest.TestLoader()
        start_dir = "."
        suite = loader.discover(start_dir, pattern="*TestCase.py")

        super().__init__()
        self._tests = suite._tests

    def run(self, result, debug=False):
        OntoAgentTestCase.driver = "sqlite"

        graph.driver = SQLiteDriver()
        Agent.build(
            Frame("@SELF.AGENT.1"),
            ontology_loader=OntologyOntoLangLoader(
                "tests.resources", "OntoAgentTestOntology.knowledge"
            ),
        )

        super().run(result, debug=debug)
