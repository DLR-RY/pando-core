#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation of the internal structure of the model.
"""

import itertools

import pdoc.model

class ModelValidator:
    
    def __init__(self, model):
        self.model = model
    
    def getUnmappedTelecommandParameters(self):
        """
        Find the UID of all telecommand parameters that are referenced through
        a telecommand in an application but have no corresponding telecommand
        parameter mapping.

        Returns a list of Parameter() objects.
        """
        unmapped = []
        for subsystem in self.model.subsystems.values():
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
        for subsystem in self.model.subsystems.values():
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
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for telemetryMapping in application.getTelemetries():
                    telemetry = telemetryMapping.telemetry
                    # Check that all parameters are available
                    unresolved, additional = self.getUnmappedParameters(telemetry, telemetryMapping)
                    if len(unresolved) > 0 or len(additional) > 0:
                        unmapped.append((telemetry, unresolved, additional, application))
        return unmapped

    @staticmethod
    def getUnmappedParameters(packet, packetMapping):
        """
        Get the UID of parameters that are unused or additionally mapped.

        Returns two lists of (uid, positionInPacket)
        """
        unresolved = []
        additional = []

        packetParameters = packet.getParametersAsFlattenedList()
        position = 0
        for parameter, mapping in itertools.zip_longest(packetParameters,
                                                        packetMapping.parameters):
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

    def _get_used_enumerations_in_subsystem(self, subsystem):
        telemetry_enumerations = {}
        telecommand_enumerations = {}
        for application in subsystem.applications.values():
            for tm in application.getTelemetries():
                for p in tm.telemetry.getParametersAsFlattenedList():
                    if p.type.identifier == pdoc.model.ParameterType.ENUMERATION:
                        uid = p.type.enumeration
                        telemetry_enumerations[uid] = self.model.enumerations[uid]

            for tc in application.getTelecommands():
                for p in tc.telecommand.getParametersAsFlattenedList():
                    if p.type.identifier == pdoc.model.ParameterType.ENUMERATION:
                        uid = p.type.enumeration
                        telecommand_enumerations[uid] = self.model.enumerations[uid]

        return telemetry_enumerations, telecommand_enumerations
    
    def _get_used_calibrations_in_subsystem(self, subsystem):
        telemetry_calibrations = {}
        telecommand_calibrations = {}
        for application in subsystem.applications.values():
            for tm in application.getTelemetries():
                for p in tm.telemetry.getParametersAsFlattenedList():
                    calibration = p.calibration
                    if calibration is not None:
                        calibration = self.model.calibrations[calibration.uid]
                        telemetry_calibrations[calibration.uid] = calibration

            for tc in application.getTelecommands():
                for p in tc.telecommand.getParametersAsFlattenedList():
                    calibration = p.calibration
                    if calibration is not None:
                        calibration = self.model.calibrations[calibration.uid]
                        telecommand_calibrations[p.calibration.uid] = calibration
        return telemetry_calibrations, telecommand_calibrations

    def getUnmappedEnumerations(self):
        unresolvedTm = []
        unresolvedTc = []
        additionalTm = []
        additionalTc = []
        
        for subsystem in self.model.subsystems.values():
            telemetry_enumerations, telecommand_enumerations = \
                self._get_used_enumerations_in_subsystem(subsystem)
            
            unresolvedTmSubsystem = telemetry_enumerations.copy()
            unresolvedTcSubsystem = telecommand_enumerations.copy()

            for m in subsystem.telemetryEnumerations.values():
                uid = m.enumeration.uid
                if uid not in telemetry_enumerations:
                    additionalTm.append(m)

                if uid in unresolvedTmSubsystem:
                    unresolvedTmSubsystem.pop(uid)

            for m in subsystem.telecommandEnumerations.values():
                uid = m.enumeration.uid
                if uid not in telecommand_enumerations:
                    additionalTc.append(m)

                if uid in unresolvedTcSubsystem:
                    unresolvedTcSubsystem.pop(uid)

            for u in unresolvedTmSubsystem.values():
                unresolvedTm.append((u, subsystem))
            for u in unresolvedTcSubsystem.values():
                unresolvedTc.append((u, subsystem))

        return (additionalTm, unresolvedTm, additionalTc, unresolvedTc)

    def getUnmappedCalibrations(self):
        unresolvedTm = []
        unresolvedTc = []
        additionalTm = []
        additionalTc = []

        for subsystem in self.model.subsystems.values():
            telemetry_calibrations, telecommand_calibrations = \
                self._get_used_calibrations_in_subsystem(subsystem)

            unresolvedTmSubsystem = telemetry_calibrations.copy()
            unresolvedTcSubsystem = telecommand_calibrations.copy()

            for m in subsystem.telemetryCalibrations.values():
                uid = m.calibration.uid
                if uid not in telemetry_calibrations:
                    additionalTm.append(m)

                if uid in unresolvedTmSubsystem:
                    unresolvedTmSubsystem.pop(uid)

            for m in subsystem.telecommandCalibrations.values():
                uid = m.calibration.uid
                if uid not in telecommand_calibrations:
                    additionalTc.append(m)

                if uid in unresolvedTcSubsystem:
                    unresolvedTcSubsystem.pop(uid)

            for u in unresolvedTmSubsystem.values():
                unresolvedTm.append((u, subsystem))
            for u in unresolvedTcSubsystem.values():
                unresolvedTc.append((u, subsystem))

        return (additionalTm, unresolvedTm, additionalTc, unresolvedTc)

    def getUnusedParameters(self):
        """
        Get all parameters which are not used in an TM or TC packet referenced
        by an application.
        """
        parameters = list(self.model.parameters.keys())
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for telemetryMapping in application.getTelemetries():
                    for parameterMapping in telemetryMapping.parameters:
                        if parameterMapping.parameter.uid in parameters:
                            parameters.remove(parameterMapping.parameter.uid)

                for telecommandMapping in application.getTelecommands():
                    for parameter in telecommandMapping.telecommand.getParametersAsFlattenedList():
                        if parameter.uid in parameters:
                            parameters.remove(parameter.uid)

        # Remove all list parameters
        for parameter in self.model.parameters.values():
            if isinstance(parameter, pdoc.model.List):
                parameters.remove(parameter.uid)

        parameters.sort()
        return parameters

    def getUnusedTelecommands(self):
        """
        Get all telecommands which are not referenced by an application.
        """
        telecommands = list(self.model.telecommands.keys())
        for subsystem in self.model.subsystems.values():
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
        telemetries = list(self.model.telemetries.keys())
        for subsystem in self.model.subsystems.values():
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
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for telemetryMapping in application.getTelemetries():
                    telemetry = telemetryMapping.telemetry
                    identifier = (application.apid, telemetry.serviceType, telemetry.serviceSubtype)

                    others = tm.get(identifier, [])
                    for other in others:
                        if len(other.identificationParameter) == \
                           len(telemetry.identificationParameter):
                            for i1, i2 in zip(other.identificationParameter,
                                              telemetry.identificationParameter):
                                if i1.parameter.uid != i2.parameter.uid or i1.value == i2.value:
                                    break
                            else:
                                # Both lists are different
                                continue

                        ambiguous.append((other, telemetry))

                    others.append(telemetry)
                    tm[identifier] = others
        return ambiguous

    def getAmbiguousPacketMappings(self):
        """
        Get all packets (TM or TC) which use the same SID.
        """
        packets = {}
        ambiguous = []

        for subsystem in self.model.subsystems.values():
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
                                ambiguous.append((parameterMapping.sid, p,
                                                  parameterMapping.parameter))
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

        for subsystem in self.model.subsystems.values():
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

        for subsystem in self.model.subsystems.values():
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
