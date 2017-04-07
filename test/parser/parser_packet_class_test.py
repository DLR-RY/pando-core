
import os
import datetime
import unittest

import pando

class ParserTest(unittest.TestCase):

    def setUp(self):
        self.model = self.parse_file("resources/packet_class.xml")

    def parse_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", filename)
        parser = pando.parser.Parser()
        model = parser.parse(filepath)

        self.assertIsNotNone(model)
        return model

    def test_should_have_packet_class_data(self):
        application = self.model.subsystems[0].applications[1]
        telemetryMappings = application.getTelemetries()

        self.assertEqual(len(telemetryMappings), 5)

        tm1a = application.getTelemetryBySid("TM1A")
        tm1b = application.getTelemetryBySid("TM1B")
        tm2a = application.getTelemetryBySid("TM2A")
        tm2b = application.getTelemetryBySid("TM2B")
        event = application.getTelemetryBySid("Event")

        self.assertIsNotNone(tm1a.telemetry.packet_class)
        self.assertIsNotNone(tm1b.telemetry.packet_class)
        self.assertIsNone(tm2a.telemetry.packet_class)
        self.assertIsNone(tm2b.telemetry.packet_class)
        self.assertIsNotNone(event.telemetry.packet_class)

        self.assertIsNotNone(tm1a.packet_class)
        self.assertIsNotNone(tm1b.packet_class)
        self.assertIsNotNone(tm2a.packet_class)
        self.assertIsNone(tm2b.packet_class)
        self.assertIsNotNone(event.packet_class)

    def test_should_have_correct_packet_class_data(self):
        application = self.model.subsystems[0].applications[1]
        telemetryMappings = application.getTelemetries()

        tm1a = application.getTelemetryBySid("TM1A")
        tm1b = application.getTelemetryBySid("TM1B")
        tm2a = application.getTelemetryBySid("TM2A")
        tm2b = application.getTelemetryBySid("TM2B")
        event = application.getTelemetryBySid("Event")

        self.assertEqual(["Housekeeping"], tm1a.packet_class)
        self.assertEqual(["Extended Housekeeping", "Realtime"], tm1b.packet_class)
        self.assertEqual(["Extended Housekeeping"], tm2a.packet_class)
        self.assertEqual(["Event"], event.packet_class)

    def test_should_provide_packets_by_class(self):
        housekeepings = self.model.get_packets_by_packet_class("Extended Housekeeping")

        self.assertEqual(2, len(housekeepings))

        application = self.model.subsystems[0].applications[1]
        tm1b = application.getTelemetryBySid("TM1B")
        tm2a = application.getTelemetryBySid("TM2A")

        self.assertIn(tm1b, housekeepings)
        self.assertIn(tm2a, housekeepings)


if __name__ == '__main__':
    unittest.main()

