from ontoagent.engine.executable import ProactiveExecutable
from ontoagent.engine.operation import Operable, Operation
from ontograph.Space import Space
from typing import List, Type, Union

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ontoagent.agent import Agent


class Proactivity(Operable):

    @classmethod
    def build(cls, space: Union[str, Space], operations: List[Operation] = None):
        if isinstance(space, str):
            space = Space(space)
        if operations is None:
            operations = []

        frame = space.frame("@.PROACTIVITY.?").add_parent("@ONT.PROACTIVITY")
        p = Proactivity(frame)

        for op in operations:
            p.add_operation(op)

        return p

    def run(self, agent: "Agent"):
        for op in self.operations():
            op.run(agent)

    def add_executable(self, executable: Type[ProactiveExecutable]):
        op = Operation.build("EXE", executable)
        self.add_operation(op)
