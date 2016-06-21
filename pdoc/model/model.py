#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internal representation of the packet format.

The model class can than be forwarded to the different builders to create
documentation from the internal representation.
"""

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

    def appendTelemetryPacket(self, packet):
        self.telemetries[packet.uid] = packet

    def appendTelecommandPacket(self, packet):
        self.telecommands[packet.uid] = packet

    def getOrAddSubsystem(self, subsystemId, name):
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

    def getSubsystems(self):
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
    def typeToString(identifier):
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
        return ParameterType.typeToString(self.identifier)


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
        self.shortName = ""

        # -> ParameterType
        self.type = parameter_type

        self.value = None
        self.valueType = self.NONE
        # -> ParameterValueRange
        self.valueRange = None

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

    def appendParameter(self, parameter):
        self.parameters.append(parameter)

    def getFlattenedMemberCount(self):
        """
        Get the number of parameters belonging to this repeater.

        The parameters of sub-repeaters are also included.
        """
        count = 0
        for parameter in self.parameters:
            if parameter.is_parameter:
                count += 1

            if parameter.is_collection:
                count += parameter.getFlattenedMemberCount()
        return count

    def updateDepth(self):
        self.depth = 1
        for parameter in self.parameters:
            if isinstance(parameter, Repeater):
                parameter.updateDepth()
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


class Packet:

    def __init__(self, name, uid, description):
        self.name = name
        self.uid = uid
        self.description = description

        # Name limited to 12 characters
        self.shortName = ""

        self.serviceType = None
        self.serviceSubtype = None

        # List of { 'name': ..., 'value': ... } pairs.
        self.designators = []

        # [('heading', 'text'), (..., ...), ...]
        self.additional = []

        self.parameters = []

        # Maximum nested parameter depth
        self.depth = 0

    def appendParameter(self, parameter):
        self.parameters.append(parameter)

    def getParameters(self):
        return self.parameters

    def getParametersAsFlattenedList(self):
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

    def updateDepth(self):
        self.depth = 1
        for parameter in self.parameters:
            if parameter.is_collection:
                parameter.updateDepth()
                self.depth = max(self.depth, parameter.depth + 1)

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

    def __init__(self, name, uid, description):
        Packet.__init__(self, name, uid, description)

        self.verification = Verification()

        self.relevantTelemetry = []

        # Flag identifying the command 'criticality'.
        #  True  - if the command is critical (also referred to as hazardous).
        #  False - meaning non-critical.
        self.critical = False


class Telemetry(Packet):

    def __init__(self, name, uid, description):
        Packet.__init__(self, name, uid, description)

        # -> TelemetryIdentificationParameter
        self.identificationParameter = []


class TelemetryIdentificationParameter:

    def __init__(self, parameter, value):
        self.parameter = parameter
        self.value = value

    def __repr__(self):
        return "%s: %s" % (self.parameter, self.value)


class Enumeration:

    def __init__(self, name, uid, width, description):
        self.name = name
        self.uid = uid
        self.description = description
        self.width = width

        self.shortName = None

        # -> EnumerationEntry
        self.entries = []

    def appendEntry(self, entry):
        self.entries.append(entry)

    def getEntryByName(self, name):
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

        self.inputType = None
        self.outputType = None
        self.extrapolate = True
        self.points = []

    def appendPoint(self, point):
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

        self.shortName = None


class Limits:

    # 'U' in MIB
    INPUT_RAW = 0
    # 'C' in MIB
    INPUT_CALIBRATED = 1

    def __init__(self, input, samples):
        self.input = input
        self.samples = samples
        
        # -> Limit
        self.warnings = []
        self.errors = []


class Limit:

    def __init__(self, lower_limit, upper_limit, description):
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
        self.telecommandEnumerations = {}
        self.telemetryEnumerations = {}

        # uid -> CalibrationMappping
        self.telecommandCalibrations = {}
        self.telemetryCalibrations = {}

        # uid -> ParameterMapping
        self.telecommandParameters = {}


class ApplicationMapping:

    def __init__(self, name, apid, description):
        self.name = name
        self.apid = apid
        self.description = description

        self.namePrefix = ""
        self.nameSuffix = ""

        # -> TelemetryMapping
        self._telemetry = []
        # -> TelecommandMapping
        self._telecommand = []


    def appendTelemetry(self, telemetry):
        self._telemetry.append(telemetry)

    def getTelemetries(self):
        return self._telemetry

    def getTelemetryByUid(self, uid):
        for t in self._telemetry:
            if t.uid == uid:
                return t
        return None

    def getTelemetryBySid(self, sid):
        for t in self._telemetry:
            if t.sid == sid:
                return t
        return None

    def appendTelecommand(self, telecommand):
        self._telecommand.append(telecommand)

    def getTelecommands(self):
        return self._telecommand

    def wrap_name(self, name):
        return self.namePrefix + name + self.nameSuffix

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
    def __init__(self, sid, telemetry):
        self.sid = sid
        self.telemetry = telemetry

        # -> ParameterMapping
        self.parameters = []

    def appendParameter(self, parameter):
        self.parameters.append(parameter)


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
