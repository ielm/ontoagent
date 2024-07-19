from ontoagent.utils.common import AnchoredObject
from ontograph.Frame import Frame
from ontograph.Identifier import Identifier
from typing import Any, List, Union


def does_state_exist(frame: Frame) -> bool:
    if frame ^ Frame("@ONT.EVENT"):
        return _is_event_satisfied(frame)
    if frame ^ Frame("@ONT.EFFECT"):
        return _is_effect_perceived(frame)
    return False


def _is_event_satisfied(event: Frame) -> bool:
    if PhasedEvent(event).is_ended():
        return True
    candidates = _find_similar_events(event)
    candidates = filter(lambda candidate: PhasedEvent(candidate).is_ended(), candidates)
    return len(list(candidates)) > 0


def _find_similar_events(event: Frame) -> List[Frame]:
    parents = event.parents()

    candidates = []
    for parent in parents:
        candidates += parent.descendants()

    case_roles = map(
        lambda cr: Identifier.parse(cr.id)[1], Frame("@ONT.CASE-ROLE").children()
    )
    case_roles = filter(lambda case_role: case_role in event, case_roles)
    case_roles = list(case_roles)

    def _is_filler_found(candidate: Frame, property: str, filler: Any) -> bool:
        if isinstance(filler, Frame):
            fillers = list(filter(lambda f: isinstance(f, Frame), candidate[property]))
            if filler in fillers:
                return True
            for f in fillers:
                if f in filler.descendants():
                    return True
            return False
        else:
            return filler in candidate[property]

    def _check_case_roles(candidate: Frame) -> bool:
        for case_role in case_roles:
            for filler in event[case_role]:
                if not _is_filler_found(candidate, case_role, filler):
                    return False
        return True

    candidates = filter(lambda candidate: _check_case_roles(candidate), candidates)
    candidates = filter(lambda candidate: candidate != event, candidates)

    return list(candidates)


def _is_effect_perceived(effect: Frame) -> bool:
    raise NotImplementedError


class PhasedEvent(AnchoredObject):

    def phase(self) -> Union[None, str]:
        if "PHASE" in self.anchor:
            return self.anchor["PHASE"].singleton()
        return None

    def set_phase(self, phase: str):
        self.anchor["PHASE"] = phase

    def set_ended(self):
        self.set_phase("END")

    def is_ended(self) -> bool:
        return self.phase() == "END"
