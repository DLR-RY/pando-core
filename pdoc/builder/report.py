#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from . import builder

class ReportBuilder(builder.Builder):

    def __init__(self, model, templateFile=None):
        builder.Builder.__init__(self, model)

        if templateFile is None:
            templateFile = '#svg.tpl'
        self.templateFile = templateFile

    def generate(self, outpath):

        applications = []
        for subsystem in self.model.subsystems.values():
            for application in subsystem.applications.values():
                applications.append((application.apid, application))

        for application in sorted(applications):
            application = application[1]
            print(application.apid, application.name)

        # for packet in self.model.telemetries.values():
        #   filename = os.path.join(outpath, "%s.svg" % packet.uid)
        #   self._write(filename, self.generatePacket(packet) + "\n")
        #for packet in self.model.telecommands.values():
        #   filename = os.path.join(outpath, "%s.svg" % packet.uid)
        #   self._write(filename, self.generatePacket(packet) + "\n")
