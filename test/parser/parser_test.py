
import os
import unittest
import pdoc

class ParserTest(unittest.TestCase):

    def setUp(self):
        self.model = self.parseFile("resources/test.xml")

    def parseFile(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", filename)
        parser = pdoc.parser.Parser()
        model = parser.parse(filepath)

        self.assertIsNotNone(model)
        return model

    def getPacketParameter(self, packet, uid):
        for p in packet.getParametersAsFlattenedList():
            if p.uid == uid:
                return p
        else:
            self.fail("Parameter '%s' not found" % uid)
        return None

    def test_shouldContainEnumerations(self):
        self.assertEqual(len(self.model.enumerations), 2)

        self.assertTrue("E0" in self.model.enumerations.keys())
        self.assertTrue("E1" in self.model.enumerations.keys())


    def test_shouldHaveCorrectEnumerationData(self):
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

    def test_shouldContainPackets(self):
        self.assertGreater(len(self.model.telemetries), 0)
        self.assertGreater(len(self.model.telecommands), 0)

    def test_shouldCalculateTheDepthOfARepeaterParameter(self):
        tm = self.model.telemetries["service_3_12"]
        self.assertEqual(tm.depth, 3)

    def test_shouldContainInformationAboutRelatedTelemetry(self):
        tc = self.model.telecommands["TEST02"]
        self.assertEqual(len(tc.relevantTelemetry), 1)

        tm = tc.relevantTelemetry[0]
        self.assertEqual(tm.uid, "service_3_12")
        self.assertEqual(tm.name, "Diagnostic Parameter Report Definitions Report (3, 12)")

    def test_shouldHaveServiceTypeInformation(self):
        tm = self.model.telemetries["service_3_12"]

        self.assertEqual(tm.serviceType, 3)
        self.assertEqual(tm.serviceSubtype, 12)

        tc = self.model.telecommands["TEST03"]

        self.assertEqual(tc.serviceType, 8)
        self.assertEqual(tc.serviceSubtype, 100)

    def test_parametersDefinedInAPacketShouldAppearAsReferenceParameters(self):
        self.assertTrue("P10" in self.model.parameters)

    def test_shouldHaveCriticality(self):
        tc1 = self.model.telecommands["TEST01"]
        self.assertFalse(tc1.critical)

        tc2 = self.model.telecommands["TEST02"]
        self.assertTrue(tc2.critical)

    def test_shouldHaveFixedValues(self):
        tc = self.model.telecommands["TEST03"]

        p = self.getPacketParameter(tc, "P10")
        self.assertEqual(p.value, "20")
        self.assertEqual(p.valueType, pdoc.model.Parameter.FIXED)

    def test_valueShouldBeInherited(self):
        tm = self.model.telemetries["service_3_12"]

        p = self.getPacketParameter(tm, "P7")
        self.assertEqual(p.value, "123456")
        self.assertEqual(p.valueType, pdoc.model.Parameter.DEFAULT)

        p = self.getPacketParameter(tm, "P21")
        self.assertEqual(p.value, "Unit1")
        self.assertEqual(p.valueType, pdoc.model.Parameter.FIXED)

    def test_inheritedValuesShouldBeOverwriteable(self):
        tc = self.model.telecommands["TEST02"]

        p = self.getPacketParameter(tc, "P21")
        self.assertEqual(p.value, "Unit17")
        self.assertEqual(p.valueType, pdoc.model.Parameter.DEFAULT)

    def test_shouldSupportUnits(self):
        p = self.model.parameters["P1"]

        self.assertEqual(p.unit, "sec")

    def test_telecommandShouldContainDefaultVerificationInformationIfNotSpecified(self):
        tc = self.model.telecommands["TEST03"]

        self.assertEqual(True, tc.verification.acceptance)
        self.assertEqual(False, tc.verification.start)
        self.assertEqual(False, tc.verification.progress)
        self.assertEqual(True, tc.verification.completion)

    def test_telecommandShouldHaveSetableVerificationInformation(self):
        tc = self.model.telecommands["TEST04"]

        self.assertEqual(True, tc.verification.acceptance)
        self.assertEqual(True, tc.verification.start)
        self.assertEqual(False, tc.verification.progress)
        self.assertEqual(True, tc.verification.completion)

    def test_telecommandShouldHaveSetableVerificationInformationWithGaps(self):
        tc = self.model.telecommands["TEST05"]

        self.assertEqual(False, tc.verification.acceptance)
        self.assertEqual(False, tc.verification.start)
        self.assertEqual(True, tc.verification.progress)
        self.assertEqual(False, tc.verification.completion)

    def test_shouldSupportLists(self):
        model = self.parseFile("resources/test_list.xml")

        tc = model.telecommands["test"]
        parameters = tc.getParametersAsFlattenedList()
        self.assertEqual(len(parameters), 3)

        self.assertEqual(parameters[0].uid, "p1")
        self.assertEqual(parameters[1].uid, "p2")
        self.assertEqual(parameters[2].uid, "p3")

        # Parameters must be accessible by their own
        self.assertEqual(model.parameters["p1"].type.width, 8)
        self.assertEqual(model.parameters["p2"].type.width, 16)

    def test_shouldSupportListsWithinLists(self):
        model = self.parseFile("resources/test_list_list.xml")

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
