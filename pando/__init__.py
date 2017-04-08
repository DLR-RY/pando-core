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

"""
pando - Packet Network Documentation Model

Creates a lot of different documentation form a XML packet description.
"""

from . import model
from . import pkg
from . import parser
from . import builder

from .pkg import naturalkey

__all__ = ['model', 'pkg', 'parser', 'builder']

__author__ = "Fabian Greif"
__copyright__ = "Copyright (c), German Aerospace Center (DLR)"
__credits__ = ["Fabian Greif"]
__license__ = "Mozilla Public License v.2.0"
__version__ = "0.1"
__maintainer__ = "Fabian Greif"
__email__ = "fabian.greif@dlr.de"
__status__ = "Pre-Alpha"
