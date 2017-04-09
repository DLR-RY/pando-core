#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016-2017, German Aerospace Center (DLR)
#
# This file is part of the development version of the pando library.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Authors:
# - 2016-2017, Fabian Greif (DLR RY-AVS)

import re
import lxml
import isodate

import pando.model


class ParserException(Exception):
    pass


def parse_text(node, tag, default_value=None):
    """
    Removes indentation from text tags.

    If the first line does not contain an indentation the next line is also
    checked. This helps e.g. for the following case:

        <description>This is some
          text which is indented only after
          the second line.</description>

    Keyword arguments:
    node -- Start node for the search
    tag -- XML tag name to look for in the XML node
    default_value --
    """
    text = node.findtext(tag, default_value)

    second_line_test = False
    if text is not None:
        to_strip = None
        lines = []
        for line in text.split('\n'):
            if to_strip is None or second_line_test:
                if line == '' or line.isspace():
                    continue

                # First line which is not only whitespace
                match = re.match(r'^(\s*)', line)
                to_strip = match.group(1)

                if second_line_test:
                    second_line_test = False
                else:
                    if to_strip == "" or to_strip is None:
                        second_line_test = True

            lines.append(line.lstrip(to_strip))
        text = ("\n".join(lines)).rstrip()

    return text


def parse_packet_classes(node, default=None):
    packet_classes = []
    for class_node in node.findall("packetClasses/class"):
        packet_classes.append(class_node.text)

    if len(packet_classes) == 0:
        # No packet class definitions found, use default value
        return default
    else:
        return packet_classes


def parse_packet_generation(packet_node):
    generation_node = packet_node.find("generation")
    if generation_node is not None:
        packet_generation = pando.model.PacketGeneration()

        for node in generation_node:
            if node.tag == "response":
                packet_generation.response = True
            elif node.tag == "event":
                packet_generation.event = True
            elif node.tag == "periodic":
                packet_generation.periodic = True
                packet_generation.periodic_interval = isodate.parse_duration(node.attrib["interval"])
            elif node.tag == lxml.etree.Comment:
                # Ignore comments
                pass
            else:
                raise ParserException("Invalid tag '{}' found".format(node.tag))

        if packet_generation.event is False \
                and packet_generation.periodic is False \
                and packet_generation.response is False:
            return None

        return packet_generation
    else:
        return None


def parse_short_name(packet, node, default=""):
    packet.short_name = node.findtext("shortName", default)

    if packet.short_name == "":
        packet.short_name = packet.name


def parse_description(node, default=""):
    return parse_text(node, "description", default)
