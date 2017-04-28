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

import pando.builder.latex


def main(argv):
	arg = argparse.ArgumentParser(description='pando Packet Documentation Generator')
	arg.add_argument('-i', '--input', dest='input', required=True, help='XML packet description ')

	arg.add_argument('--latex-path', dest='latexpath', required=True, help='Output path for LaTex tables.')
	arg.add_argument('--latex-table-template', dest='latex_table_template', help='LaTex table template')
	arg.add_argument('--latex-image-path', dest='latex_imgpath', help='Path to the generated SVG images')

	arg.add_argument('--latex-enumeration-template', dest='latex_enumeration_template', help='LaTex enumeration template')

	arg.add_argument('--latex-overview-template', dest='latex_overview_template', help='Template for the LaTex packet overview')
	arg.add_argument('--latex-overview-target', dest='latex_overview_target', help='Output file for the LaTex overview')

	args = arg.parse_args(argv)

	parser = pando.parser.Parser()
	model = parser.parse(args.input)

	# Build LaTex tables
	builder = pando.builder.latex.TableBuilder(model,
	                                          args.latex_table_template,
	                                          args.latex_imgpath)
	builder.generate(args.latexpath)

	if len(model.enumerations) > 0:
		# Build enumeration definitions
		builder = pando.builder.latex.EnumerationBuilder(model.enumerations,
			                                            args.latex_enumeration_template)
		builder.generate(args.latexpath)

	if args.latex_overview_target is not None:
		builder = pando.builder.latex.OverviewBuilder(model,
			                                         args.latex_overview_template)
		builder.generate(args.latexpath, args.latex_overview_target)
