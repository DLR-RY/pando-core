#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015-2017, German Aerospace Center (DLR)
#
# This file is part of the development version of the pando library.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Authors:
# - 2015-2017, Fabian Greif (DLR RY-AVS)

import os
import unittest
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
        self.assertGreater(len(self.model.subsystems[0].telecommand_parameters), 0)
        self.assertGreater(len(self.model.subsystems[0].telecommand_enumerations), 0)
        self.assertGreater(len(self.model.subsystems[0].telemetry_enumerations), 0)

    def test_should_contain_telemetry_for_application(self):
        app = self.model.subsystems[0].applications[0x123]

        self.assertGreater(len(app.get_telemetries()), 0)

    def test_should_contain_specific_telemetry_mapping(self):
        app = self.model.subsystems[0].applications[0x123]

        telemetries = app.get_telemetries()
        self.assertEqual(len(telemetries), 2)

        t = app.get_telemetry_by_sid("51234")
        self.assertIsNotNone(t)
        self.assertEqual(len(t.parameters), 7)

        t = app.get_telemetry_by_sid("51235")
        self.assertIsNotNone(t)
        self.assertEqual(len(t.parameters), 2)

    def test_should_contain_telecommand_mapping(self):
        app = self.model.subsystems[0].applications[0x123]

        self.assertGreater(len(app.get_telecommands()), 0)

        tc = app.get_telecommands()[0]
        self.assertEqual(tc.telecommand.uid, "TEST03")
        self.assertEqual(tc.sid, "DHSC0001")

    def test_should_contain_a_complete_mapping(self):
        validator = pando.model.validator.ModelValidator(self.model)
        self.assertEqual(len(validator.get_unmapped_telecommand_parameters()), 0)
        self.assertEqual(len(validator.get_unmapped_telemetry_parameters()), 0)

        additional_tm, unresolved_tm, additional_tc, unresolved_tc = validator.get_unmapped_enumerations()
        self.assertEqual(len(additional_tc), 0)
        self.assertEqual(len(unresolved_tc), 0)
        self.assertEqual(len(additional_tm), 0)
        self.assertEqual(len(unresolved_tm), 0)

    def test_should_have_unused_parameters(self):
        validator = pando.model.validator.ModelValidator(self.model)
        self.assertEqual(len(validator.get_unused_parameters()), 3)
        self.assertEqual(len(validator.get_unused_telecommands()), 5)
        self.assertEqual(len(validator.get_unused_telemetries()), 0)

if __name__ == '__main__':
    unittest.main()

