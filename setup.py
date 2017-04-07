#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='pando',
    packages=['pando', 'pando.builder'],
    package_dir={'pando': 'pando'},
    package_data={'pando': ['resources/*']},
    requires=['lxml', 'jinja2', 'isodate'],
    scripts=['scripts/pando'],
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
