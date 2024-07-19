from ontoagent.utils.ontolang import OntoAgentOntoLang
from ontograph import graph


class KnowledgeLoader(object):

    loaded = []

    @classmethod
    def load_script(cls, script: str):
        graph.ontolang().run(script)

    @classmethod
    def load_resource(cls, package: str, file: str):
        ontolang: OntoAgentOntoLang = graph.ontolang()
        ontolang.load_knowledge(package, file)
        KnowledgeLoader.loaded.append(package + "." + file)

    @classmethod
    def list_resources(cls, package: str):
        from pkg_resources import resource_listdir

        return list(
            map(
                lambda f: (package, f),
                filter(
                    lambda f: f.endswith(".knowledge") or f.endswith(".environment"),
                    resource_listdir(package, ""),
                ),
            )
        )

    @classmethod
    def list_all_resources(cls):
        from pathlib import Path

        resources = list(Path(".").rglob("*.knowledge"))

        def resource_to_package(resource):
            return ".".join(resource._parts[0:-1])

        def resource_to_filename(resource):
            return resource._parts[-1]

        resources = list(
            map(lambda r: (resource_to_package(r), resource_to_filename(r)), resources)
        )
        return list(filter(lambda r: not r[0].startswith("build."), resources))
