#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdoc - Packet Documentation generator

Creates a lot of different documentation form a XML packet description.
"""

from . import model
from . import pkg
from . import parser
from . import builder

from .pkg import naturalkey

__all__ = ['model', 'pkg', 'parser', 'builder']

__author__ = "Fabian Greif"
__copyright__ = "Copyright 2015, German Aerospace Center (DLR)"
__credits__ = ["Fabian Greif"]
__license__ = "Simplified BSD License"
__version__ = "0.1"
__maintainer__ = "Fabian Greif"
__email__ = "fabian.greif@dlr.de"
__status__ = "Pre-Alpha"
