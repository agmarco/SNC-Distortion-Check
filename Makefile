SHELL := /bin/bash
.SUFFIXES:
.DEFAULT:

IN_ENV := . activate cirs &&

test_data := $(patsubst data/%,tmp/%.mat,$(wildcard data/*))

all: BUILD_INFO $(test_data)

BUILD_INFO: environment.yml
	conda env create --force --file $<
	$(IN_ENV) nbstripout --install --attributes .gitattributes
	git rev-parse HEAD > $@

tmp/%.mat: data/%
	$(IN_ENV) ./dicom2mat $@ $</*


.PHONY: clean freezedeps

clean:
	. deactivate && conda remove -y --name cirs --all
	git clean -fqx tmp
	rm BUILD_INFO

freezedeps:
	$(IN_ENV) conda env export | sed '/^prefix: /d' > environment.yml
