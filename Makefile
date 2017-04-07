
# Use auto discovery to find all unittests
test:
	@python3 -m unittest discover -p *test.py

coverage:
	@coverage run --source=pando -m unittest discover -p *test.py
	@coverage report
	@coverage html -d build/coverage

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

