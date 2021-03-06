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

# Use auto discovery to find all unittests
test:
	@python3 -m unittest discover -p *test.py

coverage:
	@coverage3 run --source=pando -m unittest discover -p *test.py
	@coverage3 report
	@coverage3 html -d build/coverage

coverage-view:
	@xdg-open build/coverage/index.html

test-verify:
	@./scripts/pando-verify -i test/resources/test.xml

test-images:
	@./scripts/pando-svg -i test/resources/test.xml --svg-path=build/images

test-latex:
	@./scripts/pando-latex -i test/resources/test.xml \
		--latex-path=build/latex \
		--latex-overview-target=overview.tex

pylint-gui:
	@cd pando; pylint-gui

pylint-gui3:
	@cd pando; pylint-gui3

dist:
	@python3 setup.py sdist --formats=zip

BASENAME = pando
VERSION ?= ${shell cat latest_version.txt}-dev
FULLNAME = $(BASENAME)-$(VERSION)

zip:
	zip -r $(FULLNAME).zip pando __main__.py
	mkdir -p dist
	echo '#!/usr/bin/env python3' | cat - $(FULLNAME).zip > dist/$(FULLNAME).pyz
	chmod +x dist/$(FULLNAME).pyz
	$(RM) $(FULLNAME).zip

install:
	@python3 setup.py install --record uninstall.txt

install-user:
	@python3 setup.py install --user

# TODO: Also remove folder
uninstall:
	@cat uninstall.txt | xargs rm -rf
#rm -rf installed_files.txt

.PHONY : test dist install uninstall

