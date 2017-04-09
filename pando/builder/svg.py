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
            self.element_count = 0

    def __init__(self, model_, template_file=None, align=False):
        builder.Builder.__init__(self, model_)

        self.box_width = 90
        self.repeater_delimiter_width = 10
        self.text_height = 14

        if template_file is None:
            template_file = '#svg.tpl'
        self.template_file = template_file
        self.align = align

        self.state = self.DecodingState()

    def generate(self, outpath):
        for packet in self.model.telemetries.values():
            filename = os.path.join(outpath, "%s.svg" % packet.uid)
            self._write(filename, self.generate_packet(packet) + "\n")
        for packet in self.model.telecommands.values():
            filename = os.path.join(outpath, "%s.svg" % packet.uid)
            self._write(filename, self.generate_packet(packet) + "\n")

    def generate_packet(self, packet):
        self.state = self.DecodingState()
        elements = []

        for parameter in packet.get_parameters():
            self._packet_parameter(parameter, elements)

        default_width = 525
        if (self.state.x + 20) > default_width:
            x_offset = 10
            width = self.state.x + 20
        else:
            if self.align:
                x_offset = 10
            else:
                x_offset = int((default_width - (self.state.x)) / 2)
            width = default_width
        height = 85 + (packet.depth - 1) * 20 + 5

        substitutions = {
            'elements': elements,
            'x_offset': x_offset,
            'yOffset': 5 + packet.depth * 5,
            'width': width,
            'height': height,
        }

        template = self._template(self.template_file)
        return template.render(substitutions)

    def _packet_parameter(self, parameter, elements):
        if isinstance(parameter, model.List):
            for p in parameter.parameters:
                self._packet_parameter(p, elements)
        else:
            wrapper = textwrap.TextWrapper()
            wrapper.width = 14

            text = wrapper.wrap(parameter.name)

            texts = []
            offset = (40 - self.text_height * len(text)) / 2 - 3
            for t in text:
                offset += self.text_height
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
                'width': self.box_width,
            })
            self.state.x += self.box_width
            self.state.element_count += 1

            if isinstance(parameter, model.Repeater):
                self._packet_repeater(parameter, elements)

    def _packet_repeater(self, repeater, elements):
        elements.append({
            'type': 'repeaterStart',
            'x': self.state.x,
            'width': self.repeater_delimiter_width,
            'depth': repeater.depth,
        })
        self.state.x += self.repeater_delimiter_width
        start_position = self.state.x
        startCount = self.state.element_count

        for parameter in repeater.parameters:
            self._packet_parameter(parameter, elements)

        if elements[-1]["type"] == "repeaterEnd":
            self.state.x -= int(self.repeater_delimiter_width / 2)

        repeater_width = self.state.element_count - startCount
        elements.append({
            'type': 'repeaterEnd',
            'x': self.state.x,
            'width': self.repeater_delimiter_width,
            'depth': repeater.depth,
            'textposition': int(start_position + (self.state.x - start_position) / 2),
            'repeaterRepeatText': ("repeated %s times" if (repeater_width > 1) else "rep. %s times") % repeater.name,
        })
        self.state.x += self.repeater_delimiter_width

