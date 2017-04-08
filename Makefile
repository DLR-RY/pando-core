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
	@coverage run --source=pando -m unittest discover -p *test.py
	@coverage report
	@coverage html -d build/coverage

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

dist:
	@python3 setup.py sdist --formats=zip

install:
	@python3 setup.py install --record uninstall.txt

install-user:
	@python3 setup.py install --user

# TODO: Also remove folder
uninstall:
	@cat uninstall.txt | xargs rm -rf
#rm -rf installed_files.txt

.PHONY : test dist install uninstall

