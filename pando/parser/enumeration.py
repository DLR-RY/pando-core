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

import copy

import pando.model
import pando.parser.common


class EnumerationParser:

    def parse_service_enumeration(self, service_node, m):
        for enumerations_node in service_node.iterfind('enumerations'):
            for node in enumerations_node.iterchildren('enumeration'):
                enumeration = self._parse_enumeration(node)
                m.enumerations[enumeration.uid] = enumeration

            for node in enumerations_node.iterchildren('derivedEnumeration'):
                enumeration = self._parse_derived_enumeration(node, m.enumerations)
                m.enumerations[enumeration.uid] = enumeration

    def _parse_enumeration(self, node):
        description = pando.parser.common.parse_description(node)
        enumeration = pando.model.Enumeration(name=node.attrib.get("name"),
                                              uid=node.attrib.get("uid"),
                                              width=int(node.attrib.get("width")),
                                              description=description)

        pando.parser.common.parse_short_name(enumeration, node)

        for entry in node.iterfind("entry"):
            enumeration.append_entry(self._parse_enumeration_entry(entry))

        return enumeration

    def _parse_derived_enumeration(self, node, enumerations):
        """
        Parse a enumeration based upon an existing enumeration.

        The existing enumeration is copied and then extended with the values
        of the new enumeration. Values which already exist in the base
        enumeration are overwritten.
        """
        extends = node.attrib.get("extends")
        base = enumerations[extends]

        enumeration = copy.deepcopy(base)

        enumeration.name = node.attrib.get("name", enumeration.name)
        enumeration.uid = node.attrib.get("uid")
        enumeration.description = pando.parser.common.parse_description(node, enumeration.description)
        pando.parser.common.parse_short_name(enumeration, node, enumeration.short_name)

        # FIXME overwrite existing parameters with the same value
        for entry in node.iterfind("entry"):
            enumeration.append_entry(self._parse_enumeration_entry(entry))

        return enumeration

    def _parse_enumeration_entry(self, node):
        try:
            value = str(int(node.attrib.get("value"), 0))
        except ValueError:
            value = node.attrib.get("value")

        description = pando.parser.common.parse_description(node)
        entry = pando.model.EnumerationEntry(node.attrib.get("name"),
                                             value,
                                             description)

        pando.parser.common.parse_short_name(entry, node)
        return entry

