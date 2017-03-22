
import os
import unittest
import pdoc

class ParserTest(unittest.TestCase):

    def setUp(self):
        self.model = self.parse_file("resources/test.xml")

    def parse_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", filename)
        parser = pdoc.parser.Parser()
        model = parser.parse(filepath)

        self.assertIsNotNone(model)
        return model

    def get_packet_parameter(self, packet, uid):
        for p in packet.getParametersAsFlattenedList():
            if p.uid == uid:
                return p
        else:
            self.fail("Parameter '%s' not found" % uid)
        return None

    def test_should_contain_enumerations(self):
        self.assertEqual(len(self.model.enumerations), 2)

        self.assertTrue("E0" in self.model.enumerations.keys())
        self.assertTrue("E1" in self.model.enumerations.keys())

    def test_should_have_correct_enumeration_data(self):
        enum = self.model.enumerations["E0"]

        self.assertEqual("Large Data Unit Id", enum.name)
        self.assertEqual(8, enum.width)
        self.assertEqual(3, len(enum.entries))

        enum = self.model.enumerations["E1"]

        self.assertEqual("Some Enumeration", enum.name)
        self.assertEqual(16, enum.width)

        self.assertEqual(2, len(enum.entries))

        self.assertEqual("Key0", enum.entries[0].name)
        self.assertEqual("10", enum.entries[0].value)

        self.assertEqual("Key1", enum.entries[1].name)
        self.assertEqual("213", enum.entries[1].value)

    def test_should_contain_packets(self):
        self.assertGreater(len(self.model.telemetries), 0)
        self.assertGreater(len(self.model.telecommands), 0)

    def test_should_calculate_the_depth_of_a_repeater_parameter(self):
        tm = self.model.telemetries["service_3_12"]
        self.assertEqual(tm.depth, 3)

    def test_should_contain_information_about_related_telemetry(self):
        tc = self.model.telecommands["TEST02"]
        self.assertEqual(len(tc.relevantTelemetry), 1)

        tm = tc.relevantTelemetry[0]
        self.assertEqual(tm.uid, "service_3_12")
        self.assertEqual(tm.name, "Diagnostic Parameter Report Definitions Report (3, 12)")

    def test_should_have_service_type_information(self):
        tm = self.model.telemetries["service_3_12"]

        self.assertEqual(tm.serviceType, 3)
        self.assertEqual(tm.serviceSubtype, 12)

        tc = self.model.telecommands["TEST03"]

        self.assertEqual(tc.serviceType, 8)
        self.assertEqual(tc.serviceSubtype, 100)

    def test_parameters_defined_in_a_packet_should_appear_as_reference_parameters(self):
        self.assertTrue("P10" in self.model.parameters)

    def test_should_have_criticality(self):
        tc1 = self.model.telecommands["TEST01"]
        self.assertFalse(tc1.critical)

        tc2 = self.model.telecommands["TEST02"]
        self.assertTrue(tc2.critical)

    def test_should_have_fixed_values(self):
        tc = self.model.telecommands["TEST03"]

        p = self.get_packet_parameter(tc, "P10")
        self.assertEqual(p.value, "20")
        self.assertEqual(p.valueType, pdoc.model.Parameter.FIXED)

    def test_value_should_be_inherited(self):
        tm = self.model.telemetries["service_3_12"]

        p = self.get_packet_parameter(tm, "P7")
        self.assertEqual(p.value, "123456")
        self.assertEqual(p.valueType, pdoc.model.Parameter.DEFAULT)

        p = self.get_packet_parameter(tm, "P21")
        self.assertEqual(p.value, "Unit1")
        self.assertEqual(p.valueType, pdoc.model.Parameter.FIXED)

    def test_inherited_values_should_be_overwriteable(self):
        tc = self.model.telecommands["TEST02"]

        p = self.get_packet_parameter(tc, "P21")
        self.assertEqual(p.value, "Unit17")
        self.assertEqual(p.valueType, pdoc.model.Parameter.DEFAULT)

    def test_should_support_units(self):
        p = self.model.parameters["P1"]

        self.assertEqual(p.unit, "sec")

    def test_telecommand_should_contain_default_verification_information_if_not_specified(self):
        tc = self.model.telecommands["TEST03"]

        self.assertEqual(True, tc.verification.acceptance)
        self.assertEqual(False, tc.verification.start)
        self.assertEqual(False, tc.verification.progress)
        self.assertEqual(True, tc.verification.completion)

    def test_telecommand_should_have_setable_verification_information(self):
        tc = self.model.telecommands["TEST04"]

        self.assertEqual(True, tc.verification.acceptance)
        self.assertEqual(True, tc.verification.start)
        self.assertEqual(False, tc.verification.progress)
        self.assertEqual(True, tc.verification.completion)

    def test_telecommand_should_have_setable_verification_information_with_gaps(self):
        tc = self.model.telecommands["TEST05"]

        self.assertEqual(False, tc.verification.acceptance)
        self.assertEqual(False, tc.verification.start)
        self.assertEqual(True, tc.verification.progress)
        self.assertEqual(False, tc.verification.completion)

    def test_should_support_lists(self):
        model = self.parse_file("resources/test_list.xml")

        tc = model.telecommands["test"]
        parameters = tc.getParametersAsFlattenedList()
        self.assertEqual(len(parameters), 3)

        self.assertEqual(parameters[0].uid, "p1")
        self.assertEqual(parameters[1].uid, "p2")
        self.assertEqual(parameters[2].uid, "p3")

        # Parameters must be accessible by their own
        self.assertEqual(model.parameters["p1"].type.width, 8)
        self.assertEqual(model.parameters["p2"].type.width, 16)

    def test_should_support_lists_within_lists(self):
        model = self.parse_file("resources/test_list_list.xml")

        tc = model.telecommands["test"]
        parameters = tc.getParametersAsFlattenedList()
        self.assertEqual(len(parameters), 5)

        self.assertEqual(parameters[0].uid, "p1")
        self.assertEqual(parameters[1].uid, "p1")
        self.assertEqual(parameters[2].uid, "p2")
        self.assertEqual(parameters[3].uid, "p3")
        self.assertEqual(parameters[4].uid, "p4")


if __name__ == '__main__':
    unittest.main()
