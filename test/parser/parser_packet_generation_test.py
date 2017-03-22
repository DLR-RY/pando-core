
import os
import datetime
import unittest

import pdoc

class ParserTest(unittest.TestCase):

    def setUp(self):
        self.model = self.parse_file("resources/packet_generation.xml")

    def parse_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", filename)
        parser = pdoc.parser.Parser()
        model = parser.parse(filepath)

        self.assertIsNotNone(model)
        return model

    def test_should_have_packet_generation_data(self):
        application = self.model.subsystems[0].applications[1]
        telemetryMappings = application.getTelemetries()

        self.assertEqual(len(telemetryMappings), 5)

        tm1a = application.getTelemetryBySid("TM1A")
        tm1b = application.getTelemetryBySid("TM1B")
        tm2a = application.getTelemetryBySid("TM2A")
        tm2b = application.getTelemetryBySid("TM2B")

        self.assertIsNotNone(tm1a.telemetry.packet_generation)
        self.assertIsNotNone(tm1b.telemetry.packet_generation)
        self.assertIsNone(tm2a.telemetry.packet_generation)
        self.assertIsNone(tm2b.telemetry.packet_generation)

        self.assertIsNotNone(tm1a.packet_generation)
        self.assertIsNotNone(tm1b.packet_generation)
        self.assertIsNotNone(tm2a.packet_generation)
        self.assertIsNone(tm2b.packet_generation)

    def test_should_have_correct_packet_generation_data(self):
        application = self.model.subsystems[0].applications[1]
        telemetryMappings = application.getTelemetries()

        tm1a = application.getTelemetryBySid("TM1A")
        tm1b = application.getTelemetryBySid("TM1B")
        tm2a = application.getTelemetryBySid("TM2A")
        tm2b = application.getTelemetryBySid("TM2B")

        self.assertEqual(pdoc.model.PeriodicPacketGeneration(datetime.timedelta(seconds=2)),
                         tm1a.packet_generation)
        self.assertEqual(pdoc.model.ResponsePacketGeneration(),
                         tm1b.packet_generation)
        self.assertEqual(pdoc.model.EventPacketGeneration(response=True),
                         tm2a.packet_generation)

    def test_events_should_have_event_generation_type(self):
        application = self.model.subsystems[0].applications[1]
        telemetryMappings = application.getTelemetries()

        event = application.getTelemetryBySid("Event")

        self.assertEqual(pdoc.model.EventPacketGeneration(),
                         event.packet_generation)


if __name__ == '__main__':
    unittest.main()

