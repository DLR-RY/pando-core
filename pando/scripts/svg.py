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

import pando.builder.svg

def main():
	arg = argparse.ArgumentParser(description='pando Packet Documentation Generator')
	arg.add_argument('-i', '--input', dest='input', required=True, help='XML packet description ')

	arg.add_argument('--svg-path', dest='svgpath', required=True, help='Output path for SVG images.')
	arg.add_argument('--svg-template', dest='svgtemplate', help='SVG image template')
	arg.add_argument('--svg-align', dest='svgalign', default=False, action='store_true', help='Left align the SVG images within the default width of 150mm.')

	args = arg.parse_args()

	parser = pando.parser.Parser()

	try:
		model = parser.parse(args.input)

		builder = pando.builder.svg.ImageBuilder(model,
		                                        args.svgtemplate,
		                                        args.svgalign)
		builder.generate(args.svgpath)
	except (pando.parser.ParserException, pando.model.ModelException) as e:
		print(e)
		exit(1)
