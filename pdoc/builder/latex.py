#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
            self.useMinMax = False

    def __init__(self, model_, templateFile, imagePath):
        builder.Builder.__init__(self, model_)


        if templateFile is None:
            templateFile = '#latex_table.tpl'
        self.templateFile = templateFile
        self.imagePath = imagePath

        self.state = None

    def generate(self, outpath):
        for packet in self.model.telemetries.values():
            self._generatePacket(outpath, packet)
        for packet in self.model.telecommands.values():
            self._generatePacket(outpath, packet)

    def _generatePacket(self, outpath, packet):
        parameters = []
        self.state = self.State()
        for parameter in packet.parameters:
            self._packetParameter(packet, parameter, parameters)

        if self.imagePath is None:
            image = None
        else:
            image = os.path.join(self.imagePath, packet.uid)

        packet.sid = self._getPacketSid(packet)
        substitutions = {
            'identifier': packet.uid,
            'parameters': parameters,
            'packet': packet,
            'image': image,
            'useMinMax': self.state.useMinMax,
        }

        filename = os.path.join(outpath, "%s.tex" % packet.uid)

        template = self._template(self.templateFile, alternateMarking=True)
        self._write(filename, template.render(substitutions) + "\n")

    def _packetParameter(self, packet, parameter, parameters):
        if isinstance(parameter, model.List):
            # FIXME, missing parameter in function call!
            self._packetParameter(parameter, parameters)
        else:
            if parameter.valueType == model.Parameter.RANGE:
                minimum = xstr(parameter.valueRange.min)
                maximum = xstr(parameter.valueRange.max)
            elif parameter.valueType == model.Parameter.FIXED:
                minimum = xstr(parameter.value)
                maximum = xstr(parameter.value)
            else:
                minimum = ""
                maximum = ""

            parameters.append({
                'name': parameter.name,
                'sid' : self._getParameterSid(packet, parameter),
                'description': parameter.description,
                'shortName': parameter.shortName,
                'type': str(parameter.type),
                'width': parameter.type.width,
                'unit': xstr(parameter.unit),
                'min': minimum,
                'max': maximum,
            })

            if parameter.valueType == model.Parameter.RANGE or parameter.valueType == model.Parameter.FIXED:
                self.state.useMinMax = True

            if isinstance(parameter, model.Repeater):
                self._packetRepeater(packet, parameter, parameters)

    def _packetRepeater(self, packet, repeater, parameters):
        for parameter in repeater.parameters:
            self._packetParameter(packet, parameter, parameters)

    def _getPacketSid(self, packet):
        if type(packet) is model.Telemetry:
            for sub in self.model.subsystems.values():
                for app in sub.applications.values():
                    for tm in app.getTelemetries():
                        if tm.telemetry.uid == packet.uid:
                            return tm.sid

        elif type(packet) is model.Telecommand:
            for sub in self.model.subsystems.values():
                for app in sub.applications.values():
                    for tc in app.getTelecommands():
                        if tc.telecommand.uid == packet.uid:
                            return tc.sid
        else:
            return None

    def _getParameterSid(self, packet, parameter):
        if type(packet) is model.Telecommand:
            for sub in self.model.subsystems.values():
                for app in sub.applications.values():
                    for tc in app.getTelecommands():
                        if tc.telecommand.uid == packet.uid:
                            return sub.telecommandParameters[parameter.uid].sid

        elif type(packet) is model.Telemetry:
            for sub in self.model.subsystems.values():
                for app in sub.applications.values():
                    for tm in app.getTelemetries():
                        if tm.telemetry.uid == packet.uid:
                            for param in tm.parameters:
                                if param.parameter.uid == parameter.uid:
                                    return param.sid
        else:
            return None


class OverviewBuilder(builder.Builder):

    def __init__(self, packets, templateFile):
        builder.Builder.__init__(self, packets)

        if templateFile is None:
            templateFile = '#latex_overview.tpl'
        self.templateFile = templateFile

    def generate(self, outpath, target):
        if target is None or target == '':
            target = 'overview.tex'

        basename, ext = os.path.splitext(target)
        self._generateOverview(os.path.join(outpath, basename + '_tm' + ext), list(self.model.telemetries.values()))
        self._generateOverview(os.path.join(outpath, basename + '_tc' + ext), list(self.model.telecommands.values()))

    def _generateOverview(self, filename, packets):
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

        template = self._template(self.templateFile, alternateMarking=True)
        self._write(filename, template.render(substitutions) + "\n")


class EnumerationBuilder(builder.Builder):

    def __init__(self, enumerations, templateFile):
        builder.Builder.__init__(self, None)
        self.enumerations = enumerations

        if templateFile is None:
            templateFile = '#latex_enumeration.tpl'
        self.templateFile = templateFile

    def generate(self, outpath):
        for enumeration in self.enumerations.values():
            self._generateEnumeration(outpath, enumeration)

    def _generateEnumeration(self, outpath, enumeration):
        substitutions = {
            'enumeration': enumeration,
        }

        filename = os.path.join(outpath, "enumeration_%s.tex" % enumeration.uid)
        template = self._template(self.templateFile, alternateMarking=True)
        self._write(filename, template.render(substitutions) + "\n")

