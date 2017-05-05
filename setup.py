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

from distutils.core import setup

setup(
    name='pando',
    packages=['pando', 'pando.builder'],
    package_dir={'pando': 'pando'},
    package_data={'pando': ['resources/*']},
    requires=['lxml', 'jinja2', 'isodate'],
    scripts=['scripts/pando'],
    version=open("latest_version.txt").read().strip(),
    description='Packet Network Documentation Model',
    author='Fabian Greif',
    author_email='fabian.greif@dlr.de',
    url="http://www.dlr.de/",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Topic :: Documentation",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Embedded Systems",
    ]
)
