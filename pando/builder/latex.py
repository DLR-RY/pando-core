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
# - 2016, Jan Sommer (DLR SC-SRV)

import os
import re

from .. import model

from . import builder


def xstr(s):
    """ Converts None to an empty string """
    return '' if s is None else str(s)


def tex_escape(text):
    """
        :param text: a plain text message
        :return: the message escaped to appear correctly in LaTeX
    """
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless',
        '>': r'\textgreater',
    }
    regex = re.compile('|'.join(re.escape(key) for key in sorted(conv.keys(), key=lambda item:-len(item))))
    return regex.sub(lambda match: conv[match.group()], text)


class TableBuilder(builder.Builder):

    class State:
        def __init__(self):
            self.use_min_max = False

    def __init__(self, model_, template_file, image_path):
        builder.Builder.__init__(self, model_)

        if template_file is None:
            template_file = '#latex_table.tpl'
        self.template_file = template_file
        self.image_path = image_path

        self.state = None

    def generate(self, outpath):
        for packet in self.model.telemetries.values():
            self._generate_packet(outpath, packet)
        for packet in self.model.telecommands.values():
            self._generate_packet(outpath, packet)

    def _generate_packet(self, outpath, packet):
        parameters = []
        self.state = self.State()
        for parameter in packet.parameters:
            self._packet_parameter(packet, parameter, parameters)

        if self.image_path is None:
            image = None
        else:
            image = os.path.join(self.image_path, packet.uid)

        packet.sid = self._get_packet_sid(packet)
        substitutions = {
            'identifier': packet.uid,
            'parameters': parameters,
            'packet': packet,
            'image': image,
            'use_min_max': self.state.use_min_max,
        }

        filename = os.path.join(outpath, "%s.tex" % packet.uid)

        template = self._template(self.template_file, alternate_marking=True)
        self._write(filename, template.render(substitutions) + "\n")

    def _packet_parameter(self, packet, parameter, parameters):
        if isinstance(parameter, model.List):
            # FIXME, missing parameter in function call!
            self._packet_parameter(parameter, parameters)
        else:
            if parameter.value_type == model.Parameter.RANGE:
                minimum = xstr(parameter.value_range.min)
                maximum = xstr(parameter.value_range.max)
            elif parameter.value_type == model.Parameter.FIXED:
                minimum = xstr(parameter.value)
                maximum = xstr(parameter.value)
            else:
                minimum = ""
                maximum = ""

            parameters.append({
                'name': parameter.name,
                'sid': self._get_parameter_sid(packet, parameter),
                'description': parameter.description,
                'short_name': parameter.short_name,
                'type': str(parameter.type),
                'width': parameter.type.width,
                'unit': xstr(parameter.unit),
                'min': minimum,
                'max': maximum,
            })

            if parameter.value_type == model.Parameter.RANGE or parameter.value_type == model.Parameter.FIXED:
                self.state.use_min_max = True

            if isinstance(parameter, model.Repeater):
                self._packet_repeater(packet, parameter, parameters)

    def _packet_repeater(self, packet, repeater, parameters):
        for parameter in repeater.parameters:
            self._packet_parameter(packet, parameter, parameters)

    def _get_packet_sid(self, packet):
        if type(packet) is model.Telemetry:
            for subsystem in self.model.subsystems.values():
                for application in subsystem.applications.values():
                    for telemetry in application.get_telemetries():
                        if telemetry.telemetry.uid == packet.uid:
                            return telemetry.sid

        elif type(packet) is model.Telecommand:
            for subsystem in self.model.subsystems.values():
                for application in subsystem.applications.values():
                    for telecommand in application.get_telecommands():
                        if telecommand.telecommand.uid == packet.uid:
                            return telecommand.sid
        else:
            return None

    def _get_parameter_sid(self, packet, parameter):
        if type(packet) is model.Telecommand:
            for subsystem in self.model.subsystems.values():
                for applicaton in subsystem.applications.values():
                    for telecommand in applicaton.get_telecommands():
                        if telecommand.telecommand.uid == packet.uid:
                            return subsystem.telecommand_parameters[parameter.uid].sid

        elif type(packet) is model.Telemetry:
            for subsystem in self.model.subsystems.values():
                for applicaton in subsystem.applications.values():
                    for telemetry in applicaton.get_telemetries():
                        if telemetry.telemetry.uid == packet.uid:
                            for param in telemetry.parameters:
                                if param.parameter.uid == parameter.uid:
                                    return param.sid
        else:
            return None


class OverviewBuilder(builder.Builder):

    def __init__(self, packets, template_file):
        builder.Builder.__init__(self, packets)

        if template_file is None:
            template_file = '#latex_overview.tpl'
        self.template_file = template_file

    def generate(self, outpath, target):
        if target is None or target == '':
            target = 'overview.tex'

        basename, ext = os.path.splitext(target)
        self._generate_overview(os.path.join(outpath, basename + '_tm' + ext), list(self.model.telemetries.values()))
        self._generate_overview(os.path.join(outpath, basename + '_tc' + ext), list(self.model.telecommands.values()))

    def _generate_overview(self, filename, packets):
        headings = []
        for packet in packets:
            for designator in packet.designators:
                if designator['name'] not in headings:
                    headings.append(designator['name'])

        entries = []
        for packet in packets:
            entry = []
            for d in headings:
                for designator in packet.designators:
                    if designator['name'] == d:
                        entry.append(designator['value'])
                        break
                else:
                    entry.append("-")
            entry.append(packet.name)
            entries.append(entry)

        # 'headings' is one shorter than every entry of 'entries'.
        substitutions = {
            'headings': headings,
            'entries': sorted(entries),
        }

        template = self._template(self.template_file, alternate_marking=True)
        self._write(filename, template.render(substitutions) + "\n")


class EnumerationBuilder(builder.Builder):

    def __init__(self, enumerations, template_file):
        builder.Builder.__init__(self, None)
        self.enumerations = enumerations

        if template_file is None:
            template_file = '#latex_enumeration.tpl'
        self.template_file = template_file

    def generate(self, outpath):
        for enumeration in self.enumerations.values():
            self._generate_enumeration(outpath, enumeration)

    def _generate_enumeration(self, outpath, enumeration):
        substitutions = {
            'enumeration': enumeration,
        }

        filename = os.path.join(outpath, "enumeration_%s.tex" % enumeration.uid)
        template = self._template(self.template_file, alternate_marking=True)
        self._write(filename, template.render(substitutions) + "\n")
