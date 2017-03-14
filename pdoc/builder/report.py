#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math

from . import builder

import pdoc.model

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
                missing_packets = []

                tm_count = 0
                tm_generation_count = 0
                for telemetryMapping in application.getTelemetries():
                    tm_count += 1

                    packet = telemetryMapping
                    if packet.packet_generation is not None:
                        tm_generation_count += 1
                    else:
                        missing_packets.append(packet)


                if len(missing_packets) > 0:
                    print(application.apid, application.name)
                    for packet in missing_packets:
                        print(">", packet.sid, packet.telemetry.uid)

                total_tm_count += tm_count
                total_tm_generation_count += tm_generation_count

        print()
        print("Total")
        print("- TM {} {}".format(total_tm_count, total_tm_generation_count))

        print()
        housekeeping_data_rate = 0
        housekeepings = self.model.get_packets_by_packet_class("Realtime")
        for mapping in housekeepings:
            if mapping.packet_type == pdoc.model.Packet.TELECOMMAND:
                print("Invalid packet '{}'".format(mapping.sid))
                continue
            if mapping.packet_generation.periodic is False:
                continue

            packet = mapping.telemetry
            size = self._calculate_frame_size(packet)

            data_rate = size / mapping.packet_generation.periodic_interval.total_seconds()
            housekeeping_data_rate += data_rate
            print(packet.uid, size, data_rate)
        print()
        print("Housekeeping data rate {:.3f} kbps".format(housekeeping_data_rate / 1000))

        print()
        extended_housekeeping_size = 0
        housekeepings = self.model.get_packets_by_packet_class("Extended Housekeeping")
        for mapping in housekeepings:
            if mapping.packet_type == pdoc.model.Packet.TELECOMMAND:
                print("Invalid packet '{}'".format(mapping.sid))
                continue

            packet = mapping.telemetry
            size = self._calculate_frame_size(packet)
            extended_housekeeping_size += size
            print(packet.uid, size)
        print()
        print("Extended housekeeping size {:.3f} kB".format(extended_housekeeping_size / 1000))

        # for packet in self.model.telecommands.values():
        #   filename = os.path.join(outpath, "%s.svg" % packet.uid)
        #   self._write(filename, self.generatePacket(packet) + "\n")

    def _calculate_frame_size(self, packet):
        """
        Calculate the size of a packet including a overhead factor for
        the frame.

        The frame overhead is not exact. If only one packet is send, a whole
        frame will be used, resulting in a much higher overhead. The factor
        is only valid if the frames are completely filled.
        """
        packet_header = 16
        parameter_length = packet.get_accumulated_parameter_length()
        if parameter_length is None:
            # FIXME move to ancillary data
            if packet.uid == "pl2_data_report":
                parameter_length = 1024 * 8
            elif packet.uid == "s190_10_logging_data_report":
                parameter_length = 1024 * 8
            else:
                print("Error in {}".format(packet.uid))
        packet_size = packet_header + parameter_length // 8
        size = packet_size + self._get_frame_overheade(packet_size)
        return size

    def _get_frame_overheade(self, packet_size):
        frame_overhead = 16
        frame_application_data_length = 1028
        frame_uncertainty = 20

        size = (frame_overhead * packet_size) / frame_application_data_length \
                + frame_uncertainty
        return int(math.ceil(size))
