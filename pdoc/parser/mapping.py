#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pdoc.model
import pdoc.parser.common

from .common import ParserException

class MappingParser:

    def parse(self, rootnode, model):

        # Parse SCOS mapping information
        for mapping_node in rootnode.iterfind('mapping'):
            subsystem_id = int(mapping_node.attrib["subsystem"], 0)
            subsystem_name = mapping_node.attrib["name"]
            subsystem = model.getOrAddSubsystem(subsystem_id, subsystem_name)

            subsystem.description = pdoc.parser.common.parse_text(mapping_node, "description", "")

            for node in mapping_node.iterfind('enumerations/telecommand/enumerationMapping'):
                uid, sid = self._parse_mapping(node)
                enumeration = model.enumerations[uid]
                subsystem.telecommandEnumerations[uid] = \
                    pdoc.model.EnumerationMapping(sid=sid, enumeration=enumeration, subsystem=subsystem)
            for node in mapping_node.iterfind('enumerations/telemetry/enumerationMapping'):
                uid, sid = self._parse_mapping(node)
                enumeration = model.enumerations[uid]
                subsystem.telemetryEnumerations[uid] = \
                    pdoc.model.EnumerationMapping(sid=sid, enumeration=enumeration, subsystem=subsystem)

            for node in mapping_node.iterfind('calibrations/telecommand/calibrationMapping'):
                uid, sid = self._parse_mapping(node)
                calibration = model.calibrations[uid]
                subsystem.telecommandCalibrations[uid] = \
                    pdoc.model.CalibrationMapping(sid=sid, calibration=calibration, subsystem=subsystem)
            for node in mapping_node.iterfind('calibrations/telemetry/calibrationMapping'):
                uid, sid = self._parse_mapping(node)
                calibration = model.calibrations[uid]
                subsystem.telemetryCalibrations[uid] = \
                    pdoc.model.CalibrationMapping(sid=sid, calibration=calibration, subsystem=subsystem)

            for node in mapping_node.iterfind('telecommandParameters/parameterMapping'):
                uid, sid = self._parse_mapping(node)
                parameter = model.parameters[uid]
                subsystem.telecommandParameters[uid] = \
                    pdoc.model.ParameterMapping(sid=sid, parameter=parameter)

            for node in mapping_node.iterfind('application'):
                application = self._parse_application_mapping(node, subsystem, model)
                subsystem.applications[application.apid] = application

        self._verify_calibrations(model)

    def _parse_application_mapping(self, node, subsystem, model):
        """ Parse an application mapping.

        Returns a pdoc.model.ApplicationMapping class.
        """
        application = pdoc.model.ApplicationMapping(name=node.attrib.get("name"),
                                                    apid=int(node.attrib["apid"], 0),
                                                    description=pdoc.parser.common.parse_description(node))

        application.namePrefix = node.attrib.get("namePrefix", "")
        application.nameSuffix = node.attrib.get("nameSuffix", "")

        for telemetry_node in node.iterfind("events/event"):
            telemetry_mapping = self._parse_telemetry_mapping(telemetry_node, pdoc.model.EventMapping, model)
            self._add_packet_classes(subsystem, telemetry_mapping)
            application.appendTelemetry(telemetry_mapping)

        for telemetry_node in node.iterfind("telemetries/telemetry"):
            telemetry_mapping = self._parse_telemetry_mapping(telemetry_node, pdoc.model.TelemetryMapping, model)
            self._add_packet_classes(subsystem, telemetry_mapping)
            application.appendTelemetry(telemetry_mapping)

        for telecommand_node in node.iterfind("telecommands/telecommandMappingRef"):
            telecommand_mapping = self._parse_telecommand_mapping(telecommand_node, model)
            self._add_packet_classes(subsystem, telecommand_mapping)
            application.appendTelecommand(telecommand_mapping)

        return application

    @staticmethod
    def _add_packet_classes(subsystem, mapping):
        if mapping.packet_class is None:
            subsystem.packets_by_packet_class[None].append(mapping)
        else:
            for packet_class in mapping.packet_class:
                subsystem.packets_by_packet_class[packet_class].append(mapping)

    def _parse_telemetry_mapping(self, node, cls, model):
        uid, sid = self._parse_mapping(node)
        telemetry = model.telemetries[uid]

        telemetry_mapping = cls(sid=sid, telemetry=telemetry)

        # FIXME check for Event mapping
        if telemetry_mapping.packet_type != telemetry.packet_type:
            packet_type = {
                pdoc.model.Packet.TELEMETRY: "telemetry packet",
                pdoc.model.Packet.EVENT: "event",
            }[telemetry.packet_type]
            raise ParserException("Mapping must be done as %s for '%s' (%s)!"
                                  % (packet_type, uid, sid))

        packet_generation = pdoc.parser.common.parse_packet_generation(node, telemetry_mapping)
        if packet_generation:
            telemetry_mapping.packet_generation = packet_generation
        else:
            telemetry_mapping.packet_generation = telemetry.packet_generation

        telemetry_mapping.packet_class = \
            pdoc.parser.common.parse_packet_classes(node, telemetry.packet_class)

        for parameter_node in node.findall("parameterMapping"):
            uid, sid = self._parse_mapping(parameter_node)
            try:
                parameter = model.parameters[uid]
            except KeyError:
                raise ParserException("Parameter '%s' not found in mapping of '%s'!"
                                      % (uid, telemetry.uid))
            telemetry_mapping.appendParameter(
                pdoc.model.ParameterMapping(sid=sid, parameter=parameter))
        return telemetry_mapping

    @staticmethod
    def _parse_mapping(node):
        return node.attrib["uid"], node.attrib["sid"]

    def _parse_telecommand_mapping(self, node, model):
        uid, sid = self._parse_mapping(node)
        telecommand = model.telecommands[uid]

        telecommand_mapping = pdoc.model.TelecommandMapping(sid=sid, telecommand=telecommand)
        telecommand_mapping.packet_class = \
            pdoc.parser.common.parse_packet_classes(node, telecommand.packet_class)
        return telecommand_mapping

    def _verify_calibrations(self, m):
        for subsystem in m.subsystems.values():
            for application in subsystem.applications.values():
                for tm in application.getTelemetries():
                    for p in tm.telemetry.getParametersAsFlattenedList():
                        calibration = p.calibration
                        if calibration is not None:
                            calibration = m.calibrations[calibration.uid]
                            self._verify_telemetry_calibration(calibration, p)

                for tc in application.getTelecommands():
                    for p in tc.telecommand.getParametersAsFlattenedList():
                        calibration = p.calibration
                        if calibration is not None:
                            calibration = m.calibrations[calibration.uid]
                            self._verify_telecommand_calibration(calibration, p)

    @staticmethod
    def _verify_telemetry_calibration(calibration, parameter):
        if calibration.type == pdoc.model.Calibration.INTERPOLATION_TELECOMMAND:
            raise ParserException("Invalid calibration for parameter '%s' (%s). " \
                                  "'telecommandLinearInterpolation' is invalid for " \
                                  "telemetry parameter!"
                                  % (parameter.name, parameter.uid))
        elif calibration.type == pdoc.model.Calibration.INTERPOLATION_TELEMETRY:
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

    @staticmethod
    def _verify_telecommand_calibration(calibration, parameter):
        if calibration.type != pdoc.model.Calibration.INTERPOLATION_TELECOMMAND:
            raise ParserException("Invalid calibration for parameter '%s' (%s). " \
                                  "Only 'telecommandLinearInterpolation' is available " \
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
