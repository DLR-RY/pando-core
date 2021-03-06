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

import os
import sys
import codecs
import time
import datetime
import logging
import textwrap

import jinja2


LOGGER = logging.getLogger("pando.builder")


class BuilderException(Exception):
    pass


class Builder:

    def __init__(self, model):
        self.model = model

        self.globals = {
            'time': datetime.datetime.utcfromtimestamp(time.time()).isoformat(),
        }

    @staticmethod
    def _write(filename, data):
        # Create path if it does not exist
        directory = os.path.dirname(filename)
        if not os.path.isdir(directory):
            os.makedirs(directory)

        try:
            # write data
            with codecs.open(filename, 'w', 'utf8') as file:
                file.write(data)

            LOGGER.info("Generate '%s'", filename)
        except OSError as e:
            error_message = "Could not write to file '%s': %s" % (filename, e)
            print(error_message, file=sys.stderr)
            sys.exit(1)

    def _template(self, filename, filters=None, alternate_marking=False):
        """ Open a template file

        """
        def filter_wordwrap(value, width=79):
            return '\n\n'.join([textwrap.fill(str, width) for str in value.split('\n\n')])

        def filter_indent(value, level=0, prefix=""):
            return ('\n' + '\t' * level + prefix).join(value.split('\n'))

        def global_abort_helper(msg):
            raise BuilderException(msg)

        if filename.startswith('#'):
            name = filename[1:]
            loader = jinja2.PackageLoader('pando', 'resources')
        else:
            # if not os.path.isabs(filename):
            #   relpath = os.path.dirname(os.path.abspath(__file__))
            #   path = os.path.join(relpath, path)
            path = os.path.dirname(filename)
            name = os.path.basename(filename)
            loader = jinja2.FileSystemLoader(path)

        if alternate_marking:
            environment = jinja2.Environment(
                block_start_string='<%',
                block_end_string='%>',
                variable_start_string='<<',
                variable_end_string='>>',
                comment_start_string='<#',
                comment_end_string='#>',

                line_statement_prefix='##',
                line_comment_prefix='###',

                loader=loader,
                undefined=jinja2.StrictUndefined,
                extensions=["jinja2.ext.loopcontrols"])
        else:
            environment = jinja2.Environment(
                line_statement_prefix='##',
                line_comment_prefix='###',

                loader=loader,
                undefined=jinja2.StrictUndefined,
                extensions=["jinja2.ext.loopcontrols"])
        environment.filters['xpcc.wordwrap'] = filter_wordwrap
        environment.filters['xpcc.indent'] = filter_indent

        environment.globals['abort'] = global_abort_helper
        if filters:
            environment.filters.update(filters)
        template = environment.get_template(name, globals=self.globals)
        return template
