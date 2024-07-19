from ontograph.OntoLang import OntoLang, OntoLangScript, OntoLangTransformer
from typing import Type
import sys


class OntoAgentOntoLang(OntoLang):

    cached_processors = {}

    def __init__(self):
        super().__init__()
        self.resources.insert(0, ("ontoagent.utils.resources", "ontoagent.lark"))

    def get_transformer_type(self):
        return OntoAgentOntoLangTransformer

    def load_knowledge(self, package: str, resource: str):
        from pkgutil import get_data

        input: str = get_data(package, resource).decode("ascii")

        if package + "." + resource in OntoAgentOntoLang.cached_processors:
            processors = OntoAgentOntoLang.cached_processors[package + "." + resource]
        else:
            processors = self.parse(input)
            OntoAgentOntoLang.cached_processors[package + "." + resource] = processors

        script = OntoLangScript()
        for p in processors:
            p.run_with_script(script=script)


class OntoAgentOntoLangTransformer(OntoLangTransformer):

    def clazz(self, matches) -> Type:
        index = matches[0].rfind(".")
        module = matches[0][0:index]
        clazz = matches[0][index + 1 :]
        __import__(module)

        return getattr(sys.modules[module], clazz)
