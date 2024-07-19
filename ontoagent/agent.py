from ontoagent.engine.effector import Effector
from ontoagent.engine.executable import Executable
from ontoagent.engine.operation import Operable, Operation
from ontoagent.engine.proactivity import Proactivity
from ontoagent.engine.signal import Signal, XMR
from ontoagent.utils.analysis import Analyzer, TextAnalyzer
from ontoagent.utils.common import AnchoredObject, StoppableThread
from ontoagent.utils.loader import KnowledgeLoader
from ontoagent.utils.ontolang import OntoAgentOntoLang
from ontoagent.utils.ontology import OntologyLoader, OntologyServiceLoader
from ontoagent.views.agenda import Agenda
from ontoagent.views.evergreen import EvergreenGoals
from ontograph import graph
from ontograph.Focus import Focus
from ontograph.Frame import Frame
from threading import Thread
from typing import List, Type, Union

import time


class Agent(AnchoredObject):

    heartbeat: "HeartbeatThread" = None
    auto_join: bool = False

    @classmethod
    def build(
        cls,
        identity: Frame = None,
        agenda: Frame = None,
        evergreens: Frame = None,
        proactivity: Frame = None,
        ontology_loader: OntologyLoader = None,
    ) -> "Agent":
        if identity is None:
            identity = Frame("@SELF.AGENT.1")
        if agenda is None:
            agenda = Frame("@SELF.AGENDA.1")
        if evergreens is None:
            evergreens = Frame("@SELF.EVERGREENS.1")
        if proactivity is None:
            proactivity = Frame("@SELF.PROACTIVITY.1")
        if ontology_loader is None:
            ontology_loader = OntologyServiceLoader()

        identity["HAS-AGENDA"] = agenda
        identity["HAS-EVERGREENS"] = evergreens
        identity["HAS-PROACTIVITY"] = proactivity

        graph.set_ontolang(OntoAgentOntoLang())

        ontology_loader.load()
        KnowledgeLoader.load_resource("ontoagent.knowledge", "core.knowledge")
        KnowledgeLoader.load_resource("ontoagent.knowledge", "input.knowledge")
        KnowledgeLoader.load_resource("ontoagent.knowledge", "agenda.knowledge")
        KnowledgeLoader.load_resource("ontoagent.knowledge", "proactivity.knowledge")

        agent = Agent(identity)

        for op in Proactivity(Frame("@EXE.PROACTIVITY.1")).operations():
            agent.proactivity().add_operation(op)

        Analyzer.register_analyzer(TextAnalyzer)

        return agent

    def load_knowledge(self, package: str, file: str):
        KnowledgeLoader.load_resource(package, file)

    def identity(self) -> Frame:
        return self.anchor

    def agenda(self) -> Agenda:
        return Agenda(self.anchor["HAS-AGENDA", Focus.Inh.LOC].singleton())

    def evergreens(self) -> EvergreenGoals:
        return EvergreenGoals(self.anchor["HAS-EVERGREENS", Focus.Inh.LOC].singleton())

    def proactivity(self) -> Proactivity:
        return Proactivity(self.anchor["HAS-PROACTIVITY", Focus.Inh.LOC].singleton())

    def effectors(self) -> List[Effector]:
        return list(map(lambda filler: Effector(filler), self.anchor["HAS-EFFECTOR"]))

    def add_effector(self, effector: Union[Frame, Effector]):
        if isinstance(effector, Effector):
            effector = effector.anchor
        self.anchor["HAS-EFFECTOR"] += effector

    def set_response(
        self,
        event: Union[str, Frame],
        executable: Type[Executable],
        with_effector: Union[str, Frame, Effector] = None,
    ):
        if isinstance(event, str):
            event = Frame(event)

        event = Operable(event)
        event.clear_operations()

        self.add_response(event.anchor, executable, with_effector=with_effector)

    def add_response(
        self,
        event: Union[str, Frame],
        executable: Type[Executable],
        with_effector: Union[str, Frame, Effector] = None,
    ):
        if isinstance(event, str):
            event = Frame(event)
        if isinstance(with_effector, str):
            with_effector = Frame(with_effector)

        event = Operable(event)
        operation = Operation(Frame("@SYS.OPERATION.?").add_parent("@ONT.OPERATION"))
        operation.set_executable(executable)

        if with_effector is not None:
            operation.set_requires_effector(with_effector)

        event.add_operation(operation)

    def background(self):
        self.proactivity().run(self)

    def input(self, signal: Signal, join: bool = None):
        def _input(signal: Signal):
            if not isinstance(signal, XMR):
                analyzed = Analyzer.analyzer_for_signal(signal).to_signal(signal)
                signal.set_status(Signal.Status.CONSUMED)
                signal = analyzed
            self.handle(signal, join=join)
            graph.driver.close_connection()

        thread = Thread(target=_input, args=(signal,))
        thread.start()

        join = join if join is not None else Agent.auto_join
        if join:
            thread.join()

    def handle(self, signal: Signal, join: bool = None):
        def _handle(signal: Signal):
            concept = Operable(signal.get_root_concept())
            for operation in concept.operations():
                operation.run(self, signal=signal)
            signal.set_status(Signal.Status.CONSUMED)
            graph.driver.close_connection()

        thread = Thread(target=_handle, args=(signal,))
        thread.start()

        join = join if join is not None else Agent.auto_join
        if join:
            thread.join()

    def output(self, xmr: XMR, effector: Effector, join: bool = None):
        def _output(xmr: XMR, effector: Effector):
            effector.interrupt()
            effector.run(self, xmr)
            graph.driver.close_connection()

        thread = Thread(
            target=_output,
            args=(
                xmr,
                effector,
            ),
        )
        thread.start()

        join = join if join is not None else Agent.auto_join
        if join:
            thread.join()

    def start(self, heartbeat: float = 0.25):
        if Agent.heartbeat is None:
            Agent.heartbeat = HeartbeatThread(self, heartbeat=heartbeat)

        Agent.heartbeat.start()

    def stop(self):
        if Agent.heartbeat is None:
            return

        Agent.heartbeat.stop()
        Agent.heartbeat = None


class HeartbeatThread(StoppableThread):

    def __init__(self, agent: Agent, heartbeat: float = 0.25):
        self.agent = agent
        self.heartbeat = heartbeat
        super().__init__()

    def run(self):
        while not self.stopped():
            time.sleep(self.heartbeat)
            self.agent.background()
