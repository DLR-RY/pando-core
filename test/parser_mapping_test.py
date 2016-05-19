
import os
import unittest
import pdoc

class ParserMappingTest(unittest.TestCase):

    def setUp(self):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources/test.xml")
        self.parser = pdoc.parser.Parser()
        self.model = self.parser.parse(filepath)

        self.assertIsNotNone(self.model)

    def test_shouldContainMappingInformation(self):
        self.assertGreater(len(self.model.subsystems), 0)
        self.assertTrue(0 in self.model.subsystems)
        self.assertGreater(len(self.model.subsystems[0].applications), 0)
        self.assertGreater(len(self.model.subsystems[0].telecommandParameters), 0)
        self.assertGreater(len(self.model.subsystems[0].telecommandEnumerations), 0)
        self.assertGreater(len(self.model.subsystems[0].telemetryEnumerations), 0)

    def test_shouldContainTelemetryForApplication(self):
        app = self.model.subsystems[0].applications[0x123]

        self.assertGreater(len(app.getTelemetries()), 0)

    def test_shouldContainSpecificTelemetryMapping(self):
        app = self.model.subsystems[0].applications[0x123]

        telemetries = app.getTelemetries()
        self.assertEqual(len(telemetries), 2)

        t = app.getTelemetryBySid("51234")
        self.assertIsNotNone(t)
        self.assertEqual(len(t.parameters), 7)

        t = app.getTelemetryBySid("51235")
        self.assertIsNotNone(t)
        self.assertEqual(len(t.parameters), 2)

    def test_shouldContainTelecommandMapping(self):
        app = self.model.subsystems[0].applications[0x123]

        self.assertGreater(len(app.getTelecommands()), 0)

        tc = app.getTelecommands()[0]
        self.assertEqual(tc.telecommand.uid, "TEST03")
        self.assertEqual(tc.sid, "DHSC0001")

    def test_shouldContainACompleteMapping(self):
        self.assertEqual(len(self.model.getUnmappedTelecommandParameters()), 0)
        self.assertEqual(len(self.model.getUnmappedTelemetryParameters()), 0)

        additionalTc, unresolvedTc, additionalTm, unresolvedTm = self.model.getUnmappedEnumerations()
        self.assertEqual(len(additionalTc), 0)
        self.assertEqual(len(unresolvedTc), 0)
        self.assertEqual(len(additionalTm), 0)
        self.assertEqual(len(unresolvedTm), 0)

    def test_shouldHaveUnusedParameters(self):
        self.assertEqual(len(self.model.getUnusedParameters()), 3)
        self.assertEqual(len(self.model.getUnusedTelecommands()), 5)
        self.assertEqual(len(self.model.getUnusedTelemetries()), 0)

if __name__ == '__main__':
    unittest.main()

