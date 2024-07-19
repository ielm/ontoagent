from ontoagent.engine.effector import Effector
from ontoagent.engine.executable import Executable
from ontoagent.engine.report import Report
from ontoagent.engine.signal import Signal, XMR
from ontoagent.utils.common import AnchoredObject
from ontograph.Frame import Frame
from ontograph.Space import Space
from typing import List, Type, Union

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ontoagent.agent import Agent


class Operation(AnchoredObject):

    @classmethod
    def build(cls, space: Union[str, Space], executable: Type[Executable]):
        if isinstance(space, str):
            space = Space(space)

        frame = space.frame("@.OPERATION.?").add_parent("@ONT.OPERATION")
        op = Operation(frame)
        op.set_executable(executable)

        return op

    def run(
        self,
        agent: "Agent",
        signal: Signal = None,
        xmr: XMR = None,
        effector: Effector = None,
    ) -> Report:
        return self.executable()._run(agent, signal=signal, xmr=xmr, effector=effector)

    def executable(self) -> Executable:
        return self.anchor["EXECUTABLE"].singleton()()

    def set_executable(self, execute: Type[Executable]):
        self.anchor["EXECUTABLE"] = execute

    def requires_effector(self) -> Union[None, Effector]:
        if "REQUIRES-EFFECTOR" in self.anchor:
            effector = self.anchor["REQUIRES-EFFECTOR"].singleton()
            if isinstance(effector, Frame):
                effector = Effector(effector)
            return effector
        return None

    def set_requires_effector(self, effector: Union[Frame, Effector]):
        if isinstance(effector, Effector):
            effector = effector.anchor
        self.anchor["REQUIRES-EFFECTOR"] = effector


class Operable(AnchoredObject):

    def operations(self) -> List[Operation]:
        return list(map(lambda filler: Operation(filler), self.anchor["HAS-OPERATION"]))

    def add_operation(self, operation: Union[Frame, Operation]):
        if isinstance(operation, Operation):
            operation = operation.anchor
        self.anchor["HAS-OPERATION"] += operation

    def clear_operations(self):
        self.anchor["HAS-OPERATION"] = []
