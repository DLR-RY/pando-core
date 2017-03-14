#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='pdoc',
    packages=['pdoc', 'pdoc.builder'],
    package_dir={'pdoc': 'pdoc'},
    package_data={'pdoc': ['resources/*']},
    requires=['lxml', 'jinja2', 'isodate'],
    scripts=['scripts/pdoc'],
    version='0.1',
    description='Packet Documentation Generator',
    author='Fabian Greif',
    author_email='fabian.greif@dlr.de',
    url="http://www.dlr.de/",
    classifiers=[
    	"Programming Language :: Python",
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: BSD License",
		"Operating System :: OS Independent",
		"Development Status :: 2 - Pre-Alpha",
		"Intended Audience :: Developers",
		"Topic :: Documentation",
		"Topic :: Scientific/Engineering",
		"Topic :: Software Development :: Documentation",
		"Topic :: Software Development :: Embedded Systems",
	]
)
