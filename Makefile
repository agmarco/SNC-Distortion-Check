SHELL := /bin/bash
.SHELLFLAGS := -e
.SUFFIXES:
.DEFAULT:

BUILD_INFO: environment.yml
	conda install $<
	nbstripout --install
	git rev-parse HEAD > $@

tmp/%.mat: data/% | tmp
	./dicom2mat $@ $</*

tmp:
	mkdir -p $@


.PHONY: clean

clean:
	rm -rf tmp
