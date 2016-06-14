#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools

from . import builder

import pdoc
import pdoc.model_validator

class Assistant(builder.Builder):
    
    def __init__(self, model, templateFile=None):
        builder.Builder.__init__(self, model)
        
        self.modelValidator = pdoc.model_validator.ModelValidator(model)

        if templateFile is None:
            templateFile = '#suggestions.tpl'
        self.templateFile = templateFile
    
    def _getSuggestion(self, packet):
        parameters = []
        for parameter in packet.getParametersAsFlattenedList():
            parameters.append({
                "uid": parameter.uid,
                "sid": "",
            })
        return {
            "uid": packet.uid,
            "parameters": parameters,
        }
    
    def _getPartialSuggestion(self, packet, packet_mapping):
        unresolved, additional = self.modelValidator.getUnmappedParameters(packet, packet_mapping)
        if len(unresolved) > 0 or len(additional) > 0:
            parameters = []
            lastSid = ""
            for parameter, mapping in itertools.zip_longest(packet.getParametersAsFlattenedList(), packet_mapping.parameters):
                if parameter is not None:
                    if lastSid != "":
                        sidProposition = lastSid[0:4] + "%04i" % (int(lastSid[4:].lstrip('0')) + 1)
                    else:
                        sidProposition = ""
                    sid = mapping.sid if mapping is not None else sidProposition
                    lastSid = sid
                    parameters.append({
                        "uid": parameter.uid,
                        "sid": sid,
                    })
            return {
                "uid": packet.uid,
                "parameters": parameters, 
            }
        else:
            return None
    
    def printSuggestions(self):
        # Find all telecommand parameters without a mapping
        unmappedParameters = self.modelValidator.getUnmappedTelecommandParameters()
        parameters = [x.uid for x in unmappedParameters]
        
        # Find all telemetry packets with a partial mapping
        telemetries = []
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for packet_mapping in application.getTelemetries():
                    packet = packet_mapping.telemetry
                    suggestion = self._getPartialSuggestion(packet, packet_mapping)
                    if suggestion:
                        suggestion["apid"] = application.apid
                        suggestion["name"] = application.name
                        telemetries.append(suggestion)
        
        substitutions = {
            "parameters": sorted(parameters, key=pdoc.naturalkey),
            "telemetries": sorted(telemetries, key=lambda p: pdoc.naturalkey(p["uid"])),
        }
        
        template = self._template(self.templateFile)
        print(template.render(substitutions))

    def printSuggestionsForUnusedPackets(self):
        parameters = self.modelValidator.getUnusedParameters()
        
        telemetries = []
        unusedTelemetries = self.modelValidator.getUnusedTelemetries()
        if len(unusedTelemetries) > 0:
            for uid in unusedTelemetries:
                packet = self.model.telemetries[uid]
                telemetries.append(self._getSuggestion(packet))
        
        telecommands = []
        unusedTelecommands = self.modelValidator.getUnusedTelecommands()
        if len(unusedTelecommands) > 0:
            for uid in unusedTelecommands:
                packet = self.model.telecommands[uid]
                telecommands.append(self._getSuggestion(packet))
        
        substitutions = {
            "parameters": sorted(parameters, key=pdoc.naturalkey),
            "telemetries": sorted(telemetries, key=lambda p: pdoc.naturalkey(p["uid"])),
            "telecommands": sorted(telecommands, key=lambda p: pdoc.naturalkey(p["uid"])),
        }
        
        template = self._template(self.templateFile)
        print(template.render(substitutions))
