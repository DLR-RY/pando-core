#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re


class ParserException(Exception):
    pass


def parse_text(node, tag, default_value=None):
    """
    Removes indentation from text tags.
    
    Keyword arguments:
    node -- Start node for the search
    tag -- XML tag name to look for in the XML node
    default_value --
    """
    text = node.findtext(tag, default_value)

    if text is not None:
        to_strip = None
        lines = []
        for line in text.split('\n'):
            if to_strip is None:
                if line == '' or line.isspace():
                    continue

                # First line which is not only whitespace
                match = re.match(r'^(\s*)', text)
                to_strip = match.group(1)

            lines.append(line.lstrip(to_strip))
        text = ("\n".join(lines)).rstrip()

    return text


def parse_short_name(packet, node):
    packet.shortName = node.findtext("shortName", "")

    if packet.shortName == "":
        packet.shortName = packet.name


def parse_description(node):
    return parse_text(node, "description", "")
