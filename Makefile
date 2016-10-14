SHELL := /bin/bash
.SHELLFLAGS := -e
.SUFFIXES:
.DEFAULT:

IN_ENV = . activate cirs &&

test_data := $(patsubst data/%,tmp/%.mat,$(wildcard data/*))

all: BUILD_INFO $(test_data)

BUILD_INFO: environment.yml
	conda env create --force --file $<
	$(IN_ENV) nbstripout --install --attributes .gitattributes
	git rev-parse HEAD > $@

tmp/%.mat: data/% | tmp
	./dicom2mat $@ $</*

tmp:
	mkdir -p $@


.PHONY: clean freezedeps

clean:
	. deactivate && conda remove -y --name cirs --all
	rm -rf tmp

freezedeps:
	$(IN_ENV) conda env export | sed '/^prefix: /d' > environment.yml
