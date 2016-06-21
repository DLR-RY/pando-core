#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re


class ParserException(Exception):
    pass


def parse_text(node, tag, default_value=None):
    """
    Removes indentation from text tags.
    
    If the first line does not contain an indentation the next line is also
    checked. This helps e.g. for the following case:
    
        <description>This is some
          text which is indentated only after
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


def parse_short_name(packet, node, default=""):
    packet.shortName = node.findtext("shortName", default)

    if packet.shortName == "":
        packet.shortName = packet.name


def parse_description(node, default=""):
    return parse_text(node, "description", default)
