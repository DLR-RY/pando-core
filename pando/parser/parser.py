#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML parser for the packet description files.

Reads the description from a set of XML files and populates the model with
the result.
"""

from .. import pkg

# lxml must be imported **after** the Catalog file have been set by 'pkg', otherwise
# it runs into an endless loop during verification.
import lxml.etree

from .common import ParserException
from .calibration import CalibrationParser
from .enumeration import EnumerationParser
from .parameter import ParameterParser
from .packet import PacketParser
from .mapping import MappingParser

import pando.model
import pando.parser.common

class Parser:

    ROOTNODE = "pando"
    DATA_STRUCTURE_VERSION = "1.2.0"

    def parse(self, filename, xsdfile=None):
        rootnode = self._validate_and_parse_xml(filename, xsdfile)

        model = pando.model.Model()

        enumeration = EnumerationParser()
        calibration = CalibrationParser()
        parameter = ParameterParser()
        packet = PacketParser()

        for service_node in rootnode.iterfind('service'):
            enumeration.parse_service_enumeration(service_node, model)
            calibration.parse_service_calibration(service_node, model)
            parameter.parse_service_parameter(service_node, model)

        for service_node in rootnode.iterfind('service'):
            packet.parse_service_packets(service_node, model)

        mapping = MappingParser()
        mapping.parse(rootnode, model)

        return model

    @staticmethod
    def _validate_and_parse_xml(filename, xsdfile):
        try:
            # parse the xml-file
            parser = lxml.etree.XMLParser(no_network=True)
            xmlroot = lxml.etree.parse(filename, parser=parser)
            xmlroot.xinclude()

            if xsdfile is None:
                xsdfile = pkg.get_filename('pando', 'resources/schema/pando.xsd')

            xmlschema = lxml.etree.parse(xsdfile, parser=parser)

            schema = lxml.etree.XMLSchema(xmlschema)
            schema.assertValid(xmlroot)

            rootnode = xmlroot.getroot()
        except OSError as error:
            raise ParserException(error)
        except (lxml.etree.DocumentInvalid,
                lxml.etree.XMLSyntaxError,
                lxml.etree.XMLSchemaParseError,
                lxml.etree.XIncludeError) as error:
            raise ParserException("While parsing '%s': %s"
                                  % (error.error_log.last_error.filename, error))

        if rootnode.tag != Parser.ROOTNODE:
            raise ParserException("Expected rootnode '{}', got '{}' in file '{}'"
                                  .format(Parser.ROOTNODE, rootnode.tag, filename))

        version = rootnode.attrib["version"]
        if version != Parser.DATA_STRUCTURE_VERSION:
            raise ParserException("Invalid file structure version. Parser requires '{}' "
                                  "but the given file uses '{}'"
                                  .format(Parser.DATA_STRUCTURE_VERSION, version))

        return rootnode
