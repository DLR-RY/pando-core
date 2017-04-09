#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016-2017, German Aerospace Center (DLR)
#
# This file is part of the development version of the pando library.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Authors:
# - 2016-2017, Fabian Greif (DLR RY-AVS)

import pando.model
import pando.parser.common


class CalibrationParser:

    def parse_service_calibration(self, service_node, m):
        for calibrations_node in service_node.iterfind('calibrations'):
            self.parse_calibrations(calibrations_node, m)

    def parse_calibrations(self, node, m):
        calibrations = []
        for calibration_node in node.iterchildren('telemetryLinearInterpolation'):
            calibration = self._parse_calibration_interpolation_telemetry(calibration_node)
            m.calibrations[calibration.uid] = calibration
            calibrations.append(calibration)

        for calibration_node in node.iterchildren('telecommandLinearInterpolation'):
            calibration = self._parse_calibration_interpolation_telecommand(calibration_node)
            m.calibrations[calibration.uid] = calibration
            calibrations.append(calibration)

        for calibration_node in node.iterchildren('telemetryPolynomInterpolation'):
            calibration = self._parse_calibration_polynom(calibration_node)
            m.calibrations[calibration.uid] = calibration
            calibrations.append(calibration)

        return calibrations

    def _parse_calibration_interpolation_telemetry(self, node):
        description = pando.parser.common.parse_description(node)
        c = pando.model.Interpolation(pando.model.Calibration.INTERPOLATION_TELEMETRY,
                                      name=node.attrib.get("name"),
                                      uid=node.attrib.get("uid"),
                                      description=description)

        c.extrapolate = self._to_boolean(node.attrib.get("extrapolate", "true"))
        c.output_type = self._to_interpolation_type(node.attrib.get("outputType"))
        c.unit = node.attrib.get("unit", "")

        for point_node in node.iterfind("point"):
            c.append_point(self._parse_calibration_interpolation_point(point_node))

        return c

    def _parse_calibration_interpolation_telecommand(self, node):
        description = pando.parser.common.parse_description(node)
        c = pando.model.Interpolation(pando.model.Calibration.INTERPOLATION_TELECOMMAND,
                                      name=node.attrib.get("name"),
                                      uid=node.attrib.get("uid"),
                                      description=description)

        c.extrapolate = self._to_boolean(node.attrib.get("extrapolate", "true"))
        c.input_type = self._to_interpolation_type(node.attrib.get("inputType"))

        for point_node in node.iterfind("point"):
            c.append_point(self._parse_calibration_interpolation_point(point_node))

        return c

    @staticmethod
    def _parse_calibration_polynom(node):
        description = pando.parser.common.parse_description(node)
        c = pando.model.Polynom(name=node.attrib.get("name"),
                                uid=node.attrib.get("uid"),
                                description=description)

        c.a0 = float(node.attrib.get("a0", "0"))
        c.a1 = float(node.attrib.get("a1", "0"))
        c.a2 = float(node.attrib.get("a2", "0"))
        c.a3 = float(node.attrib.get("a3", "0"))
        c.a4 = float(node.attrib.get("a4", "0"))

        return c

    @staticmethod
    def _to_boolean(s):
        return True if (s == "true" or s == "1") else False

    @staticmethod
    def _to_interpolation_type(type_string):
        return {
            "Unsigned Integer": pando.model.Interpolation.UNSIGNED_INTEGER,
            "Signed Integer": pando.model.Interpolation.SIGNED_INTEGER,
            "Float": pando.model.Interpolation.REAL
        }[type_string]

    @staticmethod
    def _parse_calibration_interpolation_point(node):
        p = pando.model.Interpolation.Point(float(node.attrib.get("x")),
                                            float(node.attrib.get("y")))
        return p
