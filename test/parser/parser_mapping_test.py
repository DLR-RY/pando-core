
import os
import unittest
import pando
import pando.model.validator

class ParserMappingTest(unittest.TestCase):

    def setUp(self):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources/test.xml")
        self.parser = pando.parser.Parser()
        self.model = self.parser.parse(filepath)

        self.assertIsNotNone(self.model)

    def test_shouldContainMappingInformation(self):
        self.assertGreater(len(self.model.subsystems), 0)
        self.assertTrue(0 in self.model.subsystems)
        self.assertGreater(len(self.model.subsystems[0].applications), 0)
        self.assertGreater(len(self.model.subsystems[0].telecommandParameters), 0)
        self.assertGreater(len(self.model.subsystems[0].telecommandEnumerations), 0)
        self.assertGreater(len(self.model.subsystems[0].telemetryEnumerations), 0)

    def test_should_contain_telemetry_for_application(self):
        app = self.model.subsystems[0].applications[0x123]

        self.assertGreater(len(app.getTelemetries()), 0)

    def test_should_contain_specific_telemetry_mapping(self):
        app = self.model.subsystems[0].applications[0x123]

        telemetries = app.getTelemetries()
        self.assertEqual(len(telemetries), 2)

        t = app.getTelemetryBySid("51234")
        self.assertIsNotNone(t)
        self.assertEqual(len(t.parameters), 7)

        t = app.getTelemetryBySid("51235")
        self.assertIsNotNone(t)
        self.assertEqual(len(t.parameters), 2)

    def test_should_contain_telecommand_mapping(self):
        app = self.model.subsystems[0].applications[0x123]

        self.assertGreater(len(app.getTelecommands()), 0)

        tc = app.getTelecommands()[0]
        self.assertEqual(tc.telecommand.uid, "TEST03")
        self.assertEqual(tc.sid, "DHSC0001")

    def test_should_contain_a_complete_mapping(self):
        validator = pando.model.validator.ModelValidator(self.model)
        self.assertEqual(len(validator.getUnmappedTelecommandParameters()), 0)
        self.assertEqual(len(validator.getUnmappedTelemetryParameters()), 0)

        additional_tm, unresolved_tm, additional_tc, unresolved_tc = validator.getUnmappedEnumerations()
        self.assertEqual(len(additional_tc), 0)
        self.assertEqual(len(unresolved_tc), 0)
        self.assertEqual(len(additional_tm), 0)
        self.assertEqual(len(unresolved_tm), 0)

    def test_should_have_unused_parameters(self):
        validator = pando.model.validator.ModelValidator(self.model)
        self.assertEqual(len(validator.getUnusedParameters()), 3)
        self.assertEqual(len(validator.getUnusedTelecommands()), 5)
        self.assertEqual(len(validator.getUnusedTelemetries()), 0)

if __name__ == '__main__':
    unittest.main()

