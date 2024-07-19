from enum import Enum
from ontoagent.utils.common import AnchoredObject
from ontograph.Frame import Frame
from typing import List, Type
import time


class Report(AnchoredObject):

    class Status(Enum):
        PENDING = "PENDING"
        FINISHED = "FINISHED"
        FAILED = "FAILED"

    @classmethod
    def build(cls, executable: Type) -> "Report":
        r = Report(Frame("@EXE.SYSTEM-REPORT.?").add_parent("@ONT.SYSTEM-REPORT"))
        r.set_executable(executable)
        r.set_status(Report.Status.PENDING)
        r.set_timestamp(time.time_ns())
        return r

    def executable(self) -> Type:
        return self.anchor["EXECUTABLE"].singleton()

    def set_executable(self, executable: Type):
        self.anchor["EXECUTABLE"] = executable

    def status(self) -> Status:
        return self.anchor["STATUS"].singleton()

    def set_status(self, status: Status):
        self.anchor["STATUS"] = status

    def validation(self) -> bool:
        return self.anchor["VALIDATION"].singleton()

    def set_validation(self, validation: bool):
        self.anchor["VALIDATION"] = validation

    def timestamp(self) -> int:
        return self.anchor["TIMESTAMP"].singleton()

    def set_timestamp(self, timestamp: int):
        self.anchor["TIMESTAMP"] = timestamp

    def execution_exceptions(self) -> List[Exception]:
        return list(self.anchor["WITH-EXECUTION-EXCEPTION"])

    def add_execution_exception(self, exception: Exception):
        self.anchor["WITH-EXECUTION-EXCEPTION"] += exception
