
import re
import os
import itertools

from .. import model

from . import builder

def keynat(string):
    """
    A natural sort helper function for sort() and sorted()
    without using regular expression.

    >>> items = ('Z', 'a', '10', '1', '9')
    >>> sorted(items)
    ['1', '10', '9', 'Z', 'a']
    >>> sorted(items, key=keynat)
    ['1', '9', '10', 'Z', 'a']
    """
    r = []
    for c in string:
        try:
            c = int(c)
            try:
                r[-1] = r[-1] * 10 + c
            except:
                r.append(c)
        except:
            r.append(ord(c))
    return r

class Assistant(builder.Builder):
    
    def __init__(self, model, templateFile=None):
        builder.Builder.__init__(self, model)
        
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
    
    def _getPartialSuggestion(self, packet, packetMapping):
        unresolved, additional = self.model.getUnmappedParameters(packet, packetMapping)
        if len(unresolved) > 0 or len(additional) > 0:
            parameters = []
            lastSid = ""
            for parameter, mapping in itertools.zip_longest(packet.getParametersAsFlattenedList(), packetMapping.parameters):
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
        unmappedParameters = self.model.getUnmappedTelecommandParameters()
        parameters = [x.uid for x in unmappedParameters]
        
        # Find all telemetry packets with a partial mapping
        telemetries = []
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                for packetMapping in application.getTelemetries():
                    packet = packetMapping.telemetry
                    suggestion = self._getPartialSuggestion(packet, packetMapping)
                    if suggestion:
                        suggestion["apid"] = application.apid
                        suggestion["name"] = application.name
                        telemetries.append(suggestion)
        
        substitutions = {
            "parameters": sorted(parameters, key=keynat),
            "telemetries": sorted(telemetries, key=lambda p: keynat(p["uid"])),
        }
        
        template = self._template(self.templateFile)
        print(template.render(substitutions))

    def printSuggestionsForUnusedPackets(self):
        parameters = self.model.getUnusedParameters()
        
        telemetries = []
        unusedTelemetries = self.model.getUnusedTelemetries()
        if len(unusedTelemetries) > 0:
            for uid in unusedTelemetries:
                packet = self.model.telemetries[uid]
                telemetries.append(self._getSuggestion(packet))
        
        telecommands = []
        unusedTelecommands = self.model.getUnusedTelecommands()
        if len(unusedTelecommands) > 0:
            for uid in unusedTelecommands:
                packet = self.model.telecommands[uid]
                telecommands.append(self._getSuggestion(packet))
        
        substitutions = {
            "parameters": sorted(parameters, key=keynat),
            "telecommands": sorted(telecommands, key=lambda p: keynat(p["uid"])),
            "telemetries": sorted(telemetries, key=lambda p: keynat(p["uid"])),
        }
        
        template = self._template(self.templateFile)
        print(template.render(substitutions))
