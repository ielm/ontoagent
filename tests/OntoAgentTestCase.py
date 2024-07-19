from ontoagent.agent import Agent
from ontoagent.engine.executable import HandleExecutable
from ontoagent.engine.signal import Signal
from ontoagent.utils.analysis import Analyzer
from ontoagent.utils.loader import KnowledgeLoader
from ontoagent.utils.ontolang import OntoAgentOntoLang
from ontoagent.utils.ontology import OntologyOntoLangLoader
from ontoagent.views.agenda import ImpasseDetectionExecutable
from ontograph import graph
from ontograph.drivers.PostgreSQLDriver import PostgreSQLDriver
from ontograph.drivers.SQLiteDriver import SQLiteDriver
from ontograph.Frame import Frame

import unittest


class OntoAgentTestCase(unittest.TestCase):

    driver = "sqlite"

    def setUp(self):
        Agent.auto_join = True

        if OntoAgentTestCase.driver == "sqlite":
            self.setUpSQLiteDriver()
        elif OntoAgentTestCase.driver == "postgres":
            self.setUpPostgreSQLDriver()
        else:
            raise Exception

    def setUpPostgreSQLDriver(self):
        graph.driver = PostgreSQLDriver(
            database="unittest", directive=PostgreSQLDriver.InitDirective.POLL
        )

        KnowledgeLoader.loaded = []
        Analyzer._cache.clear()
        graph.driver.archiving().load("ontoagent_unittest")
        graph.set_ontolang(OntoAgentOntoLang())
        self.agent = Agent(Frame("@SELF.AGENT.1"))

    def setUpSQLiteDriver(self):
        graph.reset()
        KnowledgeLoader.loaded = []
        Analyzer._cache.clear()
        self.agent = Agent.build(
            Frame("@SELF.AGENT.1"),
            ontology_loader=OntologyOntoLangLoader(
                "tests.resources", "OntoAgentTestOntology.knowledge"
            ),
        )


class TestableExecutable(HandleExecutable):
    def __init__(self):
        super().__init__()

    def run(self, agent, signal=None):
        Frame("@TEST.RESULTS")["VALUE"] = signal.anchor

    def validate(self, agent: "Agent", signal: "Signal") -> bool:
        return Frame("@TEST.EXECUTABLE")["VALIDATE"].singleton()


class TestImpasseDetectionExecutable(ImpasseDetectionExecutable):
    def detect(self) -> bool:
        return self.step.anchor["TEST"].singleton()
