#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pdoc.model
import pdoc.parser.common

from .common import ParserException

class CalibrationParser:

    def parse_service_calibration(self, service_node, m):
        for calibrations_node in service_node.iterfind('calibrations'):
            self.parse_calibrations(calibrations_node, m)

    def parse_calibrations(self, node, m):
        calibrations = []
        for calibration_node in node.iterchildren('telemetryInterpolation'):
            calibration = self._parse_calibration_interpolation_telemetry(calibration_node)
            m.calibrations[calibration.uid] = calibration
            calibrations.append(calibration)

        for calibration_node in node.iterchildren('telecommandInterpolation'):
            calibration = self._parse_calibration_interpolation_telecommand(calibration_node)
            m.calibrations[calibration.uid] = calibration
            calibrations.append(calibration)

        for calibration_node in node.iterchildren('polynom'):
            calibration = self._parse_calibration_polynom(calibration_node)
            m.calibrations[calibration.uid] = calibration
            calibrations.append(calibration)

        return calibrations

    def _parse_calibration_interpolation_telemetry(self, node):
        description = pdoc.parser.common.parse_description(node)
        c = pdoc.model.Interpolation(pdoc.model.Calibration.INTERPOLATION_TELEMETRY,
                                     name=node.attrib.get("name"),
                                     uid=node.attrib.get("uid"),
                                     description=description)

        c.extrapolate = self._to_boolean(node.attrib.get("extrapolate", "true"))
        c.outputType = self._to_interpolation_type(node.attrib.get("outputType"))
        c.unit = node.attrib.get("unit", "")

        for point_node in node.iterfind("point"):
            c.appendPoint(self._parse_calibration_interpolation_point(point_node))

        return c

    def _parse_calibration_interpolation_telecommand(self, node):
        description = pdoc.parser.common.parse_description(node)
        c = pdoc.model.Interpolation(pdoc.model.Calibration.INTERPOLATION_TELECOMMAND,
                                     name=node.attrib.get("name"),
                                     uid=node.attrib.get("uid"),
                                     description=description)

        c.extrapolate = self._to_boolean(node.attrib.get("extrapolate", "true"))
        c.inputType = self._to_interpolation_type(node.attrib.get("inputType"))

        for point_node in node.iterfind("point"):
            c.appendPoint(self._parse_calibration_interpolation_point(point_node))

        return c

    @staticmethod
    def _parse_calibration_polynom(node):
        description = pdoc.parser.common.parse_description(node)
        c = pdoc.model.Polynom(name=node.attrib.get("name"),
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
            "Unsigned Integer": pdoc.model.Interpolation.UNSIGNED_INTEGER,
            "Signed Integer": pdoc.model.Interpolation.SIGNED_INTEGER,
            "Float": pdoc.model.Interpolation.REAL
        }[type_string]

    @staticmethod
    def _parse_calibration_interpolation_point(node):
        p = pdoc.model.Interpolation.Point(float(node.attrib.get("x")),
                                           float(node.attrib.get("y")))
        return p
