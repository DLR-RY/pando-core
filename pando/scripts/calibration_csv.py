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

import os
import argparse
import sys

rootpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
sys.path.append(rootpath)

import pando
import pando.pkg

import lxml.etree

def parse_xml(filename, xsdfile=None):
    try:
        # parse the xml-file
        parser = lxml.etree.XMLParser(no_network=True)
        xmlroot = lxml.etree.parse(filename, parser=parser)
        xmlroot.xinclude()

        if xsdfile is None:
            xsdfile = pando.pkg.get_filename('pando', 'resources/schema/service.xsd')

        xmlschema = lxml.etree.parse(xsdfile, parser=parser)

        schema = lxml.etree.XMLSchema(xmlschema)
        schema.assertValid(xmlroot)

        rootnode = xmlroot.getroot()
    except OSError as e:
        raise ParserException(e)
    except (lxml.etree.DocumentInvalid, lxml.etree.XMLSyntaxError, lxml.etree.XMLSchemaParseError) as e:
        raise ParserException("While parsing '%s': %s" % (e.error_log[0].filename, e))
    except lxml.etree.XIncludeError as e:
        raise ParserException("While including '%s': %s" % (e.error_log[0].filename, e))

    return rootnode

def xml2csv(input, output):
    rootnode = parse_xml(input)

    calibrations = []
    for calibrationNode in rootnode.iterfind('calibrations/telemetryLinearInterpolation'):
        values = []
        for pointNode in calibrationNode.iterfind('point'):
            x = pointNode.get('x')
            y = pointNode.get('y')

            values.append(x)
            values.append(y)

        calibration = {
           'name': calibrationNode.get('name'),
           'uid':  calibrationNode.get('uid'),
           'direction': "TM",
           'extrapolate': "extrapolate" if calibrationNode.get('extrapolate') == "true" else "",
           'unit': calibrationNode.get('unit'),
           'type': calibrationNode.get('outputType'),
           'values': values
        }

        calibrations.append(calibration)

    for calibrationNode in rootnode.iterfind('calibrations/telecommandLinearInterpolation'):
        values = []
        for pointNode in calibrationNode.iterfind('point'):
            x = pointNode.get('x')
            y = pointNode.get('y')

            values.append(x)
            values.append(y)

        calibration = {
           'name': calibrationNode.get('name'),
           'uid':  calibrationNode.get('uid'),
           'direction': "TC",
           'extrapolate': "extrapolate" if calibrationNode.get('extrapolate') == "true" else "",
           'unit': calibrationNode.get('unit'),
           'type': calibrationNode.get('inputType'),
           'values': values
        }

        calibrations.append(calibration)

    with open(output, 'w') as file:
        for calibration in calibrations:
            s = [calibration['name'],
                 calibration['uid'],
                 calibration['direction'],
                 calibration['extrapolate'],
                 calibration['unit'],
                 calibration['type']]
            for value in calibration['values']:
                s.append(value)
            file.write("\t".join(s) + "\n")

def csv2xml(input, output, service_name):
    fileTemplate = """<?xml version="1.0" encoding="UTF-8"?>
<service name="{service}"
         xmlns:xi="http://www.w3.org/2001/XInclude"
         xmlns:xsd="http://www.w3.org/2001/XMLSchema-instance"
         xsd:noNamespaceSchemaLocation="http://www.dlr.de/schema/pando/service.xsd">
  <calibrations>
{calibration}
  </calibrations>
</service>
"""
    telemetryCalibrationTemplate = """    <telemetryLinearInterpolation name="{name}" uid="{uid}" unit="{unit}" outputType="{type}" extrapolate="{extrapolate}">
{points}
    </telemetryLinearInterpolation>"""
    telecommandCalibrationTemplate = """    <telecommandLinearInterpolation name="{name}" uid="{uid}" unit="{unit}" inputType="{type}" extrapolate="{extrapolate}">
{points}
    </telecommandLinearInterpolation>"""
    pointTemplate = """      <point x="{x}" y="{y}"/>"""

    calibrations = []
    with open(input, 'r') as file:
        for line in file.readlines():
            line = line.rstrip('\n\r')
            t = line.split('\t')

            # If the file is not tab separated, try comma separated.
            if (len(t) == 1):
                t = line.split(',')

            calibration = {
               'name': t[0],
               'uid':  t[1],
               'direction': t[2],
               'extrapolate': "true" if t[3] == "extrapolate" else "false",
               'unit': t[4],
               'type': t[5],
            }

            values = t[6:]
            if len(values) % 2 == 1:
                print("Invalid number of calibration points")
                sys.exit(1)

            valuePairs = []
            for i in range(0, len(values), 2):
                # Ignore empty lines
                if values[i] == "" and values[i + 1] == "":
                    continue

                valuePairs.append({
                    'x': values[i],
                    'y': values[i + 1]
                })

            calibration['values'] = valuePairs
            calibrations.append(calibration)

    c = []
    for calibration in calibrations:
        points = []
        for value in calibration['values']:
            points.append(str.format(pointTemplate, **value))

        if calibration['direction'] == 'TM':
            c.append(telemetryCalibrationTemplate.format(points="\n".join(points),
                                                         **calibration))
        elif calibration['direction'] == 'TC':
            c.append(telecommandCalibrationTemplate.format(points="\n".join(points),
                                                           **calibration))
        else:
            print("Invalid direction '{}'".format(calibration['direction']))
            sys.exit(1)

    with open(output, 'w') as file:
        file.write(fileTemplate.format(calibration="\n\n".join(c),
                                       service=service_name))


arg = argparse.ArgumentParser(description='p.doc Convert a CSV calibration to XML and back.')
arg.add_argument('-i', '--input', dest='input', required=True, help='Input table. Can be XML or CSV.')
arg.add_argument('-o', '--output', dest='output', required=True, help='Output table. Can be XML or CSV.')
arg.add_argument('-s', '--service', dest='service_name', required=True, help='Name of the service.')

args = arg.parse_args()

if args.input.endswith('.xml') and args.output.endswith('.csv'):
    xml2csv(args.input, args.output)
elif args.input.endswith('.csv') and args.output.endswith('.xml'):
    csv2xml(args.input, args.output, args.service_name)
else:
    print("Invalid input and/or output formats")
    sys.exit(1)
