#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import lxml

import pdoc.model
import pdoc.parser.common

from .common import ParserException
from .parameter import ParameterParser

class PacketParser:
    """
    Parse telemetry and telecommand packets.
    """
    # EVENT_REPORT_ID_PARAMETER_UID = "event_report_id"
    EVENT_REPORT_ID_PARAMETER_UID = "s5_report_id"

    def parse_service_packets(self, service_node, model):
        for events_node in service_node.iterfind('events'):
            for node in events_node.iterchildren('event'):
                event = self._parse_event(node,
                                          model,
                                          model.parameters,
                                          model.enumerations)
                model.appendTelemetryPacket(event)

        for telemetries_node in service_node.iterfind('telemetries'):
            for node in telemetries_node.iterchildren('telemetry'):
                tm = self._parse_telemetry(node,
                                           model,
                                           model.parameters,
                                           model.enumerations)
                model.appendTelemetryPacket(tm)

            for node in telemetries_node.iterchildren('derivedTelemetry'):
                tm = self._parse_derived_telemetry(node,
                                                   model,
                                                   model.parameters,
                                                   model.enumerations,
                                                   model.telemetries)
                model.appendTelemetryPacket(tm)

        for telecommands_node in service_node.iterfind('telecommands'):
            for node in telecommands_node.iterchildren('telecommand'):
                tc = self._parse_telecommand(node,
                                             model,
                                             model.parameters,
                                             model.enumerations,
                                             model.telemetries)
                model.appendTelecommandPacket(tc)

            for node in telecommands_node.iterchildren('derivedTelecommand'):
                tc = self._parse_derived_telecommand(node,
                                                     model,
                                                     model.parameters,
                                                     model.enumerations,
                                                     model.telemetries,
                                                     model.telecommands)
                model.appendTelecommandPacket(tc)

    def _parse_event(self, node, model, reference_parameters, enumerations):
        name = node.attrib["name"]
        uid = node.attrib["uid"]
        description = pdoc.parser.common.parse_description(node)

        event = pdoc.model.Event(name=name, uid=uid, description=description)

        pdoc.parser.common.parse_short_name(event, node)

        self._parse_additional_packet_fields(event, node)

        event.report_id = int(node.findtext("reportId"))
        event.severity = {
            "progress": pdoc.model.Event.PROGRESS,
            "low": pdoc.model.Event.LOW_SEVERITY,
            "medium": pdoc.model.Event.MEDIUM_SEVERITY,
            "high": pdoc.model.Event.HIGH_SEVERITY,
        }[node.findtext("severity")]

        event.serviceType = 5
        event.serviceSubtype = int(event.severity)

        ParameterParser().parse_parameters(event,
                                           node.find("parameters"),
                                           model,
                                           reference_parameters, enumerations)

        # Copy all parameters as event parameters
        for parameter in event.getParameters():
            event.appendEventParameter(parameter)

        # Add the report identifier before the other parameters
        report_id_parameter = reference_parameters[self.EVENT_REPORT_ID_PARAMETER_UID]
        event.getParameters().insert(0, report_id_parameter)

        event.updateDepth()
        event.updateEventParameterDepth()

        identification_parameter = \
            pdoc.model.TelemetryIdentificationParameter(parameter=report_id_parameter,
                                                        value=str(event.report_id))
        event.identificationParameter.append(identification_parameter)
        return event

    def _parse_base_packet(self, cls, node, model, reference_parameters, enumerations):
        packet = cls(name=node.attrib["name"],
                     uid=node.attrib["uid"],
                     description=pdoc.parser.common.parse_description(node))

        pdoc.parser.common.parse_short_name(packet, node)
        self._parse_designators(packet, node)
        self._parse_service_type(packet, node)
        self._parse_additional_packet_fields(packet, node)
        
        ParameterParser().parse_parameters(packet,
                                           node.find("parameters"),
                                           model,
                                           reference_parameters, enumerations)
        packet.updateDepth()
        return packet

    def _parse_telemetry(self, node, model, reference_parameters, enumerations):
        packet = self._parse_base_packet(pdoc.model.Telemetry,
                                         node,
                                         model,
                                         reference_parameters,
                                         enumerations)

        parameters = packet.getParametersAsFlattenedList()
        self._parse_telemetry_identification_parameter(packet, node, parameters)
        return packet

    def _parse_telecommand(self, node, model, reference_parameters, enumerations, telemetries):
        packet = self._parse_base_packet(pdoc.model.Telecommand,
                                         node,
                                         model,
                                         reference_parameters,
                                         enumerations)
        
        self._parse_parameter_values(packet, node, enumerations)
        self._parse_telecommand_verification(packet, node)
        
        critical = pdoc.parser.common.parse_text(node, "critical", "No")
        packet.critical = {"Yes": True, "No": False}[critical]
        
        for telemetry_uid in node.iterfind("relevantTelemetry/telemetryRef"):
            uid = telemetry_uid.attrib["uid"]
            telemetry = telemetries[uid]
            packet.relevantTelemetry.append(telemetry)
        
        # TODO failureIdentification
        return packet

    def _parse_base_derived_packet(self, base_list, node, model, reference_parameters, enumerations):
        base_uid = node.attrib["extends"]
        packet = copy.deepcopy(base_list[base_uid])
        
        packet.uid = node.attrib["uid"]
        packet.name = node.attrib.get("name", packet.name)
        packet.description = pdoc.parser.common.parse_description(node, packet.description)
        pdoc.parser.common.parse_short_name(packet, node, packet.shortName)

        self._parse_designators(packet, node)
        self._parse_service_type(packet, node,
                                 packet.serviceType,
                                 packet.serviceSubtype)
        self._parse_additional_packet_fields(packet, node)

        self._parse_override_parameters(packet,
                                        node.find("parameters"),
                                        model,
                                        reference_parameters,
                                        enumerations)
        packet.updateDepth()
        return packet

    def _parse_derived_telemetry(self, node, model, reference_parameters, enumerations, telemetries):
        packet = self._parse_base_derived_packet(telemetries,
                                                 node,
                                                 model,
                                                 reference_parameters,
                                                 enumerations)

        parameters = packet.getParametersAsFlattenedList()
        self._parse_telemetry_identification_parameter(packet, node, parameters)

        return packet

    def _parse_derived_telecommand(self, node, model, reference_parameters, enumerations, telemetries, telecommands):
        packet = self._parse_base_derived_packet(telecommands,
                                                 node,
                                                 model,
                                                 reference_parameters,
                                                 enumerations)
        
        self._parse_parameter_values(packet, node, enumerations)
        self._parse_telecommand_verification(packet, node)

        critical = pdoc.parser.common.parse_text(node, "critical", None)
        if critical is not None:
            packet.critical = {"Yes": True, "No": False}[critical]

        for telemetry_uid in node.iterfind("relevantTelemetry/telemetryRef"):
            uid = telemetry_uid.attrib["uid"]
            telemetry = telemetries[uid]
            # FIXME overwrite
            packet.relevantTelemetry.append(telemetry)

        # TODO failureIdentification
        return packet

    def _parse_override_parameters(self, packet, node, model, reference_parameters, enumerations):
        if node is None:
            return

        for parameter_node in node:
            if parameter_node.tag == "overrideParameterRef":
                parameter = reference_parameters[parameter_node.attrib["uid"]]
                override_uid = parameter_node.attrib["overrides"]

                self._replace_parameter_in_packet(packet, override_uid=override_uid, override_parameter=parameter)
            elif node.tag == lxml.etree.Comment:
                pass
            else:
                parameters = ParameterParser().parse_parameter(parameter_node, model,
                                                               reference_parameters, enumerations)
                if parameters is not None:
                    for parameter in parameters:
                        packet.appendParameter(parameter)

    def _replace_parameter_in_packet(self, packet, override_uid, override_parameter):
        
        def handle_collection(collection, override_uid, override_parameter):
            for key, parameter in enumerate(collection.parameters):
                if parameter.uid == override_uid:
                    collection.parameters[key] = override_parameter
                    return True
                elif parameter.is_collection:
                    handle_collection(parameter, override_uid, override_parameter)
            return False

        handle_collection(packet, override_uid, override_parameter)

    def _parse_parameter_values(self, packet, node, enumerations):
        parameters = packet.getParametersAsFlattenedList()

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
                                          % (uid, packet.uid))

    def _parse_designators(self, packet, node):
        designators_node = node.find("designators")
        if designators_node is not None:
            for designator in designators_node.iterfind("designator"):
                # FIXME overwrite exsisting ones
                packet.designators.append({
                    "name":  designator.attrib["name"],
                    "value": designator.attrib["value"],
                })

    def _parse_service_type(self, packet, node, default_type=None, default_subtype=None):
        packet.serviceType = int(node.findtext("serviceType", str(default_type)))
        packet.serviceSubtype = int(node.findtext("serviceSubtype", str(default_subtype)))

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
                # FIXME overwrite exisiting entries
                packet.additional.append((default_heading, text))
