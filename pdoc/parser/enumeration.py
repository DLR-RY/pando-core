#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pdoc.model
import pdoc.parser.common

class EnumerationParser:

    def parse_service_enumeration(self, service_node, m):
        for enumerations_node in service_node.iterfind('enumerations'):
            for node in enumerations_node.iterchildren('enumeration'):
                enumeration = self._parse_enumeration(node)
                m.enumerations[enumeration.uid] = enumeration

    def _parse_enumeration(self, node):
        description = pdoc.parser.common.parse_description(node)
        e = pdoc.model.Enumeration(name=node.attrib.get("name"),
                                   uid=node.attrib.get("uid"),
                                   width=int(node.attrib.get("width")),
                                   description=description)

        pdoc.parser.common.parse_short_name(e, node)

        for entry in node.iterfind("entry"):
            e.appendEntry(self._parse_enumeration_entry(entry))

        return e

    def _parse_enumeration_entry(self, node):
        description = pdoc.parser.common.parse_description(node)
        entry = pdoc.model.EnumerationEntry(node.attrib.get("name"),
                                            node.attrib.get("value"),
                                            description)
        return entry

