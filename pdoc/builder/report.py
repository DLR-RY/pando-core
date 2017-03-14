#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from . import builder

class ReportBuilder(builder.Builder):

    def __init__(self, model, template_file=None):
        builder.Builder.__init__(self, model)

        if template_file is None:
            template_file = '#svg.tpl'
        self.templateFile = template_file

    def generate(self, outpath):
#         applications = []
#         for subsystem in self.model.subsystems.values():
#             for application in subsystem.applications.values():
#                 applications.append((application.apid, application))
#
#         for application in sorted(applications):
#             application = application[1]
#             print(application.apid, application.name)
        total_tm_count = 0
        total_tm_generation_count = 0
        applications = []
        for subsystem in self.model.subsystems.values():
            for application in sorted(subsystem.applications.values(), key=lambda x: x.apid):
                print(application.apid, application.name)

                tm_count = 0
                tm_generation_count = 0
                for telemetryMapping in application.getTelemetries():
                    tm_count += 1

                    packet = telemetryMapping
                    if packet.packet_generation is not None:
                        tm_generation_count += 1
                    else:
                        print(">", packet.sid, packet.telemetry.uid)

                total_tm_count += tm_count
                total_tm_generation_count += tm_generation_count

        print()
        print("Total")
        print("- TM {} {}".format(total_tm_count, total_tm_generation_count))

        # for packet in self.model.telecommands.values():
        #   filename = os.path.join(outpath, "%s.svg" % packet.uid)
        #   self._write(filename, self.generatePacket(packet) + "\n")
