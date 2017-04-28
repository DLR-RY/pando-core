#!/usr/bin/env python3

import os
import re
import sys

filename = sys.argv[1]
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