#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML parser for the packet description files.

Reads the description from a set of XML files and populates the model with
the result.
"""

import re
import copy

from . import pkg

# lxml must be imported **after** the Catalog file have been set by 'pkg', otherwise
# it runs into an endless loop during verification.
import lxml.etree

from . import model

class ParserException(Exception):
    pass


class Parser:

    def parse(self, filename, xsdfile=None):
        rootnode = self._validateAndParse(filename, xsdfile)

        m = model.Model()

        # Parse packet/parameter structure
        for serviceNode in rootnode.iterfind('service'):
            # TODO failure codes
            
            for enumerationsNode in serviceNode.iterfind('enumerations'):
                for node in enumerationsNode.iterchildren('enumeration'):
                    enumeration = self._parseEnumeration(node)
                    m.enumerations[enumeration.uid] = enumeration

            for calibrationsNode in serviceNode.iterfind('calibrations'):
                self._parseCalibrations(calibrationsNode, m)

        for serviceNode in rootnode.iterfind('service'):
            for parametersNode in serviceNode.iterfind('parameters'):
                for node in parametersNode.iterchildren():
                    self._parseParameter(node, m, m.parameters, m.enumerations)
                    # Parameter is automatically added to the list of parameters

        for serviceNode in rootnode.iterfind('service'):
            for telemtriesNode in serviceNode.iterfind('telemetries'):
                for node in telemtriesNode.iterchildren('telemetry'):
                    tm = self._parseTelemetry(node, m, m.parameters,
                                              m.enumerations)
                    m.appendTelemetryPacket(tm)

            for telecommandsNode in serviceNode.iterfind('telecommands'):
                for node in telecommandsNode.iterchildren('telecommand'):
                    tc = self._parseTelecommand(node, m, m.parameters,
                                                m.enumerations, m.telemetries)
                    m.appendTelecommandPacket(tc)

        # Parse SCOS mapping information
        for mappingNode in rootnode.iterfind('mapping'):
            subsystemId = int(mappingNode.attrib["subsystem"], 0)
            subsystemName = mappingNode.attrib["name"]
            subsystem = m.getOrAddSubsystem(subsystemId, subsystemName)

            for node in mappingNode.iterfind('enumerations/telecommand/enumerationMapping'):
                uid, sid = self._parseMapping(node)
                enumeration = m.enumerations[uid]
                subsystem.telecommandEnumerations[uid] = \
                    model.EnumerationMapping(sid=sid, enumeration=enumeration)
            for node in mappingNode.iterfind('enumerations/telemetry/enumerationMapping'):
                uid, sid = self._parseMapping(node)
                enumeration = m.enumerations[uid]
                subsystem.telemetryEnumerations[uid] = \
                    model.EnumerationMapping(sid=sid, enumeration=enumeration)

            for node in mappingNode.iterfind('calibrations/telecommand/calibrationMapping'):
                uid, sid = self._parseMapping(node)
                calibration = m.calibrations[uid]
                subsystem.telecommandCalibrations[uid] = \
                    model.CalibrationMapping(sid=sid, calibration=calibration)
            for node in mappingNode.iterfind('calibrations/telemetry/calibrationMapping'):
                uid, sid = self._parseMapping(node)
                calibration = m.calibrations[uid]
                subsystem.telemetryCalibrations[uid] = \
                    model.CalibrationMapping(sid=sid, calibration=calibration)

            for node in mappingNode.iterfind('telecommandParameters/parameterMapping'):
                uid, sid = self._parseMapping(node)
                parameter = m.parameters[uid]
                subsystem.telecommandParameters[uid] = \
                    model.ParameterMapping(sid=sid, parameter=parameter)

            for node in mappingNode.iterfind('application'):
                app = self._parseApplicationMapping(node, m)
                subsystem.applications[app.apid] = app

        # Extract telecommand and telemetry enumerations and calibrations
        for subsystem in m.subsystems.values():
            for application in subsystem.applications.values():
                for tm in application.getTelemetries():
                    for p in tm.telemetry.getParametersAsFlattenedList():
                        if p.type.identifier == model.ParameterType.ENUMERATION:
                            e = p.type.enumeration
                            m.telemetryEnumerations[e] = m.enumerations[e]

                        calibration = p.calibration
                        if calibration is not None:
                            calibration = m.calibrations[calibration.uid]
                            self._verifyTelemetryCalibration(calibration, p)
                            m.telemetryCalibrations[calibration.uid] = calibration

                for tc in application.getTelecommands():
                    for p in tc.telecommand.getParametersAsFlattenedList():
                        if p.type.identifier == model.ParameterType.ENUMERATION:
                            e = p.type.enumeration
                            m.telecommandEnumerations[e] = m.enumerations[e]

                        calibration = p.calibration
                        if calibration is not None:
                            calibration = m.calibrations[calibration.uid]
                            self._verifyTelecommandCalibration(calibration, p)
                            m.telecommandCalibrations[p.calibration.uid] = calibration
        return m

    def _verifyTelemetryCalibration(self, calibration, parameter):
        if calibration.type == model.Calibration.INTERPOLATION_TELECOMMAND:
            raise ParserException("Invalid calibration for parameter '%s' (%s). " \
                                  "'telecommandInterpolation' is invalid for " \
                                  "telemetry parameter!"
                                  % (parameter.name, parameter.uid))
        elif calibration.type == model.Calibration.INTERPOLATION_TELEMETRY:
            inputType = calibration.typeFromParameterType(parameter.type)
            if calibration.inputType is None:
                calibration.inputType = inputType
            else:
                if calibration.inputType != inputType:
                    raise ParserException("Invalid input type for telemetry " \
                                          "interpolation '%s'. Parameter %s (%s) "\
                                          "requires '%s', previous definition is '%s'"
                                          % (calibration.uid, parameter.name, parameter.uid,
                                             inputType, calibration.inputType))

    def _verifyTelecommandCalibration(self, calibration, parameter):
        if calibration.type != model.Calibration.INTERPOLATION_TELECOMMAND:
            raise ParserException("Invalid calibration for parameter '%s' (%s). " \
                                  "Only 'telecommandInterpolation' is available " \
                                  "for telecommand parameter!"
                                  % (parameter.name, parameter.uid))
        else:
            outputType = calibration.typeFromParameterType(parameter.type)
            if calibration.outputType is None:
                calibration.outputType = outputType
            else:
                if calibration.outputType != outputType:
                    raise ParserException("Invalid output type for telecommand " \
                                          "interpolation '%s'. Parameter %s (%s) "\
                                          "requires '%s', previous definition is '%s'"
                                          % (calibration.uid, parameter.name, parameter.uid,
                                             outputType, calibration.outputType))

    def _validateAndParse(self, filename, xsdfile):
        try:
            # parse the xml-file
            parser = lxml.etree.XMLParser(no_network=True)
            xmlroot = lxml.etree.parse(filename, parser=parser)
            xmlroot.xinclude()

            if xsdfile is None:
                xsdfile = pkg.get_filename('pdoc', 'resources/schema/telecommunication.xsd')

            xmlschema = lxml.etree.parse(xsdfile, parser=parser)

            schema = lxml.etree.XMLSchema(xmlschema)
            schema.assertValid(xmlroot)

            rootnode = xmlroot.getroot()
        except OSError as e:
            raise ParserException(e)
        except (lxml.etree.DocumentInvalid,
                lxml.etree.XMLSyntaxError,
                lxml.etree.XMLSchemaParseError,
                lxml.etree.XIncludeError) as e:
            raise ParserException("While parsing '%s': %s" % (e.error_log.last_error.filename, e))

        if rootnode.tag != "telecommunication":
            raise ParserException("Expected rootnode 'telecommunication', got '%s' in file '%s'" %
                                  (rootnode.tag, filename))

        return rootnode

    def _parseTelemetry(self, node, m, referenceParameters, enumerations):
        p = model.Telemetry(name=node.attrib["name"],
                            uid=node.attrib["uid"],
                            description=self._parseText(node, "description", ""))

        self._parseShortName(p, node)
        self._parseDesignators(p, node)
        self._parseServiceType(p, node)

        self._parseParameters(p, node.find("parameters"), m,
                              referenceParameters, enumerations)
        p.updateGroupDepth()

        parameters = p.getParametersAsFlattenedList()
        self._parseIdentificationParameter(p, node, parameters)
        self._parsePacketAdditionalFields(p, node)

        return p

    def _parseTelecommand(self, node, m, referenceParameters, enumerations, telemetries):
        p = model.Telecommand(name=node.attrib["name"],
                              uid=node.attrib["uid"],
                              description=self._parseText(node, "description", ""))

        self._parseShortName(p, node)
        self._parseDesignators(p, node)
        self._parseServiceType(p, node)

        self._parseParameters(p, node.find("parameters"), m,
                              referenceParameters, enumerations)
        p.updateGroupDepth()
        self._parseParameterValues(p, node, enumerations)

        self._parsePacketAdditionalFields(p, node)

        for telemetryUid in node.iterfind("relevantTelemetry/telemetryRef"):
            uid = telemetryUid.attrib["uid"]
            telemetry = telemetries[uid]
            p.relevantTelemetry.append(telemetry)

        self._parseVerification(p, node)

        critical = self._parseText(node, "critical", "No")
        p.critical = {"Yes": True, "No": False}[critical]

        # TODO failureIdentification

        return p

    def _parseDesignators(self, packet, node):
        designatorNodes = node.find("designators")
        if designatorNodes is not None:
            for designator in designatorNodes.iterfind("designator"):
                packet.designators.append({
                    "name":  designator.attrib["name"],
                    "value": designator.attrib["value"],
                })

    def _parseServiceType(self, packet, node):
        packet.serviceType = int(node.findtext("serviceType"))
        packet.serviceSubtype = int(node.findtext("serviceSubtype"))

    def _parseShortName(self, packet, node):
        packet.shortName = node.findtext("shortName", "")

        if packet.shortName == "":
            packet.shortName = packet.name

    def _parseVerification(self, packet, node):
        v = node.find("verification")

        if v is not None:
            packet.verification.acceptance = True if (v.findtext("acceptance") == "true") else False
            packet.verification.start = True if (v.findtext("start") == "true") else False
            packet.verification.progress = True if (v.findtext("progress") == "true") else False
            packet.verification.completion = True if (v.findtext("completion") == "true") else False

    def _parseIdentificationParameter(self, packet, node, parameters):
        for parameterNode in node.iterfind("packetIdentification/identificationParameter"):
            value = parameterNode.attrib["value"]
            uid = parameterNode.attrib["uid"]

            for p in parameters:
                if p.uid == uid:
                    parameter = model.TelemetryIdentificationParameter(parameter=p, value=value)
                    break
            else:
                raise ParserException("Identification parameter '%s' was not found in packet '%s'"
                                      % (uid, packet.uid))

            packet.identificationParameter.append(parameter)


    def _parsePacketAdditionalFields(self, packet, node):
        for key, defaultHeading in [('purpose', 'Purpose'),
                                    ('effects', 'Effects'),     # only for telecommand
                                    ('recommendation', 'Recommendation'),
                                    ('note', 'Note'),
                                    ('seeAlso', 'See Also'),]:
            text = self._parseText(node, key)
            if text is not None:
                packet.additional.append((defaultHeading, text))

    def _parseParameters(self, packet, node, m, referenceParameters, enumerations):
        for parameterNode in node:
            parameters = self._parseParameter(parameterNode, m,
                                              referenceParameters, enumerations)
            if parameters is not None:
                for parameter in parameters:
                    packet.appendParameter(parameter)

    def _parseParameter(self, node, m, referenceParameters, enumerations):
        parameters = []
        uid = node.attrib.get("uid", "")
        if node.tag == "parameter" or node.tag == "group":
            name = node.attrib.get("name")
            description = self._parseText(node, "description", "")

            parameterType = self._parseType(node)
            if node.tag == "parameter":
                parameter = model.Parameter(name=name, uid=uid,
                                            description=description, parameterType=parameterType)

                parameter.unit = node.attrib.get("unit")

                calibrationNode = node.find("calibration")
                if calibrationNode is not None:
                    calibrationRefNode = calibrationNode.find('calibrationRef')
                    if calibrationRefNode is not None:
                        uid = calibrationRefNode.attrib.get("uid")
                    else:
                        calibrations = self._parseCalibrations(calibrationNode, m)
                        uid = calibrations[0].uid

                    parameter.calibration = m.calibrations[uid]

            elif node.tag == "group":
                parameter = model.Group(name=name, uid=uid,
                                        description=description, parameterType=parameterType)
                self._parseParameters(parameter, node, m, referenceParameters, enumerations)

            self._parseShortName(parameter, node)

            value, valueType, valueRange = self._parseParameterValue(node)
            if valueType is not None:
                parameter.value = value
                parameter.valueType = valueType
                parameter.valueRange = valueRange

            referenceParameters[parameter.uid] = parameter
            parameters.append(parameter)
        elif node.tag == "enumerationParameter":
            name = node.attrib.get("name")
            description = self._parseText(node, "description", "")
            enumName = node.attrib.get("enumeration")

            parameterType = model.EnumerationType(enumerations[enumName].width, enumName)
            parameter = model.Parameter(name=name, uid=uid, description=description,
                                        parameterType=parameterType)

            self._parseShortName(parameter, node)

            value, valueType, valueRange = self._parseParameterValue(node)
            if valueType is not None:
                if valueType == model.Parameter.RANGE:
                    raise ParserException("Invalid value definition for enumeration '%s'. " \
                                          "Only 'fixed' or 'default' permitted" % uid)

                enum = enumerations[enumName]
                entry = enum.getEntryByName(value)
                if entry == None:
                    raise ParserException("Value '%s' not found in enumeration '%s'."
                                          % (value, uid))

                parameter.value = value
                parameter.valueType = valueType
                parameter.valueRange = valueRange

            referenceParameters[parameter.uid] = parameter
            parameters.append(parameter)
        elif node.tag == "list":
            name = node.attrib.get("name")
            uid = node.attrib.get("uid")
            description = self._parseText(node, "description", "")

            parameter = model.List(name=name, uid=uid, description=description)
            self._parseParameters(parameter, node, m, referenceParameters, enumerations)

            referenceParameters[parameter.uid] = parameter
            parameters.append(parameter)
        elif node.tag == "parameterRef":
            # The parameter needs to be copied here. Otherwise the reference
            # parameter might be changed when we later assign fixed/default
            # values to parameters in the telecommand.
            parameter = copy.deepcopy(referenceParameters[uid])
            parameters.append(parameter)
        elif node.tag == lxml.etree.Comment:
            return None
        elif node.tag in ["description", "shortName"]:
            # Description tags are already parsed for the group tags in their
            # handler. Nothing to do here.
            return None
        elif node.tag in ["fixed", "default", "range"]:
            return None
        else:
            raise ParserException("Unknown element '%s' found. Was expecting " \
                                  "'parameter|group|enumerationParameter|parameterRef'" % node.tag)

        return parameters

    def _parseCalibrations(self, node, m):
        calibrations = []
        for calibrationNode in node.iterchildren('telemetryInterpolation'):
            calibration = self._parseCalibrationInterpolationTelemetry(calibrationNode)
            m.calibrations[calibration.uid] = calibration
            calibrations.append(calibration)
        for calibrationNode in node.iterchildren('telecommandInterpolation'):
            calibration = self._parseCalibrationInterpolationTelecommand(calibrationNode)
            m.calibrations[calibration.uid] = calibration
            calibrations.append(calibration)
        for calibrationNode in node.iterchildren('polynom'):
            calibration = self._parseCalibrationPolynom(calibrationNode)
            m.calibrations[calibration.uid] = calibration
            calibrations.append(calibration)
        return calibrations

    def _parseText(self, node, tag, defaultValue=None):
        """ Removes indentation from text tags """
        text = node.findtext(tag, defaultValue)

        if text is not None:
            toStrip = None
            lines = []
            for line in text.split('\n'):
                if toStrip is None:
                    if line == '' or line.isspace():
                        continue

                    # First line which is not only whitespace
                    match = re.match(r'^(\s*)', text)
                    toStrip = match.group(1)

                lines.append(line.lstrip(toStrip))
            text = ("\n".join(lines)).rstrip()

        return text


    def _parseType(self, node):
        parameterType = None
        typeattrib = node.attrib.get("type")
        for base in ["uint", "int", "float"]:
            if typeattrib.startswith(base):
                typeid = {
                    "uint": model.ParameterType.UNSIGNED_INTEGER,
                    "int": model.ParameterType.SIGNED_INTEGER,
                    "float": model.ParameterType.REAL
                }[base]
                width = int(typeattrib[len(base):])
                parameterType = model.ParameterType(typeid, width)
                break
        else:
            if typeattrib == "octet":
                typeid = model.ParameterType.OCTET_STRING
                # convert width from bytes to bits
                width = int(node.attrib.get("width", 0)) * 8
            elif typeattrib == "ascii":
                typeid = model.ParameterType.ASCII_STRING
                # convert width from bytes to bits
                width = int(node.attrib.get("width", 0)) * 8
            elif typeattrib == "Absolute Time CUC4":
                typeid = model.ParameterType.ABSOLUTE_TIME
                width = 4 * 8
            elif typeattrib == "Absolute Time CUC4.2":
                typeid = model.ParameterType.ABSOLUTE_TIME
                width = 6 * 8
            elif typeattrib == "Relative Time CUC4":
                typeid = model.ParameterType.RELATIVE_TIME
                width = 4 * 8
            elif typeattrib == "Relative Time CUC4.2":
                typeid = model.ParameterType.RELATIVE_TIME
                width = 6 * 8
            else:
                raise ParserException("Invalid type name '%s'" % typeattrib)

            parameterType = model.ParameterType(typeid, width)
        return parameterType


    def _parseParameterValues(self, tc, node, enumerations):
        parameters = tc.getParametersAsFlattenedList()

        for parameterNode in node.iterfind("parameterValues/parameterValue"):
            uid = parameterNode.attrib.get("uid")

            value, valueType, valueRange = self._parseParameterValue(parameterNode)
            if valueType is not None:
                # Find corresponding parameter and set value
                for p in parameters:
                    if uid == p.uid:
                        if p.type.identifier is model.ParameterType.ENUMERATION:
                            enum = enumerations[p.type.enumeration]
                            entry = enum.getEntryByName(value)
                            if entry == None:
                                raise ParserException("Value '%s' not found in enumeration '%s'."
                                                      % (value, uid))
                        p.value = value
                        p.valueType = valueType
                        p.valueRange = valueRange
                        break
                else:
                    # No matching parameter found
                    raise ParserException("During value definition: " \
                                          "Parameter '%s' not found in telecommand '%s'!"
                                          % (uid, tc.uid))

    def _parseParameterValue(self, node):
        value = None
        valueType = None
        valueRange = None

        for tag in ["fixed", "default", "range"]:
            valueNode = node.find(tag)
            if valueNode is not None:
                if valueNode.tag == "fixed":
                    value = valueNode.attrib.get("value")
                    valueType = model.Parameter.FIXED
                elif valueNode.tag == "default":
                    value = valueNode.attrib.get("value")
                    valueType = model.Parameter.DEFAULT
                elif valueNode.tag == "range":
                    value = valueNode.attrib.get("default", None)
                    valueType = model.Parameter.RANGE
                    valueRange = model.ParameterValueRange(
                        minimum=valueNode.attrib.get("min"),
                        maximum=valueNode.attrib.get("max"))

        return (value, valueType, valueRange)


    def _parseEnumeration(self, node):
        e = model.Enumeration(name=node.attrib.get("name"),
                              uid=node.attrib.get("uid"),
                              width=int(node.attrib.get("width")),
                              description=self._parseText(node, "description", ""))

        self._parseShortName(e, node)

        for entry in node.iterfind("entry"):
            e.appendEntry(self._parseEnumerationEntry(entry))

        return e


    def _parseEnumerationEntry(self, node):
        entry = model.EnumerationEntry(node.attrib.get("name"),
                                       node.attrib.get("value"),
                                       self._parseText(node, "description", ""))
        return entry

    def _toBoolean(self, s):
        return True if (s == "true" or s == "1") else False

    def _toInterpolationType(self, typeString):
        return {
            "Unsigned Integer": model.Interpolation.UNSIGNED_INTEGER,
            "Signed Integer": model.Interpolation.SIGNED_INTEGER,
            "Float": model.Interpolation.REAL
        }[typeString]

    def _parseCalibrationInterpolationTelemetry(self, node):
        c = model.Interpolation(model.Calibration.INTERPOLATION_TELEMETRY,
                                name=node.attrib.get("name"),
                                uid=node.attrib.get("uid"),
                                description=self._parseText(node, "description", ""))
        c.extrapolate = self._toBoolean(node.attrib.get("extrapolate", "true"))
        c.outputType = self._toInterpolationType(node.attrib.get("outputType"))
        c.unit = node.attrib.get("unit", "")
        for pointNode in node.iterfind("point"):
            c.appendPoint(self._parseCalibrationInterpolationPoint(pointNode))
        return c

    def _parseCalibrationInterpolationTelecommand(self, node):
        c = model.Interpolation(model.Calibration.INTERPOLATION_TELECOMMAND,
                                name=node.attrib.get("name"),
                                uid=node.attrib.get("uid"),
                                description=self._parseText(node, "description", ""))
        c.extrapolate = self._toBoolean(node.attrib.get("extrapolate", "true"))
        c.inputType = self._toInterpolationType(node.attrib.get("inputType"))
        for pointNode in node.iterfind("point"):
            c.appendPoint(self._parseCalibrationInterpolationPoint(pointNode))
        return c

    def _parseCalibrationInterpolationPoint(self, node):
        p = model.Interpolation.Point(float(node.attrib.get("x")),
                                      float(node.attrib.get("y")))
        return p

    def _parseCalibrationPolynom(self, node):
        c = model.Polynom(name=node.attrib.get("name"),
                          uid=node.attrib.get("uid"),
                          description=self._parseText(node, "description", ""))

        c.a0 = float(node.attrib.get("a0", "0"))
        c.a1 = float(node.attrib.get("a1", "0"))
        c.a2 = float(node.attrib.get("a2", "0"))
        c.a3 = float(node.attrib.get("a3", "0"))
        c.a4 = float(node.attrib.get("a4", "0"))

        return c

    def _parseApplicationMapping(self, node, tmtcModel):
        """ Parse an application mapping.

        Returns a model.ApplicationMapping class.
        """
        application = model.ApplicationMapping(name=node.attrib.get("name"),
                                               apid=int(node.attrib["apid"], 0),
                                               description=self._parseText(node, "description", ""))

        application.namePrefix = node.attrib.get("namePrefix", "")
        application.nameSuffix = node.attrib.get("nameSuffix", "")

        for telemetryNode in node.iterfind("telemetries/telemetry"):
            uid, sid = self._parseMapping(telemetryNode)

            telemetry = tmtcModel.telemetries[uid]
            telemetryMapping = model.TelemetryMapping(sid=sid, telemetry=telemetry)
            for parameterNode in telemetryNode.findall("parameterMapping"):
                uid, sid = self._parseMapping(parameterNode)
                try:
                    parameter = tmtcModel.parameters[uid]
                except KeyError:
                    raise ParserException("Parameter '%s' not found in mapping of '%s'!"
                                          % (uid, telemetry.uid))
                telemetryMapping.appendParameter(
                    model.ParameterMapping(sid=sid,
                                           parameter=parameter))

            application.appendTelemetry(telemetryMapping)

        for telecommandNode in node.iterfind("telecommands/telecommandMappingRef"):
            uid, sid = self._parseMapping(telecommandNode)
            telecommand = tmtcModel.telecommands[uid]
            application.appendTelecommand(
                model.TelecommandMapping(sid=sid,
                                         telecommand=telecommand))

        return application

    def _parseMapping(self, node):
        return node.attrib["uid"], node.attrib["sid"]

