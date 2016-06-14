#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pdoc.model
import pdoc.parser.common

from .common import ParserException
from .parameter import ParameterParser

class PacketParser:
    """
    Parse telemetry and telecommand packets.
    """

    def parse_service_packets(self, service_node, m):
        for telemtries_node in service_node.iterfind('telemetries'):
            for node in telemtries_node.iterchildren('telemetry'):
                tm = self._parse_telemetry(node, m, m.parameters,
                                           m.enumerations)
                m.appendTelemetryPacket(tm)

        for telecommands_node in service_node.iterfind('telecommands'):
            for node in telecommands_node.iterchildren('telecommand'):
                tc = self._parse_telecommand(node, m, m.parameters,
                                             m.enumerations, m.telemetries)
                m.appendTelecommandPacket(tc)

    def _parse_telemetry(self, node, m, referenceParameters, enumerations):
        p = pdoc.model.Telemetry(name=node.attrib["name"],
                                 uid=node.attrib["uid"],
                                 description=pdoc.parser.common.parse_description(node))

        pdoc.parser.common.parse_short_name(p, node)
        self._parse_designators(p, node)
        self._parse_service_type(p, node)

        ParameterParser().parse_parameters(p, node.find("parameters"), m,
                                           referenceParameters, enumerations)
        p.updateRepeaterDepth()

        parameters = p.getParametersAsFlattenedList()
        self._parse_telemetry_identification_parameter(p, node, parameters)
        self._parse_additional_packet_fields(p, node)

        return p

    def _parse_telecommand(self, node, m, referenceParameters, enumerations, telemetries):
        p = pdoc.model.Telecommand(name=node.attrib["name"],
                                   uid=node.attrib["uid"],
                                   description=pdoc.parser.common.parse_description(node))

        pdoc.parser.common.parse_short_name(p, node)
        self._parse_designators(p, node)
        self._parse_service_type(p, node)

        ParameterParser().parse_parameters(p, node.find("parameters"), m,
                                           referenceParameters, enumerations)
        p.updateRepeaterDepth()
        self._parse_parameter_values(p, node, enumerations)

        self._parse_additional_packet_fields(p, node)

        for telemetry_uid in node.iterfind("relevantTelemetry/telemetryRef"):
            uid = telemetry_uid.attrib["uid"]
            telemetry = telemetries[uid]
            p.relevantTelemetry.append(telemetry)

        self._parse_telecommand_verification(p, node)

        critical = pdoc.parser.common.parse_text(node, "critical", "No")
        p.critical = {"Yes": True, "No": False}[critical]

        # TODO failureIdentification
        return p

    def _parse_parameter_values(self, tc, node, enumerations):
        parameters = tc.getParametersAsFlattenedList()

        for parameter_node in node.iterfind("parameterValues/parameterValue"):
            uid = parameter_node.attrib.get("uid")

            value, value_type, value_range = ParameterParser().parse_parameter_value(parameter_node)
            if value_type is not None:
                # Find corresponding parameter and set value
                for p in parameters:
                    if uid == p.uid:
                        if p.type.identifier is pdoc.model.ParameterType.ENUMERATION:
                            enum = enumerations[p.type.enumeration]
                            entry = enum.getEntryByName(value)
                            if entry == None:
                                raise ParserException("Value '%s' not found in enumeration '%s'."
                                                      % (value, uid))
                        p.value = value
                        p.valueType = value_type
                        p.valueRange = value_range
                        break
                else:
                    # No matching parameter found
                    raise ParserException("During value definition: " \
                                          "Parameter '%s' not found in telecommand '%s'!"
                                          % (uid, tc.uid))

    def _parse_designators(self, packet, node):
        designators_node = node.find("designators")
        if designators_node is not None:
            for designator in designators_node.iterfind("designator"):
                packet.designators.append({
                    "name":  designator.attrib["name"],
                    "value": designator.attrib["value"],
                })

    def _parse_service_type(self, packet, node):
        packet.serviceType = int(node.findtext("serviceType"))
        packet.serviceSubtype = int(node.findtext("serviceSubtype"))

    def _parse_telecommand_verification(self, packet, node):
        v = node.find("verification")

        if v is not None:
            packet.verification.acceptance = True if (v.findtext("acceptance") == "true") else False
            packet.verification.start = True if (v.findtext("start") == "true") else False
            packet.verification.progress = True if (v.findtext("progress") == "true") else False
            packet.verification.completion = True if (v.findtext("completion") == "true") else False

    def _parse_telemetry_identification_parameter(self, packet, node, parameters):
        for parameter_node in node.iterfind("packetIdentification/identificationParameter"):
            value = parameter_node.attrib["value"]
            uid = parameter_node.attrib["uid"]

            for p in parameters:
                if p.uid == uid:
                    parameter = pdoc.model.TelemetryIdentificationParameter(parameter=p, value=value)
                    break
            else:
                raise ParserException("Identification parameter '%s' was not found in packet '%s'"
                                      % (uid, packet.uid))

            packet.identificationParameter.append(parameter)


    def _parse_additional_packet_fields(self, packet, node):
        for key, default_heading in [('purpose', 'Purpose'),
                                     ('effects', 'Effects'),  # only for telecommand
                                     ('recommendation', 'Recommendation'),
                                     ('note', 'Note'),
                                     ('seeAlso', 'See Also'), ]:
            text = pdoc.parser.common.parse_text(node, key)
            if text is not None:
                packet.additional.append((default_heading, text))
