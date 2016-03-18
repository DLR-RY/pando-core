#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pkgutil

import urllib.request
import urllib.parse

def get_filename(package, resource):
    """Rewrite of pkgutil.get_data() that return the file path.
    """
    loader = pkgutil.get_loader(package)
    if loader is None or not hasattr(loader, 'get_data'):
        return None
    mod = sys.modules.get(package) or loader.load_module(package)
    if mod is None or not hasattr(mod, '__file__'):
        return None

    # Modify the resource name to be compatible with the loader.get_data
    # signature - an os.path format "filename" starting with the dirname of
    # the package's __file__
    parts = resource.split('/')
    parts.insert(0, os.path.dirname(mod.__file__))
    resource_name = os.path.normpath(os.path.join(*parts))
    
    return resource_name

catalogfile = get_filename('pdoc', 'resources/catalog.xml')
os.environ['XML_CATALOG_FILES'] = urllib.parse.urljoin('file:', urllib.request.pathname2url(catalogfile))
