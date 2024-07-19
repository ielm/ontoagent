from ontoagent.engine.signal import Signal, TMR, XMR
from ontoagent.utils.inputs import InputSignalSpeech
from ontoagent.utils.leia import ontosem_service
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.OntoLang import AssignOntoLangProcessor
from ontograph.Query import (
    AndComparator,
    ExistsComparator,
    InSpaceComparator,
    Query,
    SelectPipeline,
)
from typing import Any, List, Type, Union
import json
import re
import requests


class Analyzer(object):

    _cache = {}

    def __init__(self):
        self.header = "XMR"
        self.root_property = "XMR-ROOT"
        self.xmr_type = XMR

    @classmethod
    def register_analyzer(cls, analyzer: Type["Analyzer"]):
        Frame("@SYS.ANALYZER-REGISTRY")["HAS-ANALYZER"] += analyzer

    @classmethod
    def get_registered_analyzers(cls) -> List[Type["Analyzer"]]:
        return list(Frame("@SYS.ANALYZER-REGISTRY")["HAS-ANALYZER"])

    @classmethod
    def analyzer_for_signal(cls, signal: Signal) -> "Analyzer":
        for analyzer in Analyzer.get_registered_analyzers():
            analyzer = analyzer()
            if analyzer.is_appropriate(signal):
                return analyzer

        raise NotImplementedError

    def is_appropriate(self, signal: Signal) -> bool:
        raise NotImplementedError

    def to_signal(self, input: Any) -> XMR:

        ontolang = self.analyze(input)
        space = Signal.next_available_space(self.header)
        ontolang = ontolang.replace("@[" + self.header + "].", "@%s." % space.name)

        # Parse the ontolang
        processors = graph.ontolang().parse(ontolang)

        # Run each processor, retaining any explicitly declared frames as constituents
        constituents = []
        script = graph.ontolang().generate_script()
        for processor in processors:
            result = processor.run_with_script(script)
            if isinstance(processor, AssignOntoLangProcessor):
                constituents.append(result)

        # Identify the root
        query = Query(
            Query.AND(
                Query.inspace(space), Query.exists(slot=self.root_property, filler=True)
            )
        )
        results = query.start()
        if len(results) != 1:
            raise Exception("No single root identified for %s." % self.header)
        root = results[0]

        # Build the XMR
        xmr = self.xmr_type.build(root, space=space, constituents=constituents)
        return xmr

    def cache(self, input: Any, ontolang: str):
        Analyzer._cache[input] = ontolang

    def lookup(self, input: Any) -> Union[str, None]:
        if input in Analyzer._cache:
            return Analyzer._cache[input]
        return None

    def analyze(self, input: Any) -> str:
        ontolang = self.lookup(input)
        if ontolang is None:
            ontolang = self._analyze(input)
            self.cache(input, ontolang)
        return ontolang

    def _analyze(self, input: Any) -> str:
        raise NotImplementedError


class TextAnalyzer(Analyzer):

    def __init__(self):
        super().__init__()
        self.header = "TMR"
        self.root_property = "TMR-ROOT"
        self.xmr_type = TMR

    def is_appropriate(self, signal: Signal) -> bool:
        return signal.root() ^ Frame("@ONT.SPEECH-ACT") and signal.root()[
            "THEME"
        ].singleton() ^ Frame("@ONT.RAW-TEXT")

    def _analyze(self, input: Union[str, InputSignalSpeech]) -> str:
        if isinstance(input, InputSignalSpeech):
            input = input.text()

        analyzed = self._text_analysis_call_ontosem_service(input)
        formatted = self._text_analysis_format_ontosem_results_to_ontolang(analyzed)
        return formatted

    def _text_analysis_call_ontosem_service(self, input: str) -> dict:
        response = requests.post(
            url=ontosem_service() + "/analyze", data={"text": input}
        )
        return json.loads(response.text)

    def _text_analysis_format_ontosem_results_to_ontolang(self, ontosem: dict) -> str:
        tmr = ontosem["tmr"][0]["results"][0]["TMR"]

        inverses = (
            Query(
                AndComparator(
                    [InSpaceComparator("ONT"), ExistsComparator(slot="INVERSE")]
                )
            )
            .flatten()
            .filter(str)
            .select(SelectPipeline.Column.FILLER)
            .start()
        )

        found_ids = set()
        built_ids = set()

        out = ""

        def _fix_frame_id(frame: str) -> str:
            instance = re.findall(r"-([0-9]+)$", frame)[0]
            frame_id = re.sub(r"-[0-9]+$", ".%s?" % instance, frame)
            frame_id = "@[TMR].%s" % frame_id

            found_ids.add(frame_id)
            return frame_id

        def _convert_value(property, value):
            if isinstance(value, str):
                if value == "HUMAN":
                    value = "@[TMR].HUMAN.1?"
                    found_ids.add(value)
                    return value
                if value == "ROBOT":
                    value = "@[TMR].ROBOT.1?"
                    found_ids.add(value)
                    return value
                if Frame("@ONT.%s" % property.upper()) ^ Frame("@ONT.RELATION"):
                    return _fix_frame_id(value)
                return '"%s"' % value
            return value

        def _convert_frame(frame: str, contents: dict) -> str:
            frame_id = _fix_frame_id(frame)
            built_ids.add(frame_id)

            properties = ["IS-A @ONT.%s;" % contents["concept"]]
            for key in contents.keys():
                if key.lower() == key:
                    continue
                if key.lower() in inverses:
                    continue
                values = contents[key]
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    properties.append("%s %s;" % (key, _convert_value(key, value)))

            return "%s = {\n%s\n};" % (
                frame_id,
                "\n".join(map(lambda property: "\t" + property, properties)),
            )

        for key in tmr.keys():
            if key.lower() == key:
                continue  # Skip non-frame elements

            out += _convert_frame(key, tmr[key]) + "\n"

        for found_id in found_ids.difference(built_ids):
            isa = re.findall(r"\.(.*)\.", found_id)[0]
            out += "%s = { IS-A @ONT.%s; };\n" % (found_id, isa)

        return out
