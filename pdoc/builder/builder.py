#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import codecs

import jinja2

import time
import datetime
import textwrap


class BuilderException(Exception):
    pass


class Builder:

    def __init__(self, model):
        self.model = model
        
        self.globals = {
            'time': datetime.datetime.utcfromtimestamp(time.time()).isoformat(),
        }

    def _write(self, filename, data):
        # Create path if it does not exist
        directory = os.path.dirname(filename)
        if not os.path.isdir(directory):
            os.makedirs(directory)

        try:
            # write data
            with codecs.open(filename, 'w', 'utf8') as file:
                file.write(data)

            print("Generate '%s'" % filename)
        except OSError as e:
            error_message = "Could not write to file '%s': %s" % (filename, e)
            print(error_message, file=sys.stderr)
            sys.exit(1)

    def _template(self, filename, filters=None, alternateMarking=False):
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
            loader = jinja2.PackageLoader('pdoc', 'resources')
        else:
            #if not os.path.isabs(filename):
            #   relpath = os.path.dirname(os.path.abspath(__file__))
            #   path = os.path.join(relpath, path)
            path = os.path.dirname(filename)
            name = os.path.basename(filename)
            loader = jinja2.FileSystemLoader(path)

        if alternateMarking:
            environment = jinja2.Environment(
                block_start_string='<%',
                block_end_string='%>',
                variable_start_string='<<',
                variable_end_string='>>',
                comment_start_string='<#',
                comment_end_string='#>',

                line_statement_prefix='##',
                line_comment_prefix='###',

                # trim_blocks=True,
                # lstrip_blocks=True,

                loader=loader,
                undefined=jinja2.StrictUndefined,
                extensions=["jinja2.ext.loopcontrols"])
        else:
            environment = jinja2.Environment(
                # trim_blocks=True,
                # lstrip_blocks=True,

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
