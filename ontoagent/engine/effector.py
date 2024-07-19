from enum import Enum
from ontoagent.engine.executable import Executable
from ontoagent.engine.report import Report
from ontoagent.engine.signal import XMR
from ontoagent.utils.common import AnchoredObject
from ontograph.Frame import Frame
from ontograph.Space import Space
from typing import Type, Union

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ontoagent.agent import Agent


class Effector(AnchoredObject):

    class Status(Enum):
        AVAILABLE = "AVAILABLE"
        RESERVED = "RESERVED"

    @classmethod
    def build(
        cls,
        type: Union[Frame, "Effector"] = None,
        space: Union[str, Space] = None,
        executable: Type["Executable"] = None,
    ) -> "Effector":
        if space is None:
            space = "SELF"
        if isinstance(space, str):
            space = Space(space)
        if type is None:
            type = Frame("@ONT.EFFECTOR")
        if isinstance(type, Effector):
            type = type.anchor

        effector = Effector(space.frame("@.EFFECTOR.?"))
        effector.anchor.add_parent(type)

        if executable is not None:
            effector.set_executable(executable)

        return effector

    def status(self) -> Status:
        if "STATUS" in self.anchor:
            return self.anchor["STATUS"].singleton()
        return Effector.Status.AVAILABLE

    def set_status(self, status: Status):
        self.anchor["STATUS"] = status

    def reserved_to(self) -> Union[None, XMR]:
        if "RESERVED-TO" in self.anchor:
            return XMR(self.anchor["RESERVED-TO"].singleton())
        return None

    def set_reserved_to(self, reserved_to: XMR):
        self.anchor["RESERVED-TO"] = reserved_to.anchor

    def executable(self) -> "Executable":
        if "EXECUTABLE" not in self.anchor:
            return None
        return self.anchor["EXECUTABLE"].singleton()()

    def set_executable(self, executable: Type["Executable"]):
        self.anchor["EXECUTABLE"] = executable

    def interrupt(self) -> Type["Executable"]:
        if "INTERRUPT" not in self.anchor:
            return None
        return self.anchor["INTERRUPT"].singleton()

    def set_interrupt(self, execute: Type["Executable"]):
        self.anchor["INTERRUPT"] = execute

    def run(self, agent: "Agent", xmr: XMR) -> Report:
        self.set_reserved_to(xmr)
        return self.executable()._run(agent, xmr=xmr, effector=self)
