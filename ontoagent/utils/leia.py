import os

MONGO_HOST = os.environ["MONGO_HOST"] if "MONGO_HOST" in os.environ else "localhost"
MONGO_PORT = int(os.environ["MONGO_PORT"]) if "MONGO_PORT" in os.environ else 27017

ONTOLOGY_HOST = (
    os.environ["ONTOLOGY_HOST"] if "ONTOLOGY_HOST" in os.environ else "localhost"
)
ONTOLOGY_PORT = (
    int(os.environ["ONTOLOGY_PORT"]) if "ONTOLOGY_PORT" in os.environ else 5003
)
ONTOLOGY_DATABASE = (
    os.environ["ONTOLOGY_DATABASE"]
    if "ONTOLOGY_DATABASE" in os.environ
    else "leia-ontology"
)
ONTOLOGY_COLLECTION = (
    os.environ["ONTOLOGY_COLLECTION"]
    if "ONTOLOGY_COLLECTION" in os.environ
    else "robot-v.1.0.0"
)

networking = {
    "ontogen-host": (
        os.environ["ONTOGEN_HOST"] if "ONTOGEN_HOST" in os.environ else "localhost"
    ),
    "ontogen-port": (
        os.environ["ONTOGEN_PORT"] if "ONTOGEN_PORT" in os.environ else "5005"
    ),
    "ontosem-host": (
        os.environ["ONTOSEM_HOST"] if "ONTOSEM_HOST" in os.environ else "localhost"
    ),
    "ontosem-port": (
        os.environ["ONTOSEM_PORT"] if "ONTOSEM_PORT" in os.environ else "5000"
    ),
    "robot-host": (
        os.environ["ROBOT_HOST"] if "ROBOT_HOST" in os.environ else "localhost"
    ),
    "robot-port": os.environ["ROBOT_PORT"] if "ROBOT_PORT" in os.environ else "7777",
}


def ontogen_service():
    return "http://" + networking["ontogen-host"] + ":" + networking["ontogen-port"]


def ontosem_service():
    return "http://" + networking["ontosem-host"] + ":" + networking["ontosem-port"]


def robot_service():
    return "http://" + networking["robot-host"] + ":" + networking["robot-port"]


##### Individual APIs


def ontosem_analyze_endpoint():
    return ontosem_service() + "/analyze"
