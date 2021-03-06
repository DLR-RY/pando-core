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
# - 2016, Annika Ofenloch (DLR RY-AVS)

"""
Internal representation of the packet format.

The model class can than be forwarded to the different builders to create
documentation from the internal representation.
"""

import datetime
import collections


class ModelException(Exception):
    pass


class Model:

    def __init__(self):

        # uid -> Telemetry
        self.telemetries = {}
        # uid -> Telecommand
        self.telecommands = {}

        # uid -> Enumeration
        self.enumerations = {}
        # uid -> Calibration
        self.calibrations = {}
        # uid -> Parameter
        self.parameters = {}

        # id -> Subsystem
        self.subsystems = {}

    def get_packets_by_packet_class(self, packet_class):
        packets = []
        for subsystem in self.subsystems.values():
            packets.extend(subsystem.get_packets_by_packet_class(packet_class))
        return packets

    def append_telemetry_packet(self, packet):
        self.telemetries[packet.uid] = packet

    def append_telecommand_packet(self, packet):
        self.telecommands[packet.uid] = packet

    def get_or_add_subsystem(self, subsystemId, name):
        try:
            subsystem = self.subsystems[subsystemId]
            if subsystem.name != name:
                raise ModelException("Different names ('%s' and '%s') for same subsystem id '%i' detected"
                                     % (subsystem.name, name, subsystemId))
        except KeyError:
            # Create new subsystem entry
            subsystem = Subsystem(subsystemId, name)
            self.subsystems[subsystemId] = subsystem
        return subsystem

    def get_subsystems(self):
        return self.subsystems


class ParameterType:

    BOOLEAN = 1
    ENUMERATION = 2
    UNSIGNED_INTEGER = 3
    SIGNED_INTEGER = 4

    # float and double
    REAL = 5
    OCTET_STRING = 7
    ASCII_STRING = 8
    ABSOLUTE_TIME = 9
    RELATIVE_TIME = 10

    def __init__(self, identifier, width):
        self.identifier = identifier
        self.width = width

    @staticmethod
    def type_to_string(identifier):
        return {
            1: "Boolean",
            2: "Enumeration",
            3: "Unsigned Integer",
            4: "Signed Integer",
            5: "Floating Point",
            7: "Octet String",
            8: "ASCII String",
            9: "Absolute Time CUC",
            10: "Relative Time CUC",
        }[identifier]

    def __str__(self):
        return ParameterType.type_to_string(self.identifier)


class EnumerationType(ParameterType):

    def __init__(self, width, enumeration):
        """
        enumeration:  Name of the enumeration
        """
        ParameterType.__init__(self,
                               identifier=ParameterType.ENUMERATION,
                               width=width)

        self.enumeration = enumeration


class ParameterValueRange:

    def __init__(self, minimum, maximum):
        self.min = minimum
        self.max = maximum


class ByteOrder:

    BIG_ENDIAN = 0
    LITTLE_ENDIAN = 1


class Parameter:

    NONE = 0
    DEFAULT = 1
    FIXED = 2
    RANGE = 3

    def __init__(self, name, uid, description, parameter_type):
        self.name = name
        self.uid = uid
        self.description = description

        # see ParameterCollection
        self.is_collection = False
        self.is_parameter = True

        # Name limited to 16 characters
        self.short_name = ""

        self.byte_order = ByteOrder.BIG_ENDIAN

        # -> ParameterType
        self.type = parameter_type

        self.value = None
        self.value_type = self.NONE
        # -> ParameterValueRange
        self.value_range = None

        # str[4]
        self.unit = ""

        # -> Calibration object
        self.calibration = None

        # -> Limits
        self.limits = None

    def __repr__(self):
        return self.uid


class ParameterCollection:
    """
    Base class for groups of parameters.

    Use in list and repeater parameters. Allows to calculate the nesting
    depth of the group.
    """
    def __init__(self):
        self.is_collection = True
        self.parameters = []
        self.depth = 0

    def append_parameter(self, parameter):
        self.parameters.append(parameter)

    def get_flattened_member_count(self):
        """
        Get the number of parameters belonging to this repeater.

        The parameters of sub-repeaters are also included.
        """
        count = 0
        for parameter in self.parameters:
            if parameter.is_parameter:
                count += 1

            if parameter.is_collection:
                count += parameter.get_flattened_member_count()
        return count

    def update_depth(self):
        self.depth = 1
        for parameter in self.parameters:
            if isinstance(parameter, Repeater):
                parameter.update_depth()
                self.depth = max(self.depth, parameter.depth + 1)


class List(ParameterCollection):
    def __init__(self, name, uid, description):
        ParameterCollection.__init__(self)

        self.is_parameter = False

        self.name = name
        self.uid = uid
        self.description = description


class Repeater(Parameter, ParameterCollection):

    def __init__(self, name, uid, description, parameter_type):
        Parameter.__init__(self, name, uid, description, parameter_type)
        ParameterCollection.__init__(self)


class PacketGeneration:

    def __init__(self, event=False, periodic=False, response=False):
        self.event = event
        self.periodic = periodic
        self.response = response

        self.periodic_interval = datetime.timedelta(0)

    def __eq__(self, other):
        same_type = (self.event == other.event
                     and self.periodic == other.periodic
                     and self.response == other.response)

        if same_type and self.periodic is True:
            if self.periodic_interval != other.periodic_interval:
                same_type = False

        return same_type

    def __repr__(self):
        response_string = "+Response" if self.response else ""
        if self.event is True:
            return "<PacketGeneration: Event{}>".format(response_string)
        elif self.periodic is True:
            return "<PacketGeneration: Periodic{}, Interval={}>" \
                   .format(response_string, self.periodic_interval)
        elif self.response is True:
            return "<PacketGeneration: Response>"
        else:
            return "<PacketGeneration: None>"


class EventPacketGeneration(PacketGeneration):

    def __init__(self, response=False):
        PacketGeneration.__init__(self, event=True, periodic=False, response=response)


class PeriodicPacketGeneration(PacketGeneration):

    def __init__(self, interval, response=False):
        """
        Periodic packet generation.

        Args:
            interval (datetime.timedelta): Interval in which the packets
                will be generated.
            response: Packet will be additionally be generated as a response
                to a direct request.
        """
        PacketGeneration.__init__(self, event=False, periodic=True, response=response)
        self.periodic_interval = interval


class ResponsePacketGeneration(PacketGeneration):
    """
    Packet will only be generated as a response.
    """
    def __init__(self):
        PacketGeneration.__init__(self, event=False, periodic=False, response=True)


class Packet:

    TELECOMMAND = 0
    TELEMETRY = 1
    EVENT = 2

    def __init__(self, name, uid, description, packet_type):
        self.name = name
        self.uid = uid
        self.description = description

        # Name limited to 12 characters
        self.short_name = ""

        self.service_type = None
        self.service_subtype = None

        # List of { 'name': ..., 'value': ... } pairs.
        self.designators = []

        # [('heading', 'text'), (..., ...), ...]
        self.additional = []

        self.parameters = []

        # Packet.TELECOMMAND, Packet.TELEMETRY or Packet.EVENT
        self.packet_type = packet_type
        self.packet_class = None

        # Maximum nested parameter depth
        self.depth = 0

        self.ancillary_data = None

    def append_parameter(self, parameter):
        self.parameters.append(parameter)

    def get_parameters(self):
        return self.parameters

    def get_parameters_as_flattened_list(self):
        """ Returns all parameters as a flat list.

        Removes the nesting of repeaters. Repeater parameters still contain their
        embedded parameters.
        """
        parameters = []

        def handle_list(collection):
            for p in collection.parameters:
                handle_parameter(p)

        def handle_parameter(parameter):
            if parameter.is_parameter:
                parameters.append(parameter)

            if parameter.is_collection:
                handle_list(parameter)

        for p in self.parameters:
            handle_parameter(p)

        return parameters

    def update_depth(self):
        self.depth = 1
        for parameter in self.parameters:
            if parameter.is_collection:
                parameter.update_depth()
                self.depth = max(self.depth, parameter.depth + 1)

    def get_accumulated_parameter_length(self):
        """
        Calculate the accumulated length of all parameters in bits.

        Return:
        The accumulated length in bits or 'None' if packet contains repeater
        parameters.
        """
        packet_size = 0
        for parameter in self.get_parameters_as_flattened_list():
            if parameter.is_collection or parameter.type.width == 0:
                packet_size = None
                break
            else:
                packet_size += parameter.type.width
        return packet_size

    def __repr__(self):
        return self.uid


class Verification:
    """
    Verification of the execution stages of the telecommand.

    Used service 1 (telecommand verification service) telemetry reports.
    A 'True' means that the corresponding telemetry report is
    generated on board of the spacecraft
    """
    def __init__(self):
        self.acceptance = True
        self.start = False
        self.progress = False
        self.completion = True


class Telecommand(Packet):

    def __init__(self, name, uid, description, packet_type=Packet.TELECOMMAND):
        Packet.__init__(self, name, uid, description, packet_type)

        self.verification = Verification()

        self.relevant_telemetry = []

        # Flag identifying the command 'criticality'.
        #  True  - if the command is critical (also referred to as hazardous).
        #  False - meaning non-critical.
        self.critical = False


class Telemetry(Packet):

    def __init__(self, name, uid, description, packet_type=Packet.TELEMETRY):
        Packet.__init__(self, name, uid, description, packet_type)

        # -> TelemetryIdentificationParameter
        self.identification_parameter = []

        # -> PacketGeneration
        self.packet_generation = None


class TelemetryIdentificationParameter:

    def __init__(self, parameter, value):
        self.parameter = parameter
        self.value = value

    def __repr__(self):
        return "%s: %s" % (self.parameter, self.value)


class Event(Telemetry):

    # These values also define the telemetry packet sub-type
    PROGRESS = 1
    LOW_SEVERITY = 2
    MEDIUM_SEVERITY = 3
    HIGH_SEVERITY = 4

    def __init__(self, name, uid, description):
        Telemetry.__init__(self, name, uid, description, Packet.EVENT)

        self.severity = None
        self.report_id = None

        self.event_parameters = []
        self.event_parameters_depth = []

    def append_event_parameter(self, parameter):
        self.event_parameters.append(parameter)

    def get_event_parameters(self):
        return self.event_parameters

    def get_event_parameters_as_flattened_list(self):
        """ Returns all parameters as a flat list.

        Removes the nesting of repeaters. Repeater parameters still contain their
        embedded parameters.
        """
        parameters = []

        def handle_list(collection):
            for p in collection.parameters:
                handle_parameter(p)

        def handle_parameter(parameter):
            if parameter.is_parameter:
                parameters.append(parameter)

            if parameter.is_collection:
                handle_list(parameter)

        for p in self.event_parameters:
            handle_parameter(p)

        return parameters

    def update_event_parameter_depth(self):
        self.depth = 1
        for parameter in self.event_parameters:
            if parameter.is_collection:
                parameter.update_depth()
                self.depth = max(self.depth, parameter.depth + 1)

    def __repr__(self):
        return self.uid


class Enumeration:

    def __init__(self, name, uid, width, description):
        self.name = name
        self.uid = uid
        self.description = description
        self.width = width

        self.short_name = None

        # -> EnumerationEntry
        self.entries = []

    def append_entry(self, entry):
        self.entries.append(entry)

    def get_entry_by_name(self, name):
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None


class Calibration:

    INTERPOLATION_TELECOMMAND = 0
    INTERPOLATION_TELEMETRY = 1
    POLYNOM = 2

    def __init__(self, type_, name, uid, description):
        self.type = type_
        self.name = name
        self.uid = uid
        self.description = description

        self.unit = ""


class Interpolation(Calibration):

    UNSIGNED_INTEGER = ParameterType.UNSIGNED_INTEGER
    SIGNED_INTEGER = ParameterType.SIGNED_INTEGER
    REAL = ParameterType.REAL

    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    def __init__(self, type_, name, uid, description):
        Calibration.__init__(self, type_, name, uid, description)

        self.input_type = None
        self.output_type = None
        self.extrapolate = True
        self.points = []

    def append_point(self, point):
        self.points.append(point)

    def typeFromParameterType(self, parameterType):
        if parameterType.identifier == ParameterType.UNSIGNED_INTEGER:
            t = self.UNSIGNED_INTEGER
        elif parameterType.identifier == ParameterType.SIGNED_INTEGER:
            t = self.SIGNED_INTEGER
        elif parameterType.identifier == ParameterType.REAL:
            t = self.REAL
        else:
            raise ModelException("Invalid input type '%s' for telemetry parameter " \
                                 "interpolation '%s'" % (parameterType, self.uid))
        return t


class Polynom(Calibration):

    def __init__(self, name, uid, description):
        Calibration.__init__(self, Calibration.POLYNOM, name, uid, description)

        self.a0 = 0.0
        self.a1 = 0.0
        self.a2 = 0.0
        self.a3 = 0.0
        self.a4 = 0.0


class EnumerationEntry:

    def __init__(self, name, value, description):
        self.name = name
        self.value = value
        self.description = description

        self.short_name = None


class Limits:

    # 'U' in MIB
    INPUT_RAW = 0
    # 'C' in MIB
    INPUT_CALIBRATED = 1

    def __init__(self, input_type, value_type, samples):
        self.input = input_type
        self.value_type = value_type
        self.samples = samples

        # -> Limit
        self.checks = []


class Check:

    SOFT_LIMIT = 0
    HARD_LIMIT = 1

    def __init__(self, limit_type, lower_limit, upper_limit, description):
        self.limit_type = limit_type

        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

        self.description = description

        self.validity_parameter_sid = None
        self.validity_parameter_value = None


class Subsystem:

    def __init__(self, identifier, name):
        self.identifier = identifier
        self.name = name

        # apid -> ApplicationMapping
        self.applications = {}

        # uid -> EnumerationMapping
        self.telecommand_enumerations = {}
        self.telemetry_enumerations = {}

        # uid -> CalibrationMappping
        self.telecommand_calibrations = {}
        self.telemetry_calibrations = {}

        # uid -> ParameterMapping
        self.telecommand_parameters = {}

        # string -> Telecommand-/TelemetryMapping
        self.packets_by_packet_class = collections.defaultdict(list)

    def get_packets_by_packet_class(self, packet_class):
        return self.packets_by_packet_class.get(packet_class, [])


class ApplicationMapping:

    def __init__(self, name, apid, description):
        self.name = name
        self.apid = apid
        self.description = description

        self.name_prefix = ""
        self.name_suffix = ""

        # -> TelemetryMapping
        self._telemetry = []
        # -> TelecommandMapping
        self._telecommand = []

    def append_telemetry(self, telemetry):
        self._telemetry.append(telemetry)

    def get_telemetries(self):
        return self._telemetry

    def get_telemetry_by_uid(self, uid):
        for t in self._telemetry:
            if t.telemetry.uid == uid:
                return t
        return None

    def get_telemetry_by_sid(self, sid):
        for t in self._telemetry:
            if t.sid == sid:
                return t
        return None

    def append_telecommand(self, telecommand):
        self._telecommand.append(telecommand)

    def get_telecommands(self):
        return self._telecommand

    def wrap_name(self, name):
        return self.name_prefix + name + self.name_suffix

    def __repr__(self):
        return str(self.apid)


class EnumerationMapping:
    def __init__(self, sid, enumeration, subsystem):
        self.sid = sid
        self.enumeration = enumeration
        self.subsystem = subsystem


class CalibrationMapping:
    def __init__(self, sid, calibration, subsystem):
        self.sid = sid
        self.calibration = calibration
        self.subsystem = subsystem


class TelemetryMapping:

    def __init__(self, sid, telemetry, packet_type=Packet.TELEMETRY):
        self.sid = sid
        self.telemetry = telemetry

        self.packet_type = packet_type
        self.packet_class = None

        # -> ParameterMapping
        self.parameters = []

        # -> PacketGeneration
        self.packet_generation = None

    def append_parameter(self, parameter):
        self.parameters.append(parameter)


class EventMapping(TelemetryMapping):
    def __init__(self, sid, telemetry):
        TelemetryMapping.__init__(self, sid, telemetry, Packet.EVENT)


class ParameterMapping:
    def __init__(self, sid, parameter):
        self.sid = sid
        self.parameter = parameter


class TelecommandMapping:
    """Maps a TC SID to an application and a telecommand structure.

    Needs a TelecommandDefinitionMapping instance for the given
    uid to get the SID of the parameters.
    """
    def __init__(self, sid, telecommand):
        self.sid = sid
        self.telecommand = telecommand

        self.packet_type = Packet.TELECOMMAND
        self.packet_class = None
