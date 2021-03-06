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

import math

from . import builder

import pando.model


class ReportBuilder(builder.Builder):

    MAX_NAME_LENGTH = 40

    def __init__(self, model, template_file=None):
        builder.Builder.__init__(self, model)

        if template_file is None:
            template_file = '#svg.tpl'
        self.template_file = template_file

    def generate(self, _):
        self.print_packet_statistics()
        self.print_housekeeping_rate()
        self.print_extended_housekeeping_length()

    def print_packet_statistics(self):
        total_tm_count = 0
        total_tm_generation_count = 0
        total_tm_parameter = 0
        total_tm_filterted_parameter = 0

        total_tc_count = 0
        for subsystem in self.model.subsystems.values():
            for application in sorted(subsystem.applications.values(), key=lambda x: x.apid):
                missing_packets = []

                tm_count = 0
                tm_generation_count = 0
                for telemetry_mapping in application.get_telemetries():
                    tm_count += 1

                    packet = telemetry_mapping
                    if packet.packet_generation is not None:
                        tm_generation_count += 1
                    else:
                        missing_packets.append(packet)

                    for parameter in packet.telemetry.get_parameters_as_flattened_list():
                        total_tm_parameter += 1

                        if not parameter.uid.startswith("s1_") and not parameter.uid.startswith("s5_") \
                                and not parameter.uid.startswith("s13_") \
                                and not parameter.uid == "s8_function_id":
                            # print(parameter.uid)
                            total_tm_filterted_parameter += 1

                if len(missing_packets) > 0:
                    print(application.apid, application.name)
                    for packet in missing_packets:
                        print(">", packet.sid, packet.telemetry.uid)

                total_tm_count += tm_count
                total_tm_generation_count += tm_generation_count

                tc_count = 0
                for _ in application.get_telecommands():
                    tc_count += 1

                total_tc_count += tc_count

        print()
        print("Total")
        print("- TM Packets {} {}".format(total_tm_count, total_tm_generation_count))
        print("- TM Parameter {} {}".format(total_tm_parameter, total_tm_filterted_parameter))
        print("- TC {}".format(total_tc_count))

    def print_housekeeping_rate(self):
        print()
        housekeeping_data_rate = 0
        housekeepings = sorted(self.model.get_packets_by_packet_class("Realtime"), key=lambda x: x.sid)
        for mapping in housekeepings:
            if mapping.packet_type == pando.model.Packet.TELECOMMAND:
                print("Invalid packet '{}'".format(mapping.sid))
                continue
            if mapping.packet_generation.periodic is False:
                continue

            packet = mapping.telemetry
            size = self._calculate_frame_size(packet)

            data_rate = (size * 8) / mapping.packet_generation.periodic_interval.total_seconds()
            housekeeping_data_rate += data_rate
            print("{}  {}  {:>5} byte  {:8.0f} bps".format(mapping.sid,
                                                           self._limit_length(packet.uid, self.MAX_NAME_LENGTH),
                                                           size,
                                                           math.ceil(data_rate)))
        print()
        print("Housekeeping data rate {:.3f} kbps".format(housekeeping_data_rate / 1000))

    def print_extended_housekeeping_length(self):
        print()
        extended_housekeeping_size = 0
        housekeepings = sorted(self.model.get_packets_by_packet_class("Extended Housekeeping"), key=lambda x: x.sid)
        for mapping in housekeepings:
            if mapping.packet_type == pando.model.Packet.TELECOMMAND:
                print("Invalid packet '{}'".format(mapping.sid))
                continue

            packet = mapping.telemetry
            size = self._calculate_frame_size(packet)
            extended_housekeeping_size += size
            print("{}  {}  {:>5} byte".format(mapping.sid,
                                              self._limit_length(packet.uid, self.MAX_NAME_LENGTH),
                                              size))
        print()
        print("Extended housekeeping size {:.3f} kB".format(extended_housekeeping_size / 1000))

    @staticmethod
    def _limit_length(text, max_length):
        text_limited = text[:max_length - 1]
        if len(text_limited) == max_length - 1:
            text_limited += "~"
        return "{0:{1}}".format(text_limited, max_length)

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

    @staticmethod
    def _get_frame_overheade(packet_size):
        frame_overhead = 16
        frame_application_data_length = 1028
        frame_uncertainty = 20

        size = (frame_overhead * packet_size) / frame_application_data_length \
                + frame_uncertainty
        return int(math.ceil(size))
