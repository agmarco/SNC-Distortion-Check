SHELL := /bin/bash
.SHELLFLAGS := -e
.SUFFIXES:
.DEFAULT:

IN_ENV = . activate cirs &&


BUILD_INFO: environment.yml
	conda env create --force --file $<
	$(IN_ENV) nbstripout --install
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
