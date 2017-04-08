#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, German Aerospace Center (DLR)
#
# This file is part of the development version of the pando library.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Authors:
# - 2017, Fabian Greif (DLR RY-AVS)

import os
import datetime
import unittest

import pando


class ParserTest(unittest.TestCase):

    def setUp(self):
        self.model = self.parse_file("resources/packet_generation.xml")

    def parse_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", filename)
        parser = pando.parser.Parser()
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

        self.assertEqual(pando.model.PeriodicPacketGeneration(datetime.timedelta(seconds=2)),
                         tm1a.packet_generation)
        self.assertEqual(pando.model.ResponsePacketGeneration(),
                         tm1b.packet_generation)
        self.assertEqual(pando.model.EventPacketGeneration(response=True),
                         tm2a.packet_generation)

    def test_events_should_have_event_generation_type(self):
        application = self.model.subsystems[0].applications[1]
        telemetryMappings = application.getTelemetries()

        event = application.getTelemetryBySid("Event")

        self.assertEqual(pando.model.EventPacketGeneration(),
                         event.packet_generation)


if __name__ == '__main__':
    unittest.main()

