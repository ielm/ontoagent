from enum import Enum
from ontoagent.engine.report import Report
from ontoagent.utils.common import AnchoredObject
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Space import Space
from typing import List, Union
import time


class Signal(AnchoredObject):

    class Status(Enum):
        RECEIVED = "RECEIVED"
        CONSUMED = "CONSUMED"

    @classmethod
    def build(
        cls,
        root: Frame,
        space: Space = None,
        anchor: Union[str, Frame] = None,
        constituents: List[Frame] = None,
    ) -> "Signal":
        if anchor is None:
            anchor = Frame("@IO.SYSTEM-SIGNAL.?")
            anchor.add_parent("@ONT.SYSTEM-SIGNAL")
        if isinstance(anchor, str):
            anchor = Frame(anchor)
        if space is None:
            space = anchor.space()
        if constituents is None:
            constituents = []

        s = Signal(anchor)
        s.set_root(root)
        s.set_timestamp(time.time_ns())
        s.set_status(Signal.Status.RECEIVED)
        s.set_space(space)

        if root not in constituents:
            s.add_constituent(root)
        for constituent in constituents:
            s.add_constituent(constituent)

        return s

    @classmethod
    def next_available_space(cls, header: str = None) -> Space:
        if header is None:
            header = "XMR"

        spaces = list(graph)
        spaces = filter(lambda space: space.name.startswith(header + "#"), spaces)
        spaces = map(lambda space: int(space.name.replace(header + "#", "")), spaces)
        spaces = list(spaces)

        next = 1 if len(spaces) == 0 else max(spaces) + 1
        return Space(header + "#" + str(next))

    def status(self) -> Status:
        try:
            return self.anchor["STATUS"].singleton()
        except:
            return Signal.Status.RECEIVED

    def set_status(self, status: Status):
        self.anchor["STATUS"] = status

    def root(self) -> Frame:
        return self.anchor["ROOT"].singleton()

    def set_root(self, root: Frame):
        self.anchor["ROOT"] = root

    def timestamp(self) -> int:
        return self.anchor["TIMESTAMP"].singleton()

    def set_timestamp(self, timestamp: int):
        self.anchor["TIMESTAMP"] = timestamp

    def get_root_concept(self) -> Frame:
        root = self.root()
        if root.space() == "ONT":
            return root

        for a in root.ancestors():
            if a.space() == "ONT":
                return a

        raise Exception("Signal %s has no ontological root." % self.anchor.id)

    def space(self) -> Space:
        return Space(self.anchor["SPACE"].singleton().replace("@", "", 1))

    def set_space(self, space: Union[str, Space]):
        if isinstance(space, Space):
            space = "@" + space.name
        self.anchor["SPACE"] = space

    def constituents(self) -> List[Frame]:
        return list(self.anchor["HAS-CONSTITUENT"])

    def add_constituent(self, constituent: Frame):
        self.anchor["HAS-CONSTITUENT"] += constituent

    def reports(self) -> List[Report]:
        return list(map(lambda r: Report(r), self.anchor["HAS-REPORT"]))

    def add_report(self, report: Union[Frame, Report]):
        if isinstance(report, Report):
            report = report.anchor
        self.anchor["HAS-REPORT"] += report


class XMR(Signal):

    @classmethod
    def build(
        cls,
        root: Frame,
        space: Space = None,
        anchor: Union[str, Frame] = None,
        constituents: List[Frame] = None,
    ) -> "XMR":
        if anchor is None:
            anchor = Frame("@IO.XMR.?")
            anchor.add_parent(Frame("@ONT.XMR"))
        s = super().build(root, space=space, anchor=anchor, constituents=constituents)
        x = XMR(s.anchor)

        return x


class TMR(XMR):

    @classmethod
    def build(
        cls,
        root: Frame,
        space: Space = None,
        anchor: Union[str, Frame] = None,
        constituents: List[Frame] = None,
    ) -> "XMR":
        if anchor is None:
            anchor = Frame("@IO.TMR.?")
            anchor.add_parent(Frame("@ONT.TMR"))
        s = super().build(root, space=space, anchor=anchor, constituents=constituents)
        t = TMR(s.anchor)

        return t

    def speaker(self) -> Frame:
        return self.root()["AGENT"].singleton()

    def listeners(self) -> List[Frame]:
        return list(self.root()["BENEFICIARY"])


class VMR(XMR):

    @classmethod
    def build(
        cls,
        themes: List[Frame],
        space: Space = None,
        anchor: Union[str, Frame] = None,
        agent: Frame = None,
    ) -> "VMR":
        if anchor is None:
            anchor = Frame("@IO.VMR.?")
            anchor.add_parent(Frame("@ONT.VMR"))
        if isinstance(anchor, str):
            anchor = Frame(anchor)
        if space is None:
            space = anchor.space()
        if agent is None:
            agent = Frame("@SELF.AGENT.1")

        root = space.frame("@.VISUAL-EVENT.?").add_parent(Frame("@ONT.VISUAL-EVENT"))
        root["AGENT"] = agent
        root["THEME"] = themes

        xmr = super().build(root, space=space, anchor=anchor)
        return VMR(xmr.anchor)
