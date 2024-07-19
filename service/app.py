from flask import Flask, request, abort, render_template
from flask_cors import CORS
from flask_socketio import SocketIO
from ontoagent.agent import Agent
from ontoagent.engine.report import Report
from ontoagent.engine.signal import Signal, XMR
from ontoagent.utils.instancing import instanceof, Instantiable
from ontoagent.utils.loader import KnowledgeLoader
from ontoagent.views.agenda import Impasse
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Space import Space
from service.heartbeat import HeartbeatThread
from service.input import input_speech
from service.payload import Payload
from typing import List
import json
import sys


app = Flask(
    __name__, template_folder="templates/", static_folder="static/", static_url_path=""
)
CORS(app)
socketio = SocketIO(app)

_agent = None
_heartbeat = None

# ---- Maintenance -----


@app.after_request
def close_ontograph_connect(response):
    # Each request is a separate thread, so we explicitly
    # close those connections in this environment.
    graph.driver.close_connection()
    return response


# ---- Heartbeat -----


def emit_pulse_payload():
    payload = {
        "agenda": Payload.output_agenda(_agent.agenda()),
        "running": not _thread.stopped() and _thread.is_alive(),
    }
    socketio.emit("heartbeat pulsed", payload)


@app.route("/heartbeat/pulse", methods=["POST"])
def heartbeat_pulse():
    _agent.background()

    emit_pulse_payload()

    return "OK"


@app.route("/heartbeat/start", methods=["POST"])
def heartbeat_start():
    global _thread

    if _thread.is_alive():
        abort(400)

    _thread = HeartbeatThread(host, port)
    _thread.start()

    return "OK"


@app.route("/heartbeat/stop", methods=["POST"])
def heartbeat_stop():
    _thread.stop()

    return "OK"


# ---- Agent Signaling -----


@app.route("/input", methods=["POST"])
def input():
    # TODO signal = ... parse from POST

    signal = XMR.build(Frame("@TEST.FRAME.?").add_parent(Frame("@ONT.FRAME")))
    _agent.input(signal)

    emit_pulse_payload()

    return "OK"


@app.route("/signal/release", methods=["POST"])
def signal_release():
    if not request.get_json():
        abort(400)

    data = request.get_json()
    effector = Frame(data["effector"])

    variable = Frame("@ONT.RELEASE-EFFECTOR")["THEME"].singleton()

    space = XMR.next_available_space("RMR")
    root = instanceof(
        Frame("@ONT.RELEASE-EFFECTOR"), in_space=space, variables={variable: effector}
    )
    mmr = XMR.build(root, anchor="@IO.RMR.?", space=space)
    _agent.input(mmr)

    emit_pulse_payload()

    return "OK"


@app.route("/signal/speech", methods=["POST"])
def signal_speech():
    if not request.get_json():
        abort(400)

    data = request.get_json()
    signal = input_speech(data)
    _agent.input(signal)

    emit_pulse_payload()

    return json.dumps({"signal": "speech received"})


# ---- API -----


@app.route("/api/agenda", methods=["GET"])
def api_agenda():
    payload = Payload.output_agenda(_agent.agenda())
    return json.dumps(payload)


@app.route("/api/impasse", methods=["GET"])
def api_impasse():
    impasse = Payload.output_impasse(Impasse(Frame(request.args["id"])))
    return json.dumps(impasse)


@app.route("/api/signals", methods=["GET"])
def api_queue():
    queue = Payload.output_signals(status=Signal.Status[request.args["status"]])
    return json.dumps(queue)


@app.route("/api/report", methods=["GET"])
def api_report():
    report = Payload.output_report(Report(Frame(request.args["id"])))
    return json.dumps(report)


@app.route("/api/signal", methods=["GET"])
def api_signal():
    signal = Signal(Frame(request.args["id"]))

    payload = {
        "signal-anchor": Payload.output_signal_anchor(signal),
        "signal-contents": Payload.output_signal_contents(signal),
    }
    return json.dumps(payload)


@app.route("/api/frame", methods=["GET"])
def api_frame():
    frame = Frame(request.args["id"])

    payload = Payload.output_frame(frame)
    return json.dumps(payload)


# ---- OntoLang ----


@app.route("/ontolang/execute", methods=["POST"])
def ontolang_execute():
    if not request.get_json():
        abort(400)

    data = request.get_json()

    payload = {"message": "OK", "frames": [], "success": True}

    try:
        result = graph.ontolang().run(data["ontolang"])
        if (
            isinstance(result, list)
            and len(result) > 0
            and isinstance(result[0], Frame)
        ):
            payload["message"] = "%d frames found:" % len(result)
            payload["frames"] = list(map(lambda f: Payload.output_frame(f), result))
    except Exception as e:
        payload["message"] = str(e)
        payload["success"] = False

    return json.dumps(payload)


@app.route("/ontolang/load", methods=["POST"])
def ontolang_load():
    if not request.get_json():
        abort(400)

    data = request.get_json()

    KnowledgeLoader.load_resource(data["package"], data["file"])

    payload = Payload.output_knowledge_resources()
    return json.dumps(payload)


# ---- Demo -----


@app.route("/demo/agenda/add_goal", methods=["POST"])
def api_agenda_add_goal():
    if not request.get_json():
        abort(400)

    data = request.get_json()

    from ontoagent.knowledge.operations.agenda import AddGoalInstanceExecutable

    class DemoAddGoalInstanceExecutable(AddGoalInstanceExecutable):

        def __init__(self, definition: Frame, variables: dict, subgoal_of: List[Frame]):
            self.definition = definition
            self.variables = variables
            self.subgoal_of = subgoal_of

        def _instance_goal(self, signal: Signal) -> Frame:
            goal = instanceof(self.definition, "AGENDA", variables=self.variables)
            return goal

        def _subgoal_of(self, signal: Signal) -> List[Frame]:
            return self.subgoal_of

    definition = Frame(data["definition"])

    variables = {}
    for k in data["variables"]:
        variables[Frame(k)] = Frame(data["variables"][k])

    subgoal_of = list(map(lambda subgoal: Frame(subgoal), data["subgoal_of"]))

    DemoAddGoalInstanceExecutable(definition, variables, subgoal_of).run()

    emit_pulse_payload()

    return json.dumps({"demo": "goal directly added"})


# ---- UI -----


@app.route("/ui/agenda", methods=["GET"])
def ui_agenda():
    payload = {
        "agenda": Payload.output_agenda(_agent.agenda()),
        "goal-definitions": list(
            map(lambda definition: definition.id, list(Space("GOALS")))
        ),
    }

    return render_template("agenda.html", payload=json.dumps(payload))


@app.route("/ui/memory", methods=["GET"])
def ui_memory():
    payload = {}

    return render_template("memory.html", payload=json.dumps(payload))


@app.route("/ui/ontolang", methods=["GET"])
def ui_ontolang():
    payload = {"knowledge": Payload.output_knowledge_resources()}

    return render_template("ontolang.html", payload=json.dumps(payload))


@app.route("/ui/signals", methods=["GET"])
def ui_signals():
    payload = {"signals": Payload.output_signals()}

    return render_template("signals.html", payload=json.dumps(payload))


# ---- Application -----

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5009

    for arg in sys.argv:
        if "=" in arg:
            k = arg.split("=")[0]
            v = arg.split("=")[1]

            if k == "host":
                host = v
            if k == "port":
                port = int(v)

    Agent.auto_join = True

    from ontograph.drivers.SQLiteDriver import SQLiteDriver

    graph.driver = SQLiteDriver()

    from ontoagent.utils.ontology import OntologyOntoLangLoader

    _agent = Agent.build(
        ontology_loader=OntologyOntoLangLoader(
            "tests.resources", "OntoAgentTestOntology.knowledge"
        )
    )
    _thread = HeartbeatThread(host, port)

    # -- LOAD AND SETUP A PARTICULAR DEMO HERE IF DESIRED -- #

    # ------------------------------------------------------ #

    Agent.auto_join = False

    socketio.run(app, host=host, port=port, debug=False)
