from ontoagent.utils.common import StoppableThread


class HeartbeatThread(StoppableThread):

    def __init__(self, host, port):
        self.endpoint = "http://" + str(host) + ":" + str(port) + "/heartbeat/pulse"
        super().__init__()

    def run(self):
        while not self.stopped():

            import time

            time.sleep(0.25)

            import urllib.request

            contents = urllib.request.urlopen(self.endpoint, []).read()
