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
import pando


class ParserCalibrationTest(unittest.TestCase):

    def setUp(self):
        self.model = self.parse_file("resources/calibration_services.xml")

    def parse_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", filename)
        parser = pando.parser.Parser()
        model = parser.parse(filepath)

        self.assertIsNotNone(model)
        return model

    def test_should_contain_calibrations(self):
        self.assertEqual(4, len(self.model.calibrations))

    def test_should_contain_calibration_mappings(self):
        self.assertEqual(2, len(self.model.subsystems[0].telemetryCalibrations))
        self.assertEqual(1, len(self.model.subsystems[0].telecommandCalibrations))

    def test_should_have_telecommand_parameter_calibration(self):
        packet = self.model.parameters["P7"]
        self.assertEqual("calibration_test", packet.calibration.uid)
        self.assertEqual(True, packet.calibration.extrapolate)
        self.assertEqual(5, len(packet.calibration.points))

        self.assertEqual(0, packet.calibration.points[0].x)
        self.assertEqual(10, packet.calibration.points[0].y)

        self.assertEqual(pando.model.Interpolation.UNSIGNED_INTEGER, packet.calibration.inputType)
        self.assertEqual(pando.model.Interpolation.UNSIGNED_INTEGER, packet.calibration.outputType)

    def test_should_have_telemetry_parameter_calibration(self):
        packet = self.model.parameters["P100"]
        self.assertEqual("calibration_parameter", packet.calibration.uid)
        self.assertEqual(False, packet.calibration.extrapolate)
        self.assertEqual(2, len(packet.calibration.points))

        self.assertEqual(100.12, packet.calibration.points[0].x)
        self.assertEqual(-2, packet.calibration.points[0].y)

        self.assertEqual(pando.model.Interpolation.REAL, packet.calibration.inputType)
        self.assertEqual(pando.model.Interpolation.SIGNED_INTEGER, packet.calibration.outputType)

    def test_should_have_polynom_parameter_calibration(self):
        packet = self.model.parameters["P101"]

        self.assertEqual("calibration_polynom", packet.calibration.uid)
        self.assertEqual(1, packet.calibration.a0)
        self.assertEqual(2, packet.calibration.a1)
        self.assertEqual(3.5, packet.calibration.a2)
        self.assertEqual(7, packet.calibration.a3)
        self.assertEqual(100.1, packet.calibration.a4)

    def test_should_have_unmapped_calibrations(self):
        validator = pando.model.validator.ModelValidator(self.model)
        additional_tm, unresolved_tm, additional_tc, unresolved_tc = validator.getUnmappedCalibrations()

        self.assertEqual(0, len(additional_tc))
        self.assertEqual(0, len(unresolved_tc))
        self.assertEqual(1, len(additional_tm))
        self.assertEqual(1, len(unresolved_tm))

        self.assertEqual("0201", additional_tm[0].sid)
        self.assertEqual("calibration_polynom2", additional_tm[0].calibration.uid)

        tm, subsystem = unresolved_tm[0]
        self.assertEqual("calibration_polynom", tm.uid)


if __name__ == '__main__':
    unittest.main()
