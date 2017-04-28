#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015-2017, German Aerospace Center (DLR)
#
# This file is part of the development version of the pando library.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Authors:
# - 2015-2017, Fabian Greif (DLR RY-AVS)

import argparse

import pando.builder.assistant

def main(argv):
	arg = argparse.ArgumentParser(description='pando Mapping suggestions based on missing packets and parameters')
	arg.add_argument('-i', '--input', dest='input', required=True, help='XML packet description ')
	arg.add_argument('-d', '--detailed',
					dest='detailed',
					default=False, action='store_true', required=False,
					help='Detailed analysis about all unused (without mapping) TM/TC packets and parameters.')
	args = arg.parse_args(argv)

	parser = pando.parser.Parser()

	try:
		model = parser.parse(args.input)

		assistant = pando.builder.assistant.Assistant(model)
		assistant.print_suggestions()
		if args.detailed:
			assistant.print_suggestions_for_unused_packets()
	except (pando.parser.ParserException, pando.model.ModelException) as e:
		print("\nError: %s" % e)
		exit(1)
