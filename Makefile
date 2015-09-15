
# Use auto discovery to find all unittests
test:
	@python3 -m unittest discover -p *test.py

test-verify:
	@./scripts/pdoc-verify -i test/resources/test.xml

test-images:
	@./scripts/pdoc-svg -i test/resources/test.xml --svg-path=build/images

test-latex:
	@./scripts/pdoc-latex -i test/resources/test.xml \
		--latex-path=build/latex \
		--latex-overview-target=overview.tex

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

