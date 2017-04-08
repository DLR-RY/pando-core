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

import os
import textwrap

from .. import model

from . import builder


class ImageBuilder(builder.Builder):

    class DecodingState:
        def __init__(self):
            self.x = 0
            self.elementCount = 0

    def __init__(self, model_, templateFile=None, align=False):
        builder.Builder.__init__(self, model_)

        self.boxWidth = 90
        self.repeaterDelimiterWidth = 10
        self.textHeight = 14

        if templateFile is None:
            templateFile = '#svg.tpl'
        self.templateFile = templateFile
        self.align = align

        self.state = self.DecodingState()

    def generate(self, outpath):
        for packet in self.model.telemetries.values():
            filename = os.path.join(outpath, "%s.svg" % packet.uid)
            self._write(filename, self.generatePacket(packet) + "\n")
        for packet in self.model.telecommands.values():
            filename = os.path.join(outpath, "%s.svg" % packet.uid)
            self._write(filename, self.generatePacket(packet) + "\n")

    def generatePacket(self, packet):
        self.state = self.DecodingState()
        elements = []

        for parameter in packet.getParameters():
            self._packetParameter(parameter, elements)

        defaultWidth = 525
        if (self.state.x + 20) > defaultWidth:
            xOffset = 10
            width = self.state.x + 20
        else:
            if self.align:
                xOffset = 10
            else:
                xOffset = int((defaultWidth - (self.state.x)) / 2)
            width = defaultWidth
        height = 85 + (packet.depth - 1) * 20 + 5

        substitutions = {
            'elements': elements,
            'xOffset': xOffset,
            'yOffset': 5 + packet.depth * 5,
            'width': width,
            'height': height,
        }

        template = self._template(self.templateFile)
        return template.render(substitutions)

    def _packetParameter(self, parameter, elements):
        if isinstance(parameter, model.List):
            for p in parameter.parameters:
                self._packetParameter(p, elements)
        else:
            wrapper = textwrap.TextWrapper()
            wrapper.width = 14

            text = wrapper.wrap(parameter.name)

            texts = []
            offset = (40 - self.textHeight * len(text)) / 2 - 3
            for t in text:
                offset += self.textHeight
                texts.append({
                    'text': t,
                    'y': offset,
                })

            elements.append({
                'type': 'element',
                'parameterName': texts,
                'parameterType': str(parameter.type),
                'parameterWidth': parameter.type.width,
                'x': self.state.x,
                'width': self.boxWidth,
            })
            self.state.x += self.boxWidth
            self.state.elementCount += 1

            if isinstance(parameter, model.Repeater):
                self._packetRepeater(parameter, elements)

    def _packetRepeater(self, repeater, elements):
        elements.append({
            'type': 'repeaterStart',
            'x': self.state.x,
            'width': self.repeaterDelimiterWidth,
            'depth': repeater.depth,
        })
        self.state.x += self.repeaterDelimiterWidth
        startPosition = self.state.x
        startCount = self.state.elementCount

        for parameter in repeater.parameters:
            self._packetParameter(parameter, elements)

        if elements[-1]["type"] == "repeaterEnd":
            self.state.x -= int(self.repeaterDelimiterWidth / 2)

        repeaterWidth = self.state.elementCount - startCount
        elements.append({
            'type': 'repeaterEnd',
            'x': self.state.x,
            'width': self.repeaterDelimiterWidth,
            'depth': repeater.depth,
            'textposition': int(startPosition + (self.state.x - startPosition) / 2),
            'repeaterRepeatText': ("repeated %s times" if (repeaterWidth > 1) else "rep. %s times") % repeater.name,
        })
        self.state.x += self.repeaterDelimiterWidth

