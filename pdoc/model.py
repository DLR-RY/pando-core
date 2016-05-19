#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools

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

        # uid -> Enumeration
        self.telecommandEnumerations = {}
        self.telemetryEnumerations = {}

        # uid -> Calibration
        self.telecommandCalibrations = {}
        self.telemetryCalibrations = {}

    def appendTelemetryPacket(self, packet):
        self.telemetries[packet.uid] = packet

    def appendTelecommandPacket(self, packet):
        self.telecommands[packet.uid] = packet

    def getOrAddSubsystem(self, subsystemId):
        try:
            return self.subsystems[subsystemId]
        except KeyError:
            # Create new subsystem entry
            subsystem = Subsystem(subsystemId)
            self.subsystems[subsystemId] = subsystem
            return subsystem

    def getSubsystems(self):
        return self.subsystems

    def getTelecommandEnumerationMapping(self, uid):
        for subsystem in self.subsystems.values():
            try:
                return subsystem.telecommandEnumerations[uid]
            except KeyError:
                pass
        else:
            raise ModelException("Could not find mapping for telecommand enumeration '%s'" % uid)

    def getTelemetryEnumerationMapping(self, uid):
        for subsystem in self.subsystems.values():
            try:
                return subsystem.telemetryEnumerations[uid]
            except KeyError:
                pass
        else:
            raise ModelException("Could not find mapping for telemetry enumeration '%s'" % uid)

    def getTelecommandCalibrationMapping(self, uid):
        for subsystem in self.subsystems.values():
            try:
                return subsystem.telecommandCalibrations[uid]
            except KeyError:
                pass
        else:
            raise ModelException("Could not find mapping for telecommand calibration '%s'" % uid)

    def getTelemetryCalibrationMapping(self, uid):
        for subsystem in self.subsystems.values():
            try:
                return subsystem.telemetryCalibrations[uid]
            except KeyError:
                pass
        else:
            raise ModelException("Could not find mapping for telemetry calibration '%s'" % uid)

    def getUnmappedTelecommandParameters(self):
        """
        Find the UID of all telecommand parameters that are referenced through
        a telecommand in an application but have no corresponding telecommand
        parameter mapping.

        Returns a list of Parameter() objects.
        """
        unmapped = []
        for subsystem in self.subsystems.values():
            for application in subsystem.applications.values():
                for telecommand in application.getTelecommands():
                    for parameter in telecommand.telecommand.getParametersAsFlattenedList():
                        if parameter.uid not in subsystem.telecommandParameters:
                            # Only add the parameter if it is not already
                            # in the list
                            for p in unmapped:
                                if p.uid == parameter.uid:
                                    break
                            else:
                                unmapped.append(parameter)
        return unmapped

    def getMappedButUnreferencedTelecommandParameter(self):
        """
        Find parameters that are used in TC parameter mapping but not
        referenced in any TC packet.

        Returns a list of Parameter() objects.
        """
        unreferenced = []
        for subsystem in self.subsystems.values():
            # Store the list of all parameters in the subsystem.
            # With the function getUnmappedTelecommandParameters() it is
            # checked that this is complete.
            parameters = subsystem.telecommandParameters.copy()

            # Remove all parameters which are used in any TC packet
            # of this subsystem
            for application in subsystem.applications.values():
                for telecommand in application.getTelecommands():
                    for parameter in telecommand.telecommand.getParametersAsFlattenedList():
                        if parameter.uid in parameters:
                            del parameters[parameter.uid]

            # Add all parameters which are still left to the list of
            # unreferenced parameters
            for p in parameters.values():
                unreferenced.append(p.parameter)

        return unreferenced


    def getUnmappedTelemetryParameters(self):
        """
        Returns a list of tuples of (Telemetry(), [uid], [uid], Application())
        """
        unmapped = []
        for subsystem in self.subsystems.values():
            for application in subsystem.applications.values():
                for telemetryMapping in application.getTelemetries():
                    telemetry = telemetryMapping.telemetry
                    # Check that all parameters are available
                    unresolved, additional = self.getUnmappedParameters(telemetry, telemetryMapping)
                    if len(unresolved) > 0 or len(additional) > 0:
                        unmapped.append((telemetry, unresolved, additional, application))
        return unmapped

    def getUnmappedParameters(self, packet, packetMapping):
        """
        Get the UID of parameters that are unused or additionally mapped.

        Returns two lists of (uid, positionInPacket)
        """
        unresolved = []
        additional = []

        packetParameters = packet.getParametersAsFlattenedList()
        position = 0
        for parameter, mapping in itertools.zip_longest(packetParameters, packetMapping.parameters):
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

    def getUnmappedEnumerations(self):
        unresolvedTc = self.telecommandEnumerations.copy()
        additionalTc = []
        for subsystem in self.subsystems.values():
            for m in subsystem.telecommandEnumerations.values():
                uid = m.enumeration.uid
                if uid not in self.telecommandEnumerations:
                    additionalTc.append(m)

                if uid in unresolvedTc:
                    unresolvedTc.pop(uid)

        unresolvedTm = self.telemetryEnumerations.copy()
        additionalTm = []
        for subsystem in self.subsystems.values():
            for m in subsystem.telemetryEnumerations.values():
                uid = m.enumeration.uid
                if uid not in self.telemetryEnumerations:
                    additionalTm.append(m)

                if uid in unresolvedTm:
                    unresolvedTm.pop(uid)

        return (additionalTc, unresolvedTc, additionalTm, unresolvedTm)

    def getUnmappedCalibrations(self):
        unresolvedTc = self.telecommandCalibrations.copy()
        additionalTc = []
        for subsystem in self.subsystems.values():
            for m in subsystem.telecommandCalibrations.values():
                uid = m.calibration.uid
                if uid not in self.telecommandCalibrations:
                    additionalTc.append(m)

                if uid in unresolvedTc:
                    unresolvedTc.pop(uid)

        unresolvedTm = self.telemetryCalibrations.copy()
        additionalTm = []
        for subsystem in self.subsystems.values():
            for m in subsystem.telemetryCalibrations.values():
                uid = m.calibration.uid
                if uid not in self.telemetryCalibrations:
                    additionalTm.append(m)

                if uid in unresolvedTm:
                    unresolvedTm.pop(uid)

        return (additionalTc, unresolvedTc, additionalTm, unresolvedTm)

    def getUnusedParameters(self):
        """
        Get all parameters which are not used in an TM or TC packet referenced
        by an application.
        """
        parameters = list(self.parameters.keys())
        for subsystem in self.subsystems.values():
            for application in subsystem.applications.values():
                for telemetryMapping in application.getTelemetries():
                    for parameterMapping in telemetryMapping.parameters:
                        if parameterMapping.parameter.uid in parameters:
                            parameters.remove(parameterMapping.parameter.uid)

                for telecommandMapping in application.getTelecommands():
                    for parameter in telecommandMapping.telecommand.getParametersAsFlattenedList():
                        if parameter.uid in parameters:
                            parameters.remove(parameter.uid)
        parameters.sort()
        return parameters

    def getUnusedTelecommands(self):
        """
        Get all telecommands which are not referenced by an application.
        """
        telecommands = list(self.telecommands.keys())
        for subsystem in self.subsystems.values():
            for application in subsystem.applications.values():
                for telecommandMapping in application.getTelecommands():
                    if telecommandMapping.telecommand.uid in telecommands:
                        telecommands.remove(telecommandMapping.telecommand.uid)
        telecommands.sort()
        return telecommands

    def getUnusedTelemetries(self):
        """
        Get all telemetry packets which are not referenced by an application.
        """
        telemetries = list(self.telemetries.keys())
        for subsystem in self.subsystems.values():
            for application in subsystem.applications.values():
                for telemetryMapping in application.getTelemetries():
                    if telemetryMapping.telemetry.uid in telemetries:
                        telemetries.remove(telemetryMapping.telemetry.uid)
        telemetries.sort()
        return telemetries

    def getAmbiguousTelemetryPackets(self):
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
        identifier = {}
        for subsystem in self.subsystems.values():
            for application in subsystem.applications.values():
                for telemetryMapping in application.getTelemetries():
                    telemetry = telemetryMapping.telemetry
                    id = (application.apid, telemetry.serviceType, telemetry.serviceSubtype)

                    others = tm.get(id, [])
                    for other in others:
                        if len(other.identificationParameter) == len(telemetry.identificationParameter):
                            for i1, i2 in zip(other.identificationParameter, telemetry.identificationParameter):
                                if i1.parameter.uid != i2.parameter.uid or i1.value == i2.value:
                                    break
                            else:
                                # Both lists are different
                                continue

                        ambiguous.append((other, telemetry))

                    others.append(telemetry)
                    tm[id] = others
        return ambiguous

    def getAmbiguousPacketMappings(self):
        """
        Get all packets (TM or TC) which use the same SID.
        """
        packets = {}
        ambiguous = []

        for subsystem in self.subsystems.values():
            for application in subsystem.applications.values():
                for mapping in application.getTelemetries():
                    p = packets.get(mapping.sid)
                    if p is not None:
                        ambiguous.append((mapping.sid, p, mapping.telemetry))
                    else:
                        packets[mapping.sid] = mapping.telemetry

                    for parameterMapping in mapping.parameters:
                        p = packets.get(parameterMapping.sid)
                        if p is not None:
                            if p.uid != parameterMapping.parameter.uid:
                                ambiguous.append((parameterMapping.sid, p, parameterMapping.parameter))
                        else:
                            packets[parameterMapping.sid] = parameterMapping.parameter

                for mapping in application.getTelecommands():
                    p = packets.get(mapping.sid)
                    if p is not None:
                        ambiguous.append((mapping.sid, p, mapping.telecommand))
                    else:
                        packets[mapping.sid] = mapping.telecommand

        return ambiguous

    def getAmbiguousTelemetryParametersWithinMapping(self):
        """
        Find all telemetry parameters within a packet that use the same
        identifier.

        The same identifier is allow in different packets, but not within
        the same packet.
        """
        ambiguous = []

        for subsystem in self.subsystems.values():
            for application in subsystem.applications.values():
                for mapping in application.getTelemetries():
                    parameters = {}

                    for parameterMapping in mapping.parameters:
                        sid = parameterMapping.sid
                        if sid in parameters:
                            ambiguous.append((mapping.sid, sid))
                        else:
                            parameters[sid] = parameterMapping

        return ambiguous

    def getAmbiguousTelemetryServiceIdentifier(self):
        """
        Check that all telemetry generated from an application either
        have a unique combination of service and sub-service id or a parameter
        identification tag.
        """
        ambiguous = []

        for subsystem in self.subsystems.values():
            for application in subsystem.applications.values():
                ids = {}
                for mapping in application.getTelemetries():
                    identification = {
                        "__service_type": mapping.telemetry.serviceType,
                        "__service_subtype": mapping.telemetry.serviceSubtype,
                    }

                    for p in mapping.telemetry.identificationParameter:
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

    def __init__(self, name, uid, description, parameterType):
        self.name = name
        self.uid = uid
        self.description = description

        # Name limited to 16 characters
        self.shortName = ""

        # -> ParameterType
        self.type = parameterType

        self.value = None
        self.valueType = self.NONE
        # -> ParameterValueRange
        self.valueRange = None

        # str[4]
        self.unit = ""

        # -> Calibration object
        self.calibration = None

    def __repr__(self):
        return self.uid


class Group(Parameter):

    def __init__(self, name, uid, description, parameterType):
        Parameter.__init__(self, name, uid, description, parameterType)

        self.parameters = []
        self.depth = 0

    def appendParameter(self, parameter):
        self.parameters.append(parameter)

    def getFlattenedGroupMemberCount(self):
        """
        Get the number of parameters belonging to this group.

        The parameters of subgroups are also included.
        """
        count = 0
        for parameter in self.parameters:
            count += 1
            if isinstance(parameter, Group):
                count += parameter.getFlattenedGroupMemberCount()
        return count

    def updateGroupDepth(self):
        if self.depth == 0:
            self.depth = 1
            for parameter in self.parameters:
                if isinstance(parameter, Group):
                    parameter.updateGroupDepth()
                    self.depth = max(self.depth, parameter.depth + 1)


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

        # Maximum nested group depth
        self.depth = 0

    def appendParameter(self, parameter):
        self.parameters.append(parameter)

    def getParametersAsFlattenedList(self):
        """ Returns all parameters as a flat list.

        Removes the nesting of groups. Group parameters still contain their
        embedded parameters.
        """
        parameters = []

        def handleGroup(group):
            for p in group.parameters:
                handleParameter(p)

        def handleParameter(parameter):
            parameters.append(parameter)
            if isinstance(parameter, Group):
                handleGroup(parameter)

        for p in self.parameters:
            handleParameter(p)

        return parameters

    def updateGroupDepth(self):
        if self.depth == 0:
            self.depth = 1
            for parameter in self.parameters:
                if isinstance(parameter, Group):
                    parameter.updateGroupDepth()
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
        self.value     = value

    def __repr__(self):
        return "%s: %s" % (self.parameter, self.value)

class Enumeration:

    def __init__(self, name, uid, width, description):
        self.name = name
        self.uid = uid
        self.description = description
        self.width = width

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

    def __init__(self, type, name, uid, description):
        self.type = type
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

    def __init__(self, type, name, uid, description):
        Calibration.__init__(self, type, name, uid, description)

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
            raise ParserException("Invalid input type '%s' for telemetry parameter " \
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

class Subsystem:

    def __init__(self, identifier):
        self.identifier = identifier

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
        self._telemetry   = []
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

    def __repr__(self):
        return str(self.apid)


class EnumerationMapping:
    def __init__(self, sid, enumeration):
        self.sid = sid
        self.enumeration = enumeration

class CalibrationMapping:
    def __init__(self, sid, calibration):
        self.sid = sid
        self.calibration = calibration

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
