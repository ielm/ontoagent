from ontograph.Frame import Frame
import threading


class AnchoredObject(object):

    def __init__(self, anchor: Frame):
        self.anchor = anchor

    def __eq__(self, other):
        if isinstance(other, AnchoredObject):
            return self.anchor == other.anchor
        if isinstance(other, Frame):
            return self.anchor == other
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.anchor.id)


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
