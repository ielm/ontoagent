from ontoagent.agent import Agent
from ontoagent.utils.ontology import OntologyOntoLangLoader
from ontograph import graph
from ontograph.drivers.PostgreSQLDriver import PostgreSQLDriver
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase
import unittest


class OntoAgentPostgreSQLTestSuite(unittest.TestSuite):

    def __init__(self):
        loader = unittest.TestLoader()
        start_dir = "."
        suite = loader.discover(start_dir, pattern="*TestCase.py")

        super().__init__()
        self._tests = suite._tests

    def run(self, result, debug=False):
        OntoAgentTestCase.driver = "postgres"

        graph.driver = PostgreSQLDriver(
            database="unittest", directive=PostgreSQLDriver.InitDirective.POLL
        )
        Agent.build(
            Frame("@SELF.AGENT.1"),
            ontology_loader=OntologyOntoLangLoader(
                "tests.resources", "OntoAgentTestOntology.knowledge"
            ),
        )
        graph.driver.archiving().archive("ontoagent_unittest")

        super().run(result, debug=debug)
