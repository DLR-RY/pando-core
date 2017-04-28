#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, German Aerospace Center (DLR)
#
# This file is part of the development version of the pando library.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Authors:
# - 2017, Fabian Greif (DLR RY-AVS)

import argparse

import pando.scripts
from subprocess import SubprocessError

def main():
    arg = argparse.ArgumentParser(prog='pando',
                                  description='pando tool suite')

    subparsers = arg.add_subparsers()

    parser_assistant = subparsers.add_parser('assistant')
    parser_assistant.set_defaults(function=pando.scripts.assistant.main)

    parser_calibration = subparsers.add_parser('calibration_csv')
    parser_calibration.set_defaults(function=pando.scripts.calibration_csv.main)

    parser_indent = subparsers.add_parser('indent')
    parser_indent.set_defaults(function=pando.scripts.indent.main)

    parser_latex = subparsers.add_parser('latex')
    parser_latex.set_defaults(function=pando.scripts.latex.main)

    parser_structure = subparsers.add_parser('structure')
    parser_structure.set_defaults(function=pando.scripts.structure.main)

    parser_svg = subparsers.add_parser('svg')
    parser_svg.set_defaults(function=pando.scripts.svg.main)

    parser_verify = subparsers.add_parser('verify')
    parser_verify.set_defaults(function=pando.scripts.verify.main)

    args, remaining_args = arg.parse_known_args()

    if "function" not in args:
        # Print a help message if no command has been selected.
        arg.print_help()
    else:
        try:
            args.function(remaining_args)
        except (pando.parser.ParserException, pando.model.ModelException) as error:
            print("\nError: {}".format(error))
            exit(1)
