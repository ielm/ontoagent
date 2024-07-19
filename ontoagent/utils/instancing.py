from ontoagent.utils.common import AnchoredObject
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Identifier import Identifier
from ontograph.Space import Space
from typing import Any, List, Set, Tuple, Union


def instanceof(
    target: Union[Frame, "Instantiable"],
    in_space: Union[str, Space],
    variables: dict = None,
) -> Frame:
    if isinstance(target, Instantiable):
        target = target.anchor

    if variables is None:
        variables = {}

    if isinstance(in_space, Space):
        in_space = in_space.name

    # Create the instance
    instance = _create_instance(target, in_space)
    _map_instance(instance, target, in_space, variables)

    return instance


def _create_instance(target: Frame, in_space: str) -> Frame:
    if isinstance(in_space, Space):
        in_space = in_space.name

    target_type = Identifier.parse(target.id)
    instance = Frame("@" + in_space + "." + target_type[1] + ".?")
    instance["INSTANCE-OF"] += target

    return instance


def _map_instance(instance: Frame, target: Frame, in_space: str, mapping: dict = None):
    if mapping is None:
        mapping = {}

    # Find all frames to be instanced
    tbi = _to_be_instanced(target, in_space)

    # Generate new frame instances if needed
    for hint in tbi:
        frame = hint[0]
        space = hint[1]

        if frame in mapping:
            continue

        subinstance = _create_instance(frame, space)
        mapping[frame] = subinstance

    # Build all varmaps
    for frame in mapping:
        Instantiable(instance).build_varmap(frame, mapping[frame])

    # Replace all local fillers with instanced fillers
    ancestors = list(graph.driver.ancestors(instance.id)) + [instance.id]
    for hint in tbi:
        frame = hint[0]

        rows = graph.driver.rows(frame=ancestors, filler=Identifier(frame.id))
        for row in rows:
            instance[row["slot"]][row["facet"]] -= frame
            instance[row["slot"]][row["facet"]] += mapping[frame]

    # Recursively populate subinstances
    for hint in tbi:
        frame = hint[0]
        subinstance = mapping[frame]
        _map_instance(
            subinstance,
            frame,
            in_space,
            mapping=_mappings_for_subinstance(instance, frame),
        )


def _to_be_instanced(target: Frame, in_space: str) -> List[Tuple[Frame, str]]:
    results = []

    for slot in target:
        for filler in slot:
            if (
                isinstance(filler, Frame)
                and filler.space() == "ONT"
                and Identifier.parse(filler.id)[2] is not None
            ):
                results.append((filler, "???"))

    for property in target["IS-INSTANTIABLE"]:
        for filler in target[property]:
            if isinstance(filler, Frame) and filler.id != "@ONT.EVENT":
                results.append((filler, in_space))

    return results


def _mappings_for_subinstance(
    domain: Union[Frame, "Instantiable"], range: Frame
) -> dict:
    results = _mappings_from_varmaps(domain)
    results.update(_mappings_from_bindings(domain, range))
    return results


def _mappings_from_varmaps(domain: Union[Frame, "Instantiable"]) -> dict:
    if isinstance(domain, Frame):
        domain = Instantiable(domain)

    results = {}

    for varmap in domain.varmaps():
        results[varmap.defined()] = varmap.realized()

    return results


def _mappings_from_bindings(domain: Union[Frame, "Instantiable"], range: Frame) -> dict:
    if isinstance(domain, Frame):
        domain = Instantiable(domain)

    results = {}

    for binding in domain.bindings():
        if binding.range() == range:
            varmap = domain.find_varmap_for_defined(binding.bind_local())
            results[binding.bind_to()] = varmap.realized()

    return results


class Instantiable(AnchoredObject):

    def instantiable_slots(self) -> Set[str]:
        return set(self.anchor["IS-INSTANTIABLE"])

    def add_instantiable_slot(self, slot: str):
        self.anchor["IS-INSTANTIABLE"] += slot

    def varmaps(self) -> List["VarMap"]:
        return list(map(lambda filler: VarMap(filler), self.anchor["HAS-VARMAP"]))

    def add_varmap(self, varmap: Union[Frame, "VarMap"]):
        if isinstance(varmap, VarMap):
            varmap = varmap.anchor
        self.anchor["HAS-VARMAP"] += varmap

    def build_varmap(
        self, defined: Frame, realized: Any, space: Union[str, Space] = "EXE"
    ) -> "VarMap":
        varmap = VarMap.build(defined, realized, space=space)
        self.add_varmap(varmap)
        return varmap

    def find_varmap_for_defined(self, defined: Frame) -> Union[None, "VarMap"]:
        for varmap in self.varmaps():
            if varmap.defined() == defined:
                return varmap
        return None

    def bindings(self) -> List["Binding"]:
        return list(map(lambda filler: Binding(filler), self.anchor["HAS-BINDING"]))

    def add_binding(self, binding: Union[Frame, "Binding"]):
        if isinstance(binding, Binding):
            binding = binding.anchor

        self.anchor["HAS-BINDING"] += binding

    def build_binding(
        self,
        range: Frame,
        bind_local: Frame,
        bind_to: Frame,
        space: Union[str, Space] = "SYS",
    ) -> "Binding":
        binding = Binding.build(range, bind_local, bind_to, space=space)
        self.add_binding(binding)
        return binding


class Binding(AnchoredObject):

    @classmethod
    def build(
        cls,
        range: Frame,
        bind_local: Frame,
        bind_to: Frame,
        space: Union[str, Space] = "SYS",
    ) -> "Binding":
        if isinstance(space, str):
            space = Space(space)

        frame = space.frame("@.BINDING.?")
        frame["INSTANCE-OF"] = Frame("@ONT.BINDING")

        binding = Binding(frame)
        binding.set_range(range)
        binding.set_bind_local(bind_local)
        binding.set_bind_to(bind_to)
        return binding

    def range(self) -> Frame:
        return self.anchor["RANGE"].singleton()

    def set_range(self, range: Frame):
        self.anchor["RANGE"] = range

    def bind_local(self) -> Frame:
        return self.anchor["BIND-LOCAL"].singleton()

    def set_bind_local(self, bind_from: Frame):
        self.anchor["BIND-LOCAL"] = bind_from

    def bind_to(self) -> Frame:
        return self.anchor["BIND-TO"].singleton()

    def set_bind_to(self, bind_to: Frame):
        self.anchor["BIND-TO"] = bind_to


class VarMap(AnchoredObject):

    @classmethod
    def build(
        cls, defined: Frame, realized: Any, space: Union[str, Space] = "EXE"
    ) -> "VarMap":
        if isinstance(space, str):
            space = Space(space)

        frame = space.frame("@.VARMAP.?")
        frame["INSTANCE-OF"] = Frame("@ONT.VARMAP")

        varmap = VarMap(frame)
        varmap.set_defined(defined)
        varmap.set_realized(realized)

        return varmap

    def defined(self) -> Frame:
        return self.anchor["DEFINED"].singleton()

    def set_defined(self, defined: Frame):
        self.anchor["DEFINED"] = defined

    def realized(self) -> Any:
        return self.anchor["REALIZED"].singleton()

    def set_realized(self, realized: Any):
        self.anchor["REALIZED"] = realized

    def __repr__(self):
        return self.defined().id + " -> " + self.realized().id
