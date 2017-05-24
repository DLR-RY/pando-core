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

"""
Validation of the internal structure of the model.
"""

import itertools

import pando.model

class ModelValidator:

    def __init__(self, model):
        self.model = model

    def get_unmapped_telecommand_parameters(self):
        """
        Find the UID of all telecommand_mapping parameters that are referenced through
        a telecommand_mapping in an application but have no corresponding telecommand_mapping
        parameter mapping.

        Returns a list of Parameter() objects.
        """
        unmapped_parameters = []
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for telecommand_mapping in application.get_telecommands():
                    for parameter in telecommand_mapping.telecommand.get_parameters_as_flattened_list():
                        if parameter.uid not in subsystem.telecommand_parameters:
                            # Only add the parameter if it is not already
                            # in the list
                            for unmapped_parameter in unmapped_parameters:
                                if unmapped_parameter.uid == parameter.uid:
                                    break
                            else:
                                unmapped_parameters.append(parameter)
        return unmapped_parameters

    def get_packets_with_unaligned_length(self):
        """
        Check for packets which have a length that is not byte aligned.
        """
        unaligend_packets = []
        for packet in itertools.chain(self.model.telecommands.values(),
                                      self.model.telemetries.values()):
            length = packet.get_accumulated_parameter_length()
            if length is not None and length % 8 != 0:
                unaligend_packets.append(packet)
            # print(packet.uid)

        return unaligend_packets


    def get_mapped_but_unreferenced_telecommand_parameter(self):
        """
        Find parameter_mappings that are used in TC parameter mapping but not
        referenced in any TC packet.

        Returns a list of Parameter() objects.
        """
        unreferenced_parameters = []
        for subsystem in self.model.subsystems.values():
            # Store the list of all parameter_mappings in the subsystem.
            # With the function get_unmapped_telecommand_parameters() it is
            # checked that this is complete.
            parameter_mappings = subsystem.telecommand_parameters.copy()

            # Remove all parameter_mappings which are used in any TC packet
            # of this subsystem
            for application in subsystem.applications.values():
                for telecommand_mapping in application.get_telecommands():
                    for parameter in telecommand_mapping.telecommand.get_parameters_as_flattened_list():
                        if parameter.uid in parameter_mappings:
                            del parameter_mappings[parameter.uid]

            # Add all parameter_mappings which are still left to the list of
            # unreferenced_parameters parameter_mappings
            for parameter_mapping in parameter_mappings.values():
                unreferenced_parameters.append(parameter_mapping.parameter)

        return unreferenced_parameters

    def get_unmapped_telemetry_parameters(self):
        """
        Returns a list of tuples of (Telemetry(), [uid], [uid], Application())
        """
        unmapped = []
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for telemetry_mapping in application.get_telemetries():
                    telemetry = telemetry_mapping.telemetry
                    # Check that all parameters are available
                    unresolved, additional = self.get_unmapped_parameters(telemetry,
                                                                          telemetry_mapping)
                    if len(unresolved) > 0 or len(additional) > 0:
                        unmapped.append((telemetry, unresolved, additional, application))
        return unmapped

    @staticmethod
    def get_unmapped_parameters(packet, packet_mapping):
        """
        Get the UID of parameters that are unused or additionally mapped.

        Returns two lists of (uid, positionInPacket)
        """
        unresolved = []
        additional = []

        packet_parameters = packet.get_parameters_as_flattened_list()
        position = 0
        for parameter, mapping in itertools.zip_longest(packet_parameters,
                                                        packet_mapping.parameters):
            if parameter is None:
                additional.append((mapping.parameter.uid, position))
            elif mapping is None:
                unresolved.append((parameter.uid, position))
            elif parameter.uid != mapping.parameter.uid:
                # Found a parameter which is in the structure but not the
                # mapping.
                unresolved.append((parameter.uid, position))
                additional.append((mapping.parameter.uid, position))
            position += 1

        return unresolved, additional

    def _get_used_enumerations(self, subsystem):
        telemetry_enumerations = {}
        telecommand_enumerations = {}
        for application in subsystem.applications.values():
            for tm in application.get_telemetries():
                for p in tm.telemetry.get_parameters_as_flattened_list():
                    if p.type.identifier == pando.model.ParameterType.ENUMERATION:
                        uid = p.type.enumeration
                        telemetry_enumerations[uid] = self.model.enumerations[uid]

            for tc in application.get_telecommands():
                for p in tc.telecommand.get_parameters_as_flattened_list():
                    if p.type.identifier == pando.model.ParameterType.ENUMERATION:
                        uid = p.type.enumeration
                        telecommand_enumerations[uid] = self.model.enumerations[uid]

        return telemetry_enumerations, telecommand_enumerations

    def _get_used_calibrations(self, subsystem):
        telemetry_calibrations = {}
        telecommand_calibrations = {}
        for application in subsystem.applications.values():
            for telemetry_mapping in application.get_telemetries():
                for parameter in telemetry_mapping.telemetry.get_parameters_as_flattened_list():
                    calibration = parameter.calibration
                    if calibration is not None:
                        calibration = self.model.calibrations[calibration.uid]
                        telemetry_calibrations[calibration.uid] = calibration

            for telecommand_mapping in application.get_telecommands():
                for parameter in telecommand_mapping.telecommand.get_parameters_as_flattened_list():
                    calibration = parameter.calibration
                    if calibration is not None:
                        calibration = self.model.calibrations[calibration.uid]
                        telecommand_calibrations[parameter.calibration.uid] = calibration
        return telemetry_calibrations, telecommand_calibrations

    def get_unmapped_enumerations(self):
        unresolved_tm = []
        unresolved_tc = []
        additional_tm = []
        additional_tc = []

        for subsystem in self.model.subsystems.values():
            telemetry_enumerations, telecommand_enumerations = \
                self._get_used_enumerations(subsystem)

            unresolved_tms_subsystem = telemetry_enumerations.copy()
            unresolved_tcs_subsystem = telecommand_enumerations.copy()

            for m in subsystem.telemetry_enumerations.values():
                uid = m.enumeration.uid
                if uid not in telemetry_enumerations:
                    additional_tm.append(m)

                if uid in unresolved_tms_subsystem:
                    unresolved_tms_subsystem.pop(uid)

            for m in subsystem.telecommand_enumerations.values():
                uid = m.enumeration.uid
                if uid not in telecommand_enumerations:
                    additional_tc.append(m)

                if uid in unresolved_tcs_subsystem:
                    unresolved_tcs_subsystem.pop(uid)

            for unresolved_tm_subsystem in unresolved_tms_subsystem.values():
                unresolved_tm.append((unresolved_tm_subsystem, subsystem))
            for unresolved_tc_subsystem in unresolved_tcs_subsystem.values():
                unresolved_tc.append((unresolved_tc_subsystem, subsystem))

        return (additional_tm, unresolved_tm, additional_tc, unresolved_tc)

    def get_unmapped_calibrations(self):
        unresolved_tm = []
        unresolved_tc = []
        additional_tm = []
        additional_tc = []

        for subsystem in self.model.subsystems.values():
            telemetry_calibrations, telecommand_calibrations = \
                self._get_used_calibrations(subsystem)

            unresolved_tms_subsystem = telemetry_calibrations.copy()
            unresolved_tcs_subsystem = telecommand_calibrations.copy()

            for m in subsystem.telemetry_calibrations.values():
                uid = m.calibration.uid
                if uid not in telemetry_calibrations:
                    additional_tm.append(m)

                if uid in unresolved_tms_subsystem:
                    unresolved_tms_subsystem.pop(uid)

            for m in subsystem.telecommand_calibrations.values():
                uid = m.calibration.uid
                if uid not in telecommand_calibrations:
                    additional_tc.append(m)

                if uid in unresolved_tcs_subsystem:
                    unresolved_tcs_subsystem.pop(uid)

            for unresolved_tm_subsystem in unresolved_tms_subsystem.values():
                unresolved_tm.append((unresolved_tm_subsystem, subsystem))
            for unresolved_tc_subsystem in unresolved_tcs_subsystem.values():
                unresolved_tc.append((unresolved_tc_subsystem, subsystem))

        return (additional_tm, unresolved_tm, additional_tc, unresolved_tc)

    def get_unused_parameters(self):
        """
        Get all parameters which are not used in an TM or TC packet referenced
        by an application.
        """
        parameters = list(self.model.parameters.keys())
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for telemetry_mapping in application.get_telemetries():
                    for parameter_mapping in telemetry_mapping.parameters:
                        if parameter_mapping.parameter.uid in parameters:
                            parameters.remove(parameter_mapping.parameter.uid)

                for telecommand_mapping in application.get_telecommands():
                    for parameter in telecommand_mapping.telecommand.get_parameters_as_flattened_list():
                        if parameter.uid in parameters:
                            parameters.remove(parameter.uid)

        # Remove all list parameters
        for parameter in self.model.parameters.values():
            if isinstance(parameter, pando.model.List):
                parameters.remove(parameter.uid)

        parameters.sort()
        return parameters

    def get_unused_telecommands(self):
        """
        Get all telecommands which are not referenced by an application.
        """
        telecommands = list(self.model.telecommands.keys())
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for telecommand_mapping in application.get_telecommands():
                    if telecommand_mapping.telecommand.uid in telecommands:
                        telecommands.remove(telecommand_mapping.telecommand.uid)
        telecommands.sort()
        return telecommands

    def get_unused_telemetries(self):
        """
        Get all telemetry packets which are not referenced by an application.
        """
        telemetries = list(self.model.telemetries.keys())
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for telemetry_mapping in application.get_telemetries():
                    if telemetry_mapping.telemetry.uid in telemetries:
                        telemetries.remove(telemetry_mapping.telemetry.uid)
        telemetries.sort()
        return telemetries

    def get_ambiguous_telemetry_packets(self):
        """
        Get all ambiguous telemetry packets.

        Find telemetry packets which are not uniquely defined through
        APID, service type, service sub-type and the up to two additional
        identification fields.

        Returns a list of ambiguous tuples of telemetry packets.
        """
        ambiguous = []
        # tuple -> list of tm packets
        tm = {}
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for telemetry_mapping in application.get_telemetries():
                    telemetry = telemetry_mapping.telemetry
                    identifier = (application.apid, telemetry.service_type, telemetry.service_subtype)

                    others = tm.get(identifier, [])
                    for other in others:
                        if len(other.identification_parameter) == \
                           len(telemetry.identification_parameter):
                            for i1, i2 in zip(other.identification_parameter,
                                              telemetry.identification_parameter):
                                if i1.parameter.uid != i2.parameter.uid or i1.value == i2.value:
                                    break
                            else:
                                # Both lists are different
                                continue

                        ambiguous.append((other, telemetry))

                    others.append(telemetry)
                    tm[identifier] = others
        return ambiguous

    def get_ambiguous_packet_mappings(self):
        """
        Get all packets (TM or TC) which use the same SID.
        """
        packets = {}
        ambiguous = []

        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for mapping in application.get_telemetries():
                    p = packets.get(mapping.sid)
                    if p is not None:
                        ambiguous.append((mapping.sid, p, mapping.telemetry))
                    else:
                        packets[mapping.sid] = mapping.telemetry

                    for parameter_mapping in mapping.parameters:
                        p = packets.get(parameter_mapping.sid)
                        if p is not None:
                            if p.uid != parameter_mapping.parameter.uid:
                                ambiguous.append((parameter_mapping.sid, p,
                                                  parameter_mapping.parameter))
                        else:
                            packets[parameter_mapping.sid] = parameter_mapping.parameter

                for mapping in application.get_telecommands():
                    p = packets.get(mapping.sid)
                    if p is not None:
                        ambiguous.append((mapping.sid, p, mapping.telecommand))
                    else:
                        packets[mapping.sid] = mapping.telecommand

        return ambiguous

    def get_ambiguous_telemetry_parameters_within_mapping(self):
        """
        Find all telemetry parameters within a packet that use the same
        identifier.

        The same identifier is allow in different packets, but not within
        the same packet.
        """
        ambiguous = []

        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for mapping in application.get_telemetries():
                    parameters = {}

                    for parameter_mapping in mapping.parameters:
                        sid = parameter_mapping.sid
                        if sid in parameters:
                            ambiguous.append((mapping.sid, sid))
                        else:
                            parameters[sid] = parameter_mapping

        return ambiguous

    def get_ambiguous_telemetry_service_identifier(self):
        """
        Check that all telemetry generated from an application either
        have a unique combination of service and sub-service id or a parameter
        identification tag.
        """
        ambiguous = []

        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                ids = {}
                for mapping in application.get_telemetries():
                    identification = {
                        "__service_type": mapping.telemetry.service_type,
                        "__service_subtype": mapping.telemetry.service_subtype,
                    }

                    for p in mapping.telemetry.identification_parameter:
                        identification[p.parameter.uid] = p.value

                    entry = {
                        "apid": application.apid,
                        "mapping": mapping,
                        "identification": identification,
                    }

                    key = hash(frozenset(identification.items()))
                    t = ids.get(key, None)
                    if t is None:
                        ids[key] = entry
                    else:
                        if not t in ambiguous:
                            ambiguous.append(t)
                        ambiguous.append(entry)

        return ambiguous

    def get_enumeration_with_non_unqiue_values(self):
        """
        Find enumerations with multiple entries that map to the same value.

        Returns:
            List of enumerations with non unique values.
        """
        enumerations = []
        for enumeration in self.model.enumerations.values():
            values = {}
            for entry in enumeration.entries:
                if entry.value in values:
                    enumerations.append(enumeration)
                    break
                else:
                    values[entry.value] = entry
        return enumerations
