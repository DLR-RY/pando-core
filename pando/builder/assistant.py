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

import itertools

from . import builder

import pando.model.validator


class Assistant(builder.Builder):

    def __init__(self, model, template_file=None):
        builder.Builder.__init__(self, model)

        self.model_validator = pando.model.validator.ModelValidator(model)

        if template_file is None:
            template_file = '#suggestions.tpl'
        self.template_file = template_file

    @staticmethod
    def _get_suggestion(packet):
        parameters = []
        for parameter in packet.get_parameters_as_flattened_list():
            parameters.append({
                "uid": parameter.uid,
                "sid": "",
            })
        return {
            "uid": packet.uid,
            "name": packet.name,
            "apid": "",
            "parameters": parameters,
        }

    def _get_partial_suggestion(self, packet, packet_mapping):
        unresolved, additional = self.model_validator.get_unmapped_parameters(packet, packet_mapping)
        if len(unresolved) > 0 or len(additional) > 0:
            parameters = []
            last_sid = ""
            for parameter, mapping in itertools.zip_longest(packet.get_parameters_as_flattened_list(),
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
        unmapped_parameters = self.model_validator.get_unmapped_telecommand_parameters()
        parameters = [x.uid for x in unmapped_parameters]

        # Find all telemetry packets with a partial mapping
        telemetries = []
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for packet_mapping in application.get_telemetries():
                    packet = packet_mapping.telemetry
                    suggestion = self._get_partial_suggestion(packet, packet_mapping)
                    if suggestion:
                        suggestion["apid"] = application.apid
                        suggestion["name"] = application.name
                        telemetries.append(suggestion)

        substitutions = {
            "parameters": sorted(parameters, key=pando.naturalkey),
            "events": [],
            "telemetries": sorted(telemetries, key=lambda p: pando.naturalkey(p["uid"])),
            "telecommands": [],
        }

        template = self._template(self.template_file)
        print(template.render(substitutions))

    def print_suggestions_for_unused_packets(self):
        parameters = self.model_validator.get_unused_parameters()

        events = []
        telemetries = []
        unused_telemetries = self.model_validator.get_unused_telemetries()
        if len(unused_telemetries) > 0:
            for uid in unused_telemetries:
                packet = self.model.telemetries[uid]

                if packet.packet_type == pando.model.Packet.EVENT:
                    events.append(self._get_suggestion(packet))
                else:
                    telemetries.append(self._get_suggestion(packet))

        telecommands = []
        unused_telecommands = self.model_validator.get_unused_telecommands()
        if len(unused_telecommands) > 0:
            for uid in unused_telecommands:
                packet = self.model.telecommands[uid]
                telecommands.append(self._get_suggestion(packet))

        substitutions = {
            "parameters": sorted(parameters, key=pando.naturalkey),
            "events": sorted(events, key=lambda p: pando.naturalkey(p["uid"])),
            "telemetries": sorted(telemetries, key=lambda p: pando.naturalkey(p["uid"])),
            "telecommands": sorted(telecommands, key=lambda p: pando.naturalkey(p["uid"])),
        }

        template = self._template(self.template_file)
        print(template.render(substitutions))
