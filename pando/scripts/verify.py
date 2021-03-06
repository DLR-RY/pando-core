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

import logging
import argparse

import pando.model.validator

logger = logging.getLogger('pando.verify')


def _print_unmapped_parameters(packet, unresolved, additional):
    for parameter in unresolved:
        logger.error("Packet '%s': parameter '%s' (position %i) not found in mapping" % (packet.uid, parameter[0], parameter[1]))
    for parameter in additional:
        logger.error("Packet '%s': unexpected parameter '%s' (position %i) found in mapping" % (packet.uid, parameter[0], parameter[1]))


def main(argv):
    arg = argparse.ArgumentParser(description='pando Mapping Verification')
    arg.add_argument('-i', '--input', dest='input', required=True, help='XML packet description ')
    arg.add_argument('-d', '--detailed',
                     dest='detailed',
                     default=False, action='store_true', required=False,
                     help='Detailed analysis about all unused (without mapping) TM/TC packets and parameters.')
    args = arg.parse_args(argv)

    parser = pando.parser.Parser()
    model_validator = pando.model.validator.ModelValidator(parser.parse(args.input))

    # Verify that all telecommands and telemetry packets in the
    # mapping section define all the parameters defined in the structure.
    success = True

    # Check telecommand parameters
    for p in model_validator.get_unmapped_telecommand_parameters():
        success = False
        logger.error("Parameter '%s' not found in mapping" % (p.uid))

    # Find parameters that are used in TC parameter mapping but not
    # referenced in any TC packet
    for p in model_validator.get_mapped_but_unreferenced_telecommand_parameter():
        success = False
        logger.error("Parameter '%s' found in mapping but not in any TC packet" % (p.uid))

    # Check telemetry parameters
    for p in model_validator.get_unmapped_telemetry_parameters():
        success = False
        _print_unmapped_parameters(p[0], p[1], p[2])

    # Check that for all enumerations a corresponding mapping is available
    # and that all mapped enumerations are defined somewhere in the XML file.
    atm, utm, atc, utc = model_validator.get_unmapped_enumerations()
    for unresolved, subsystem in utm:
        logger.error("No telemetry enumeration mapping found for uid '%s' in subsystem '%s'" % (unresolved.uid, subsystem.name))
        success = False
    for unresolved, subsystem in utc:
        logger.error("No telecommand enumeration mapping found for uid '%s' in subsystem '%s'" % (unresolved.uid, subsystem.name))
        success = False
    for additional in atm:
        logger.error("Telemetry enumeration mapping '%s' for uid '%s' not used!" % (additional.sid, additional.enumeration.uid))
        success = False
    for additional in atc:
        logger.error("Telecommand enumeration mapping '%s' for uid '%s' not used!" % (additional.sid, additional.enumeration.uid))
        success = False

    atm, utm, atc, utc = model_validator.get_unmapped_calibrations()
    for unresolved, subsystem in utm:
        logger.error("No telemetry calibration mapping found for uid '%s' in subsystem '%s'" % (unresolved.uid, subsystem.name))
        success = False
    for unresolved, subsystem in utc:
        logger.error("No telecommand calibration mapping found for uid '%s' in subsystem '%s'" % (unresolved.uid, subsystem.name))
        success = False
    for additional in atm:
        logger.error("Telemetry calibration mapping '%s' for uid '%s' not used!" % (additional.sid, additional.calibration.uid))
        success = False
    for additional in atc:
        logger.error("Telecommand calibration mapping '%s' for uid '%s' not used!" % (additional.sid, additional.calibration.uid))
        success = False

    # Verify that the combination of APID, STYPE, SSTYPE and the two
    # identification fields is unique.
    for packet in model_validator.get_ambiguous_telemetry_packets():
        logger.error("TM packet '%s' and '%s' are ambiguous" % (packet[0].uid, packet[1].uid))
        success = False

    for packet in model_validator.get_ambiguous_packet_mappings():
        logger.error("packet SID '%s' is used for '%s' and '%s'" % (packet[0], packet[1].uid, packet[2].uid))
        success = False

    for parameter in model_validator.get_ambiguous_telemetry_parameters_within_mapping():
        logger.error("Parameter SID '%s' is used multiple times in telemetry packet '%s'" % (parameter[1], parameter[0]))
        success = False

    for t in model_validator.get_ambiguous_telemetry_service_identifier():
        logger.error("Telemetry packet SID '%s' (%d, %d) is ambiguous within " \
                     "APID %d (0x%03X). Either use a different combination of "\
                     "service and sub-service type or add an identification " \
                     "parameter." %
                    (t["mapping"].sid, t["mapping"].telemetry.serviceType, t["mapping"].telemetry.serviceSubtype, t["apid"], t["apid"]))
        success = False

    for packet in model_validator.get_packets_with_unaligned_length():
        length = packet.get_accumulated_parameter_length()
        bits_per_byte = 8

        missing = bits_per_byte - (length % bits_per_byte)

        logger.error("Length of packet uid '{}' is not byte aligned "
                     "(total length {} bit -> add {} bit)"
                     .format(packet.uid, length, missing))
        success = False

    for enumeration in model_validator.get_enumeration_with_non_unqiue_values():
        logger.error("Enumeration '{}' ({}) has non unique entries!"
                     .format(enumeration.name, enumeration.uid))
        success = False

    if not success:
        raise pando.parser.ParserException("Incomplete mapping. Please add/remove the requested elements!")
    else:
        if args.detailed:
            parameters = model_validator.get_unused_parameters()
            if len(parameters) > 0:
                print("\nUnused parameters:")
                for parameter in parameters:
                    print("-", parameter)

            telemetries = model_validator.get_unused_telemetries()
            if len(telemetries) > 0:
                print("\nUnused telemetry packets:")
                for telemetry in telemetries:
                    print("-", telemetry)

            telecommands = model_validator.get_unused_telecommands()
            if len(telecommands) > 0:
                print("\nUnused telecommand packets:")
                for telecommand in telecommands:
                    print("-", telecommand)
        else:
            print("Verify Ok!")
