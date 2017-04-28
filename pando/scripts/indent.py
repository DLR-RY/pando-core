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

import re


def main(argv):
    filename = argv[0]
    pattern = '(description|purpose|recommendation)'

    with open(filename) as file:
        indent = None
        next_indent = None
        for line in file:
            match = re.match('^(\s*)<%s>' % pattern, line)
            if match:
                indent = match.group(1)
                next_indent = indent
                if re.search('</%s>' % pattern, line):
                    indent = None
                    next_indent = None
            elif re.search('</%s>' % pattern, line):
                next_indent = None

            if indent is not None:
                if re.search('%s>' % pattern, line):
                    line = ''.join([indent, line.strip()])
                else:
                    line = ''.join([indent, "  ", line.strip()])
            else:
                line = line.rstrip()

            indent = next_indent
            print(line)
