#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import lxml

import pdoc.model
import pdoc.parser.common

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
            description = pdoc.parser.common.parse_description(node)

            parameter_type = self._parse_type(node)
            if node.tag == "parameter":
                parameter = pdoc.model.Parameter(name=name,
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
                
                self._parse_parameter_limits(node, parameter)

            elif node.tag == "repeater":
                parameter = pdoc.model.Repeater(name=name,
                                                uid=uid,
                                                description=description,
                                                parameter_type=parameter_type)
                self.parse_parameters(parameter, node, model, reference_parameters, enumerations)

            pdoc.parser.common.parse_short_name(parameter, node)

            value, value_type, value_range = self.parse_parameter_value(node)
            if value_type is not None:
                parameter.value = value
                parameter.valueType = value_type
                parameter.valueRange = value_range

            reference_parameters[parameter.uid] = parameter
            parameters.append(parameter)
        elif node.tag == "enumerationParameter":
            name = node.attrib.get("name")
            description = pdoc.parser.common.parse_description(node)
            enumName = node.attrib.get("enumeration")

            parameter_type = pdoc.model.EnumerationType(enumerations[enumName].width, enumName)
            parameter = pdoc.model.Parameter(name=name,
                                             uid=uid,
                                             description=description,
                                             parameter_type=parameter_type)

            pdoc.parser.common.parse_short_name(parameter, node)

            value, value_type, value_range = self.parse_parameter_value(node)
            if value_type is not None:
                if value_type == pdoc.model.Parameter.RANGE:
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
            description = pdoc.parser.common.parse_description(node)

            parameter = pdoc.model.List(name=name, uid=uid, description=description)
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
        elif node.tag in ["description", "shortName"]:
            # Description tags are already parsed for the repeater tags in their
            # handler. Nothing to do here.
            return None
        elif node.tag in ["fixed", "default", "range"]:
            return None
        else:
            raise ParserException("Unknown element '%s' found. Was expecting " \
                                  "'parameter|repeater|enumerationParameter|parameterRef'" % node.tag)

        return parameters

    @staticmethod
    def _parse_type(node):
        parameter_type = None
        typeattrib = node.attrib.get("type")
        for base in ["uint", "int", "float"]:
            if typeattrib.startswith(base):
                typeid = {
                    "uint": pdoc.model.ParameterType.UNSIGNED_INTEGER,
                    "int": pdoc.model.ParameterType.SIGNED_INTEGER,
                    "float": pdoc.model.ParameterType.REAL
                }[base]
                width = int(typeattrib[len(base):])
                parameter_type = pdoc.model.ParameterType(typeid, width)
                break
        else:
            if typeattrib == "octet":
                typeid = pdoc.model.ParameterType.OCTET_STRING
                # convert width from bytes to bits
                width = int(node.attrib.get("width", 0)) * 8
            elif typeattrib == "ascii":
                typeid = pdoc.model.ParameterType.ASCII_STRING
                # convert width from bytes to bits
                width = int(node.attrib.get("width", 0)) * 8
            elif typeattrib == "Absolute Time CUC4":
                typeid = pdoc.model.ParameterType.ABSOLUTE_TIME
                width = 4 * 8
            elif typeattrib == "Absolute Time CUC4.2":
                typeid = pdoc.model.ParameterType.ABSOLUTE_TIME
                width = 6 * 8
            elif typeattrib == "Relative Time CUC4":
                typeid = pdoc.model.ParameterType.RELATIVE_TIME
                width = 4 * 8
            elif typeattrib == "Relative Time CUC4.2":
                typeid = pdoc.model.ParameterType.RELATIVE_TIME
                width = 6 * 8
            else:
                raise ParserException("Invalid type name '%s'" % typeattrib)

            parameter_type = pdoc.model.ParameterType(typeid, width)
        return parameter_type
    
    @staticmethod
    def _parse_parameter_limits(parameter_node, parameter):
        limits_node = parameter_node.find('limits')
        if limits_node is not None:
            if limits_node.attrib["input"] == "calibrated":
                input = pdoc.model.Limits.INPUT_CALIBRATED
            else:
                input = pdoc.model.Limits.INPUT_RAW
            
            limits = pdoc.model.Limits(input, int(limits_node.attrib["samples"], 0))
            
            for limit_node in limits_node.iterfind("warning"):
                limit = ParameterParser._parse_parameter_limit(limit_node)
                limits.warnings.append(limit)
            
            for limit_node in limits_node.iterfind("error"):
                limit = ParameterParser._parse_parameter_limit(limit_node)
                limits.errors.append(limit)
            
            parameter.limits = limits
    
    @staticmethod
    def _parse_parameter_limit(limit_node):
        """
        Parse a single error or warning block.
        
        Both have the same semantic, therefore they are not differentiated here.
        """
        lower_limit = limit_node.attrib["lower"]
        upper_limit = limit_node.attrib["upper"]
        description = pdoc.parser.common.parse_description(limit_node)
        
        limit = pdoc.model.Limit(lower_limit, upper_limit, description)
        
        validity_node = limit_node.find("validIfEqual")
        if validity_node is not None:
            limit.validity_parameter_sid = validity_node.attrib["sid"]
            limit.validity_parameter_value = validity_node.attrib["value"]
        
        return limit
    
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
                    value_type = pdoc.model.Parameter.FIXED
                elif value_node.tag == "default":
                    value = value_node.attrib.get("value")
                    value_type = pdoc.model.Parameter.DEFAULT
                elif value_node.tag == "range":
                    value = value_node.attrib.get("default", None)
                    value_type = pdoc.model.Parameter.RANGE
                    value_range = pdoc.model.ParameterValueRange(
                        minimum=value_node.attrib.get("min"),
                        maximum=value_node.attrib.get("max"))

        return (value, value_type, value_range)
