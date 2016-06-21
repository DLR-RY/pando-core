#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools

from . import builder

import pdoc
import pdoc.model.validator

class Assistant(builder.Builder):

    def __init__(self, model, template_file=None):
        builder.Builder.__init__(self, model)

        self.model_validator = pdoc.model.validator.ModelValidator(model)

        if template_file is None:
            template_file = '#suggestions.tpl'
        self.template_file = template_file

    @staticmethod
    def _get_suggestion(packet):
        parameters = []
        for parameter in packet.getParametersAsFlattenedList():
            parameters.append({
                "uid": parameter.uid,
                "sid": "",
            })
        return {
            "uid": packet.uid,
            "parameters": parameters,
        }

    def _get_partial_suggestion(self, packet, packet_mapping):
        unresolved, additional = self.model_validator.getUnmappedParameters(packet, packet_mapping)
        if len(unresolved) > 0 or len(additional) > 0:
            parameters = []
            last_sid = ""
            for parameter, mapping in itertools.zip_longest(packet.getParametersAsFlattenedList(),
                                                            packet_mapping.parameters):
                if parameter is not None:
                    if last_sid != "":
                        sid_proposition = last_sid[0:4] \
                            + "%04i" % (int(last_sid[4:].lstrip('0')) + 1)
                    else:
                        sid_proposition = ""
                    sid = mapping.sid if mapping is not None else sid_proposition
                    last_sid = sid
                    parameters.append({
                        "uid": parameter.uid,
                        "sid": sid,
                    })
            return {
                "uid": packet.uid,
                "parameters": parameters,
            }
        else:
            return None

    def print_suggestions(self):
        # Find all telecommand parameters without a mapping
        unmapped_parameters = self.model_validator.getUnmappedTelecommandParameters()
        parameters = [x.uid for x in unmapped_parameters]

        # Find all telemetry packets with a partial mapping
        telemetries = []
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for packet_mapping in application.getTelemetries():
                    packet = packet_mapping.telemetry
                    suggestion = self._get_partial_suggestion(packet, packet_mapping)
                    if suggestion:
                        suggestion["apid"] = application.apid
                        suggestion["name"] = application.name
                        telemetries.append(suggestion)

        substitutions = {
            "parameters": sorted(parameters, key=pdoc.naturalkey),
            "telemetries": sorted(telemetries, key=lambda p: pdoc.naturalkey(p["uid"])),
        }

        template = self._template(self.template_file)
        print(template.render(substitutions))

    def print_suggestions_for_unused_packets(self):
        parameters = self.model_validator.getUnusedParameters()

        telemetries = []
        unused_telemetries = self.model_validator.getUnusedTelemetries()
        if len(unused_telemetries) > 0:
            for uid in unused_telemetries:
                packet = self.model.telemetries[uid]
                telemetries.append(self._get_suggestion(packet))

        telecommands = []
        unused_telecommands = self.model_validator.getUnusedTelecommands()
        if len(unused_telecommands) > 0:
            for uid in unused_telecommands:
                packet = self.model.telecommands[uid]
                telecommands.append(self._get_suggestion(packet))

        substitutions = {
            "parameters": sorted(parameters, key=pdoc.naturalkey),
            "telemetries": sorted(telemetries, key=lambda p: pdoc.naturalkey(p["uid"])),
            "telecommands": sorted(telecommands, key=lambda p: pdoc.naturalkey(p["uid"])),
        }

        template = self._template(self.template_file)
        print(template.render(substitutions))
