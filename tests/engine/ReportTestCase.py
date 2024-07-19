from ontoagent.engine.report import Report
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase, TestableExecutable


class ReportTestCase(OntoAgentTestCase):

    def test_executable(self):
        r = Frame("@TEST.REPORT.?")
        r["EXECUTABLE"] = TestableExecutable
        self.assertEqual(TestableExecutable, Report(r).executable())

    def test_set_executable(self):
        r = Frame("@TEST.REPORT.?")
        Report(r).set_executable(TestableExecutable)
        self.assertEqual(TestableExecutable, r["EXECUTABLE"])

    def test_status(self):
        r = Frame("@TEST.REPORT.?")
        r["STATUS"] = Report.Status.PENDING
        self.assertEqual(Report.Status.PENDING, Report(r).status())

    def test_set_status(self):
        r = Frame("@TEST.REPORT.?")
        Report(r).set_status(Report.Status.PENDING)
        self.assertEqual(Report.Status.PENDING, r["STATUS"])

    def test_validation(self):
        r = Frame("@TEST.REPORT.?")
        r["VALIDATION"] = True
        self.assertEqual(True, Report(r).validation())

    def test_set_validation(self):
        r = Frame("@TEST.REPORT.?")
        Report(r).set_validation(True)
        self.assertEqual(True, r["VALIDATION"])

    def test_timestamp(self):
        r = Frame("@TEST.REPORT.?")
        r["TIMESTAMP"] = 1234

        self.assertEqual(1234, Report(r).timestamp())

    def test_set_timestamp(self):
        r = Frame("@TEST.REPORT.?")

        self.assertEqual([], r["TIMESTAMP"])
        Report(r).set_timestamp(1234)
        self.assertEqual(1234, r["TIMESTAMP"])

    def test_execution_exception(self):
        r = Frame("@TEST.REPORT.?")
        self.assertEqual([], Report(r).execution_exceptions())

        e = Exception("Something went wrong.")

        r["WITH-EXECUTION-EXCEPTION"] = e

        self.assertEqual(1, len(Report(r).execution_exceptions()))
        self.assertEqual(type(e), type(Report(r).execution_exceptions()[0]))
        self.assertEqual(e.args, Report(r).execution_exceptions()[0].args)

    def test_add_execution_exception(self):
        r = Frame("@TEST.REPORT.?")
        e1 = Exception("Something went wrong 1.")
        e2 = Exception("Something went wrong 2.")

        self.assertEqual([], r["WITH-EXECUTION-EXCEPTION"])

        Report(r).add_execution_exception(e1)

        self.assertEqual(1, len(Report(r).execution_exceptions()))
        self.assertEqual(type(e1), type(Report(r).execution_exceptions()[0]))
        self.assertEqual(e1.args, Report(r).execution_exceptions()[0].args)

        Report(r).add_execution_exception(e2)

        self.assertEqual(2, len(Report(r).execution_exceptions()))
        self.assertEqual(type(e2), type(Report(r).execution_exceptions()[1]))
        self.assertEqual(e2.args, Report(r).execution_exceptions()[1].args)
