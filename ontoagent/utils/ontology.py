from ontoagent.utils.leia import (
    MONGO_HOST,
    MONGO_PORT,
    ONTOLOGY_COLLECTION,
    ONTOLOGY_DATABASE,
)
from ontoagent.utils.loader import KnowledgeLoader
from ontograph import graph
from ontograph.Identifier import Identifier
from pymongo import MongoClient


class OntologyLoader(object):

    def load(self):
        raise NotImplementedError


class OntologyNullLoader(OntologyLoader):

    def load(self):
        pass


class OntologyOntoLangLoader(OntologyLoader):

    def __init__(self, package: str, file: str):
        self.package = package
        self.file = file

    def load(self):
        KnowledgeLoader.load_resource(self.package, self.file)


class OntologyServiceLoader(OntologyLoader):

    def load(self):
        self.__import_graph()

    def __get_client(self, host: str, port: int) -> MongoClient:
        client = MongoClient(host, port)
        with client:
            return client

    def __get_handle(self):
        client = self.__get_client(MONGO_HOST, MONGO_PORT)
        db = client[ONTOLOGY_DATABASE]
        return db[ONTOLOGY_COLLECTION]

    def __list_concepts(self, handle):
        concepts = list(handle.find({}))
        return concepts

    def __import_graph(self):

        driver = graph.driver
        driver.disable_auto_commit()

        handle = self.__get_handle()
        concepts = self.__list_concepts(handle)
        all = set(map(lambda c: c["name"], concepts))

        for c in concepts:
            name = "@ONT." + c["name"].upper()
            for parent in c["parents"]:
                parent = Identifier("@ONT." + parent.upper())
                driver.add_row(name, "IS-A", "SEM", parent)
            for prop in c["localProperties"]:
                filler = prop["filler"]
                if filler in all:
                    filler = Identifier("@ONT." + filler.upper())
                driver.add_row(
                    name, prop["slot"].upper(), prop["facet"].upper(), filler
                )

        driver.enable_auto_commit(commit_now=True)
