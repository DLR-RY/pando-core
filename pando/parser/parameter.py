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

import copy
import lxml

import pando.model
import pando.parser.common

from .common import ParserException
from .calibration import CalibrationParser


class ParameterParser:

    def parse_service_parameter(self, service_node, m):
        """
        Parse all parameters defined for a serivce.

        Iterates over all parameter tags and adds them to the list of
        parameters in the model.
        """
        for parameters_node in service_node.iterfind('parameters'):
            for node in parameters_node.iterchildren():
                self.parse_parameter(node, m, m.parameters, m.enumerations)
                # Parameter is automatically added to the list of parameters

    def parse_parameters(self, packet, node, m, reference_parameters, enumerations):
        for parameter_node in node:
            parameters = self.parse_parameter(parameter_node, m,
                                              reference_parameters, enumerations)
            if parameters is not None:
                for parameter in parameters:
                    packet.appendParameter(parameter)

    def parse_parameter(self, node, model, reference_parameters, enumerations):
        parameters = []
        uid = node.attrib.get("uid", "")
        if node.tag == "parameter" or node.tag == "repeater":
            name = node.attrib.get("name")
            description = pando.parser.common.parse_description(node)

            parameter_type = self._parse_type(node)
            if node.tag == "parameter":
                parameter = pando.model.Parameter(name=name,
                                                 uid=uid,
                                                 description=description,
                                                 parameter_type=parameter_type)

                parameter.unit = node.attrib.get("unit")

                calibration_node = node.find("calibration")
                if calibration_node is not None:
                    calibration_ref_node = calibration_node.find('calibrationRef')
                    if calibration_ref_node is not None:
                        uid = calibration_ref_node.attrib.get("uid")
                    else:
                        calibrations = CalibrationParser().parse_calibrations(calibration_node, model)
                        uid = calibrations[0].uid

                    parameter.calibration = model.calibrations[uid]

                self._parse_parameter_limits(node, parameter, parameter.calibration)

            elif node.tag == "repeater":
                parameter = pando.model.Repeater(name=name,
                                                uid=uid,
                                                description=description,
                                                parameter_type=parameter_type)
                self.parse_parameters(parameter, node, model, reference_parameters, enumerations)

            pando.parser.common.parse_short_name(parameter, node)
            self._parse_and_update_byte_order(node, parameter)

            value, value_type, value_range = self.parse_parameter_value(node)
            if value_type is not None:
                parameter.value = value
                parameter.valueType = value_type
                parameter.valueRange = value_range

            reference_parameters[parameter.uid] = parameter
            parameters.append(parameter)
        elif node.tag == "enumerationParameter":
            name = node.attrib.get("name")
            description = pando.parser.common.parse_description(node)
            enumName = node.attrib.get("enumeration")

            parameter_type = pando.model.EnumerationType(enumerations[enumName].width, enumName)
            parameter = pando.model.Parameter(name=name,
                                             uid=uid,
                                             description=description,
                                             parameter_type=parameter_type)

            pando.parser.common.parse_short_name(parameter, node)
            self._parse_and_update_byte_order(node, parameter)

            value, value_type, value_range = self.parse_parameter_value(node)
            if value_type is not None:
                if value_type == pando.model.Parameter.RANGE:
                    raise ParserException("Invalid value definition for enumeration '%s'. " \
                                          "Only 'fixed' or 'default' permitted" % uid)

                enum = enumerations[enumName]
                entry = enum.getEntryByName(value)
                if entry == None:
                    raise ParserException("Value '%s' not found in enumeration '%s'."
                                          % (value, uid))

                parameter.value = value
                parameter.valueType = value_type
                parameter.valueRange = value_range

            reference_parameters[parameter.uid] = parameter
            parameters.append(parameter)
        elif node.tag == "list":
            name = node.attrib.get("name")
            uid = node.attrib.get("uid")
            description = pando.parser.common.parse_description(node)

            parameter = pando.model.List(name=name, uid=uid, description=description)
            self.parse_parameters(parameter, node, model, reference_parameters, enumerations)

            reference_parameters[parameter.uid] = parameter
            parameters.append(parameter)
        elif node.tag == "parameterRef":
            # The parameter needs to be copied here. Otherwise the reference
            # parameter might be changed when we later assign fixed/default
            # values to parameters in the telecommand.
            parameter = copy.deepcopy(reference_parameters[uid])
            parameters.append(parameter)
        elif node.tag == lxml.etree.Comment:
            return None
        elif node.tag in ["description", "shortName", "byteOrder"]:
            # Description tags are already parsed for the repeater tags in their
            # handler. Nothing to do here.
            return None
        elif node.tag in ["fixed", "default", "range"]:
            return None
        else:
            raise ParserException("Unknown element '%s' found. Was expecting " \
                                  "'byteOrder|parameter|repeater|enumerationParameter|parameterRef'" % node.tag)

        return parameters

    @staticmethod
    def _parse_type(node):
        parameter_type = None
        typeattrib = node.attrib.get("type")
        for base in ["uint", "int", "float"]:
            if typeattrib.startswith(base):
                typeid = {
                    "uint": pando.model.ParameterType.UNSIGNED_INTEGER,
                    "int": pando.model.ParameterType.SIGNED_INTEGER,
                    "float": pando.model.ParameterType.REAL
                }[base]
                width = int(typeattrib[len(base):])
                parameter_type = pando.model.ParameterType(typeid, width)
                break
        else:
            if typeattrib == "boolean":
                typeid = pando.model.ParameterType.BOOLEAN
                width = 1
            elif typeattrib == "octet":
                typeid = pando.model.ParameterType.OCTET_STRING
                # convert width from bytes to bits
                width = int(node.attrib.get("width", 0)) * 8
            elif typeattrib == "ascii":
                typeid = pando.model.ParameterType.ASCII_STRING
                # convert width from bytes to bits
                width = int(node.attrib.get("width", 0)) * 8
            elif typeattrib == "Absolute Time CUC4":
                typeid = pando.model.ParameterType.ABSOLUTE_TIME
                width = 4 * 8
            elif typeattrib == "Absolute Time CUC4.2":
                typeid = pando.model.ParameterType.ABSOLUTE_TIME
                width = 6 * 8
            elif typeattrib == "Relative Time CUC4":
                typeid = pando.model.ParameterType.RELATIVE_TIME
                width = 4 * 8
            elif typeattrib == "Relative Time CUC4.2":
                typeid = pando.model.ParameterType.RELATIVE_TIME
                width = 6 * 8
            else:
                raise ParserException("Invalid type name '%s'" % typeattrib)

            parameter_type = pando.model.ParameterType(typeid, width)
        return parameter_type

    @staticmethod
    def _parse_parameter_limits(parameter_node, parameter, calibration):
        """
        Parse the telemetry parameter limits.

        Has to be done after the calibration for the parameter has been set,
        because the output type of the calibration is required if the limit
        input depends on the calibrated parameter value.
        """
        limits_node = parameter_node.find('limits')
        if limits_node is not None:
            sample_count = int(limits_node.attrib["samples"], 0)
            if limits_node.attrib["input"] == "calibrated":
                value_type = calibration.outputType
                limits = pando.model.Limits(input_type=pando.model.Limits.INPUT_CALIBRATED,
                                           value_type=value_type,
                                           samples=sample_count)
            else:
                value_type = parameter.valueType
                limits = pando.model.Limits(input_type=pando.model.Limits.INPUT_RAW,
                                           value_type=value_type,
                                           samples=sample_count)

            for check_node in limits_node:
                if check_node.tag == "warning":
                    limit = ParameterParser._parse_parameter_check(pando.model.Check.SOFT_LIMIT,
                                                                   value_type, check_node)
                    limits.checks.append(limit)
                elif check_node.tag == "error":
                    limit = ParameterParser._parse_parameter_check(pando.model.Check.HARD_LIMIT,
                                                                   value_type, check_node)
                    limits.checks.append(limit)

            parameter.limits = limits

    @staticmethod
    def _parse_parameter_check(limit_type, value_type, check_node):
        """
        Parse a single error or warning block.

        Both have the same semantic, therefore they are not differentiated here.
        """
        if value_type == pando.model.ParameterType.REAL:
            lower_limit = float(check_node.attrib["lower"])
            upper_limit = float(check_node.attrib["upper"])
        else:
            lower_limit = int(check_node.attrib["lower"], 0)
            upper_limit = int(check_node.attrib["upper"], 0)

        description = pando.parser.common.parse_description(check_node)

        check = pando.model.Check(limit_type, lower_limit, upper_limit, description)

        validity_node = check_node.find("validIfEqual")
        if validity_node is not None:
            check.validity_parameter_sid = validity_node.attrib["sid"]
            check.validity_parameter_value = validity_node.attrib["value"]

        return check

    @staticmethod
    def parse_parameter_value(node):
        value = None
        value_type = None
        value_range = None

        for tag in ["fixed", "default", "range"]:
            value_node = node.find(tag)
            if value_node is not None:
                if value_node.tag == "fixed":
                    value = value_node.attrib.get("value")
                    value_type = pando.model.Parameter.FIXED
                elif value_node.tag == "default":
                    value = value_node.attrib.get("value")
                    value_type = pando.model.Parameter.DEFAULT
                elif value_node.tag == "range":
                    value = value_node.attrib.get("default", None)
                    value_type = pando.model.Parameter.RANGE
                    value_range = pando.model.ParameterValueRange(
                        minimum=value_node.attrib.get("min"),
                        maximum=value_node.attrib.get("max"))

        return (value, value_type, value_range)

    @staticmethod
    def _parse_and_update_byte_order(node, parameter):
        for byte_order_node in node.findall("byteOrder"):
            parameter.byte_order = {
                "big-endian": pando.model.ByteOrder.BIG_ENDIAN,
                "little-endian": pando.model.ByteOrder.LITTLE_ENDIAN,
            }[byte_order_node.text]
