from ontoagent.utils.instancing import (
    instanceof,
    _map_instance,
    _mappings_from_bindings,
    _mappings_from_varmaps,
    _mappings_for_subinstance,
    _to_be_instanced,
)
from ontoagent.utils.instancing import Binding, Instantiable, VarMap
from ontograph.Frame import Frame
from tests.OntoAgentTestCase import OntoAgentTestCase
from unittest.mock import call, patch


class InstanceTestCase(OntoAgentTestCase):

    def test_instance_simple(self):
        f = Frame("@ONT.FRAME")
        i = instanceof(f, "TEST")

        self.assertEqual("@TEST.FRAME.1", i.id)
        self.assertEqual(f, i["INSTANCE-OF"])
        self.assertIn(f, i.parents())

    def test_instance_with_subinstances(self):
        f = Frame("@ONT.FRAME")
        o1 = Frame("@ONT.SUB.?")
        o2 = Frame("@ONT.SUB.?")

        f["X"] += o1
        f["Y"] += o2
        i = instanceof(f, "TEST")

        self.assertIn(o1, i["X"][0].parents())
        self.assertIn(o2, i["Y"][0].parents())

    def test_instance_with_multiple_fillers_per_slot(self):
        f = Frame("@ONT.FRAME")
        o1 = Frame("@ONT.SUB.?")
        o2 = Frame("@ONT.SUB.?")

        f["X"] = [o1, o2]
        i = instanceof(f, "TEST")

        self.assertEqual(2, len(list(i["X"])))
        parents = list(map(lambda sub: sub.parents()[0], i["X"]))
        self.assertIn(o1, parents)
        self.assertIn(o2, parents)


class MapInstanceTestCase(OntoAgentTestCase):

    def test_input_mappings_replace_specified_instances(self):
        target = Frame("@TEST.FRAME")
        instance = Frame("@TEST.FRAME.?").add_parent(target)
        inst1 = Frame("@ONT.FRAME.?")
        inst2 = Frame("@ONT.FRAME.?")
        realized1 = Frame("@???.FRAME.?")
        realized2 = Frame("@???.FRAME.?")

        target["AGENT"] = inst1
        target["THEME"] = inst2

        mapping = {inst1: realized1, inst2: realized2}
        _map_instance(instance, target, "TEST", mapping)

        self.assertEqual([realized1], instance["AGENT"])
        self.assertEqual([realized2], instance["THEME"])

        varmaps = Instantiable(instance).varmaps()
        self.assertEqual(2, len(varmaps))
        self.assertIn(
            (inst1, realized1),
            list(map(lambda varmap: (varmap.defined(), varmap.realized()), varmaps)),
        )
        self.assertIn(
            (inst2, realized2),
            list(map(lambda varmap: (varmap.defined(), varmap.realized()), varmaps)),
        )

    @patch("ontoagent.utils.instancing._to_be_instanced")
    def test_unmapped_instances_are_generated_in_specified_space(
        self, mock_to_be_instanced
    ):
        target = Frame("@TEST.FRAME")
        instance = Frame("@TEST.FRAME.?").add_parent(target)
        inst1 = Frame("@ONT.FRAME.?")
        inst2 = Frame("@ONT.FRAME.?")

        target["AGENT"] = inst1
        target["THEME"] = inst2

        def _mock_to_be_instanced(t: Frame, in_space: str):
            if t == target:
                return [(inst1, "???"), (inst2, "TEST")]
            return []

        mock_to_be_instanced.side_effect = _mock_to_be_instanced

        _map_instance(instance, target, "TEST", {})

        self.assertEqual("???", instance["AGENT"].singleton().space())
        self.assertEqual("TEST", instance["THEME"].singleton().space())

    def test_input_mappings_not_found_are_still_added_as_varmaps(self):
        target = Frame("@TEST.FRAME")
        instance = Frame("@TEST.FRAME.?").add_parent(target)

        inst1 = Frame("@ONT.FRAME.?")
        realized1 = Frame("@???.FRAME.?")
        mapping = {inst1: realized1}

        _map_instance(instance, target, "TEST", mapping)

        varmaps = Instantiable(instance).varmaps()
        self.assertEqual(1, len(varmaps))
        self.assertIn(
            (inst1, realized1),
            list(map(lambda varmap: (varmap.defined(), varmap.realized()), varmaps)),
        )

    @patch("ontoagent.utils.instancing._map_instance")
    @patch("ontoagent.utils.instancing._mappings_for_subinstance")
    def test_generated_subinstances_are_recursively_mapped(
        self, mock_mappings_for_subinstance, mock_map_instance
    ):
        target = Frame("@TEST.FRAME")
        instance = Frame("@TEST.FRAME.?").add_parent(target)
        inst1 = Frame("@ONT.FRAME.?")

        target["AGENT"] = inst1

        mappings = {target: 123}
        mock_map_instance.side_effect = _map_instance
        mock_mappings_for_subinstance.return_value = mappings

        mock_map_instance(instance, target, "TEST")

        self.assertEqual(2, mock_map_instance.call_count)
        mock_map_instance.assert_has_calls(
            [
                call(instance, target, "TEST"),
                call(Frame("@???.FRAME.1"), inst1, "TEST", mapping=mappings),
            ]
        )


class ToBeInstancedTestCase(OntoAgentTestCase):

    def test_to_be_instanced_finds_all_normal_onto_instances(self):
        f = Frame("@ONT.FRAME")
        o1 = Frame("@ONT.TEST.?")
        o2 = Frame("@ONT.TEST.?")

        f["X"] = o1
        f["Y"]["FACET"] = o2

        self.assertEqual({(o1, "???"), (o2, "???")}, set(_to_be_instanced(f, "TEST")))

    def test_to_be_instanced_ignores_all_non_onto_instances(self):
        f = Frame("@ONT.FRAME")
        o1 = Frame("@ONT.TEST.?")
        o2 = Frame("@ONT.TEST")

        f["X"] = o1
        f["Y"]["FACET"] = o2

        self.assertEqual([(o1, "???")], _to_be_instanced(f, "TEST"))

    def test_to_be_instanced_finds_all_is_instanced_fillers(self):
        f = Frame("@ONT.FRAME")
        o1 = Frame("@ONT.A")
        o2 = Frame("@ONT.B")

        f["IS-INSTANTIABLE"] = "X"
        f["X"] = o1
        f["Y"] = o2

        self.assertEqual([(o1, "TEST")], _to_be_instanced(f, "TEST"))

    def test_to_be_instanced_ignores_all_non_instanced(self):
        f = Frame("@ONT.FRAME")
        o1 = Frame("@ONT.A")
        o2 = Frame("@ONT.B")

        f["X"] = o1
        f["Y"] = o2

        self.assertEqual([], _to_be_instanced(f, "TEST"))

    def test_to_be_instanced_ignores_all_non_frames(self):
        f = Frame("@ONT.FRAME")

        f["IS-INSTANTIABLE"] = "X"
        f["X"] = 1
        f["Y"] = True

        self.assertEqual([], _to_be_instanced(f, "TEST"))


class MappingsForSubInstanceTestCase(OntoAgentTestCase):

    @patch("ontoagent.utils.instancing._mappings_from_bindings")
    @patch("ontoagent.utils.instancing._mappings_from_varmaps")
    def test_mappings_for_subinstance_combines_varmaps_and_bindings(
        self, mock_mappings_from_varmaps, mock_mappings_from_bindings
    ):
        domain = Frame("@TEST.FRAME.?")
        range = Frame("@TEST.FRAME.?")

        f1 = Frame("@ONT.FRAME.?")
        f2 = Frame("@ONT.FRAME.?")
        inst1 = Frame("@???.FRAME.?")
        inst2 = Frame("@???.FRAME.?")

        mock_mappings_from_varmaps.return_value = {f1: inst1}
        mock_mappings_from_bindings.return_value = {f2: inst2}

        results = _mappings_for_subinstance(domain, range)
        self.assertEqual({f1: inst1, f2: inst2}, results)

        mock_mappings_from_bindings.assert_called_once_with(domain, range)
        mock_mappings_from_varmaps.assert_called_once_with(domain)

    @patch("ontoagent.utils.instancing._mappings_from_bindings")
    @patch("ontoagent.utils.instancing._mappings_from_varmaps")
    def test_mappings_for_subinstance_overrides_varmaps_with_bindings(
        self, mock_mappings_from_varmaps, mock_mappings_from_bindings
    ):
        domain = Frame("@TEST.FRAME.?")
        range = Frame("@TEST.FRAME.?")

        f1 = Frame("@ONT.FRAME.?")
        f2 = Frame("@ONT.FRAME.?")
        inst1 = Frame("@???.FRAME.?")
        inst2 = Frame("@???.FRAME.?")

        mock_mappings_from_varmaps.return_value = {f1: inst1}
        mock_mappings_from_bindings.return_value = {f1: inst2}

        results = _mappings_for_subinstance(domain, range)
        self.assertEqual({f1: inst2}, results)

        mock_mappings_from_bindings.assert_called_once_with(domain, range)
        mock_mappings_from_varmaps.assert_called_once_with(domain)


class MappingsFromVarmapsTestCase(OntoAgentTestCase):

    def test_mappings_from_varmaps(self):
        instance = Instantiable(Frame("@ONT.TEST.?"))

        ontoinstance1 = Frame("@ONT.OBJECT.?")
        ontoinstance2 = Frame("@ONT.OBJECT.?")
        grounded1 = Frame("@???.OBJECT.?")
        grounded2 = Frame("@???.OBJECT.?")

        instance.build_varmap(ontoinstance1, grounded1)
        instance.build_varmap(ontoinstance2, grounded2)

        results = _mappings_from_varmaps(instance)
        self.assertEqual({ontoinstance1: grounded1, ontoinstance2: grounded2}, results)


class MappingsFromBindingsTestCase(OntoAgentTestCase):

    def test_mappings_from_bindings(self):
        instance = Instantiable(Frame("@ONT.TEST.?"))
        sub1 = Frame("@ONT.TEST.?")
        sub2 = Frame("@ONT.TEST.?")

        ontoinstance1 = Frame("@ONT.OBJECT.?")
        ontoinstance2 = Frame("@ONT.OBJECT.?")
        grounded1 = Frame("@???.OBJECT.?")
        grounded2 = Frame("@???.OBJECT.?")

        sub_ontoinstance1 = Frame("@ONT.OBJECT.?")
        sub_ontoinstance2 = Frame("@ONT.OBJECT.?")

        instance.build_varmap(ontoinstance1, grounded1)
        instance.build_varmap(ontoinstance2, grounded2)

        instance.build_binding(sub1, ontoinstance1, sub_ontoinstance1)
        instance.build_binding(sub1, ontoinstance2, sub_ontoinstance2)
        instance.build_binding(sub2, ontoinstance1, sub_ontoinstance2)

        results = _mappings_from_bindings(instance, sub1)
        self.assertEqual(
            {sub_ontoinstance1: grounded1, sub_ontoinstance2: grounded2}, results
        )

        results = _mappings_from_bindings(instance, sub2)
        self.assertEqual({sub_ontoinstance2: grounded1}, results)


class BindingTestCase(OntoAgentTestCase):

    def test_range(self):
        f = Frame("@SYS.BINDING.?")
        o = Frame("@TEST.OBJECT.?")

        f["RANGE"] = o

        self.assertEqual(o, Binding(f).range())

    def test_set_range(self):
        f = Frame("@SYS.BINDING.?")
        o = Frame("@TEST.OBJECT.?")

        self.assertEqual([], f["RANGE"])

        Binding(f).set_range(o)

        self.assertEqual(o, f["RANGE"])

    def test_bind_local(self):
        f = Frame("@SYS.BINDING.?")
        o = Frame("@TEST.OBJECT.?")

        f["BIND-LOCAL"] = o

        self.assertEqual(o, Binding(f).bind_local())

    def test_set_bind_local(self):
        f = Frame("@SYS.BINDING.?")
        o = Frame("@TEST.OBJECT.?")

        self.assertEqual([], f["BIND-LOCAL"])

        Binding(f).set_bind_local(o)

        self.assertEqual(o, f["BIND-LOCAL"])

    def test_bind_to(self):
        f = Frame("@SYS.BINDING.?")
        o = Frame("@TEST.OBJECT.?")

        f["BIND-TO"] = o

        self.assertEqual(o, Binding(f).bind_to())

    def test_set_bind_to(self):
        f = Frame("@SYS.BINDING.?")
        o = Frame("@TEST.OBJECT.?")

        self.assertEqual([], f["BIND-TO"])

        Binding(f).set_bind_to(o)

        self.assertEqual(o, f["BIND-TO"])


class InstantiableTestCase(OntoAgentTestCase):

    def test_instantiable_slots(self):
        f = Frame("@ONT.INSTANTIABLE.?")
        f["IS-INSTANTIABLE"] = ["THEME", "AGENT"]

        self.assertEqual({"THEME", "AGENT"}, Instantiable(f).instantiable_slots())

    def test_add_instantiable_slot(self):
        f = Frame("@ONT.INSTANTIABLE.?")
        self.assertEqual([], f["IS-INSTANTIABLE"])

        Instantiable(f).add_instantiable_slot("THEME")
        Instantiable(f).add_instantiable_slot("AGENT")

        self.assertEqual(["THEME", "AGENT"], f["IS-INSTANTIABLE"])

    def test_varmaps(self):
        f = Frame("@ONT.INSTANTIABLE.?")
        vm1 = Frame("@SYS.VARMAP.?")
        vm2 = Frame("@SYS.VARMAP.?")

        f["HAS-VARMAP"] = [vm1, vm2]
        self.assertEqual([vm1, vm2], Instantiable(f).varmaps())

    def test_add_varmaps(self):
        f = Frame("@ONT.INSTANTIABLE.?")
        vm1 = Frame("@SYS.VARMAP.?")
        vm2 = Frame("@SYS.VARMAP.?")

        self.assertEqual([], f["HAS-VARMAP"])

        Instantiable(f).add_varmap(vm1)
        Instantiable(f).add_varmap(vm2)

        self.assertEqual([vm1, vm2], f["HAS-VARMAP"])

    def test_build_varmap(self):
        i = Instantiable(Frame("@ONT.INSTANTIABLE.?"))
        d = Frame("@TEST.FRAME.?")
        r = Frame("@TEST.OBJECT.?")

        i.build_varmap(d, r)

        self.assertEqual(1, len(i.varmaps()))

        varmap = i.varmaps()[0]

        self.assertEqual(d, varmap.defined())
        self.assertEqual(r, varmap.realized())

    def test_find_varmap_for_defined(self):
        i = Instantiable(Frame("@ONT.INSTANTIABLE.?"))
        d1 = Frame("@TEST.FRAME.?")
        d2 = Frame("@TEST.FRAME.?")
        r1 = Frame("@TEST.OBJECT.?")
        r2 = Frame("@TEST.OBJECT.?")

        v1 = i.build_varmap(d1, r1)
        v2 = i.build_varmap(d2, r2)

        self.assertEqual(v1, i.find_varmap_for_defined(d1))
        self.assertEqual(v2, i.find_varmap_for_defined(d2))

    def test_bindings(self):
        f = Frame("@ONT.INSTANTIABLE.?")
        b1 = Frame("@SYS.BINDING.?")
        b2 = Frame("@SYS.BINDING.?")
        f["HAS-BINDING"] = [b1, b2]

        self.assertEqual([b1, b2], Instantiable(f).bindings())
        self.assertIsInstance(Instantiable(f).bindings()[0], Binding)
        self.assertIsInstance(Instantiable(f).bindings()[1], Binding)

    def test_add_binding(self):
        f = Frame("@ONT.INSTANTIABLE.?")
        self.assertEqual([], f["HAS-BINDING"])

        b1 = Frame("@SYS.BINDING.?")
        b2 = Frame("@SYS.BINDING.?")

        Instantiable(f).add_binding(b1)
        Instantiable(f).add_binding(Binding(b2))

        self.assertEqual([b1, b2], f["HAS-BINDING"])
        self.assertIsInstance(f["HAS-BINDING"][0], Frame)
        self.assertIsInstance(f["HAS-BINDING"][1], Frame)

    def test_build_binding(self):
        i = Instantiable(Frame("@ONT.INSTANTIABLE.?"))
        f = Frame("@TEST.FRAME.?")
        o = Frame("@TEST.OBJECT.?")
        v = Frame("@SYS.VARIABLE.?")

        i.build_binding(f, o, v)

        self.assertEqual(1, len(i.bindings()))

        binding = i.bindings()[0]

        self.assertEqual(f, binding.range())
        self.assertEqual(o, binding.bind_local())
        self.assertEqual(v, binding.bind_to())


class VarMapTestCase(OntoAgentTestCase):

    def test_defined(self):
        m = Frame("@SYS.VARMAP.?")
        v = Frame("@SYS.VARIABLE.?")

        m["DEFINED"] = v
        self.assertEqual(v, VarMap(m).defined())

    def test_set_defined(self):
        m = Frame("@SYS.VARMAP.?")
        v = Frame("@SYS.VARIABLE.?")

        self.assertEqual([], m["DEFINED"])
        VarMap(m).set_defined(v)

        self.assertEqual(v, m["DEFINED"])

    def test_realized(self):
        m = Frame("@SYS.VARMAP.?")
        v = Frame("@SYS.VALUE.?")

        m["REALIZED"] = v
        self.assertEqual(v, VarMap(m).realized())

    def test_set_realized(self):
        m = Frame("@SYS.VARMAP.?")
        v = Frame("@SYS.VALUE.?")

        self.assertEqual([], m["REALIZED"])
        VarMap(m).set_realized(v)

        self.assertEqual(v, m["REALIZED"])
