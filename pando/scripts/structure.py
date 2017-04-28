#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, 2017, German Aerospace Center (DLR)
#
# This file is part of the development version of the pando library.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Authors:
# - 2015, 2017, Fabian Greif (DLR RY-AVS)

import logging
import argparse

import pando


logger = logging.getLogger('pando.model')

def main():
	arg = argparse.ArgumentParser(description='pando Mapping Verification')
	arg.add_argument('-i', '--input', dest='input', required=True, help='XML packet description ')
	arg.add_argument('-u', '--uid', dest='uid', required=True, help='Packet UID to be analyzed')

	args = arg.parse_args()

	parser = pando.parser.Parser()

	try:
		model = parser.parse(args.input)

		try:
			packet = model.telecommands[args.uid]
		except KeyError:
			try:
				packet = model.telemetries[args.uid]
			except KeyError:
				raise pando.parser.ParserException("Packet '%s' not found!" % args.uid)

		print()
		print("{} ({})".format(packet.name, packet.uid))
		print()

		print(" Byte |  Bit | Width | Short name           | Name")
		print("------|------|-------|----------------------|----------------------------")
		bitposition = 0
		for parameter in packet.getParametersAsFlattenedList():
			width = parameter.type.width

			print(" {:4d} | {:4d} | {:5d} | {:20s} | {}".format(bitposition // 8, bitposition, width, parameter.shortName, parameter.name))
			bitposition += width

			if (bitposition % 8 == 0):
				print("------|------|-------|----------------------|----------------------------")

	except (pando.parser.ParserException, pando.model.ModelException) as e:
		print("\nError: %s" % e)
		exit(1)
